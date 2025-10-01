import re
from typing import List, Dict
from datetime import datetime
from ..database import SessionLocal, Submissions

def parse_grading_output(output: str, expected_student_id: str, expected_assignment_id: str) -> List[Dict]:
    """Parse grading output and extract results."""
    results = []
    
    print(f"DEBUG parse_grading_output: Full output length={len(output)}")
    print(f"DEBUG parse_grading_output: Looking for student_id='{expected_student_id}', assignment_id='{expected_assignment_id}'")
    
    lines = output.split('\n')
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        if not line or not (line.startswith('{') and '"student_id"' in line):
            continue
        
        print(f"DEBUG parse_grading_output: Found potential JSON on line {i}")
        
        # Collect multi-line JSON
        json_lines = [line]
        j = i + 1
        while j < len(lines) and not json_lines[-1].endswith('}'):
            next_line = lines[j].rstrip()
            if next_line:
                json_lines.append(next_line)
            j += 1
        
        full_json = '\n'.join(json_lines)
        
        # Extract fields using regex
        pattern = r'\{[^}]*"student_id"\s*:\s*"([^"]+)"[^}]*"assignment_id"\s*:\s*"([^"]+)"[^}]*"score"\s*:\s*(\d+)[^}]*"total"\s*:\s*(\d+)'
        match = re.search(pattern, full_json, re.DOTALL)
        
        if match:
            json_student_id = match.group(1)
            json_assignment_id = match.group(2)
            score = int(match.group(3))
            total = int(match.group(4))
            
            print(f"DEBUG: Extracted student_id='{json_student_id}', assignment_id='{json_assignment_id}', score={score}, total={total}")
            
            if (json_student_id == expected_student_id and 
                json_assignment_id == expected_assignment_id):
                
                grade_str = f"{score}/{total}"
                
                # Extract output field
                output_match = re.search(r'"output"\s*:\s*"([^"]*(?:\n[^"]*)*)"', full_json, re.DOTALL)
                student_output = output_match.group(1) if output_match else ""
                
                results.append({
                    "assignment": expected_assignment_id,
                    "student_id": expected_student_id,
                    "grade": grade_str,
                    "display_text": f"Final grade: {grade_str}",
                    "output": student_output
                })
                
                return results
    
    print(f"DEBUG parse_grading_output: No valid JSON result found")
    
    results.append({
        "assignment": expected_assignment_id,
        "student_id": expected_student_id,
        "grade": "0/100",
        "display_text": "Final grade: 0/100 (Unknown error)",
        "output": output
    })
    
    return results

def save_submission_to_db(user_id: str, assignment_id: str, grade_str: str):
    """Save or update submission in database."""
    try:
        print(f"DEBUG save_submission_to_db: Received grade_str='{grade_str}'")
        
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
            if grade_percentage >= (existing.grade or 0):
                existing.grade = grade_percentage
                existing.submission_time = datetime.now()
                print(f"Updated submission: {grade_percentage}%")
            else:
                print(f"Keeping existing grade: {existing.grade}%")
        else:
            new_submission = Submissions(
                user_id=user_id,
                assignment_id=assignment_id,
                submission_time=datetime.now(),
                grade=grade_percentage
            )
            db.add(new_submission)
            print(f"Created new submission: {grade_percentage}%")
        
        db.commit()
        db.close()
        
    except Exception as e:
        print(f"Error saving submission: {e}")
        if 'db' in locals():
            db.close()