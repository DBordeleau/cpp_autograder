/*
Autograder class is responsible for grading student submissions once the grader has unzipped and compiled the submission code.
It loads its configuration from the database.
The grade function checks the student's output for each item and sums the corresponding values to produce a final mark.
*/

#include "autograder.h"
#include <sqlite3.h>
#include <cstring>

Autograder::Autograder() {
    numItems = 0;
}

Autograder::Autograder(const std::string items[], const int values[], int count) {
    numItems = (count > MAX_AUTOGRADE_ITEMS) ? MAX_AUTOGRADE_ITEMS : count;
    for (int i = 0; i < numItems; ++i) {
        outputItems[i] = items[i];
        gradeValues[i] = values[i];
    }
}

Autograder::Autograder(const std::string& autograderName) {
    numItems = 0;
    loadFromDatabase(autograderName);
}

bool Autograder::loadFromDatabase(const std::string& autograderName) {
    sqlite3* db;
    std::string dbPath = "/data/database.db";
    
    int rc = sqlite3_open(dbPath.c_str(), &db);
    if (rc) {
        std::cerr << "Can't open database: " << sqlite3_errmsg(db) << std::endl;
        return false;
    }
    
    const char* sql = "SELECT outputs, grade_weights FROM autograders WHERE name = ?";
    sqlite3_stmt* stmt;
    
    rc = sqlite3_prepare_v2(db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        std::cerr << "SQL prepare error: " << sqlite3_errmsg(db) << std::endl;
        sqlite3_close(db);
        return false;
    }
    
    sqlite3_bind_text(stmt, 1, autograderName.c_str(), -1, SQLITE_STATIC);
    
    bool found = false;
    if (sqlite3_step(stmt) == SQLITE_ROW) {
        found = true;
        
        // Get JSON strings
        const char* outputs_json = (const char*)sqlite3_column_text(stmt, 0);
        const char* weights_json = (const char*)sqlite3_column_text(stmt, 1);
        
        parseOutputsFromJSON(outputs_json);
        parseWeightsFromJSON(weights_json);
        
        std::cout << "Loaded autograder '" << autograderName << "' from database with " << numItems << " items" << std::endl;
    }
    
    sqlite3_finalize(stmt);
    sqlite3_close(db);
    
    return found;
}

// JSON parser for ["item1", "item2", "item3"] format
void Autograder::parseOutputsFromJSON(const char* json) {
    if (!json) return;
    
    std::string jsonStr(json);
    numItems = 0;
    
    // Find all strings between quotes
    size_t pos = 0;
    while (pos < jsonStr.length() && numItems < MAX_AUTOGRADE_ITEMS) {
        size_t start = jsonStr.find('"', pos);
        if (start == std::string::npos) break;
        
        size_t end = jsonStr.find('"', start + 1);
        if (end == std::string::npos) break;
        
        outputItems[numItems] = jsonStr.substr(start + 1, end - start - 1);
        numItems++;
        pos = end + 1;
    }
}

// JSON parser for [50, 50, 100] format
void Autograder::parseWeightsFromJSON(const char* json) {
    if (!json) return;
    
    std::string jsonStr(json);
    int weightIndex = 0;
    
    // Find all numbers
    size_t pos = 0;
    while (pos < jsonStr.length() && weightIndex < numItems) {
        // Skip non-digits
        while (pos < jsonStr.length() && !std::isdigit(jsonStr[pos])) {
            pos++;
        }
        
        if (pos >= jsonStr.length()) break;
        
        // Extract number
        size_t start = pos;
        while (pos < jsonStr.length() && std::isdigit(jsonStr[pos])) {
            pos++;
        }
        
        std::string numberStr = jsonStr.substr(start, pos - start);
        gradeValues[weightIndex] = std::stoi(numberStr);
        weightIndex++;
    }
}

// Grade the student's output based on the autograder items.
// If the student's output contains an item, they get the corresponding grade value.
// The total mark is the sum of all matched items, out of the total possible points.
void Autograder::grade(std::string studentOutput, Mark &mark) {
    std::cout << "=== GRADING RESULTS ===" << std::endl;
    std::cout << "Grading output: '" << studentOutput << "'" << std::endl;
    
    int totalMarks = 0;
    int totalOutOf = 0;
    
    for (int i = 0; i < numItems; ++i) {
        totalOutOf += gradeValues[i];
        std::cout << "Looking for: '" << outputItems[i] << "'" << std::endl;

        if (studentOutput.find(outputItems[i]) != std::string::npos) {
            totalMarks += gradeValues[i];
            std::cout << "Found! Added " << gradeValues[i] << " points" << std::endl;
        } else {
            std::cout << "Not found!" << std::endl;
        }
    }
    
    mark.setMark(totalMarks, totalOutOf);
    std::cout << "Final grade: " << totalMarks << "/" << totalOutOf << std::endl;
}