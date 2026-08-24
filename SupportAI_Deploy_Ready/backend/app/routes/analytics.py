from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.utils.security import get_current_user
from app.utils.database import get_database
from app.services.vector_store import index_admin_answer
from bson import ObjectId
from datetime import datetime, timedelta
import re

router = APIRouter()


# ─── Text Helpers ─────────────────────────────────────────────────────────────

def normalize_question(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def word_overlap_ratio(a: str, b: str) -> float:
    """Jaccard similarity ignoring stop words."""
    STOP = {"the", "a", "an", "is", "are", "was", "were", "i", "you", "we",
            "can", "could", "do", "does", "what", "how", "why", "when",
            "where", "tell", "me", "your", "my", "our", "about", "it"}
    wa = set(normalize_question(a).split()) - STOP
    wb = set(normalize_question(b).split()) - STOP
    if not wa or not wb:
        wa = set(normalize_question(a).split())
        wb = set(normalize_question(b).split())
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


def group_similar_questions(questions: list, threshold: float = 0.55) -> list:
    """
    Clusters a list of question strings by Jaccard similarity.
    Each occurrence is counted individually — so if the same question
    (or a near-duplicate) appears twice, count=2 but it shows as ONE group.
    Returns [{question, count, variants}] sorted by count desc.
    """
    groups = []

    for q in questions:
        norm_q = normalize_question(q)
        if not norm_q:
            continue

        matched = False
        for group in groups:
            if word_overlap_ratio(norm_q, group["norm"]) >= threshold:
                group["count"] += 1          # ← count every occurrence
                if q not in group["variants"]:
                    group["variants"].append(q)
                # keep the most descriptive phrasing as label
                if len(q) > len(group["representative"]):
                    group["representative"] = q
                matched = True
                break

        if not matched:
            groups.append({
                "representative": q,
                "norm": norm_q,
                "count": 1,
                "variants": [q],
            })

    groups.sort(key=lambda g: g["count"], reverse=True)
    return [
        {"question": g["representative"], "count": g["count"], "variants": g["variants"]}
        for g in groups
    ]


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/chat-history")
async def get_chat_history(
    search: str = "",
    current_user=Depends(get_current_user),
):
    """Returns chat logs. Optionally filters by `search` query param."""
    db = get_database()
    business = await db.businesses.find_one({"user_id": current_user["sub"]})
    if not business:
        return []

    business_id = str(business["_id"])

    query: dict = {"business_id": business_id}
    if search.strip():
        # Case-insensitive substring match on user message OR bot response
        pattern = {"$regex": re.escape(search.strip()), "$options": "i"}
        query["$or"] = [
            {"user_message": pattern},
            {"bot_response": pattern},
        ]

    cursor = db.chat_logs.find(query, sort=[("created_at", -1)], limit=200)
    logs = await cursor.to_list(length=200)

    return [
        {
            "id": str(log["_id"]),
            "user_message": log.get("user_message", ""),
            "bot_response": log.get("bot_response", ""),
            "unanswered": log.get("unanswered", False),
            "created_at": log["created_at"].isoformat() if log.get("created_at") else "",
        }
        for log in logs
    ]


@router.get("/analytics")
async def get_analytics(current_user=Depends(get_current_user)):
    db = get_database()
    business = await db.businesses.find_one({"user_id": current_user["sub"]})
    if not business:
        return {"total_chats": 0, "today_chats": 0, "unanswered_count": 0, "weekly_chats": []}

    business_id = str(business["_id"])
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total = await db.chat_logs.count_documents({"business_id": business_id})
    today = await db.chat_logs.count_documents({
        "business_id": business_id,
        "created_at": {"$gte": today_start},
    })

    # Unanswered count = number of GROUPS (not raw logs) so grouping is reflected
    raw_unanswered_cursor = db.chat_logs.find({
        "business_id": business_id,
        "unanswered": True,
        "resolved": {"$ne": True},
    })
    raw_unanswered = await raw_unanswered_cursor.to_list(length=2000)
    raw_questions = [log.get("user_message", "").strip() for log in raw_unanswered if log.get("user_message")]
    grouped_unanswered = group_similar_questions(raw_questions, threshold=0.55)
    unanswered_count = len(grouped_unanswered)

    weekly = []
    for i in range(7):
        day_start = today_start - timedelta(days=(6 - i))
        day_end = day_start + timedelta(days=1)
        count = await db.chat_logs.count_documents({
            "business_id": business_id,
            "created_at": {"$gte": day_start, "$lt": day_end},
        })
        weekly.append({"day": day_start.strftime("%a"), "date": day_start.strftime("%m/%d"), "count": count})

    return {
        "total_chats": total,
        "today_chats": today,
        "unanswered_count": unanswered_count,   # grouped count
        "weekly_chats": weekly,
    }


@router.get("/faq")
async def get_faq(current_user=Depends(get_current_user)):
    db = get_database()
    business = await db.businesses.find_one({"user_id": current_user["sub"]})
    if not business:
        return []

    business_id = str(business["_id"])
    cursor = db.chat_logs.find({"business_id": business_id, "unanswered": {"$ne": True}})
    logs = await cursor.to_list(length=2000)
    questions = [log.get("user_message", "").strip() for log in logs if log.get("user_message")]

    grouped = group_similar_questions(questions, threshold=0.55)
    return grouped[:15]


@router.get("/unanswered")
async def get_unanswered(current_user=Depends(get_current_user)):
    db = get_database()
    business = await db.businesses.find_one({"user_id": current_user["sub"]})
    if not business:
        return []

    business_id = str(business["_id"])
    cursor = db.chat_logs.find(
        {"business_id": business_id, "unanswered": True, "resolved": {"$ne": True}},
        sort=[("created_at", -1)],
    )
    logs = await cursor.to_list(length=500)

    # Group by NLP similarity — "tell about the founder" × 2 → ONE entry, count=2
    raw = [log.get("user_message", "").strip() for log in logs if log.get("user_message")]
    grouped = group_similar_questions(raw, threshold=0.55)

    result = []
    for g in grouped:
        rep_log = next(
            (log for log in logs if log.get("user_message", "").strip() in g["variants"]),
            None,
        )
        result.append({**g, "log_id": str(rep_log["_id"]) if rep_log else None})
    return result


class AdminAnswerRequest(BaseModel):
    question: str
    answer: str


@router.post("/admin-answer")
async def submit_admin_answer(
    body: AdminAnswerRequest,
    current_user=Depends(get_current_user),
):
    db = get_database()
    business = await db.businesses.find_one({"user_id": current_user["sub"]})
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    business_id = str(business["_id"])
    qa_text = f"Q: {body.question.strip()}\nA: {body.answer.strip()}"

    try:
        index_admin_answer(business_id, body.question.strip(), qa_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to index answer: {str(e)}")

    q_norm = normalize_question(body.question)
    await db.admin_answers.update_one(
        {"business_id": business_id, "question_norm": q_norm},
        {
            "$set": {
                "business_id": business_id,
                "question": body.question.strip(),
                "answer": body.answer.strip(),
                "qa_text": qa_text,
                "updated_at": datetime.utcnow(),
            },
            "$setOnInsert": {"created_at": datetime.utcnow()},
        },
        upsert=True,
    )

    # Resolve all matching unanswered logs (including similar phrasing variants)
    cursor = db.chat_logs.find({
        "business_id": business_id,
        "unanswered": True,
        "resolved": {"$ne": True},
    })
    all_logs = await cursor.to_list(length=2000)
    ids_to_resolve = [
        log["_id"] for log in all_logs
        if word_overlap_ratio(normalize_question(log.get("user_message", "")), q_norm) >= 0.55
    ]
    if ids_to_resolve:
        await db.chat_logs.update_many(
            {"_id": {"$in": ids_to_resolve}},
            {"$set": {"resolved": True}},
        )

    return {"message": "Answer indexed successfully"}