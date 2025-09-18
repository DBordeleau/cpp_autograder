# C++ Autograder System

A simple autograding system for C++ programming assignments. This tool automatically extracts, compiles, runs, and grades student submissions based on expected output criteria.

## Features

- **Automated grading** of C++ programming assignments
- **Flexible test configuration** with custom input/output scenarios
- **Support for multiple assignments** with different grading criteria
- **Batch processing** of multiple submissions across multiple assignments.

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

### Defining Assignments and Grading Criteria

1. **Define the autograder** in `main.cpp`:
```cpp
std::string items[] = {"Expected Output 1", "Expected Output 2"};
int values[] = {40, 60};
Autograder autograder1(items, values, 1);
```

2. **Create the assignment**:
```cpp
assignments[assignmentCount] = Assignment("A1", "First Assignment", 
                                        Date(2025, 10, 22), autograder2);
assignmentCount++;
```

3. **Add test function** in `tests.cpp`:
```cpp
std::string testAssignment1(const std::string& directory) {
    std::string input = "5\n10\n";  // Multiple inputs separated with new lines
    return runProgram(directory, "A1", input);
}
```

4. **Update the test router** in `tests.cpp`:
```cpp
std::string runTest(const std::string& assignmentName, const std::string& directory) {
    if (assignmentName == "A1") {
        return testAssignment1(directory);
    } else if (assignmentName == "A2") {
        return testAssignment2(directory);
    }
    // ... more cases
}
```

## 📁 Project Structure

```
autograder/
├── main.cpp              # Assignment/autograder configuration
├── grader.h/cpp          # Core grading utilities (zip extraction, compilation)
├── tests.h/cpp           # Test definitions and program execution
├── assignment.h/cpp      # Assignment class and submission management
├── autograder.h/cpp      # Grading logic and criteria matching
├── submission.h/cpp      # Individual submission representation
├── mark.h/cpp            # Grade calculation
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

1. **Student submits** `123456_A1.zip` containing:
   ```
   main.cpp
   Makefile
   ```
- Store student submissions in the same directory.
- Run the autograder with the path to this directory as the only argument.

2. **Autograder processes**:
   - Extracts zip to temporary directory
   - Runs `make` to compile code
   - Executes `./A1` with test input
   - Captures program output

3. **Grading occurs**:
   - Searches output for expected strings
   - Awards points for matches
   - Generates final grade

4. **Results displayed**:
   ```
   Assignment A1 by student 123456 Marked: 85/100
   ```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

For questions or issues, please open a GitHub issue or contact me directly.
