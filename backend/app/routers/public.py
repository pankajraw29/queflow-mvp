"""Public (no login) endpoints: view queue, join, poll ticket status."""
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pymongo import ReturnDocument

from ..db import get_db
from ..models import JoinIn
from ..ratelimit import limiter
from ..utils import utcnow

router = APIRouter(prefix="/api/pub", tags=["public"])


async def _open_queue(code: str, db) -> dict:
    queue = await db.queues.find_one({"code": code})
    if not queue:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Queue not found")
    if not queue.get("is_open", True):
        raise HTTPException(status.HTTP_410_GONE, "This queue is closed")
    return queue


@router.get("/q/{code}")
@limiter.limit("60/minute")
async def queue_info(code: str, request: Request, db=Depends(get_db)):
    queue = await _open_queue(code, db)
    biz = await db.businesses.find_one({"_id": queue["business_id"]})
    waiting = await db.tickets.count_documents({"queue_id": queue["_id"], "status": "waiting"})
    return {
        "code": queue["code"],
        "queue_name": queue["name"],
        "business_name": biz["business_name"] if biz else "",
        "waiting_count": waiting,
    }


@router.post("/q/{code}/join", status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def join_queue(code: str, data: JoinIn, request: Request, db=Depends(get_db)):
    queue = await _open_queue(code, db)
    # Atomic per-queue counter -> A01, A02, ...
    counter = await db.counters.find_one_and_update(
        {"_id": f"queue:{queue['_id']}"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    seq = counter["seq"]
    ticket = {
        "queue_id": queue["_id"],
        "seq": seq,
        "number": f"A{seq:02d}",
        "customer_name": data.customer_name.strip(),
        "status": "waiting",
        "created_at": utcnow(),
    }
    result = await db.tickets.insert_one(ticket)
    ticket["_id"] = result.inserted_id
    # Position among waiting tickets (1 = next up)
    ahead = await db.tickets.count_documents(
        {"queue_id": queue["_id"], "status": "waiting", "seq": {"$lt": seq}}
    )
    return {
        "ticket_id": str(result.inserted_id),
        "number": ticket["number"],
        "position": ahead + 1,
        "queue_name": queue["name"],
    }


@router.get("/q/{code}/t/{ticket_id}")
@limiter.limit("60/minute")
async def ticket_status(code: str, ticket_id: str, request: Request, db=Depends(get_db)):
    queue = await db.queues.find_one({"code": code})
    if not queue:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Queue not found")
    try:
        tid = ObjectId(ticket_id)
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid ticket id")
    ticket = await db.tickets.find_one({"_id": tid, "queue_id": queue["_id"]})
    if not ticket:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ticket not found")
    ahead = 0
    if ticket["status"] == "waiting":
        ahead = await db.tickets.count_documents(
            {"queue_id": queue["_id"], "status": "waiting", "seq": {"$lt": ticket["seq"]}}
        )
    return {
        "number": ticket["number"],
        "status": ticket["status"],
        "ahead_count": ahead,
        "queue_name": queue["name"],
    }
