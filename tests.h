#ifndef TESTS_H
#define TESTS_H

#include <string>

// Main function to run tests based on assignment name
std::string runTest(const std::string& assignmentName, const std::string& directory);

// Individual test functions for each assignment
std::string testAssignment1(const std::string& directory);
std::string testAssignment2(const std::string& directory);
// Add more test functions as needed

// Utility functions for running programs
std::string runProgram(const std::string& directory, const std::string& assignmentName, const std::string& input = "");
std::string runProgramWithTimeout(const std::string& directory, const std::string& input = "", int timeoutSeconds = 5);

#endif