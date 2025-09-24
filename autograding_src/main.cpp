/*
Main autograder program.
Extracts, compiles, runs, and grades student C++ submissions
*/

#include <iostream>
#include <filesystem>
#include <sqlite3.h>
#include "grader.h"
#include "tests.h"
#include "autograder.h"
#include "mark.h"

namespace fs = std::filesystem;

// Get autograder and test info from database
std::string getAutograderForAssignment(const std::string& assignmentName) {
    sqlite3* db;
    std::string dbPath = "../data/database.db";
    
    int rc = sqlite3_open(dbPath.c_str(), &db);
    if (rc) {
        std::cerr << "Can't open database: " << sqlite3_errmsg(db) << std::endl;
        return "";
    }
    
    const char* sql = "SELECT autograder FROM assignments WHERE assignment_id = ?";
    sqlite3_stmt* stmt;
    
    rc = sqlite3_prepare_v2(db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        std::cerr << "SQL prepare error: " << sqlite3_errmsg(db) << std::endl;
        sqlite3_close(db);
        return "";
    }
    
    sqlite3_bind_text(stmt, 1, assignmentName.c_str(), -1, SQLITE_STATIC);
    
    std::string autograderName = "";
    if (sqlite3_step(stmt) == SQLITE_ROW) {
        autograderName = (char*)sqlite3_column_text(stmt, 0);
    }
    
    sqlite3_finalize(stmt);
    sqlite3_close(db);
    
    return autograderName;
}

bool getTestInputs(const std::string& assignmentName, std::string inputs[], int& inputCount) {
    sqlite3* db;
    std::string dbPath = "../data/database.db";
    
    int rc = sqlite3_open(dbPath.c_str(), &db);
    if (rc) {
        std::cerr << "Can't open database: " << sqlite3_errmsg(db) << std::endl;
        return false;
    }
    
    const char* sql = "SELECT input_data FROM tests WHERE assignment_id = ?";
    sqlite3_stmt* stmt;
    
    rc = sqlite3_prepare_v2(db, sql, -1, &stmt, NULL);
    sqlite3_bind_text(stmt, 1, assignmentName.c_str(), -1, SQLITE_STATIC);
    
    inputCount = 0;
    if (sqlite3_step(stmt) == SQLITE_ROW) {
        const char* json = (const char*)sqlite3_column_text(stmt, 0);
        
        std::string jsonStr(json);
        size_t pos = 0;
        while (pos < jsonStr.length() && inputCount < 10) {
            size_t start = jsonStr.find('"', pos);
            if (start == std::string::npos) break;
            
            size_t end = jsonStr.find('"', start + 1);
            if (end == std::string::npos) break;
            
            inputs[inputCount] = jsonStr.substr(start + 1, end - start - 1);
            inputCount++;
            pos = end + 1;
        }
    }
    
    sqlite3_finalize(stmt);
    sqlite3_close(db);
    
    return inputCount > 0;
}

int main(int argc, char* argv[]) {
    if (argc != 2) {
        std::cerr << "Usage: " << argv[0] << " <zip_file_path>" << std::endl;
        return 1;
    }
    
    std::string zipPath = argv[1];
    
    // Parse filename to get assignment info
    std::string filename = fs::path(zipPath).filename().string();
    auto [studentId, assignmentName] = parseFilename(filename);
    
    if (studentId == -1 || assignmentName.empty()) {
        std::cout << "Invalid filename format: " << filename << std::endl;
        return 1;
    }
    
    std::cout << "Processing single zip file: " << zipPath << std::endl;
    
    std::string autograderName = getAutograderForAssignment(assignmentName);
    if (autograderName.empty()) {
        std::cout << "Assignment " << assignmentName << " not found in database" << std::endl;
        return 1;
    }
    
    std::string testInputs[10];
    int inputCount;
    if (!getTestInputs(assignmentName, testInputs, inputCount)) {
        std::cout << "No test defined for assignment " << assignmentName << std::endl;
        return 1;
    }
    
    // create temporary directory for extraction
    std::string tempDir = "/tmp/grading_" + std::to_string(studentId) + "_" + assignmentName;
    std::cout << "Creating temp directory: " << tempDir << std::endl;
    fs::create_directories(tempDir);
    
    // unzip and compile
    if (!unzipFile(zipPath, tempDir)) {
        std::cout << "Failed to unzip: " << filename << std::endl;
        fs::remove_all(tempDir);
        return 1;
    }
    
    std::string output = "";
    if (compileCode(tempDir)) {
        // Build input string from database inputs
        std::string input = "";
        for (int i = 0; i < inputCount; ++i) {
            input += testInputs[i] + "\n";
        }
        output = runProgram(tempDir, assignmentName, input);
    } else {
        output = "COMPILATION_FAILED";
    }
    
    Autograder autograder(autograderName);
    Mark mark;
    autograder.grade(output, mark);
    
    std::cout << "Assignment " << assignmentName << " by student " << studentId 
              << " Graded: " << mark.getMark() << "/" << mark.getOutOf() << std::endl;
    
    // Clean up
    fs::remove_all(tempDir);
    
    return 0;
}