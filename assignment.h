#ifndef ASSIGNMENT_H
#define ASSIGNMENT_H

#include <string>
#include <iostream>
#include "date.h"
#include "submission.h"
#include "autograder.h"

#define MAX_SUBMISSION_COUNT 100

class Assignment {
private:
    std::string name;
    std::string description;
    Date dueDate;
    Submission* submissions[MAX_SUBMISSION_COUNT];
    int submissionCount;
    Autograder autograder;
public:
    Assignment();
    Assignment(const std::string& name, const std::string& description, const Date& dueDate, const Autograder& autograder);
    void updateDueDate(const Date& dueDate);
    bool addSubmission(int studentId, const std::string& submissionOutput, const Date& submissionDate);
    bool removeSubmission(int studentId, const Date& submissionDate);
    std::string getName() const;
    Date getDueDate() const;
    void print();
    void printAllSubmissions();
    void printSubmissionByStudent(int studentId);
    void gradeAllSubmissions();
};

#endif