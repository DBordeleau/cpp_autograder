/*
Tests for various assignments. Modify the runTest function to specify which tests to run for each assignment.
Every test function you create should return the result of runProgram, which handles execution and output capture.
runProgram assumed the compiled binary is named the same as the assignment name. If it isn't, modify runProgram accordingly.
*/

#include "tests.h"
#include "config.h"
#include <iostream>
#include <fstream>
#include <cstdlib>
#include <unistd.h>
#include <sys/wait.h>
#include <signal.h>
#include <filesystem>

namespace fs = std::filesystem;

// Utility function to check if a file exists
bool fileExists(const std::string& path) {
    return fs::exists(path);
}

// Global variable to store test configurations
static std::map<std::string, TestConfig> testConfigs;

void loadTestConfigs(const std::map<std::string, TestConfig>& configs) {
    testConfigs = configs;
}

std::string runTest(const std::string& assignmentName, const std::string& directory) {
    // Look for a test configuration for this assignment
    for (const auto& pair : testConfigs) {
        const TestConfig& config = pair.second;
        if (config.assignmentName == assignmentName) {
            return runTestFromConfig(config, directory);
        }
    }
    
    std::cout << "No test defined for assignment " << assignmentName << std::endl;
    return "NO_TEST_DEFINED";
}

std::string runTestFromConfig(const TestConfig& config, const std::string& directory) {
    std::string input = "";
    
    // Combine all inputs with newlines
    for (int i = 0; i < config.inputCount; ++i) {
        input += config.inputs[i] + "\n";
    }
    
    return runProgram(directory, config.assignmentName, input);
}

/*
std::string testAssignment1(const std::string& directory) {
    std::string input = "Frodo\n";
    return runProgram(directory, "A1", input);
}

std::string testAssignment2(const std::string& directory) {
    std::string input = "5\n10\n";
    return runProgram(directory, "A2", input);
}
*/

// Utility function to run a program in a given directory with optional input and capture its output.
std::string runProgram(const std::string& directory, const std::string& assignmentName, const std::string& input) {
    std::string binaryPath = directory + "/" + assignmentName;
    
    // Simplified debug - remove commands that don't exist in container
    std::cout << "Checking binary: " << binaryPath << std::endl;
    if (fileExists(binaryPath)) {
        std::cout << "Binary exists" << std::endl;
        
        // Check permissions with ls (which exists in container)
        std::string lsCommand = "ls -la \"" + binaryPath + "\" | cut -d' ' -f1";
        system(lsCommand.c_str());
        std::cout << "Permissions before chmod: ";
        
        // Make executable
        std::string chmodCommand = "chmod +x \"" + binaryPath + "\"";
        std::cout << "Running: " << chmodCommand << std::endl;
        int chmodResult = system(chmodCommand.c_str());
        std::cout << "chmod exit code: " << chmodResult << std::endl;
        
        // Check permissions after
        system(lsCommand.c_str());
        std::cout << "Permissions after chmod: ";
    } else {
        std::cout << "Binary does not exist!" << std::endl;
        return "[BINARY_NOT_FOUND]";
    }
    
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