# C++ Autograder System

A flexible and extensible autograding system for C++ programming assignments. This tool automatically extracts, compiles, runs, and grades student submissions based on expected output criteria defined in a simple configuration file.

**Two ways to use the autograder:**
- **Command-line interface** for batch processing multiple submissions
- **Web interface** for students to submit individual file uploads with real-time results

## Features

- **Automated grading** of C++ programming assignments
- **Flexible test configuration** with custom input/output scenarios
- **Support for multiple assignments** with different grading criteria
- **Batch processing (via command-line)** of multiple submissions across multiple assignments
- **FastAPI Web interface** for students to upload their submissions

## Requirements

### Core Autograder
- C++20 compatible compiler (clang++ or g++)
- `make` utility
- `unzip` command-line tool
- macOS or Linux environment

### Web Interface (Optional)
- Python 3.7+
- FastAPI
- Uvicorn

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/DBordeleau/cpp_autograder
cd cpp_autograder
```

### 2. Compile the autograder
```bash
cd autograding_src
make
cd ..
```
*Note: You may will to modify the Makefile if not using clang*

### 3. Install Python dependencies for web interface (optional)
```bash
pip install -r requirements.txt
```

## Usage

### Option 1: Command-Line Interface

For batch processing multiple submissions:

```bash
cd autograding_src
./autograder path/to/submissions/directory/
```

### Option 2: Web Interface

For easy single-file uploads with real-time results:

#### Start the web server:
```bash
cd web
python app.py
```

#### Access the interface:
Open your browser to `http://localhost:8000`

- **Drag & drop** or click to upload `.zip` files
- **Real-time grading** with immediate results
- **Clean output** showing only final grades
- **Detailed logging** in your server console

### Submission Format

Student submissions must follow this naming convention:
```
<student_id>_<assignment_name>.zip
```

Examples:
- `123456_A1.zip` - Student ID 123456 submitting assignment A1
- `789012_Assignment2.zip` - Student ID 789012 submitting assignment Assignment2

### Submission Requirements

Each zip file must contain:
- A `Makefile` that compiles the code
- All source files and dependencies
- The Makefile must produce an executable named exactly like the assignment name

Example: For assignment "A1", the Makefile should create an executable called "A1".

## Configuration

The autograder uses a simple `config.txt` file to define assignments, autograders, and tests.

### config.txt Format

The configuration file has three sections:

#### Assignments Section
Define assignments with their descriptions, due dates, and associated autograders:
```
### Assignments

A1 = {"First Programming Assignment", "2025-10-31", "autograder1"}
A2 = {"Second Assignment", "2025-11-15", "autograder2"}
```

Format: `AssignmentName = {"Description", "YYYY-MM-DD", "autograder_name"}`

#### Autograders Section
Define what outputs to look for and their point values. The item at outputItems[i] is worth gradeValue[i]:
```
### Autograders

autograder1 = {["Hello World!", "Goodbye!"], [50, 50]}
autograder2 = {["Result: 42"], [100]}
```

Format: `AutograderName = {["output1", "output2"], [points_for_output1, points_for_output2]}`

#### Tests Section
Define test inputs for each assignment:
```
### Tests

Test1 = {"A1", ["John", "25"]}
Test2 = {"A2", ["10", "5"]}
```

Format: `TestName = {"AssignmentName", ["input1", "input2"]}`

### Complete Example config.txt

```
### Assignments

A1 = {"Hello World Program", "2025-10-31", "autograder1"}
A2 = {"Calculator Program", "2025-11-15", "autograder2"}

### Autograders

autograder1 = {["Hello Frodo!"], [100]}
autograder2 = {["Sum: 15", "Product: 50"], [50, 50]}

### Tests

Test1 = {"A1", ["Frodo"]}
Test2 = {"A2", ["10", "5"]}
```

## Project Structure

```
autograder/
├── autograding_src/      # Core autograder (C++)
│   ├── main.cpp          # Main entry point
│   ├── config.txt        # Configuration file
│   ├── config.h/cpp      # Configuration parser
│   ├── grader.h/cpp      # Core grading utilities
│   ├── tests.h/cpp       # Test routing and execution
│   ├── assignment.h/cpp  # Assignment management
│   ├── autograder.h/cpp  # Grading logic based on expected output
│   ├── submission.h/cpp  # Submission representation
│   ├── mark.h/cpp        # Grade representation (gradeValue / outOf)
│   ├── date.h/cpp        # Date object
│   └── Makefile          # Build configuration
├── web/                  # Web interface (Python/FastAPI)
│   ├── app.py            # FastAPI web server
│   ├── templates/        # HTML Files (currently 1 page)
│   │   └── index.html    # Main upload page
│   └── static/           # CSS and assets
│       └── style.css     # Styling
├── submissions/          # Uploaded submissions storage
├── requirements.txt      # Python dependencies
└── README.md             # You are here
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

### Using Command-Line Interface

1. **Configure the autograder** by editing `autograding_src/config.txt`:
   ```
   ### Assignments
   A1 = {"Hello Program", "2025-10-31", "autograder1"}
   
   ### Autograders
   autograder1 = {["Hello Frodo!"], [100]}
   
   ### Tests
   Test1 = {"A1", ["Frodo"]}
   ```

2. **Store student submissions** in the /submissions directory in the format: `<student_ID>_<assignment_name>.zip`

3. **Batch process submissions**:
   ```bash
   cd autograding_src
   ./autograder ../submissions/
   ```

4. **View results** saved in `autograder_output.txt`

### Using Web Interface

1. **Start the web server**:
   ```bash
   cd web
   python app.py
   ```

2. **Students visit** `http://localhost:8000`

3. **Upload and grade**:
   - Student drags `123456_A1.zip` to upload area
   - Clicks "Grade Assignment"
   - Sees result immediately: "Final grade: 100/100"

### Processing Details

- **Loads configuration** from `config.txt`
- **Extracts zip** to temporary directory
- **Compiles code** using student's Makefile
- **Executes program** with associated test input
- **Captures output** and searches for output defined by the autograder
- **Awards points** based on matches found
- **Displays results** in front-end with detailed logging in the console

## License

This project is licensed under the MIT License.