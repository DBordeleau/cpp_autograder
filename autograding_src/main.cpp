/*
Main autograder program.
Extracts, compiles, runs, and grades student C++ submissions
Takes student_id and assignment_id as command line arguments instead of parsing filename
*/

#include <iostream>
#include <filesystem>
#include <sqlite3.h>
#include "grader.h"
#include "tests.h"
#include "autograder.h"
#include "mark.h"

namespace fs = std::filesystem;

// Get autograder name from database using assignment_id
std::string getAutograderForAssignment(const std::string& assignmentId) {
    sqlite3* db;
    std::string dbPath = "/data/database.db";
    
    int rc = sqlite3_open(dbPath.c_str(), &db);
    if (rc) {
        std::cout << "Error: Cannot open database: " << sqlite3_errmsg(db) << std::endl;
        return "";
    }
    
    const char* sql = "SELECT autograder FROM assignments WHERE assignment_id = ?";
    sqlite3_stmt* stmt;
    
    rc = sqlite3_prepare_v2(db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        std::cout << "Error: Failed to prepare statement: " << sqlite3_errmsg(db) << std::endl;
        sqlite3_close(db);
        return "";
    }
    
    sqlite3_bind_text(stmt, 1, assignmentId.c_str(), -1, SQLITE_STATIC);
    
    std::string autograderName = "";
    if (sqlite3_step(stmt) == SQLITE_ROW) {
        const char* result = (const char*)sqlite3_column_text(stmt, 0);
        if (result) {
            autograderName = result;
        }
    }
    
    sqlite3_finalize(stmt);
    sqlite3_close(db);
    
    return autograderName;
}

// Check if assignment exists in database
bool assignmentExists(const std::string& assignmentId) {
    sqlite3* db;
    std::string dbPath = "/data/database.db";
    
    int rc = sqlite3_open(dbPath.c_str(), &db);
    if (rc) {
        std::cout << "Error: Cannot open database: " << sqlite3_errmsg(db) << std::endl;
        return false;
    }
    
    const char* sql = "SELECT COUNT(*) FROM assignments WHERE assignment_id = ?";
    sqlite3_stmt* stmt;
    
    rc = sqlite3_prepare_v2(db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        std::cout << "Error: Failed to prepare statement: " << sqlite3_errmsg(db) << std::endl;
        sqlite3_close(db);
        return false;
    }
    
    sqlite3_bind_text(stmt, 1, assignmentId.c_str(), -1, SQLITE_STATIC);
    
    bool exists = false;
    if (sqlite3_step(stmt) == SQLITE_ROW) {
        int count = sqlite3_column_int(stmt, 0);
        exists = (count > 0);
    }
    
    sqlite3_finalize(stmt);
    sqlite3_close(db);
    
    return exists;
}

// Load test inputs from database for this assignment
std::string getTestInputsFromDatabase(const std::string& assignmentId) {
    sqlite3* db;
    std::string dbPath = "/data/database.db";
    
    int rc = sqlite3_open(dbPath.c_str(), &db);
    if (rc) {
        std::cout << "Error: Cannot open database: " << sqlite3_errmsg(db) << std::endl;
        return "";
    }
    
    const char* sql = "SELECT input_data FROM tests WHERE assignment_id = ?";
    sqlite3_stmt* stmt;
    
    rc = sqlite3_prepare_v2(db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        std::cout << "Error: Failed to prepare test statement: " << sqlite3_errmsg(db) << std::endl;
        sqlite3_close(db);
        return "";
    }
    
    sqlite3_bind_text(stmt, 1, assignmentId.c_str(), -1, SQLITE_STATIC);
    
    std::string inputData = "";
    if (sqlite3_step(stmt) == SQLITE_ROW) {
        const char* result = (const char*)sqlite3_column_text(stmt, 0);
        if (result) {
            inputData = result;
        }
    }
    
    sqlite3_finalize(stmt);
    sqlite3_close(db);
    
    return inputData;
}

// Parse JSON input data and create input string
std::string parseInputsFromJSON(const std::string& jsonData) {
    if (jsonData.empty()) {
        return "";
    }
    
    std::string inputs = "";
    
    // Simple JSON array parser for ["input1", "input2", ...] format
    size_t start = jsonData.find('[');
    size_t end = jsonData.find(']');
    
    if (start == std::string::npos || end == std::string::npos) {
        return "";
    }
    
    std::string content = jsonData.substr(start + 1, end - start - 1);
    
    // Split by comma and extract strings
    size_t pos = 0;
    while (pos < content.length()) {
        size_t quote1 = content.find('"', pos);
        if (quote1 == std::string::npos) break;
        
        size_t quote2 = content.find('"', quote1 + 1);
        if (quote2 == std::string::npos) break;
        
        std::string input = content.substr(quote1 + 1, quote2 - quote1 - 1);
        inputs += input + "\n";
        
        pos = quote2 + 1;
    }
    
    return inputs;
}

int main(int argc, char* argv[]) {
    if (argc != 4) {
        std::cout << "Usage: " << argv[0] << " <zip_file_path> <student_id> <assignment_id>" << std::endl;
        return 1;
    }
    
    std::string zipPath = argv[1];      // /input.zip
    std::string studentId = argv[2];    // e.g., "101038853"
    std::string assignmentId = argv[3]; // e.g., "Assignment_2"
    
    std::cout << "Processing submission: Student " << studentId << ", Assignment " << assignmentId << std::endl;
    
    // Check if assignment exists in database
    if (!assignmentExists(assignmentId)) {
        std::cout << "Error: Assignment not found: " << assignmentId << std::endl;
        return 1;
    }
    
    std::cout << "Assignment found: " << assignmentId << std::endl;
    
    // Create temporary directory for extraction
    std::string extractDir = "/tmp/student_" + studentId;
    fs::create_directories(extractDir);
    
    // Extract the submission
    if (!unzipFile(zipPath, extractDir)) {
        std::cout << "Error: Failed to extract zip file" << std::endl;
        return 1;
    }
    
    // Compile the code
    if (!compileCode(extractDir)) {
        std::cout << "Error: Compilation failed" << std::endl;
        return 1;
    }
    
    // Get test inputs from database
    std::string testInputsJSON = getTestInputsFromDatabase(assignmentId);
    std::string testInputs = parseInputsFromJSON(testInputsJSON);
    
    // Run the compiled program with test inputs
    std::string testOutput;
    if (!testInputs.empty()) {
        std::cout << "Running test with inputs from database" << std::endl;
        testOutput = runProgram(extractDir, assignmentId, testInputs);
    } else {
        std::cout << "No test inputs found for assignment: " << assignmentId << std::endl;
        testOutput = "NO_TEST_DEFINED";
    }
    
    // Grade the output
    std::string autograderName = getAutograderForAssignment(assignmentId);
    if (autograderName.empty()) {
        std::cout << "Error: No autograder found for assignment: " << assignmentId << std::endl;
        return 1;
    }
    
    Autograder autograder(autograderName);
    Mark mark;
    autograder.grade(testOutput, mark);
    
    // Output results in JSON format for web app to parse
    std::cout << "{"
              << "\"student_id\":\"" << studentId << "\","
              << "\"assignment_id\":\"" << assignmentId << "\","
              << "\"score\":" << mark.getMark() << ","
              << "\"total\":" << mark.getOutOf() << ","
              << "\"output\":\"" << testOutput << "\""
              << "}" << std::endl;
    
    return 0;
}