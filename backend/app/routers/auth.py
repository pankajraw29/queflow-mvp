"""Business account auth: register / login / me."""
from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..auth import create_token, get_current_business, hash_password, verify_password
from ..db import get_db
from ..models import LoginIn, RegisterIn
from ..ratelimit import limiter
from ..utils import utcnow

router = APIRouter(prefix="/api/auth", tags=["auth"])


def business_out(biz: dict) -> dict:
    return {
        "id": str(biz["_id"]),
        "name": biz["name"],
        "email": biz["email"],
        "business_name": biz["business_name"],
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def register(data: RegisterIn, request: Request, db=Depends(get_db)):
    email = data.email.lower()
    if await db.businesses.find_one({"email": email}):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already registered")
    doc = {
        "name": data.name.strip(),
        "email": email,
        "password_hash": hash_password(data.password),
        "business_name": data.business_name.strip(),
        "created_at": utcnow(),
    }
    result = await db.businesses.insert_one(doc)
    doc["_id"] = result.inserted_id
    return {"access_token": create_token(str(result.inserted_id)), "business": business_out(doc)}


@router.post("/login")
@limiter.limit("30/minute")
async def login(data: LoginIn, request: Request, db=Depends(get_db)):
    biz = await db.businesses.find_one({"email": data.email.lower()})
    if not biz or not verify_password(data.password, biz["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    return {"access_token": create_token(str(biz["_id"])), "business": business_out(biz)}


@router.get("/me")
async def me(biz=Depends(get_current_business)):
    return business_out(biz)
