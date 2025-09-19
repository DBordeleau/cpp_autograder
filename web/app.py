from fastapi import FastAPI, File, UploadFile, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import subprocess
import os
import shutil
import tempfile
from pathlib import Path
import uuid
import re

app = FastAPI(title="C++ Autograder", description="Automatically grade C++ programming assignments.")

BASE_DIR = Path(__file__).parent.parent
SUBMISSIONS_DIR = BASE_DIR / "submissions" # where uploaded submissions are stored
AUTOGRADER_DIR = BASE_DIR / "autograding_src" # where the autograder executable is located
WEB_DIR = Path(__file__).parent

# create submissions directory if it doesn't exist
SUBMISSIONS_DIR.mkdir(exist_ok=True)

templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")

# serve home page with upload form
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# handle file upload and invoke autograder
@app.post("/upload")
async def upload_and_grade(file: UploadFile = File(...)):    
    # only .zip files are accepted
    if not file.filename or not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Please upload a .zip file")

    unique_id = str(uuid.uuid4())[:8]
    safe_filename = f"{unique_id}_{file.filename}"
    file_path = SUBMISSIONS_DIR / safe_filename
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        result = await run_autograder(file_path, file.filename)
        
        return {
            "success": True,
            "filename": file.filename,
            "results": result
        }
        
    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Grading failed: {str(e)}")

async def run_autograder(zip_path: Path, original_filename: str) -> dict:
    original_dir = os.getcwd()
    temp_file_path = None
    
    try:
        os.chdir(AUTOGRADER_DIR)
        
        temp_file_path = SUBMISSIONS_DIR / original_filename
        
        if temp_file_path.exists():
            temp_file_path.unlink()
        
        shutil.copy2(zip_path, temp_file_path)
        
        # Still log for server debugging, but don't include in response
        print(f"DEBUG: Processing file: {original_filename}")
        
        cmd = ["./autograder", str(temp_file_path)]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30  
        )
        
        stdout = result.stdout
        stderr = result.stderr
        
        # Log full output for server debugging
        print(f"DEBUG: Autograder stdout: {stdout}")
        if stderr:
            print(f"DEBUG: Autograder stderr: {stderr}")
        
        grading_results = parse_grading_output(stdout)
        
        return {
            "exit_code": result.returncode,
            "grading_results": grading_results,
            "success": result.returncode == 0,
            # Only include stderr in response if there's an actual error
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
        if temp_file_path and temp_file_path.exists():
            try:
                temp_file_path.unlink()
                print(f"DEBUG: Cleaned up temporary file: {temp_file_path}")
            except Exception as e:
                print(f"DEBUG: Failed to clean up temporary file: {e}")
        
        os.chdir(original_dir)

def parse_grading_output(output: str) -> list:
    """Extract only the final grading results, hiding all debug information"""
    results = []
    lines = output.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Look for the final grading line: "Assignment A2 by student 123456779 Graded: 0/100"
        if "Graded:" in line and "Assignment" in line and "student" in line:
            try:
                # Extract assignment name, student ID, and grade using regex
                match = re.search(r'Assignment (\w+) by student (\w+) Graded: (\d+/\d+)', line)
                if match:
                    assignment = match.group(1)
                    student_id = match.group(2)
                    grade = match.group(3)
                    
                    results.append({
                        "assignment": assignment,
                        "student_id": student_id,
                        "grade": grade,
                        "display_text": f"Final grade: {grade}"
                    })
            except Exception as e:
                print(f"DEBUG: Error parsing grade line: {e}")
                continue
    
    # If no proper grading results found, check for common error conditions
    if not results:
        output_lower = output.lower()
        if "compilation failed" in output_lower:
            results.append({
                "assignment": "Unknown",
                "student_id": "Unknown", 
                "grade": "0/100",
                "display_text": "Final grade: 0/100 (Compilation failed)"
            })
        elif "no test defined" in output_lower:
            results.append({
                "assignment": "Unknown",
                "student_id": "Unknown",
                "grade": "0/100", 
                "display_text": "Final grade: 0/100 (No test defined)"
            })
        elif "timeout" in output_lower:
            results.append({
                "assignment": "Unknown",
                "student_id": "Unknown",
                "grade": "0/100",
                "display_text": "Final grade: 0/100 (Execution timeout)"
            })
        else:
            results.append({
                "assignment": "Unknown",
                "student_id": "Unknown", 
                "grade": "0/100",
                "display_text": "Final grade: 0/100 (Processing error)"
            })
    
    return results

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
    """Debug endpoint - only accessible for troubleshooting"""
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