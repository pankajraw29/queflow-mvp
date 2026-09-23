"""Owner-scoped queue management: CRUD + call-next / complete / skip / reset."""
import secrets

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo import ReturnDocument

from ..auth import get_current_business
from ..db import get_db
from ..models import QueueCreateIn, QueueUpdateIn
from ..utils import utcnow

router = APIRouter(prefix="/api/queues", tags=["queues"])


def _oid(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid id")


def queue_out(queue: dict, waiting_count: int = 0) -> dict:
    return {
        "id": str(queue["_id"]),
        "code": queue["code"],
        "name": queue["name"],
        "is_open": queue.get("is_open", True),
        "waiting_count": waiting_count,
        "created_at": queue.get("created_at"),
    }


def ticket_out(ticket: dict) -> dict:
    return {
        "id": str(ticket["_id"]),
        "number": ticket["number"],
        "seq": ticket["seq"],
        "customer_name": ticket["customer_name"],
        "status": ticket["status"],
        "created_at": ticket.get("created_at"),
    }


async def _owned_queue(queue_id: str, biz: dict, db) -> dict:
    queue = await db.queues.find_one({"_id": _oid(queue_id), "business_id": biz["_id"]})
    if not queue:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Queue not found")
    return queue


async def _new_code(db) -> str:
    # Short URL-safe code, e.g. "aB3_xQ"
    for _ in range(10):
        code = secrets.token_urlsafe(4)[:6]
        if not await db.queues.find_one({"code": code}):
            return code
    raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Could not generate queue code")


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_queue(data: QueueCreateIn, biz=Depends(get_current_business), db=Depends(get_db)):
    doc = {
        "code": await _new_code(db),
        "business_id": biz["_id"],
        "name": data.name.strip(),
        "is_open": True,
        "created_at": utcnow(),
    }
    result = await db.queues.insert_one(doc)
    doc["_id"] = result.inserted_id
    return queue_out(doc)


@router.get("")
async def list_queues(biz=Depends(get_current_business), db=Depends(get_db)):
    queues = await db.queues.find({"business_id": biz["_id"]}).sort("created_at", -1).to_list(200)
    out = []
    for q in queues:
        waiting = await db.tickets.count_documents({"queue_id": q["_id"], "status": "waiting"})
        out.append(queue_out(q, waiting))
    return out


@router.get("/{queue_id}")
async def get_queue(queue_id: str, biz=Depends(get_current_business), db=Depends(get_db)):
    queue = await _owned_queue(queue_id, biz, db)
    tickets = (
        await db.tickets.find(
            {"queue_id": queue["_id"], "status": {"$in": ["waiting", "serving"]}}
        )
        .sort("seq", 1)
        .to_list(500)
    )
    return {"queue": queue_out(queue), "tickets": [ticket_out(t) for t in tickets]}


@router.patch("/{queue_id}")
async def update_queue(
    queue_id: str, data: QueueUpdateIn, biz=Depends(get_current_business), db=Depends(get_db)
):
    queue = await _owned_queue(queue_id, biz, db)
    changes = {}
    if data.name is not None:
        changes["name"] = data.name.strip()
    if data.is_open is not None:
        changes["is_open"] = data.is_open
    if changes:
        await db.queues.update_one({"_id": queue["_id"]}, {"$set": changes})
        queue = await db.queues.find_one({"_id": queue["_id"]})
    return queue_out(queue)


@router.delete("/{queue_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_queue(queue_id: str, biz=Depends(get_current_business), db=Depends(get_db)):
    queue = await _owned_queue(queue_id, biz, db)
    await db.tickets.delete_many({"queue_id": queue["_id"]})
    await db.counters.delete_one({"_id": f"queue:{queue['_id']}"})
    await db.queues.delete_one({"_id": queue["_id"]})
    return None


@router.post("/{queue_id}/reset")
async def reset_queue(queue_id: str, biz=Depends(get_current_business), db=Depends(get_db)):
    """Clear all tickets and restart numbering from A01."""
    queue = await _owned_queue(queue_id, biz, db)
    await db.tickets.delete_many({"queue_id": queue["_id"]})
    await db.counters.delete_one({"_id": f"queue:{queue['_id']}"})
    return {"ok": True}


def _oldest(queue_id: ObjectId, db, statuses):
    return db.tickets.find({"queue_id": queue_id, "status": {"$in": statuses}}).sort("seq", 1)


@router.post("/{queue_id}/call-next")
async def call_next(queue_id: str, biz=Depends(get_current_business), db=Depends(get_db)):
    queue = await _owned_queue(queue_id, biz, db)
    serving = await _oldest(queue["_id"], db, ["serving"]).to_list(1)
    if serving:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Finish or skip the current ticket first"
        )
    waiting = await _oldest(queue["_id"], db, ["waiting"]).to_list(1)
    if not waiting:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No waiting tickets")
    ticket = waiting[0]
    await db.tickets.update_one(
        {"_id": ticket["_id"]}, {"$set": {"status": "serving", "called_at": utcnow()}}
    )
    ticket["status"] = "serving"
    return ticket_out(ticket)


@router.post("/{queue_id}/complete-current")
async def complete_current(queue_id: str, biz=Depends(get_current_business), db=Depends(get_db)):
    queue = await _owned_queue(queue_id, biz, db)
    serving = await _oldest(queue["_id"], db, ["serving"]).to_list(1)
    if not serving:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No ticket being served")
    ticket = serving[0]
    await db.tickets.update_one(
        {"_id": ticket["_id"]}, {"$set": {"status": "done", "finished_at": utcnow()}}
    )
    ticket["status"] = "done"
    return ticket_out(ticket)


@router.post("/{queue_id}/skip-current")
async def skip_current(queue_id: str, biz=Depends(get_current_business), db=Depends(get_db)):
    queue = await _owned_queue(queue_id, biz, db)
    serving = await _oldest(queue["_id"], db, ["serving"]).to_list(1)
    if not serving:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No ticket being served")
    ticket = serving[0]
    await db.tickets.update_one(
        {"_id": ticket["_id"]}, {"$set": {"status": "skipped", "finished_at": utcnow()}}
    )
    ticket["status"] = "skipped"
    return ticket_out(ticket)
