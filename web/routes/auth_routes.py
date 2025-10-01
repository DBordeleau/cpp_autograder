# Routing for /login, /register and /logout

from fastapi import APIRouter, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
from ..config import WEB_DIR
from ..auth import authenticate_user, create_access_token, hash_password
from ..database import SessionLocal, Users, Assignments, Submissions
from ..dependencies import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))

@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    user_id = get_current_user(request)
    
    if not user_id:
        return templates.TemplateResponse("login.html", {"request": request})
    
    db = SessionLocal()
    user = db.query(Users).filter(Users.user_id == user_id).first()
    
    if user and user.role == "admin":
        db.close()
        return RedirectResponse(url="/admin", status_code=302)
    
    all_assignments = db.query(Assignments).all()
    submissions = db.query(Submissions).filter(Submissions.user_id == user_id).all()
    db.close()
    
    submission_dict = {s.assignment_id: s for s in submissions}
    
    assignments = []
    for assignment in all_assignments:
        submission = submission_dict.get(assignment.assignment_id)
        
        # Check if overdue
        is_overdue = False
        if assignment.due_date:
            is_overdue = datetime.now().date() > assignment.due_date
        
        assignments.append({
            'assignment_id': assignment.assignment_id,
            'description': assignment.description,
            'due_date': assignment.due_date,
            'is_overdue': is_overdue,
            'has_submission': submission is not None,
            'grade': submission.grade if submission else 0
        })
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "student": user,
        "assignments": assignments
    })

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login(request: Request, user_id: str = Form(...), password: str = Form(...)):
    user = authenticate_user(user_id, password)
    
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid credentials"}
        )
    
    token = create_access_token(data={"sub": user_id})
    response = RedirectResponse(url="/admin" if user.role == "admin" else "/", status_code=302)
    response.set_cookie(key="access_token", value=token, httponly=True)
    
    return response

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
async def register(
    request: Request,
    student_id: str = Form(...),  # Changed from user_id to student_id
    name: str = Form(...),
    password: str = Form(...)
):
    db = SessionLocal()
    
    existing = db.query(Users).filter(Users.user_id == student_id).first()  # Use student_id
    if existing:
        db.close()
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "User ID already exists"}
        )
    
    new_user = Users(
        user_id=student_id,  # Use student_id
        name=name,
        password_hash=hash_password(password),
        role="student"
    )
    
    db.add(new_user)
    db.commit()
    db.close()
    
    return RedirectResponse(url="/login", status_code=302)

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response