#ifndef TESTS_H
#define TESTS_H

#include <string>
#include <map>

// Forward declaration
struct TestConfig;

// Function to load test configurations
void loadTestConfigs(const std::map<std::string, TestConfig>& configs);

// Main function to run tests based on assignment name
std::string runTest(const std::string& assignmentName, const std::string& directory);

// Function to run test from configuration
std::string runTestFromConfig(const TestConfig& config, const std::string& directory);

// Individual test functions for each assignment (for backward compatibility)
std::string testAssignment1(const std::string& directory);
std::string testAssignment2(const std::string& directory);

// Utility functions for running programs
std::string runProgram(const std::string& directory, const std::string& assignmentName, const std::string& input = "");
std::string runProgramWithTimeout(const std::string& directory, const std::string& input = "", int timeoutSeconds = 5);

#endif