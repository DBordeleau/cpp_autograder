# Routing logic for student accounts

from fastapi import APIRouter, Request, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import shutil
from ..config import WEB_DIR, SUBMISSIONS_DIR
from ..database import SessionLocal, Assignments, Submissions, Users
from ..dependencies import require_auth
from ..grading.docker_run import run_autograder
from ..grading.grader import parse_grading_output, save_submission_to_db

router = APIRouter()
templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))

@router.get("/assignment/{assignment_id}", response_class=HTMLResponse)
async def assignment_detail(request: Request, assignment_id: str):
    user_id = require_auth(request)
    
    db = SessionLocal()
    
    assignment = db.query(Assignments).filter(Assignments.assignment_id == assignment_id).first()
    if not assignment:
        db.close()
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    student = db.query(Users).filter(Users.user_id == user_id).first()
    
    submission = db.query(Submissions).filter(
        Submissions.user_id == user_id,
        Submissions.assignment_id == assignment_id
    ).first()
    
    db.close()
    
    return templates.TemplateResponse("assignment.html", {
        "request": request,
        "assignment": assignment,
        "student": student,
        "submission": submission
    })

# Invokes the autograder Docker container and processes the results
@router.post("/upload")
async def upload_and_grade(
    request: Request,
    assignment_id: str = Form(...),
    file: UploadFile = File(...)
):
    user_id = require_auth(request)
    
    if not file.filename or not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Please upload a .zip file")

    db = SessionLocal()
    assignment = db.query(Assignments).filter(Assignments.assignment_id == assignment_id).first()
    db.close()
    
    if not assignment:
        raise HTTPException(status_code=400, detail="Invalid assignment ID")

    autograder_filename = f"{user_id}_{assignment_id}.zip"
    file_path = SUBMISSIONS_DIR / autograder_filename
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        docker_result = await run_autograder(file_path, autograder_filename, user_id, assignment_id)
        
        if docker_result.get("output"):
            parsed_results = parse_grading_output(
                docker_result["output"],
                user_id,
                assignment_id
            )
            
            if parsed_results:
                for result in parsed_results:
                    save_submission_to_db(user_id, assignment_id, result["grade"])
        else:
            parsed_results = []
        
        return {
            "success": True,
            "filename": file.filename,
            "assignment_id": assignment_id,
            "user_id": user_id,
            "results": {
                "grading_results": parsed_results,
                "docker_output": docker_result.get("output", ""),
                "docker_error": docker_result.get("error")
            }
        }
        
    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Grading failed: {str(e)}")