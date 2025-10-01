/*
This file contains utility functions for handling zip files, compiling code, and processing submissions.
Each submission is a zip file named in the format <student_id>_<assignment_name>.zip
The binary to run after compilation must be named the same as the assignment name.
*/

#include "grader.h"
#include "tests.h"
#include <iostream>
#include <filesystem>
#include <cstdlib>
#include <unistd.h> 
#include <fstream>

namespace fs = std::filesystem;

// Extract student ID and assignment name.
std::pair<int, std::string> parseFilename(const std::string& filename) {
    size_t underscorePos = filename.find('_');
    size_t dotPos = filename.find(".zip");
    
    if (underscorePos == std::string::npos || dotPos == std::string::npos) {
        return {-1, ""}; // Invalid format
    }
    
    int studentId = std::stoi(filename.substr(0, underscorePos));
    std::string assignmentName = filename.substr(underscorePos + 1, dotPos - underscorePos - 1);

    return {studentId, assignmentName};
}

// Unzips the file at zipPath into the directory extractPath.
// Returns true if successful, false otherwise. If this fails the assignment will be graded as 0.
bool unzipFile(const std::string& zipPath, const std::string& extractPath) {
    std::string command = "unzip -q \"" + zipPath + "\" -d \"" + extractPath + "\"";
    std::cout << "Running command: " << command << std::endl;
    
    int result = system(command.c_str());
    std::cout << "Unzip result code: " << result << std::endl;
    
    // Check if extraction was successful by looking for files
    if (fs::exists(extractPath) && !fs::is_empty(extractPath)) {
        std::cout << "Extraction successful, contents:" << std::endl;
        for (const auto& entry : fs::directory_iterator(extractPath)) {
            std::cout << "  " << entry.path().filename() << std::endl;
        }
        return true;
    } else {
        std::cout << "Error: Extraction failed or directory is empty" << std::endl;
        return false;
    }
}

// Attempts to compile the extracted code using the Makefile in the directory.
// Returns true if compilation was successful, false otherwise.
// If compilation fails the assignment will be graded as 0.
bool compileCode(const std::string& directory) {
    std::string command = "cd \"" + directory + "\" && make";
    return system(command.c_str()) == 0;
}

Assignment* findAssignment(Assignment assignments[], int assignmentCount, const std::string& assignmentName) {
    for (int i = 0; i < assignmentCount; ++i) {
        if (assignments[i].getName() == assignmentName) {
            return &assignments[i];
        }
    }
    return nullptr;
}

void processZipFile(const std::string& zipPath, Assignment assignments[], int assignmentCount) {
    std::cout << "Looking for zip file at: " << zipPath << std::endl;
    if (!fs::exists(zipPath)) {
        std::cout << "ERROR: Zip file does not exist!" << std::endl;
        return;
    }
    
    std::string filename = fs::path(zipPath).filename().string();
    auto [studentId, assignmentName] = parseFilename(filename);
    
    if (studentId == -1 || assignmentName.empty()) {
        std::cout << "Invalid filename format: " << filename << std::endl;
        return;
    }
    
    Assignment* assignment = findAssignment(assignments, assignmentCount, assignmentName);
    if (!assignment) {
        std::cout << "Assignment " << assignmentName << " not found for student " << studentId << std::endl;
        return;
    }
    
    std::string output = runInDocker(zipPath, assignmentName, studentId);
    Date submissionDate = Date();
    
    if (assignment->addSubmission(studentId, output, submissionDate)) {
        std::cout << "Added submission for student " << studentId << " to assignment " << assignmentName << std::endl;
    } else {
        std::cout << "Failed to add submission for student " << studentId << std::endl;
    }
}

// Grade inside docker container
std::string runInDocker(const std::string& zipPath, const std::string& assignmentName, int studentId) {
    std::string containerName = "grader_" + std::to_string(studentId) + "_" + std::to_string(time(nullptr));
    
    std::string command = "docker run --rm --name " + containerName + 
                         " --memory=128m --cpus=0.5 --network=none" +
                         " --read-only --tmpfs /tmp:noexec,nosuid,size=50m" +
                         " -v \"" + zipPath + ":/input.zip:ro\"" +
                         " -v \"" + fs::current_path().parent_path().string() + "/data:/data:ro\"" +
                         " autograder:latest ./autograding_src/main /input.zip";
    
    std::cout << "Running Docker command: " << command << std::endl;
    
    std::string tempOutputFile = "/tmp/docker_output_" + std::to_string(getpid()) + ".txt";
    command += " > " + tempOutputFile + " 2>&1";
    
    int result = system(command.c_str());
    
    std::ifstream file(tempOutputFile);
    std::string output, line;
    while (std::getline(file, line)) {
        output += line + "\n";
    }
    file.close();
    remove(tempOutputFile.c_str());
    
    if (result != 0) {
        output += "\n[DOCKER_EXECUTION_ERROR: Exit code " + std::to_string(result) + "]";
    }
    
    return output;
}