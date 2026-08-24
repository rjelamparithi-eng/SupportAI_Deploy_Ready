from fastapi import APIRouter, HTTPException, status
from app.models.schemas import UserRegister, UserLogin
from app.utils.security import hash_password, verify_password, create_access_token
from app.utils.database import get_database
from datetime import datetime

router = APIRouter()

@router.post("/register")
async def register(user: UserRegister):
    db = get_database()
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_doc = {
        "email": user.email,
        "name": user.name,
        "password": hash_password(user.password),
        "created_at": datetime.utcnow()
    }
    result = await db.users.insert_one(user_doc)
    token = create_access_token({"sub": str(result.inserted_id), "email": user.email})
    return {"access_token": token, "token_type": "bearer", "user": {"email": user.email, "name": user.name}}

@router.post("/login")
async def login(user: UserLogin):
    db = get_database()
    db_user = await db.users.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": str(db_user["_id"]), "email": user.email})
    return {"access_token": token, "token_type": "bearer", "user": {"email": user.email, "name": db_user.get("name", "")}}
