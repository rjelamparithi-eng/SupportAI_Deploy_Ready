from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
from app.models.schemas import BusinessCreate
from app.utils.security import get_current_user
from app.utils.database import get_database
from app.services.document_processor import process_file, process_url
from app.services.vector_store import index_chunks
from bson import ObjectId
from datetime import datetime

router = APIRouter()


# ── Existing: Create Business ─────────────────────────────────────────────────

@router.post("/create")
async def create_business(business: BusinessCreate, current_user=Depends(get_current_user)):
    db = get_database()
    user_id = current_user["sub"]

    existing = await db.businesses.find_one({"user_id": user_id})
    if existing:
        await db.businesses.update_one(
            {"user_id": user_id},
            {"$set": {"company_name": business.company_name}}
        )
        updated = await db.businesses.find_one({"user_id": user_id})
        return {"business_id": str(updated["_id"]), "company_name": updated["company_name"]}

    doc = {
        "user_id": user_id,
        "company_name": business.company_name,
        "trained": False,
        "created_at": datetime.utcnow()
    }
    result = await db.businesses.insert_one(doc)
    return {"business_id": str(result.inserted_id), "company_name": business.company_name}


# ── Existing: Get My Business ─────────────────────────────────────────────────

@router.get("/me")
async def get_my_business(current_user=Depends(get_current_user)):
    db = get_database()
    business = await db.businesses.find_one({"user_id": current_user["sub"]})
    if not business:
        return None
    return {
        "business_id": str(business["_id"]),
        "company_name": business["company_name"],
        "trained": business.get("trained", False)
    }


# ── Existing: Train from File ─────────────────────────────────────────────────

@router.post("/train")
async def train_chatbot(
    file: UploadFile = File(...),
    business_id: str = Form(...),
    current_user=Depends(get_current_user)
):
    db = get_database()

    business = await db.businesses.find_one({"_id": ObjectId(business_id), "user_id": current_user["sub"]})
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    content = await file.read()

    try:
        chunks = process_file(file.filename, content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        index_chunks(business_id, chunks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to index document: {str(e)}")

    await db.businesses.update_one(
        {"_id": ObjectId(business_id)},
        {"$set": {"trained": True, "last_trained": datetime.utcnow(), "chunk_count": len(chunks)}}
    )

    return {
        "message": "Chatbot trained successfully!",
        "chunks_indexed": len(chunks),
        "business_id": business_id
    }


# ── Existing: Get Public Business ────────────────────────────────────────────

@router.get("/public/{business_id}")
async def get_business_public(business_id: str):
    db = get_database()
    try:
        business = await db.businesses.find_one({"_id": ObjectId(business_id)})
    except Exception:
        raise HTTPException(status_code=404, detail="Business not found")

    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    return {
        "business_id": str(business["_id"]),
        "company_name": business["company_name"],
        "trained": business.get("trained", False)
    }


# ── NEW: Train from URL (Web Scraping) ───────────────────────────────────────

class ScrapeTrainRequest(BaseModel):
    business_id: str
    url: str
    crawl: bool = False


@router.post("/train-from-url")
async def train_from_url(
    request: ScrapeTrainRequest,
    current_user=Depends(get_current_user)
):
    db = get_database()

    # Verify ownership — same pattern as /train
    try:
        business = await db.businesses.find_one({
            "_id": ObjectId(request.business_id),
            "user_id": current_user["sub"]
        })
    except Exception:
        raise HTTPException(status_code=404, detail="Business not found")

    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    # Scrape and chunk the website
    try:
        chunks = await process_url(request.url, request.crawl)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

    # Store embeddings in ChromaDB — same as /train
    try:
        index_chunks(request.business_id, chunks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to index content: {str(e)}")

    # Update MongoDB — same as /train
    await db.businesses.update_one(
        {"_id": ObjectId(request.business_id)},
        {"$set": {
            "trained": True,
            "last_trained": datetime.utcnow(),
            "chunk_count": len(chunks),
            "trained_from_url": request.url
        }}
    )

    return {
        "message": "Chatbot trained successfully from website!",
        "chunks_indexed": len(chunks),
        "business_id": request.business_id,
        "source_url": request.url
    }