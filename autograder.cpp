/*
Autograder class is responsible for grading student submissions once the grader has unzipped and compiled the submission code.
It contains an array of output items and corresponding grade values.
The grade function checks the student's output for each item and sums the corresponding values to produce a final mark.

Example: If an autograder has 2 items: "Hello World" worth 50 points and "Goodbye World" worth 50 points,
and the student's output contains both strings, they receive a mark of 100/100.

If the student's output only contains one of "Hello World" or "Goodbye World", they receive a mark of 50/100.
If the student's output contains neither string, they receive a mark of 0/100.
*/

#include "autograder.h"

Autograder::Autograder() {
    numItems = 0;
}

Autograder::Autograder(const std::string items[], const int values[], int count) {
    numItems = (count > MAX_AUTOGRADE_ITEMS) ? MAX_AUTOGRADE_ITEMS : count;
    for (int i = 0; i < numItems; ++i) {
        outputItems[i] = items[i];
        gradeValues[i] = values[i];
    }
}

// Grade the student's output based on the autograder items.
// If the student's output contains an item, they get the corresponding grade value.
// The total mark is the sum of all matched items, out of the total possible points.
void Autograder::grade(std::string studentOutput, Mark &mark) {
    std::cout << "Grading output: '" << studentOutput << "'" << std::endl;
    
    int totalMarks = 0;
    int totalOutOf = 0;
    
    for (int i = 0; i < numItems; ++i) {
        totalOutOf += gradeValues[i];
        std::cout << "Looking for: '" << outputItems[i] << "'" << std::endl;

        if (studentOutput.find(outputItems[i]) != std::string::npos) {
            totalMarks += gradeValues[i];
            std::cout << "Found! Added " << gradeValues[i] << " points" << std::endl;
        } else {
            std::cout << "Not found!" << std::endl;
        }
    }
    
    mark.setMark(totalMarks, totalOutOf);
    std::cout << "Final grade: " << totalMarks << "/" << totalOutOf << std::endl;
}
