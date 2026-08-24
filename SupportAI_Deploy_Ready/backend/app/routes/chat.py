from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatMessage
from app.utils.database import get_database
from app.services.vector_store import query_chunks
from app.services.llm_service import generate_response, UNANSWERED_SENTINEL
from bson import ObjectId
from datetime import datetime

router = APIRouter()


@router.post("/message")
async def chat(msg: ChatMessage):
    db = get_database()

    try:
        business = await db.businesses.find_one({"_id": ObjectId(msg.business_id)})
    except Exception:
        raise HTTPException(status_code=404, detail="Business not found")

    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    if not business.get("trained", False):
        return {"response": "This chatbot hasn't been trained yet. Please contact the business owner."}

    company_name = business["company_name"]

    try:
        context_chunks = query_chunks(msg.business_id, msg.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vector search failed: {str(e)}")

    try:
        raw_response = generate_response(company_name, context_chunks, msg.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")

    # ── Detect unanswered via sentinel tag ────────────────────────────────────
    unanswered = UNANSWERED_SENTINEL in raw_response
    # Strip sentinel before returning to the user
    clean_response = raw_response.replace(UNANSWERED_SENTINEL, "").strip()

    # ── Save chat log ─────────────────────────────────────────────────────────
    try:
        await db.chat_logs.insert_one({
            "business_id": msg.business_id,
            "user_message": msg.message,
            "bot_response": clean_response,
            "unanswered": unanswered,
            "resolved": False,
            "created_at": datetime.utcnow(),
        })
    except Exception:
        pass  # Never fail the user-facing chat due to logging errors

    return {"response": clean_response}