/*
Submission class represents a student's submission for an assignment. The assignment class maintains an array of submissions.
The submission is what is graded by the autograder. The submissionOutput is what is searched by the autograder to determine the mark.
For every string in the autograder's outputItems array that is found in the submissionOutput, the corresponding value in the gradeValues array is added to the mark.
*/

#include "submission.h"

Submission::Submission(int studentId, const std::string& assignmentName, const std::string& submissionOutput, const Date& submissionDate, const Mark& mark) {
    this->studentId = studentId;
    this->assignmentName = assignmentName;
    this->submissionOutput = submissionOutput;
    this->submissionDate = submissionDate;
    this->mark = mark;
}

// Getter functions
std::string Submission::getOutput() const {
    return submissionOutput;
}

int Submission::getStudentId() const {
    return studentId;
}

std::string Submission::getAssignmentName() const {
    return assignmentName;
}

Date Submission::getSubmissionDate() const {
    return submissionDate;
}

// Returns true if this submission matches the given student ID and submission date.
bool Submission::equals(int studentId, const Date& submissionDate) const {
    return (this->studentId == studentId && this->submissionDate.equals(submissionDate));
}

// Print submission details formatted on multiple lines
void Submission::print() {
    std::cout << "Student ID: " << studentId << std::endl;
    std::cout << "Assignment Name: " << assignmentName << std::endl;
    std::cout << "Submission Date: " << submissionDate.toString() << std::endl;
    std::cout << "Submission Output: " << submissionOutput << std::endl;
    std::cout << "Mark: ";
    mark.print();
}

void Submission::setMark(const Mark& newMark) {
    this->mark = newMark;
}

void Submission::printMark() {
    std::cout << "Assignment " << assignmentName << " by student " << studentId << " Graded: " << mark.print() << std::endl;
}