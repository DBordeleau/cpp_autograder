/*
Tests for various assignments. Modify the runTest function to specify which tests to run for each assignment.
Every test function you create should return the result of runProgram, which handles execution and output capture.
runProgram assumed the compiled binary is named the same as the assignment name. If it isn't, modify runProgram accordingly.
*/

#include "tests.h"
#include <iostream>
#include <fstream>
#include <cstdlib>
#include <unistd.h>
#include <sys/wait.h>
#include <signal.h>

// Main function to run tests based on assignment name
std::string runTest(const std::string& assignmentName, const std::string& directory) {
    if (assignmentName == "A1") {
        return testAssignment1(directory);
    } else if (assignmentName == "Assignment 2") {
        return testAssignment2(directory);
    } else {
        std::cout << "No test defined for assignment " << assignmentName << std::endl;
        return "NO_TEST_DEFINED";
    }
}

// Individual test functions for each assignment
std::string testAssignment1(const std::string& directory) {
    // Test that inputs "Frodo" and expects "Hello Frodo!" output
    std::string input = "Frodo\n";
    return runProgram(directory, "A1", input);
}

std::string testAssignment2(const std::string& directory) {
    // Example test with specific input
    std::string input = "5\n10\n";  // Simulate user entering "5" then "10"
    return runProgram(directory, "A2", input);
}

// Utility function to run a program in a given directory with optional input and capture its output.
std::string runProgram(const std::string& directory, const std::string& assignmentName, const std::string& input) {
    std::string tempOutputFile = "/tmp/output_" + std::to_string(getpid()) + ".txt";
    std::string tempInputFile = "/tmp/input_" + std::to_string(getpid()) + ".txt";
    
    // Write input to temporary file if provided
    if (!input.empty()) {
        std::ofstream inputFile(tempInputFile);
        inputFile << input;
        inputFile.close();
        std::cout << "Input written to temp file: '" << input << "'" << std::endl;
    }
    
    // Build command - executable name matches assignment name
    std::string executable = "./" + assignmentName;
    std::string command = "cd \"" + directory + "\" && ";
    if (!input.empty()) {
        command += executable + " < " + tempInputFile + " > " + tempOutputFile + " 2>&1";
    } else {
        command += executable + " > " + tempOutputFile + " 2>&1";
    }
    
    std::cout << "Running command: " << command << std::endl;
    int result = system(command.c_str());
    std::cout << "Program exit code: " << result << std::endl;
    
    // Read output
    std::ifstream file(tempOutputFile);
    std::string output, line;
    while (std::getline(file, line)) {
        output += line + "\n";
    }
    file.close();
    
    std::cout << "Program output: '" << output << "'" << std::endl;
    
    // Clean up temp files
    remove(tempOutputFile.c_str());
    if (!input.empty()) {
        remove(tempInputFile.c_str());
    }
    
    // If program failed to run, include error info
    if (result != 0) {
        output += "\n[PROGRAM_EXECUTION_ERROR: Exit code " + std::to_string(result) + "]";
    }
    
    return output;
}