import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict
from ..config import DOCKER_IMAGE, DOCKER_MEMORY_LIMIT, DOCKER_CPU_LIMIT, DOCKER_TIMEOUT, BASE_DIR, DATA_DIR

async def run_autograder(zip_path: Path, autograder_filename: str, student_id: str, assignment_id: str) -> Dict:
    """Run Docker container to grade submission."""
    try:
        print(f"DEBUG: Starting grading for {student_id}, assignment {assignment_id}")
        
        # Check if image exists
        check_image = subprocess.run(
            ["docker", "images", "-q", DOCKER_IMAGE],
            capture_output=True, text=True
        )
        
        if not check_image.stdout.strip():
            print("DEBUG: Docker image not found, building...")
            build_result = subprocess.run(
                ["docker", "build", "-t", DOCKER_IMAGE, str(BASE_DIR)],
                capture_output=True, text=True, timeout=300
            )
            
            if build_result.returncode != 0:
                return {"error": f"Docker build failed: {build_result.stderr}"}
        
        container_name = f"grader_{student_id}_{int(datetime.now().timestamp())}"
        
        docker_cmd = [
            "docker", "run", "--rm",
            "--name", container_name,
            f"--memory={DOCKER_MEMORY_LIMIT}",
            f"--cpus={DOCKER_CPU_LIMIT}",
            "--network=none",
            "--security-opt", "no-new-privileges:false",
            "--tmpfs", "/tmp:exec,size=100m",
            "-v", f"{zip_path}:/input.zip:ro",
            "-v", f"{DATA_DIR}:/data:ro",
            DOCKER_IMAGE,
            "./autograding_src/autograder", "/input.zip", student_id, assignment_id
        ]
        
        print(f"DEBUG: Running Docker command: {' '.join(docker_cmd)}")
        
        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=DOCKER_TIMEOUT
        )
        
        print(f"DEBUG: Docker exit code: {result.returncode}")
        print(f"DEBUG: Docker stdout: {result.stdout}")
        print(f"DEBUG: Docker stderr: {result.stderr}")
        
        return {
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }
            
    except subprocess.TimeoutExpired:
        print(f"DEBUG: Docker container {container_name} timed out")
        subprocess.run(["docker", "kill", container_name], capture_output=True)
        return {"error": "Execution timeout - program took too long to run"}
    except Exception as e:
        print(f"DEBUG: Exception in run_autograder: {str(e)}")
        return {"error": f"Docker execution failed: {str(e)}"}