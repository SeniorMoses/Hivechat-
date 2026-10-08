from pydantic import BaseModel, EmailStr, Field, field_validator
import re

class SignupRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, pas):
        if len(pas) < 8:
            raise ValueError(
            "password must be at least 8 characters"
            )
        if not re.search(r"[A-Z]", pas):
            raise ValueError(
            "password must contain an Upper case letter"
            )
        if not re.search(r"\d", pas):
            raise ValueError(
            "password must contain a digit" 
            )
        return pas


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    message:str
    access_token: str
    token_type: str


class MessageResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    content: str
    delivered: bool
    read: bool
