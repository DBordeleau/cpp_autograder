#ifndef SUBMISSION_H
#define SUBMISSION_H

#include <string>
#include "date.h"
#include "mark.h"

class Submission {
private:
    int studentId;
    std::string assignmentName;
    std::string submissionOutput;
    Date submissionDate;
    Mark mark;
public:
    Submission(int studentId, const std::string& assignmentName, const std::string& submissionOutput, const Date& submissionDate, const Mark& mark);
    std::string getOutput() const;
    int getStudentId() const;
    std::string getAssignmentName() const;
    Date getSubmissionDate() const;
    bool equals(int studentId, const Date& submissionDate) const;
    void setMark(const Mark& newMark);
    void print();
    void printMark();
    void printMark(std::ofstream& outputFile);
};

#endif