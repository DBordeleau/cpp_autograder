# C++ Autograder System

A full-stack autograding system for C++ programming assignments. This tool automatically extracts, compiles, runs, and grades student submissions based on expected output criteria defined in a simple configuration file. Students receive instant results. Grades are stored in a sqlite database and can be viewed by the server admin.

## Features

- **User Authentication** - Students create accounts and login securely.
- **Database Integration** - SQLite database stores users, assignments, tests/autograder criteria and grading results.
- **Automated grading** with instant results available to students.
- **Grade tracking** - Students can view their current grades and submission history.
- **Flexible test configuration** with custom input/output scenarios.
- **Support for multiple assignments** with different grading criteria.
- **Web Interface** for students to submit assignments and view results. And a separate interface for server admins to view results by student, assignment and to create new assignments and tests.
- **Docker containerization** protects the rest of the server from malicious submissions.

## Requirements

### Core Autograder
- C++20 compatible compiler (g++ by default)
- `make` utility
- `unzip` command-line tool
- SQLite3 development libraries
- macOS or Linux environment

### Web Interface
- Python 3.7+
- FastAPI
- SQLAlchemy
- bcrypt
- PyJWT 

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/DBordeleau/cpp_autograder
cd cpp_autograder
```

### 2. Install SQLite3 development libraries
```bash
# macOS
brew install sqlite3

# Ubuntu/Debian
sudo apt-get install libsqlite3-dev
```

### 3. Compile the autograder
```bash
cd autograding_src
make all
cd ..
```
*Note: You may need to modify the Makefile if not using clang*

### 4. Install Python dependencies
```bash
pip install -r requirements.txt
```

## Usage

### Start the Web Server
```bash
python run.py
```

The first time the server is started, the system will automatically detect that no admin account exists and prompt you to create one:

```
==================================================
FIRST TIME SETUP - CREATE ADMIN ACCOUNT
==================================================
No admin account found. Creating admin user...
Enter password for admin user: [hidden input]
Confirm password: [hidden input]
Admin user created successfully!
You can now login with username 'admin' and your chosen password.
==================================================
```

**Note**: This admin creation only happens on the very first server startup. Once created, the admin account persists in the database.

### Access the System
Open your browser to `http://127.0.0.1:8000`

### Student Workflow

1. **Create Account**: New students register with their student ID, name, and password
2. **Login**: Students login with their student ID and password.
3. **View Assignments**: See all available assignments with due dates and current grades.
4. **Submit Work**: Click on an assignment to view details and upload a zip file.
5. **View Results**: Get immediate grading feedback and grade updates.

### Submission Requirements

Each zip file must contain:
- A `Makefile` that compiles the code
- All source files and dependencies
- The Makefile must produce an executable named exactly like the assignment ID

Example: For an assignment with the ID "Assignment_1", the Makefile should produce an executable called "Assignment_1".

## Database

The system uses SQLite to store all data with the following tables:

### Users
- `user_id` (Primary Key) - Student's unique identifier
- `name` - Student's full name
- `role` - Admin/Student
- `email` - Student's email address
- `password_hash` - Securely hashed password
- `created_at` - Account creation timestamp

### Assignments
- `assignment_id` (Primary Key) - Assignment identifier
- `description` - Assignment description/instructions
- `due_date` - Assignment due date
- `autograder` - Associated autograder name

### Autograders
- `name` (Primary Key) - Autograder identifier
- `outputs` - JSON array of expected output strings
- `grade_weights` - JSON array of point values for each output

### Tests
- `test_id` (Primary Key) - Test identifier
- `assignment_id` (Foreign Key) - Associated assignment
- `input_data` - JSON array of test inputs

### Submissions
- `id` (Primary Key) - Unique submission identifier
- `student_id` (Foreign Key) - Student this submission belongs to
- `assignment_id` (Foreign Key) - Assignment submitted for
- `submission_time` - When the submission was made
- `grade` - Grade achieved (percentage)

## Authentication

The system uses secure authentication with the following features:

- **Password Hashing**: Passwords are hashed using bcrypt with salt.
- **JWT Tokens**: Session management via JSON Web Tokens stored in HTTP-only cookies.
- **SQL Injection Protection**: All database queries use parameterized statements.
- **Session Timeout**: Tokens expire after 8 hours of inactivity.
- **Role-Based Access**: Students and admins have different access levels and interfaces.

### Admin Account

The system automatically creates an admin account on first startup:
- **Username**: `admin`
- **Password**: Set during first startup (prompted in terminal)
- **Access**: Full administrative dashboard with CRUD operations
- **Interface**: Separate admin interface at `/admin` with comprehensive management tools

## Configuration

The autograder uses a simple `config.txt` file to define assignments, autograders, and tests. This configuration is automatically loaded into the database when the server is started. The server admin can also create assignments, autograders and tests using the web interface if they prefer to not interact with the config file. Though the config file is the fastest way to create many assignments/tests/autograders at once.

### config.txt Format

The configuration file has three sections:

#### Assignments Section
Define assignments with their descriptions, due dates, and associated autograders:
```
### Assignments

Assignment_1 = {"Write a program that accepts a string as user input and outputs 'Hello <input>!'", "2025-10-31", "autograder1"}
Assignment_2 = {"Write a program that prompts the user for two integers. Output the sum and product of the two integers.", "2025-12-25", "autograder2"}
```

Format: `AssignmentName = {"Description/Instructions", "YYYY-MM-DD", "autograder_name"}`

#### Autograders Section
Define what outputs to look for and their point values. The item at outputItems[i] is worth gradeValue[i]:
```
### Autograders

autograder1 = {["Hello Frodo!"], [100]}
autograder2 = {[15, 50], [50, 50]}
```

Format: `AutograderName = {["output1", "output2"], [points_for_output1, points_for_output2]}`

#### Tests Section
Define test inputs for each assignment:
```
### Tests

Test1 = {"Assignment_1", ["Frodo"]}
Test2 = {"Assignment_2", [10, 5]}
```

Format: `TestName = {"AssignmentName", ["input1", "input2"]}`

### Complete Example config.txt

```
### Assignments

Assignment_1 = {"Write a program that accepts a string as user input and outputs 'Hello <input>!'", "2025-10-31", "autograder1"}
Assignment_2 = {"Write a program that prompts the user for two integers. Output the sum and product of the two integers.", "2025-12-25", "autograder2"}

### Autograders

autograder1 = {["Hello Frodo!"], [100]}
autograder2 = {["15", "50"], [50, 50]}

### Tests

Test1 = {"Assignment_1", ["Frodo"]}
Test2 = {"Assignment_2", ["5", "10"]}
```

### Loading Configuration

After editing `config.txt`, reload it into the database by visiting:
`http://127.0.0.1:8000/reload-config`

or restart the web server

## Project Structure

```
autograder/
├── autograding_src/         # Core autograder (C++)
│   ├── main.cpp             # Main entry point
│   ├── config.h/cpp         # Config.txt parser
│   ├── grader.h/cpp         # Core grading utilities
│   ├── tests.h/cpp          # Test routing and execution
│   ├── assignment.h/cpp     # Assignment representation
│   ├── autograder.h/cpp     # Grading logic based on expected output
│   ├── submission.h/cpp     # Submission representation
│   ├── mark.h/cpp           # Grade representation (gradeValue / outOf)
│   ├── date.h/cpp           # Date object
│   └── Makefile             # Build configuration
├── web/                     # Web interface (Python/FastAPI)
│   ├── app.py               # FastAPI application setup
│   ├── config.py            # Webapp configuration
│   ├── database.py          # Database models and setup
│   ├── auth.py              # Auth utilities
│   ├── dependencies.py      # FastAPI dependencies
│   ├── config_loader.py     # Config to DB loader
│   ├── routes/              # Route handlers
│   │   ├── ...
│   ├── grading/             # Grading interface
│   │   ├── ...
│   ├── templates/           # HTML templates
│   │   ├── ...
│   └── static/              # CSS and assets
│       ├── ...
├── data/                    # Database and data storage
│   └── database.db          # SQLite database (created on first run)
├── submissions/             # Uploaded submissions storage
├── config.txt               # System configuration file
├── Dockerfile               # Docker container configuration
├── run.py                   # Server startup script
├── requirements.txt         # Python dependencies
└── README.md                # You are here
```

## Components

### Assignment
Represents a programming assignment with:
- Name and description
- Due date
- Associated autograder
- Collection of student submissions

### Autograder
Defines grading criteria:
- Expected output strings
- Point values for each string
- Automatic grade calculation

### Submission
Individual student submission containing:
- Student ID
- Assignment name
- Program output
- Calculated grade

### Tests
Custom test scenarios for each assignment:
- Input simulation
- Program execution
- Output capture

## Example Workflow

### For Students

1. **Account Creation**:
   - Visit `http://localhost:8000`
   - Click "Create Account" to create a new account
   - Enter student ID (e.g., "123456789"), full name, and password
   - Click "Create Account" to create account and login

2. **Assignment Dashboard**:
   - View all available assignments with descriptions and due dates
   - See current grades and submission status
   - Overdue assignments are highlighted in red
   - Click on any assignment to view details and submit

3. **Submitting Work**:
   - Click on an assignment (e.g., "Assignment_1")
   - View assignment details, due date, and current grade
   - Upload zip file containing your source code
   - Submit to receive instant feedback and grade

4. **Grade Tracking**:
   - Dashboard shows all grades with color-coded badges
   - Green badges indicate passing grades
   - View submission history for each assignment

### For Instructors

1. **Initial Setup**:
   ```bash
   # Configure assignments and tests
   by editing autograding_src/config.txt
   or by logging in with your admin account and using the dashboard
   
   # Start the web server
   python run.py
   ```

2. **Configuring Autograding**:
   
   **Web Interface**: Create, edit, or delete assignments/tests/autograders through admin dashboard.
   
   **Config File**: Edit `config.txt` then visit `http://127.0.0.1:8000/reload-config` or restart server

3. **Admin Dashboard Features**:
   - **Student Overview**: View all registered students, submission counts, and average grades
   - **Recent Activity**: Monitor latest submissions and grades
   - **Assignment/Autograder/Test Management**: Full CRUD operations with form validation

### System Processing Details

When a student submits work, the system:
1. **Saves submission** to database with timestamp
2. **Extracts zip file** to temporary directory
3. **Compiles code** using student's Makefile
4. **Runs tests** with predefined inputs from database
5. **Captures output** and compares against expected results
6. **Calculates grade** based on matching outputs and weights
7. **Updates database** with new grade and submission record
8. **Displays results** to student with detailed feedback

### Security Features

- **Secure Authentication**: Passwords hashed with bcrypt
- **Session Management**: JWT tokens with 8-hour expiration
- **Database Protection**: Parameterized queries prevent SQL injection
- **File Validation**: Uploaded files are validated and sandboxed
- **Access Control**: Students can only view their own grades and submissions

## License

This project is licensed under the MIT License.