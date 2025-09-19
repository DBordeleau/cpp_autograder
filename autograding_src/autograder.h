#ifndef AUTOGRADER_H
#define AUTOGRADER_H

#include <string>
#include "mark.h"

#define MAX_AUTOGRADE_ITEMS 100

class Autograder {
private:
    std::string outputItems[MAX_AUTOGRADE_ITEMS];
    int gradeValues[MAX_AUTOGRADE_ITEMS];
    int numItems;
public:
    Autograder();
    Autograder(const std::string items[], const int values[], int count);
    void grade(std::string student_output, Mark &mark);
};

#endif