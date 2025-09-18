/*
Compilation: Run `make` in the terminal to compile the program.
Execution: Run the compiled binary with a zip file or directory of zip files to be graded as the only argument

This project is configured by default so that programs to be graded must be contained in 
zip files named in the format <student_id>_<assignment_name>.zip
For example: 123456_A1.zip for student ID 123456 submitting assignment A1

The zip file should contain a makefile and all required dependencies to compile the code.
The binary produced by the makefile must be named the same as the assignment name to be graded.

This main file is where you define assignments and their autograder criteria.
Autograders are defined by specifying expected output strings and the points associated with each string.
For example: if an assignment has 2 test cases worth 50 points each, you would define the autograder like this:
std::string items[] = {"Test case 1 output", "Test case 2 output"};
int values[] = {50, 50};
Autograder autograder1(items, values, 2);

You can then create an assignment using this autograder:
assignments[assignmentCount] = Assignment("Assignment Name", "Assignment description", Date(2025, 10, 15), autograder1);
assignmentCount++;

If you need to provide input for an assignment, you can define specific tests for each assignment in tests.cpp and tests.h
*/

#include <iostream>
#include <string>
#include <filesystem>
#include <fstream>
#include "assignment.h"
#include "grader.h"
#include "config.h"
#include "tests.h"

namespace fs = std::filesystem;

int main(int argc, char* argv[]) {
    if (argc != 2) {
        std::cout << "Usage: " << argv[0] << " <filename of .zip file> or <filepath to directory of .zip files>" << std::endl;
        return 1;
    }
    
    // Load configuration
    ConfigParser parser;
    if (!parser.loadConfig("config.txt")) {
        std::cout << "Error: Could not load configuration file" << std::endl;
        return 1;
    }
    
    // Create assignments from configuration using arrays
    Assignment assignments[MAX_ASSIGNMENTS];
    int assignmentCount = parser.createAssignments(assignments, MAX_ASSIGNMENTS);
    
    if (assignmentCount == 0) {
        std::cout << "Error: No valid assignments found in configuration" << std::endl;
        return 1;
    }
    
    // Load test configurations
    loadTestConfigs(parser.getTests());
    
    std::cout << "Loaded " << assignmentCount << " assignments from configuration" << std::endl;
    
    std::string inputPath = argv[1];
    
    if (fs::is_regular_file(inputPath) && inputPath.ends_with(".zip")) {
        std::cout << "Processing single zip file: " << inputPath << std::endl;
        processZipFile(inputPath, assignments, assignmentCount);
    } else if (fs::is_directory(inputPath)) {
        std::cout << "Processing directory: " << inputPath << std::endl;
        for (const auto& entry : fs::directory_iterator(inputPath)) {
            if (entry.is_regular_file() && entry.path().extension() == ".zip") {
                processZipFile(entry.path().string(), assignments, assignmentCount);
            }
        }
    } else {
        std::cout << "Invalid input: " << inputPath << " (must be a zip file or directory)" << std::endl;
        return 1;
    }
    
    // Grade all submissions and print results
    std::cout << "\n=== GRADING RESULTS ===" << std::endl;
    
    std::ofstream outputFile("autograder_output.txt");
    if (outputFile.is_open()) {
        outputFile << "=== AUTOGRADER RESULTS ===" << std::endl;
        
        for (int i = 0; i < assignmentCount; ++i) {
            assignments[i].gradeAllSubmissions(outputFile);
        }
        
        outputFile.close();
        std::cout << "\nResults saved to autograder_output.txt" << std::endl;
    } else {
        std::cout << "Warning: Could not create output file, printing to console only" << std::endl;
        for (int i = 0; i < assignmentCount; ++i) {
            assignments[i].gradeAllSubmissions();
        }
    }
    
    return 0;
}