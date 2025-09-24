#ifndef AUTOGRADER_H
#define AUTOGRADER_H

#include <string>
#include <iostream>
#include "mark.h"

const int MAX_AUTOGRADE_ITEMS = 100;

class Autograder {
public:
    Autograder();
    Autograder(const std::string items[], const int values[], int count);
    
    // constructor that loads autograder parameters from database
    Autograder(const std::string& autograderName);
    
    void grade(std::string studentOutput, Mark &mark);
    
    bool loadFromDatabase(const std::string& autograderName);
    
    int getNumItems() const { return numItems; }
    std::string getOutputItem(int index) const { return outputItems[index]; }
    int getGradeValue(int index) const { return gradeValues[index]; }

// Add these private method declarations to autograder.h
private:
    std::string outputItems[MAX_AUTOGRADE_ITEMS];
    int gradeValues[MAX_AUTOGRADE_ITEMS];
    int numItems;
    
    // JSON parsing helper methods
    void parseOutputsFromJSON(const char* json);
    void parseWeightsFromJSON(const char* json);
};

#endif