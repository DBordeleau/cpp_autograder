# Web dependency functions for user authentication and role-based access control

from fastapi import Request, HTTPException
from typing import Optional
from .auth import verify_token
from .database import SessionLocal, Users

def get_current_user(request: Request) -> Optional[str]:
    token = request.cookies.get("access_token")
    if not token:
        return None
    return verify_token(token)

def get_current_user_info(request: Request) -> Optional[Users]:
    user_id = get_current_user(request)
    if not user_id:
        return None
    
    db = SessionLocal()
    user = db.query(Users).filter(Users.user_id == user_id).first()
    db.close()
    return user

def require_auth(request: Request) -> str:
    user_id = get_current_user(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user_id

def require_admin(request: Request) -> str:
    user = get_current_user_info(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user.user_id

def require_student(request: Request) -> str:
    user = get_current_user_info(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Student access required")
    return user.user_id