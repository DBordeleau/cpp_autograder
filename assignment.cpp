/*
Assignment class represents an assignment with a name, description, due date, and an autograder
It maintains an array of submissions made by students for this assignment.
The autograder is used to grade each submission based on its output.
*/

#include "assignment.h"

Assignment::Assignment() {
    this->name = "";
    this->description = "";
    this->dueDate = Date(); // Uses Date's default constructor
    this->autograder = Autograder(); // Uses Autograder's default constructor
    this->submissionCount = 0;

    for (int i = 0; i < MAX_SUBMISSION_COUNT; ++i) {
        submissions[i] = nullptr;
    }
}

Assignment::Assignment(const std::string& name, const std::string& description, const Date& dueDate, const Autograder& autograder) {
    this->name = name;
    this->description = description;
    this->dueDate = dueDate;
    this->autograder = autograder;
    this->submissionCount = 0;

    for (int i = 0; i < MAX_SUBMISSION_COUNT; ++i) {
        submissions[i] = nullptr;
    }
}

// Update the due date of the assignment.
void Assignment::updateDueDate(const Date& dueDate) {
    this->dueDate = dueDate;
}

// Attempt to add a submission to the submissions array.
// Return true if successful, false if the array is full or a duplicate submission.
// Or if the submission date is after the due date.
bool Assignment::addSubmission(int studentId, const std::string& submissionOutput, const Date& submissionDate) {
    if (submissionCount >= MAX_SUBMISSION_COUNT) {
        return false;
    }

    if (dueDate.lessThan(submissionDate)) {
        return false;
    }

    for (int i = 0; i < submissionCount; ++i) {
        if (submissions[i]->equals(studentId, submissionDate)) {
            return false;
        }
    }

    submissions[submissionCount] = new Submission(studentId, name, submissionOutput, submissionDate, Mark());
    submissionCount++;

    return true;
}

// Attempt to remove a submission from the submissions array.
// Return true if successful, false if not found.
bool Assignment::removeSubmission(int studentId, const Date& submissionDate) {
    for (int i = 0; i < submissionCount; ++i) {
        if (submissions[i]->equals(studentId, submissionDate)) {
            delete submissions[i];
            // No need to maintain order so swap with last element instead of shifting
            submissions[i] = submissions[submissionCount - 1];
            submissions[submissionCount - 1] = nullptr;
            submissionCount--;
            return true;
        }
    }
    return false;
}

// Getter functions
std::string Assignment::getName() const {
    return name;
}

Date Assignment::getDueDate() const {
    return dueDate;
}

// Prints assignment details formatted on multiple lines
void Assignment::print() {
    std::cout << "Assignment: " << name << "\n";
    std::cout << "Name: " << name << "\n";
    std::cout << "Description: " << description << "\n";
    std::cout << "Due Date: " << dueDate.toString() << "\n";
}

// Print all submissions for this assignment
void Assignment::printAllSubmissions() {
    if (submissionCount > 0) {
        std::cout << "All Submissions for Assignment " << name << ":\n";
        for (int i = 0; i < submissionCount; ++i) {
            submissions[i]->print();
            std::cout << "\n";
    }
} else {
        std::cout << "No submissions found for assignment: " << name << ".\n";
    }
}

// Print submissions for a specific student
void Assignment::printSubmissionByStudent(int studentId) {
    bool found = false;
    for (int i = 0; i < submissionCount; ++i) {
        if (submissions[i]->getStudentId() == studentId) {
            if (!found) {
                std::cout << "Submissions for Student ID " << studentId << ":\n";
                found = true;
            }
            submissions[i]->print();
            std::cout << "\n";
        }
    }
    if (!found) {
        std::cout << "No submissions found for Student ID " << studentId << ".\n";
    }
}

void Assignment::gradeAllSubmissions() {
    for (int i = 0; i < submissionCount; ++i) {
        Mark newMark;
        autograder.grade(submissions[i]->getOutput(), newMark);
        
        submissions[i]->setMark(newMark);
        
        submissions[i]->printMark();
    }
}