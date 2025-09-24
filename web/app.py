from fastapi import FastAPI, File, UploadFile, Request, HTTPException, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import subprocess
import os
import shutil
import tempfile
from pathlib import Path
import uuid
import re
from datetime import date, datetime, timedelta
from sqlalchemy import Column, String, Float, Date, create_engine, UniqueConstraint, Text, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
import json
import bcrypt
import jwt
from typing import Optional

# JWT settings
SECRET_KEY = "your-secret-key-change-this-in-production"  # NOT READY FOR PRODUCTION
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480 

BASE_DIR = Path(__file__).parent.parent
SUBMISSIONS_DIR = BASE_DIR / "submissions"
AUTOGRADER_DIR = BASE_DIR / "autograding_src"
DATA_DIR = BASE_DIR / "data"
WEB_DIR = Path(__file__).parent

# Database setup
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATA_DIR}/database.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Users(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True)  # Can be student_id or admin username
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="student")  # "student" or "admin"
    created_at = Column(DateTime, default=datetime.utcnow)

    submissions = relationship("Submissions", back_populates="user")

class Assignments(Base):
    __tablename__ = "assignments"

    assignment_id = Column(String, primary_key=True)
    description = Column(String)
    due_date = Column(Date)
    autograder = Column(String)  # autograder name

    submissions = relationship("Submissions", back_populates="assignment")

class Autograders(Base):
    __tablename__ = "autograders"

    name = Column(String, primary_key=True)
    outputs = Column(Text) 
    grade_weights = Column(Text)

class Tests(Base):
    __tablename__ = "tests"

    test_id = Column(String, primary_key=True)
    assignment_id = Column(String, ForeignKey('assignments.assignment_id'))
    input_data = Column(Text)

    assignment = relationship("Assignments")

class Submissions(Base):
    __tablename__ = "submissions"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.user_id'), nullable=False)
    assignment_id = Column(String, ForeignKey('assignments.assignment_id'), nullable=False)
    submission_time = Column(DateTime, default=datetime.utcnow)
    grade = Column(Float)
    
    __table_args__ = (
        UniqueConstraint('user_id', 'assignment_id', name='unique_user_assignment'),
    )

    user = relationship("Users", back_populates="submissions")
    assignment = relationship("Assignments", back_populates="submissions")
    
    def __init__(self, user_id, assignment_id, submission_time, grade):
        self.id = f"{user_id}_{assignment_id}"
        self.user_id = user_id 
        self.assignment_id = assignment_id
        self.submission_time = submission_time
        self.grade = grade

# Hash with bcrypt
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

# Verify password against hash
def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# Returns an encoded JWT token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Returns user_id if token is valid, else None
def verify_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        student_id: str = payload.get("sub")
        if student_id is None:
            return None
        return student_id
    except jwt.PyJWTError:
        return None

# Prompt user for a password for the admin account if it does not exist
def create_admin_if_not_exists():
    db = SessionLocal()
    
    existing_admin = db.query(Users).filter(Users.user_id == "admin").first()
    if existing_admin:
        db.close()
        print("Admin user already exists.")
        return
    
    print("\n" + "="*50)
    print("FIRST TIME SETUP - CREATE ADMIN ACCOUNT")
    print("="*50)
    print("No admin account found. Creating admin user...")
    
    import getpass
    while True:
        password = getpass.getpass("Enter password for admin user: ")
        if len(password) < 6:
            print("Password must be at least 6 characters long. Please try again.")
            continue
        
        confirm_password = getpass.getpass("Confirm password: ")
        if password != confirm_password:
            print("Passwords don't match. Please try again.")
            continue
        
        break
    
    hashed_password = hash_password(password)
    admin_user = Users(
        user_id="admin",
        name="System Administrator",
        password_hash=hashed_password,
        role="admin"
    )
    
    db.add(admin_user)
    db.commit()
    db.close()
    
    print("Admin user created successfully!")
    print("You can now login with username 'admin' and your chosen password.")
    print("="*50 + "\n")

# Main auth function for students and admin
def authenticate_user(user_id: str, password: str) -> Optional[Users]:
    db = SessionLocal()
    user = db.query(Users).filter(Users.user_id == user_id).first()
    db.close()
    
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

# Get user from cookie
def get_current_user(request: Request) -> Optional[str]:
    token = request.cookies.get("access_token")
    if not token:
        return None
    return verify_token(token)

# Returns user info if token is valid
def get_current_user_info(request: Request) -> Optional[Users]:
    user_id = get_current_user(request)
    if not user_id:
        return None
    
    db = SessionLocal()
    user = db.query(Users).filter(Users.user_id == user_id).first()
    db.close()
    return user

# Dependency to require auth
def require_auth(request: Request) -> str:
    user_id = get_current_user(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user_id

# Dependency to require admin role
def require_admin(request: Request) -> str:
    user = get_current_user_info(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user.user_id

# Dependency to require student role
def require_student(request: Request) -> str:
    user = get_current_user_info(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Student access required")
    return user.user_id

# Creates rows for objects defined in config.txt using the config_parser executable
def load_config_to_database():
    try:
        config_parser_path = AUTOGRADER_DIR / "config_parser"
        
        if not config_parser_path.exists():
            print("Config parser executable not found. Attempting to compile...")
            compile_result = subprocess.run(
                ["clang++", "-std=c++20", "-DCONFIG_PARSER_MAIN", "-o", "config_parser", "config.cpp", "date.cpp"],
                cwd=AUTOGRADER_DIR,
                capture_output=True,
                text=True
            )
            if compile_result.returncode != 0:
                print(f"Failed to compile config parser: {compile_result.stderr}")
                return False
        
        result = subprocess.run(
            [str(config_parser_path)],
            cwd=AUTOGRADER_DIR,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Config parser failed: {result.stderr}")
            return False
        
        try:
            config_data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            print(f"Failed to parse config JSON: {e}")
            return False
        
        db = SessionLocal()
        
        db.query(Tests).delete()
        db.query(Autograders).delete()
        db.query(Assignments).delete()
        
        for name, data in config_data.get("autograders", {}).items():
            autograder = Autograders(
                name=name,
                outputs=json.dumps(data["outputs"]),
                grade_weights=json.dumps(data["weights"])
            )
            db.add(autograder)
            print(f"Added autograder: {name}")
        
        for name, data in config_data.get("assignments", {}).items():
            assignment = Assignments(
                assignment_id=name,
                description=data["description"],
                due_date=date.fromisoformat(data["due_date"]) if data["due_date"] else None,
                autograder=data["autograder"]
            )
            db.add(assignment)
            print(f"Added assignment: {name}")
        
        for name, data in config_data.get("tests", {}).items():
            test = Tests(
                test_id=name,
                assignment_id=data["assignment"],
                input_data=json.dumps(data["inputs"])
            )
            db.add(test)
            print(f"Added test: {name}")
        
        db.commit()
        db.close()
        print("Successfully loaded config data to database")
        return True
        
    except Exception as e:
        print(f"Error loading config to database: {e}")
        return False

# Creates database if it does not exist and loads config data
def initialize_app():
    SUBMISSIONS_DIR.mkdir(exist_ok=True)
    DATA_DIR.mkdir(exist_ok=True)
    
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")
    
    load_config_to_database()

initialize_app()

app = FastAPI(title="C++ Autograder", description="Automatically grade C++ programming assignments.")

# Setup templates and static files
templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")

# Create admin if not exists on startup
@app.on_event("startup")
async def startup_event():
    create_admin_if_not_exists()

# auth routes
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, user_id: str = Form(...), password: str = Form(...)):
    user = authenticate_user(user_id, password)
    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "error": "Invalid user ID or password"
        })
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.user_id}, expires_delta=access_token_expires
    )
    
    # Redirect based on role
    redirect_url = "/admin" if user.role == "admin" else "/"
    response = RedirectResponse(url=redirect_url, status_code=302)
    response.set_cookie(
        key="access_token", 
        value=access_token, 
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=False  # Set to True in production with HTTPS
    )
    return response

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register(request: Request, student_id: str = Form(...), name: str = Form(...), password: str = Form(...)):
    # Validate input
    if len(student_id.strip()) == 0:
        return templates.TemplateResponse("register.html", {
            "request": request, 
            "error": "Student ID cannot be empty"
        })
    
    if len(name.strip()) == 0:
        return templates.TemplateResponse("register.html", {
            "request": request, 
            "error": "Name cannot be empty"
        })
    
    if len(password) < 6:
        return templates.TemplateResponse("register.html", {
            "request": request, 
            "error": "Password must be at least 6 characters long"
        })
    
    # Check if user already exists
    db = SessionLocal()
    existing_user = db.query(Users).filter(Users.user_id == student_id).first()
    if existing_user:
        db.close()
        return templates.TemplateResponse("register.html", {
            "request": request, 
            "error": "Student ID already exists"
        })
    
    # Create new student user
    hashed_password = hash_password(password)
    new_user = Users(
        user_id=student_id,
        name=name.strip(),
        password_hash=hashed_password,
        role="student"  # Always create as student
    )
    
    db.add(new_user)
    db.commit()
    db.close()
    
    return templates.TemplateResponse("register.html", {
        "request": request, 
        "success": "Account created successfully! You can now log in."
    })

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response

# Student routes (require student role)
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = get_current_user_info(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    if user.role == "admin":
        return RedirectResponse(url="/admin", status_code=302)
    
    db = SessionLocal()
    assignments = db.query(Assignments).all()
    
    submissions = db.query(Submissions).filter(Submissions.user_id == user.user_id).all()
    submission_grades = {sub.assignment_id: sub.grade for sub in submissions}
    
    db.close()
    
    assignments_with_grades = []
    today = date.today()
    
    for assignment in assignments:
        is_overdue = assignment.due_date and assignment.due_date < today
        
        assignment_data = {
            "assignment_id": assignment.assignment_id,
            "description": assignment.description,
            "due_date": assignment.due_date,
            "grade": submission_grades.get(assignment.assignment_id),
            "has_submission": assignment.assignment_id in submission_grades,
            "is_overdue": is_overdue
        }
        assignments_with_grades.append(assignment_data)
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "student": user,  # For compatibility with existing template
        "assignments": assignments_with_grades
    })

@app.get("/assignment/{assignment_id}", response_class=HTMLResponse)
async def assignment_page(request: Request, assignment_id: str):
    user = get_current_user_info(request)
    if not user or user.role != "student":
        return RedirectResponse(url="/login", status_code=302)
    
    db = SessionLocal()
    assignment = db.query(Assignments).filter(Assignments.assignment_id == assignment_id).first()
    
    if not assignment:
        db.close()
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    submission = db.query(Submissions).filter(
        Submissions.user_id == user.user_id,
        Submissions.assignment_id == assignment_id
    ).first()
    
    db.close()
    
    return templates.TemplateResponse("assignment.html", {
        "request": request,
        "student": user,
        "assignment": assignment,
        "submission": submission
    })

# Admin routes (require admin role)
@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    user = get_current_user_info(request)
    if not user or user.role != "admin":
        return RedirectResponse(url="/login", status_code=302)
    
    db = SessionLocal()
    
    try:
        total_students = db.query(Users).filter(Users.role == "student").count()
        total_assignments = db.query(Assignments).count()
        total_submissions = db.query(Submissions).count()
        
        recent_submissions_query = db.query(Submissions).join(Users).join(Assignments).order_by(
            Submissions.submission_time.desc()
        ).limit(10).all()
        
        recent_submissions = []
        for sub in recent_submissions_query:
            recent_submissions.append({
                "id": sub.id,
                "user_id": sub.user_id,
                "assignment_id": sub.assignment_id,
                "submission_time": sub.submission_time,
                "grade": sub.grade,
                "user_name": sub.user.name,  
                "assignment_description": sub.assignment.description  
            })
        
        students = db.query(Users).filter(Users.role == "student").all()
        student_stats = []
        for student in students:
            submission_count = db.query(Submissions).filter(Submissions.user_id == student.user_id).count()
            grades = db.query(Submissions.grade).filter(Submissions.user_id == student.user_id).all()
            grades = [g[0] for g in grades if g[0] is not None]
            avg_grade = sum(grades) / len(grades) if grades else 0
            
            student_stats.append({
                "user_id": student.user_id,
                "name": student.name,
                "submission_count": submission_count,
                "avg_grade": round(avg_grade, 1)
            })
        
        assignments = db.query(Assignments).all()
        assignments_data = []
        for assignment in assignments:
            assignments_data.append({
                "assignment_id": assignment.assignment_id,
                "description": assignment.description,
                "due_date": assignment.due_date,
                "autograder": assignment.autograder
            })
        
    finally:
        db.close()
    
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "admin": user,
        "total_students": total_students,
        "total_assignments": total_assignments,
        "total_submissions": total_submissions,
        "recent_submissions": recent_submissions,
        "student_stats": student_stats,
        "assignments": assignments_data
    })

@app.get("/admin/students", response_class=HTMLResponse)
async def admin_students(request: Request):
    user = get_current_user_info(request)
    if not user or user.role != "admin":
        return RedirectResponse(url="/login", status_code=302)
    
    db = SessionLocal()
    students = db.query(Users).filter(Users.role == "student").all()
    
    student_data = []
    for student in students:
        submissions = db.query(Submissions).filter(Submissions.user_id == student.user_id).all()
        student_data.append({
            "student": student,
            "submissions": submissions
        })
    
    db.close()
    
    return templates.TemplateResponse("admin_students.html", {
        "request": request,
        "admin": user,
        "student_data": student_data
    })

# CRUD routes for assignments, autograders and tests (requires admin)

# Assignments CRUD
@app.get("/admin/assignments", response_class=HTMLResponse)
async def admin_assignments(request: Request):
    user = get_current_user_info(request)
    if not user or user.role != "admin":
        return RedirectResponse(url="/login", status_code=302)
    
    db = SessionLocal()
    assignments = db.query(Assignments).all()
    autograders = db.query(Autograders).all()  # For dropdown in forms
    db.close()
    
    return templates.TemplateResponse("admin_assignments.html", {
        "request": request,
        "admin": user,
        "assignments": assignments,
        "autograders": autograders
    })

@app.post("/admin/assignments/create")
async def create_assignment(
    request: Request,
    assignment_id: str = Form(...),
    description: str = Form(...),
    due_date: str = Form(None),
    autograder: str = Form(...)
):
    user = get_current_user_info(request)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    db = SessionLocal()
    
    existing = db.query(Assignments).filter(Assignments.assignment_id == assignment_id).first()
    if existing:
        db.close()
        return RedirectResponse(url="/admin/assignments?error=Assignment ID already exists", status_code=302)
    
    due_date_obj = None
    if due_date and due_date.strip():
        try:
            due_date_obj = date.fromisoformat(due_date)
        except ValueError:
            db.close()
            return RedirectResponse(url="/admin/assignments?error=Invalid date format", status_code=302)
    
    new_assignment = Assignments(
        assignment_id=assignment_id.strip(),
        description=description.strip(),
        due_date=due_date_obj,
        autograder=autograder.strip()
    )
    
    db.add(new_assignment)
    db.commit()
    db.close()
    
    return RedirectResponse(url="/admin/assignments?success=Assignment created successfully", status_code=302)

@app.post("/admin/assignments/{assignment_id}/update")
async def update_assignment(
    request: Request,
    assignment_id: str,
    description: str = Form(...),
    due_date: str = Form(None),
    autograder: str = Form(...)
):
    user = get_current_user_info(request)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    db = SessionLocal()
    assignment = db.query(Assignments).filter(Assignments.assignment_id == assignment_id).first()
    
    if not assignment:
        db.close()
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    due_date_obj = None
    if due_date and due_date.strip():
        try:
            due_date_obj = date.fromisoformat(due_date)
        except ValueError:
            db.close()
            return RedirectResponse(url="/admin/assignments?error=Invalid date format", status_code=302)
    
    assignment.description = description.strip()
    assignment.due_date = due_date_obj
    assignment.autograder = autograder.strip()
    
    db.commit()
    db.close()
    
    return RedirectResponse(url="/admin/assignments?success=Assignment updated successfully", status_code=302)

@app.post("/admin/assignments/{assignment_id}/delete")
async def delete_assignment(request: Request, assignment_id: str):
    user = get_current_user_info(request)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    db = SessionLocal()
    
    db.query(Tests).filter(Tests.assignment_id == assignment_id).delete()
    
    db.query(Submissions).filter(Submissions.assignment_id == assignment_id).delete()
    
    assignment = db.query(Assignments).filter(Assignments.assignment_id == assignment_id).first()
    if assignment:
        db.delete(assignment)
    
    db.commit()
    db.close()
    
    return RedirectResponse(url="/admin/assignments?success=Assignment deleted successfully", status_code=302)

# Autograders CRUD
@app.get("/admin/autograders", response_class=HTMLResponse)
async def admin_autograders(request: Request):
    user = get_current_user_info(request)
    if not user or user.role != "admin":
        return RedirectResponse(url="/login", status_code=302)
    
    db = SessionLocal()
    autograders = db.query(Autograders).all()
    
    autograders_data = []
    for ag in autograders:
        try:
            outputs = json.loads(ag.outputs) if ag.outputs else {}
            weights = json.loads(ag.grade_weights) if ag.grade_weights else {}
        except json.JSONDecodeError:
            outputs = {}
            weights = {}
        
        autograders_data.append({
            "name": ag.name,
            "outputs": outputs,
            "weights": weights,
            "outputs_json": ag.outputs,
            "weights_json": ag.grade_weights
        })
    
    db.close()
    
    return templates.TemplateResponse("admin_autograders.html", {
        "request": request,
        "admin": user,
        "autograders": autograders_data
    })

@app.post("/admin/autograders/create")
async def create_autograder(
    request: Request,
    name: str = Form(...),
    outputs: str = Form(...),
    weights: str = Form(...)
):
    user = get_current_user_info(request)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        outputs_data = json.loads(outputs)
        weights_data = json.loads(weights)
    except json.JSONDecodeError as e:
        return RedirectResponse(url=f"/admin/autograders?error=Invalid JSON format: {str(e)}", status_code=302)
    
    db = SessionLocal()
    
    existing = db.query(Autograders).filter(Autograders.name == name).first()
    if existing:
        db.close()
        return RedirectResponse(url="/admin/autograders?error=Autograder name already exists", status_code=302)
    
    new_autograder = Autograders(
        name=name.strip(),
        outputs=outputs.strip(),
        grade_weights=weights.strip()
    )
    
    db.add(new_autograder)
    db.commit()
    db.close()
    
    return RedirectResponse(url="/admin/autograders?success=Autograder created successfully", status_code=302)

@app.post("/admin/autograders/{name}/update")
async def update_autograder(
    request: Request,
    name: str,
    outputs: str = Form(...),
    weights: str = Form(...)
):
    user = get_current_user_info(request)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        outputs_data = json.loads(outputs)
        weights_data = json.loads(weights)
    except json.JSONDecodeError as e:
        return RedirectResponse(url=f"/admin/autograders?error=Invalid JSON format: {str(e)}", status_code=302)
    
    db = SessionLocal()
    autograder = db.query(Autograders).filter(Autograders.name == name).first()
    
    if not autograder:
        db.close()
        raise HTTPException(status_code=404, detail="Autograder not found")
    
    autograder.outputs = outputs.strip()
    autograder.grade_weights = weights.strip()
    
    db.commit()
    db.close()
    
    return RedirectResponse(url="/admin/autograders?success=Autograder updated successfully", status_code=302)

@app.post("/admin/autograders/{name}/delete")
async def delete_autograder(request: Request, name: str):
    user = get_current_user_info(request)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    db = SessionLocal()
    
    dependent_assignments = db.query(Assignments).filter(Assignments.autograder == name).all()
    if dependent_assignments:
        assignment_names = [a.assignment_id for a in dependent_assignments]
        db.close()
        error_msg = f"Cannot delete autograder. Used by assignments: {', '.join(assignment_names)}"
        return RedirectResponse(url=f"/admin/autograders?error={error_msg}", status_code=302)
    
    autograder = db.query(Autograders).filter(Autograders.name == name).first()
    if autograder:
        db.delete(autograder)
    
    db.commit()
    db.close()
    
    return RedirectResponse(url="/admin/autograders?success=Autograder deleted successfully", status_code=302)

# Tests CRUD
@app.get("/admin/tests", response_class=HTMLResponse)
async def admin_tests(request: Request):
    user = get_current_user_info(request)
    if not user or user.role != "admin":
        return RedirectResponse(url="/login", status_code=302)
    
    db = SessionLocal()
    tests = db.query(Tests).join(Assignments).all()
    assignments = db.query(Assignments).all()
    
    tests_data = []
    for test in tests:
        try:
            inputs = json.loads(test.input_data) if test.input_data else {}
        except json.JSONDecodeError:
            inputs = {}
        
        tests_data.append({
            "test_id": test.test_id,
            "assignment_id": test.assignment_id,
            "assignment": test.assignment,
            "inputs": inputs,
            "inputs_json": test.input_data
        })
    
    db.close()
    
    return templates.TemplateResponse("admin_tests.html", {
        "request": request,
        "admin": user,
        "tests": tests_data,
        "assignments": assignments
    })

@app.post("/admin/tests/create")
async def create_test(
    request: Request,
    test_id: str = Form(...),
    assignment_id: str = Form(...),
    input_data: str = Form(...)
):
    user = get_current_user_info(request)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        inputs = json.loads(input_data)
    except json.JSONDecodeError as e:
        return RedirectResponse(url=f"/admin/tests?error=Invalid JSON format: {str(e)}", status_code=302)
    
    db = SessionLocal()
    
    existing = db.query(Tests).filter(Tests.test_id == test_id).first()
    if existing:
        db.close()
        return RedirectResponse(url="/admin/tests?error=Test ID already exists", status_code=302)
    
    assignment = db.query(Assignments).filter(Assignments.assignment_id == assignment_id).first()
    if not assignment:
        db.close()
        return RedirectResponse(url="/admin/tests?error=Assignment does not exist", status_code=302)
    
    new_test = Tests(
        test_id=test_id.strip(),
        assignment_id=assignment_id.strip(),
        input_data=input_data.strip()
    )
    
    db.add(new_test)
    db.commit()
    db.close()
    
    return RedirectResponse(url="/admin/tests?success=Test created successfully", status_code=302)

@app.post("/admin/tests/{test_id}/update")
async def update_test(
    request: Request,
    test_id: str,
    assignment_id: str = Form(...),
    input_data: str = Form(...)
):
    user = get_current_user_info(request)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        inputs = json.loads(input_data)
    except json.JSONDecodeError as e:
        return RedirectResponse(url=f"/admin/tests?error=Invalid JSON format: {str(e)}", status_code=302)
    
    db = SessionLocal()
    test = db.query(Tests).filter(Tests.test_id == test_id).first()
    
    if not test:
        db.close()
        raise HTTPException(status_code=404, detail="Test not found")
    
    assignment = db.query(Assignments).filter(Assignments.assignment_id == assignment_id).first()
    if not assignment:
        db.close()
        return RedirectResponse(url="/admin/tests?error=Assignment does not exist", status_code=302)
    
    test.assignment_id = assignment_id.strip()
    test.input_data = input_data.strip()
    
    db.commit()
    db.close()
    
    return RedirectResponse(url="/admin/tests?success=Test updated successfully", status_code=302)

@app.post("/admin/tests/{test_id}/delete")
async def delete_test(request: Request, test_id: str):
    user = get_current_user_info(request)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    db = SessionLocal()
    
    test = db.query(Tests).filter(Tests.test_id == test_id).first()
    if test:
        db.delete(test)
    
    db.commit()
    db.close()
    
    return RedirectResponse(url="/admin/tests?success=Test deleted successfully", status_code=302)

# File upload endpoint for students
@app.post("/upload")
async def upload_and_grade(request: Request, assignment_id: str = Form(...), file: UploadFile = File(...)):
    user_id = require_auth(request)
    
    # Only .zip files are accepted
    if not file.filename or not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Please upload a .zip file")

    db = SessionLocal()
    assignment = db.query(Assignments).filter(Assignments.assignment_id == assignment_id).first()
    db.close()
    
    if not assignment:
        raise HTTPException(status_code=400, detail="Invalid assignment ID")

    unique_id = str(uuid.uuid4())[:8]
    autograder_filename = f"{user_id}_{assignment_id}.zip"
    file_path = SUBMISSIONS_DIR / autograder_filename
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        result = await run_autograder(file_path, autograder_filename, user_id, assignment_id)
        
        return {
            "success": True,
            "filename": file.filename,
            "assignment_id": assignment_id,
            "user_id": user_id,
            "results": result
        }
        
    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Grading failed: {str(e)}")

# Grading functions
async def run_autograder(zip_path: Path, autograder_filename: str, student_id: str, assignment_id: str) -> dict:
    original_dir = os.getcwd()
    
    try:
        os.chdir(AUTOGRADER_DIR)
        
        print(f"DEBUG: Processing file: {autograder_filename} for student {student_id}, assignment {assignment_id}")
        
        cmd = ["./autograder", str(zip_path)]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30  
        )
        
        stdout = result.stdout
        stderr = result.stderr
        
        print(f"DEBUG: Autograder stdout: {stdout}")
        if stderr:
            print(f"DEBUG: Autograder stderr: {stderr}")
        
        grading_results = parse_grading_output(stdout, student_id, assignment_id)
        
        return {
            "exit_code": result.returncode,
            "grading_results": grading_results,
            "success": result.returncode == 0,
            "error_message": stderr if result.returncode != 0 else None
        }
        
    except subprocess.TimeoutExpired:
        return {
            "exit_code": -1,
            "grading_results": [],
            "success": False,
            "error_message": "Grading timed out after 30 seconds"
        }
    except Exception as e:
        return {
            "exit_code": -1,
            "grading_results": [],
            "success": False,
            "error_message": f"Internal error: {str(e)}"
        }
    finally:
        os.chdir(original_dir)

# Parse results and save to db
def parse_grading_output(output: str, expected_student_id: str, expected_assignment_id: str) -> list:
    results = []
    lines = output.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if "Graded:" in line and "Assignment" in line and "student" in line:
            try:
                match = re.search(r'Assignment (\w+) by student (\w+) Graded: (\d+/\d+)', line)
                if match:
                    assignment = match.group(1)
                    student_id = match.group(2)
                    grade = match.group(3)
                    
                    if student_id == expected_student_id and assignment == expected_assignment_id:
                        save_submission_to_db(student_id, assignment, grade)
                        
                        results.append({
                            "assignment": assignment,
                            "student_id": student_id,
                            "grade": grade,
                            "display_text": f"Final grade: {grade}"
                        })
            except Exception as e:
                print(f"DEBUG: Error parsing grade line: {e}")
                continue
    
    if not results:
        save_submission_to_db(expected_student_id, expected_assignment_id, "0/100")
        
        output_lower = output.lower()
        if "compilation failed" in output_lower:
            error_msg = "Compilation failed"
        elif "no test defined" in output_lower:
            error_msg = "No test defined"
        elif "timeout" in output_lower:
            error_msg = "Execution timeout"
        else:
            error_msg = "Processing error"
            
        results.append({
            "assignment": expected_assignment_id,
            "student_id": expected_student_id,
            "grade": "0/100",
            "display_text": f"Final grade: 0/100 ({error_msg})"
        })
    
    return results

# Add submission to db or update if higher grade
def save_submission_to_db(user_id: str, assignment_id: str, grade_str: str):
    try:
        if "/" in grade_str:
            earned, total = grade_str.split("/")
            grade_percentage = (float(earned) / float(total)) * 100
        else:
            grade_percentage = 0.0
        
        db = SessionLocal()
        
        existing = db.query(Submissions).filter(
            Submissions.user_id == user_id,
            Submissions.assignment_id == assignment_id
        ).first()
        
        if existing:
            if grade_percentage > existing.grade:
                existing.grade = grade_percentage
                existing.submission_time = datetime.utcnow()
                print(f"Updated submission for user {user_id}, assignment {assignment_id}: {grade_percentage}%")
            else:
                print(f"Keeping existing higher grade for user {user_id}, assignment {assignment_id}")
        else:
            new_submission = Submissions(
                user_id=user_id,
                assignment_id=assignment_id,
                submission_time=datetime.utcnow(),
                grade=grade_percentage
            )
            db.add(new_submission)
            print(f"Created new submission for user {user_id}, assignment {assignment_id}: {grade_percentage}%")
        
        db.commit()
        db.close()
        
    except Exception as e:
        print(f"Error saving submission to database: {e}")
        if 'db' in locals():
            db.close()

# Returns submission for the authenticated user
@app.get("/submissions")
async def get_submissions(request: Request):
    user_id = require_auth(request)
    
    try:
        db = SessionLocal()
        submissions = db.query(Submissions).filter(Submissions.user_id == user_id).all()
        
        result = []
        for sub in submissions:
            result.append({
                "assignment_id": sub.assignment_id,
                "submission_date": sub.submission_time.isoformat() if sub.submission_time else None,
                "grade": sub.grade
            })
        
        db.close()
        return {"user_id": user_id, "submissions": result}
        
    except Exception as e:
        return {"error": str(e)}

# Reload config file and update db
@app.post("/reload-config")
async def reload_config():
    success = load_config_to_database()
    return {"success": success, "message": "Config reloaded" if success else "Failed to reload config"}

@app.get("/health")
async def health_check():
    autograder_path = AUTOGRADER_DIR / "autograder"
    return {
        "status": "healthy", 
        "autograder_available": autograder_path.exists(),
        "autograder_executable": autograder_path.exists() and os.access(autograder_path, os.X_OK),
        "submissions_dir_exists": SUBMISSIONS_DIR.exists(),
        "autograder_dir_exists": AUTOGRADER_DIR.exists()
    }

@app.get("/debug")
async def debug_info():
    autograder_path = AUTOGRADER_DIR / "autograder"
    
    files_in_autograder_dir = []
    if AUTOGRADER_DIR.exists():
        files_in_autograder_dir = [f.name for f in AUTOGRADER_DIR.iterdir()]
    
    files_in_submissions_dir = []
    if SUBMISSIONS_DIR.exists():
        files_in_submissions_dir = [f.name for f in SUBMISSIONS_DIR.iterdir()]
    
    return {
        "base_dir": str(BASE_DIR),
        "autograder_dir": str(AUTOGRADER_DIR),
        "submissions_dir": str(SUBMISSIONS_DIR),
        "autograder_path": str(autograder_path),
        "autograder_exists": autograder_path.exists(),
        "autograder_executable": autograder_path.exists() and os.access(autograder_path, os.X_OK),
        "files_in_autograder_dir": files_in_autograder_dir,
        "files_in_submissions_dir": files_in_submissions_dir,
        "current_working_dir": os.getcwd()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)