#ifndef GRADER_H
#define GRADER_H

#include <string>
#include "assignment.h"

// Utility functions for grading
std::pair<int, std::string> parseFilename(const std::string& filename);
bool unzipFile(const std::string& zipPath, const std::string& extractPath);
bool compileCode(const std::string& directory);
Assignment* findAssignment(Assignment assignments[], int assignmentCount, const std::string& assignmentName);
void processZipFile(const std::string& zipPath, Assignment assignments[], int assignmentCount);

#endif