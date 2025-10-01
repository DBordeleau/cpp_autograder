# Handles loading configuration from config.json into the database
# and creating a default admin user if none exists

import json
import subprocess
from pathlib import Path
from datetime import date
from .database import SessionLocal, Users, Assignments, Autograders, Tests
from .auth import hash_password
from .config import AUTOGRADER_DIR

def load_config_to_database():
    """Load configuration from config.txt using the C++ config_parser."""
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
            print(f"Parser output: {result.stdout}")
            return False
        
        db = SessionLocal()
        
        # Clear existing data
        db.query(Tests).delete()
        db.query(Autograders).delete()
        db.query(Assignments).delete()
        
        # Add autograders
        for name, data in config_data.get("autograders", {}).items():
            autograder = Autograders(
                name=name,
                outputs=json.dumps(data["outputs"]),
                grade_weights=json.dumps(data["weights"])
            )
            db.add(autograder)
            print(f"Added autograder: {name}")
        
        # Add assignments
        for name, data in config_data.get("assignments", {}).items():
            assignment = Assignments(
                assignment_id=name,
                description=data["description"],
                due_date=date.fromisoformat(data["due_date"]) if data["due_date"] else None,
                autograder=data["autograder"]
            )
            db.add(assignment)
            print(f"Added assignment: {name}")
        
        # Add tests
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
        import traceback
        traceback.print_exc()
        return False

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