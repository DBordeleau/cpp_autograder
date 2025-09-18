# C++ Autograder System

A flexible and extensible autograding system for C++ programming assignments. This tool automatically extracts, compiles, runs, and grades student submissions based on expected output criteria defined in a simple configuration file.

## Features

- **Automated grading** of C++ programming assignments
- **Flexible test configuration** with custom input/output scenarios
- **Support for multiple assignments** with different grading criteria
- **Batch processing** of multiple submissions across multiple assignments

## Requirements

- C++20 compatible compiler (clang++ or g++)
- `make` utility
- `unzip` command-line tool
- macOS or Linux environment

## Installation

1. Clone the repository:
```bash
git clone https://github.com/DBordeleau/cpp_autograder
```

2. Compile the autograder:
```bash
make
```
- You will need to modify the makefile if not using clang

## Usage

### Basic Usage

Grade a single submission:
```bash
./autograder path/to/submission.zip
```

Grade multiple submissions in a directory:
```bash
./autograder path/to/submissions/directory/
```

### Submission Format

Student submissions must follow this naming convention:
```
<student_id>_<assignment_name>.zip
```

Examples:
- `123456_A1.zip` - Student ID 123456 submitting assignment A1
- `789012_Assignment2.zip` - Student ID 789012 submitting Assignment2

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
Define what outputs to look for and their point values. The item at outputItems[i] is worth gradeValue[i] points:
```
### Autograders

autograder1 = {["Hello World!", "Goodbye!"], [50, 50]}
autograder2 = {["Result: 42"], [100]}
```

Format: `AutograderName = {["output1", "output2"], [points1, points2]}`

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

## 📁 Project Structure

```
autograder/
├── main.cpp              # Main entry point
├── config.txt            # Configuration file (assignments, autograders, tests)
├── config.h/cpp          # Configuration parser
├── grader.h/cpp          # Core grading utilities (zip extraction, compilation)
├── tests.h/cpp           # Test routing and program execution
├── assignment.h/cpp      # Assignment class and submission management
├── autograder.h/cpp      # Grading logic and criteria matching
├── submission.h/cpp      # Individual submission representation
├── mark.h/cpp            # Individual grade representation
├── date.h/cpp            # Date handling for due dates and submission dates
├── Makefile              # Build configuration
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

1. **Configure the autograder** by editing `config.txt`:
   ```
   ### Assignments
   A1 = {"Hello Program", "2025-10-31", "autograder1"}
   
   ### Autograders
   autograder1 = {["Hello Frodo!"], [100]}
   
   ### Tests
   Test1 = {"A1", ["Frodo"]}
   ```

2. **Student submits** `123456_A1.zip` containing:
   ```
   main.cpp
   Makefile
   ```
   - Store student submissions in the same directory
   - Run the autograder with the path to this directory as the only argument

3. **Autograder processes**:
   - Loads configuration from `config.txt`
   - Extracts zip to temporary directory
   - Runs `make` to compile code
   - Executes `./A1` with test input "Frodo"
   - Captures program output

4. **Grading occurs**:
   - Searches output for "Hello Frodo!"
   - Awards 100 points if found, 0 if not
   - Generates final grade

5. **Results displayed and saved**:
   ```
   Assignment A1 by student 123456 Marked: 100/100
   ```
   - Results are both displayed in console and saved to `autograder_output.txt`

## Configuration Tips

- **Test your configuration** by running the autograder on sample submissions
- **Use descriptive assignment names** that match your course structure
- **Multiple test inputs** are joined with newlines automatically
- **Date format** must be "YYYY-MM-DD" for due dates
- **Output matching** is case-sensitive and looks for exact substring matches

## License

This project is licensed under the MIT License - see the LICENSE file for details.