from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class BusinessCreate(BaseModel):
    company_name: str

class ChatMessage(BaseModel):
    message: str
    business_id: str
