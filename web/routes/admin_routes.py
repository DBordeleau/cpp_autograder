# Routing logic for all admin pages

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
import json
from sqlalchemy import func
from ..config import WEB_DIR
from ..database import SessionLocal, Users, Assignments, Submissions, Autograders, Tests
from ..dependencies import require_admin, get_current_user_info
from ..auth import hash_password

router = APIRouter()
templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))

# Admin dashboard
@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    require_admin(request)
    admin = get_current_user_info(request)
    
    db = SessionLocal()
    
    total_students = db.query(Users).filter(Users.role == "student").count()
    total_assignments = db.query(Assignments).count()
    total_submissions = db.query(Submissions).count()
    
    recent_subs = db.query(Submissions, Users.name).join(Users).order_by(Submissions.submission_time.desc()).limit(10).all()
    recent_submissions = []
    for sub, name in recent_subs:
        recent_submissions.append({
            'user_name': name,
            'assignment_id': sub.assignment_id,
            'grade': sub.grade or 0,
            'submission_time': sub.submission_time
        })
    
    students = db.query(Users).filter(Users.role == "student").all()
    student_stats = []
    for student in students:
        subs = db.query(Submissions).filter(Submissions.user_id == student.user_id).all()
        grades = [s.grade for s in subs if s.grade is not None]
        avg_grade = sum(grades) / len(grades) if grades else 0
        student_stats.append({
            'user_id': student.user_id,
            'name': student.name,
            'submission_count': len(subs),
            'avg_grade': avg_grade
        })
    
    assignments = db.query(Assignments).all()
    
    db.close()
    
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "admin": admin,
        "total_students": total_students,
        "total_assignments": total_assignments,
        "total_submissions": total_submissions,
        "recent_submissions": recent_submissions,
        "student_stats": student_stats,
        "assignments": assignments
    })

# Student view/management
@router.get("/admin/students", response_class=HTMLResponse)
async def admin_students(request: Request):
    require_admin(request)
    admin = get_current_user_info(request)
    
    db = SessionLocal()
    students = db.query(Users).filter(Users.role == "student").all()
    
    student_data = []
    for student in students:
        submissions = db.query(Submissions).filter(Submissions.user_id == student.user_id).all()
        student_data.append({
            'student': student,
            'submissions': submissions
        })
    
    db.close()
    
    return templates.TemplateResponse("admin_students.html", {
        "request": request,
        "admin": admin,
        "student_data": student_data
    })

# Assignment management/CRUD interface
@router.get("/admin/assignments", response_class=HTMLResponse)
async def admin_assignments(request: Request):
    require_admin(request)
    admin = get_current_user_info(request)
    
    db = SessionLocal()
    assignments = db.query(Assignments).all()
    autograders = db.query(Autograders).all()
    db.close()
    
    return templates.TemplateResponse("admin_assignments.html", {
        "request": request,
        "admin": admin,
        "assignments": assignments,
        "autograders": autograders
    })

@router.post("/admin/assignments/create")
async def create_assignment(
    request: Request,
    assignment_id: str = Form(...),
    description: str = Form(...),
    due_date: str = Form(None),
    autograder: str = Form(...)
):
    require_admin(request)
    
    db = SessionLocal()
    existing = db.query(Assignments).filter(Assignments.assignment_id == assignment_id).first()
    
    if existing:
        db.close()
        return RedirectResponse(url="/admin/assignments?error=Assignment already exists", status_code=302)
    
    new_assignment = Assignments(
        assignment_id=assignment_id,
        description=description,
        due_date=datetime.strptime(due_date, "%Y-%m-%d").date() if due_date else None,
        autograder=autograder
    )
    
    db.add(new_assignment)
    db.commit()
    db.close()
    
    return RedirectResponse(url="/admin/assignments?success=Assignment created successfully", status_code=302)

@router.post("/admin/assignments/{assignment_id}/update")
async def update_assignment(
    request: Request,
    assignment_id: str,
    description: str = Form(...),
    due_date: str = Form(None),
    autograder: str = Form(...)
):
    require_admin(request)
    
    db = SessionLocal()
    assignment = db.query(Assignments).filter(Assignments.assignment_id == assignment_id).first()
    
    if not assignment:
        db.close()
        return RedirectResponse(url="/admin/assignments?error=Assignment not found", status_code=302)
    
    assignment.description = description
    assignment.due_date = datetime.strptime(due_date, "%Y-%m-%d").date() if due_date else None
    assignment.autograder = autograder
    
    db.commit()
    db.close()
    
    return RedirectResponse(url="/admin/assignments?success=Assignment updated successfully", status_code=302)

@router.post("/admin/assignments/{assignment_id}/delete")
async def delete_assignment(request: Request, assignment_id: str):
    require_admin(request)
    
    db = SessionLocal()
    assignment = db.query(Assignments).filter(Assignments.assignment_id == assignment_id).first()
    
    if not assignment:
        db.close()
        return RedirectResponse(url="/admin/assignments?error=Assignment not found", status_code=302)
    
    # Delete any related submissions and tests
    db.query(Submissions).filter(Submissions.assignment_id == assignment_id).delete()
    db.query(Tests).filter(Tests.assignment_id == assignment_id).delete()
    db.delete(assignment)
    db.commit()
    db.close()
    
    return RedirectResponse(url="/admin/assignments?success=Assignment deleted successfully", status_code=302)

# Autograder management/CRUD interface
@router.get("/admin/autograders", response_class=HTMLResponse)
async def admin_autograders(request: Request):
    require_admin(request)
    admin = get_current_user_info(request)
    
    db = SessionLocal()
    autograders = db.query(Autograders).all()
    db.close()
    
    for ag in autograders:
        ag.outputs_json = ag.outputs
        ag.weights_json = ag.grade_weights
    
    return templates.TemplateResponse("admin_autograders.html", {
        "request": request,
        "admin": admin,
        "autograders": autograders
    })

@router.post("/admin/autograders/create")
async def create_autograder(
    request: Request,
    name: str = Form(...),
    outputs: str = Form(...),
    weights: str = Form(...)
):
    require_admin(request)
    
    try:
        json.loads(outputs)
        json.loads(weights)
    except json.JSONDecodeError:
        return RedirectResponse(url="/admin/autograders?error=Invalid JSON format", status_code=302)
    
    db = SessionLocal()
    existing = db.query(Autograders).filter(Autograders.name == name).first()
    
    if existing:
        db.close()
        return RedirectResponse(url="/admin/autograders?error=Autograder already exists", status_code=302)
    
    new_autograder = Autograders(
        name=name,
        outputs=outputs,
        grade_weights=weights
    )
    
    db.add(new_autograder)
    db.commit()
    db.close()
    
    return RedirectResponse(url="/admin/autograders?success=Autograder created successfully", status_code=302)

@router.post("/admin/autograders/{name}/update")
async def update_autograder(
    request: Request,
    name: str,
    outputs: str = Form(...),
    weights: str = Form(...)
):
    require_admin(request)
    
    try:
        json.loads(outputs)
        json.loads(weights)
    except json.JSONDecodeError:
        return RedirectResponse(url="/admin/autograders?error=Invalid JSON format", status_code=302)
    
    db = SessionLocal()
    autograder = db.query(Autograders).filter(Autograders.name == name).first()
    
    if not autograder:
        db.close()
        return RedirectResponse(url="/admin/autograders?error=Autograder not found", status_code=302)
    
    autograder.outputs = outputs
    autograder.grade_weights = weights
    
    db.commit()
    db.close()
    
    return RedirectResponse(url="/admin/autograders?success=Autograder updated successfully", status_code=302)

@router.post("/admin/autograders/{name}/delete")
async def delete_autograder(request: Request, name: str):
    require_admin(request)
    
    db = SessionLocal()
    autograder = db.query(Autograders).filter(Autograders.name == name).first()
    
    if not autograder:
        db.close()
        return RedirectResponse(url="/admin/autograders?error=Autograder not found", status_code=302)
    
    # Check if any assignments use this autograder
    # You must edit the assignment to remove the autograder before deleting the autograder
    using_assignments = db.query(Assignments).filter(Assignments.autograder == name).count()
    if using_assignments > 0:
        db.close()
        return RedirectResponse(url="/admin/autograders?error=Cannot delete: autograder is in use", status_code=302)
    
    db.delete(autograder)
    db.commit()
    db.close()
    
    return RedirectResponse(url="/admin/autograders?success=Autograder deleted successfully", status_code=302)

# Test management/CRUD interface
@router.get("/admin/tests", response_class=HTMLResponse)
async def admin_tests(request: Request):
    require_admin(request)
    admin = get_current_user_info(request)
    
    db = SessionLocal()
    tests = db.query(Tests).all()
    assignments = db.query(Assignments).all()
    db.close()
    
    for test in tests:
        test.inputs_json = test.input_data
    
    return templates.TemplateResponse("admin_tests.html", {
        "request": request,
        "admin": admin,
        "tests": tests,
        "assignments": assignments
    })

@router.post("/admin/tests/create")
async def create_test(
    request: Request,
    test_id: str = Form(...),
    assignment_id: str = Form(...),
    input_data: str = Form(...)
):
    require_admin(request)
    
    try:
        json.loads(input_data)
    except json.JSONDecodeError:
        return RedirectResponse(url="/admin/tests?error=Invalid JSON format", status_code=302)
    
    db = SessionLocal()
    existing = db.query(Tests).filter(Tests.test_id == test_id).first()
    
    if existing:
        db.close()
        return RedirectResponse(url="/admin/tests?error=Test ID already exists", status_code=302)
    
    new_test = Tests(
        test_id=test_id,
        assignment_id=assignment_id,
        input_data=input_data
    )
    
    db.add(new_test)
    db.commit()
    db.close()
    
    return RedirectResponse(url="/admin/tests?success=Test created successfully", status_code=302)

@router.post("/admin/tests/{test_id}/update")
async def update_test(
    request: Request,
    test_id: str,
    assignment_id: str = Form(...),
    input_data: str = Form(...)
):
    require_admin(request)
    
    try:
        json.loads(input_data)
    except json.JSONDecodeError:
        return RedirectResponse(url="/admin/tests?error=Invalid JSON format", status_code=302)
    
    db = SessionLocal()
    test = db.query(Tests).filter(Tests.test_id == test_id).first()
    
    if not test:
        db.close()
        return RedirectResponse(url="/admin/tests?error=Test not found", status_code=302)
    
    test.assignment_id = assignment_id
    test.input_data = input_data
    
    db.commit()
    db.close()
    
    return RedirectResponse(url="/admin/tests?success=Test updated successfully", status_code=302)

@router.post("/admin/tests/{test_id}/delete")
async def delete_test(request: Request, test_id: str):
    require_admin(request)
    
    db = SessionLocal()
    test = db.query(Tests).filter(Tests.test_id == test_id).first()
    
    if not test:
        db.close()
        return RedirectResponse(url="/admin/tests?error=Test not found", status_code=302)
    
    db.delete(test)
    db.commit()
    db.close()
    
    return RedirectResponse(url="/admin/tests?success=Test deleted successfully", status_code=302)

@router.get("/reload-config")
async def reload_config(request: Request):
    require_admin(request)
    
    from ..config_loader import load_config_to_database
    load_config_to_database()
    
    return RedirectResponse(url="/admin?success=Configuration reloaded successfully", status_code=302)