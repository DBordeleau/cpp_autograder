/*
Parses text in the config.txt file and creates the corresponding assignments, autograders, and tests.
*/

#include "config.h"
#include <fstream>
#include <iostream>
#include <sstream>
#include <algorithm>

std::string ConfigParser::trim(const std::string& str) {
    size_t start = str.find_first_not_of(" \t\n\r");
    if (start == std::string::npos) return "";
    size_t end = str.find_last_not_of(" \t\n\r");
    return str.substr(start, end - start + 1);
}

// Used to parse outputItems and input arrays
int ConfigParser::parseStringList(const std::string& listStr, std::string* outputArray, int maxItems) {
    std::string cleaned = listStr;
    
    // Remove brackets
    cleaned.erase(std::remove(cleaned.begin(), cleaned.end(), '['), cleaned.end());
    cleaned.erase(std::remove(cleaned.begin(), cleaned.end(), ']'), cleaned.end());
    
    std::stringstream ss(cleaned);
    std::string item;
    int count = 0;
    
    while (std::getline(ss, item, ',') && count < maxItems) {
        item = trim(item);
        // Remove quotes if present
        if (!item.empty() && item.front() == '"' && item.back() == '"') {
            item = item.substr(1, item.length() - 2);
        }
        if (!item.empty()) {
            outputArray[count] = item;
            count++;
        }
    }
    
    return count;
}

// Used to parse gradeValues array
int ConfigParser::parseIntList(const std::string& listStr, int* outputArray, int maxItems) {
    std::string cleaned = listStr;
    
    // Remove brackets
    cleaned.erase(std::remove(cleaned.begin(), cleaned.end(), '['), cleaned.end());
    cleaned.erase(std::remove(cleaned.begin(), cleaned.end(), ']'), cleaned.end());
    
    std::stringstream ss(cleaned);
    std::string item;
    int count = 0;
    
    while (std::getline(ss, item, ',') && count < maxItems) {
        item = trim(item);
        if (!item.empty()) {
            outputArray[count] = std::stoi(item);
            count++;
        }
    }
    
    return count;
}

// Used to parse due dates. Expected Format: "YYYY-MM-DD"
Date ConfigParser::parseDate(const std::string& dateStr) {
    if (dateStr.length() == 10 && dateStr[4] == '-' && dateStr[7] == '-') {
        try {
            int year = std::stoi(dateStr.substr(0, 4));
            int month = std::stoi(dateStr.substr(5, 2));
            int day = std::stoi(dateStr.substr(8, 2));
            return Date(year, month, day);
        } catch (const std::exception& e) {
            std::cout << "Warning: Invalid date format '" << dateStr << "', using default date" << std::endl;
        }
    } else {
        std::cout << "Warning: Invalid date format '" << dateStr << "', using default date" << std::endl;
    }
    
    return Date(); // Default date, you can change this as needed or modify the default constructor in date.cpp
}

// Used to parse assignments in the format: assignmentName = {"Description", "2025-10-31", "autograder1"}
void ConfigParser::parseAssignment(const std::string& name, const std::string& value) {
    std::cout << "DEBUG: Parsing assignment - Name: '" << name << "', Value: '" << value << "'" << std::endl;
    
    if (value.front() == '{' && value.back() == '}') {
        std::string content = value.substr(1, value.length() - 2); // Remove { }
        
        // Split by commas, but be careful of commas inside quotes
        std::string parts[3]; 
        int partCount = 0;
        std::string current;
        bool inQuotes = false;
        
        for (char c : content) {
            if (c == '"') {
                inQuotes = !inQuotes;
                current += c;
            } else if (c == ',' && !inQuotes) {
                if (partCount < 3) {
                    parts[partCount] = trim(current);
                    partCount++;
                }
                current.clear();
            } else {
                current += c;
            }
        }
        if (!current.empty() && partCount < 3) {
            parts[partCount] = trim(current);
            partCount++;
        }
        
        std::cout << "DEBUG: Found " << partCount << " parts:" << std::endl;
        for (int i = 0; i < partCount; ++i) {
            std::cout << "  Part " << i << ": '" << parts[i] << "'" << std::endl;
        }
        
        if (partCount == 3) {
            AssignmentConfig config;
            config.name = name;
            
            // Remove quotes from each part if they exist
            config.description = parts[0];
            if (config.description.front() == '"' && config.description.back() == '"') {
                config.description = config.description.substr(1, config.description.length() - 2);
            }
            
            config.dueDate = parts[1];
            if (config.dueDate.front() == '"' && config.dueDate.back() == '"') {
                config.dueDate = config.dueDate.substr(1, config.dueDate.length() - 2);
            }
            
            config.autograderName = parts[2];
            if (config.autograderName.front() == '"' && config.autograderName.back() == '"') {
                config.autograderName = config.autograderName.substr(1, config.autograderName.length() - 2);
            }
            
            assignments[name] = config;
            std::cout << "Loaded assignment: " << name << std::endl;
            std::cout << "  Description: '" << config.description << "'" << std::endl;
            std::cout << "  Due Date: '" << config.dueDate << "'" << std::endl;
            std::cout << "  Autograder: '" << config.autograderName << "'" << std::endl;
        } else {
            std::cout << "Warning: Invalid assignment format for " << name << " (expected 3 parts, got " << partCount << ")" << std::endl;
        }
    } else {
        std::cout << "Warning: Invalid assignment format for " << name << std::endl;
        std::cout << "Expected format: {\"Description\", \"YYYY-MM-DD\", \"autograder_name\"}" << std::endl;
    }
}

// Used to parse autograders in the format: autograderName = {["output1", "output2"], [50, 50]}
void ConfigParser::parseAutograder(const std::string& name, const std::string& value) {
    std::cout << "DEBUG: Parsing autograder - Name: '" << name << "', Value: '" << value << "'" << std::endl;
    
    if (value.front() == '{' && value.back() == '}') {
        std::string content = value.substr(1, value.length() - 2); // Remove { }
        
        size_t firstBracket = content.find('[');
        size_t firstCloseBracket = content.find(']');
        size_t secondBracket = content.find('[', firstCloseBracket);
        size_t secondCloseBracket = content.find(']', secondBracket);
        
        if (firstBracket != std::string::npos && firstCloseBracket != std::string::npos &&
            secondBracket != std::string::npos && secondCloseBracket != std::string::npos) {
            
            std::string outputList = content.substr(firstBracket, firstCloseBracket - firstBracket + 1);
            std::string valueList = content.substr(secondBracket, secondCloseBracket - secondBracket + 1);
            
            std::cout << "DEBUG: Output list: '" << outputList << "'" << std::endl;
            std::cout << "DEBUG: Value list: '" << valueList << "'" << std::endl;
            
            AutograderConfig config;
            config.name = name;
            config.itemCount = parseStringList(outputList, config.outputItems, MAX_OUTPUT_ITEMS);
            int valueCount = parseIntList(valueList, config.gradeValues, MAX_OUTPUT_ITEMS);
            
            std::cout << "  Parsed " << config.itemCount << " output items" << std::endl;
            for (int i = 0; i < config.itemCount; ++i) {
                std::cout << "    Item " << i << ": '" << config.outputItems[i] << "'" << std::endl;
            }
            std::cout << "  Parsed " << valueCount << " grade values" << std::endl;
            for (int i = 0; i < valueCount; ++i) {
                std::cout << "    Value " << i << ": " << config.gradeValues[i] << std::endl;
            }
            
            if (config.itemCount != valueCount) {
                std::cout << "Warning: Mismatch between output items and grade values for " << name << std::endl;
                return;
            }
            
            autograders[name] = config;
            std::cout << "Loaded autograder: " << name << std::endl;
        } else {
            std::cout << "Warning: Invalid autograder format for " << name << std::endl;
            std::cout << "DEBUG: firstBracket=" << firstBracket << ", firstCloseBracket=" << firstCloseBracket 
                      << ", secondBracket=" << secondBracket << ", secondCloseBracket=" << secondCloseBracket << std::endl;
        }
    } else {
        std::cout << "Warning: Invalid autograder format for " << name << std::endl;
        std::cout << "Expected format: {[\"output1\", \"output2\"], [value1, value2]}" << std::endl;
    }
}

// Used to parse tests in the format: testName = {"assignmentName", ["input1", "input2"]}
void ConfigParser::parseTest(const std::string& name, const std::string& value) {
    std::cout << "DEBUG: Parsing test - Name: '" << name << "', Value: '" << value << "'" << std::endl;
    
    if (value.front() == '{' && value.back() == '}') {
        std::string content = value.substr(1, value.length() - 2);
        
        // Find the assignment name (first quoted string) and the array
        size_t firstQuote = content.find('"');
        size_t secondQuote = content.find('"', firstQuote + 1);
        size_t arrayStart = content.find('[');
        size_t arrayEnd = content.find(']');
        
        if (firstQuote != std::string::npos && secondQuote != std::string::npos &&
            arrayStart != std::string::npos && arrayEnd != std::string::npos) {
            
            std::string assignmentName = content.substr(firstQuote + 1, secondQuote - firstQuote - 1);
            std::string inputList = content.substr(arrayStart, arrayEnd - arrayStart + 1);
            
            std::cout << "DEBUG: Assignment name: '" << assignmentName << "'" << std::endl;
            std::cout << "DEBUG: Input list: '" << inputList << "'" << std::endl;
            
            TestConfig config;
            config.name = name;
            config.assignmentName = assignmentName;
            config.inputCount = parseStringList(inputList, config.inputs, MAX_INPUT_ITEMS);
            
            // ✅ ADD THIS LINE - Actually store the test!
            tests[name] = config;
            
            std::cout << "Loaded test: " << name << std::endl;
            std::cout << "  Assignment: '" << config.assignmentName << "'" << std::endl;
            std::cout << "  Inputs: " << config.inputCount << " items" << std::endl;
            for (int i = 0; i < config.inputCount; ++i) {
                std::cout << "    Input " << i << ": '" << config.inputs[i] << "'" << std::endl;
            }
        } else {
            std::cout << "Warning: Invalid test format for " << name << std::endl;
            std::cout << "DEBUG: firstQuote=" << firstQuote << ", secondQuote=" << secondQuote 
                      << ", arrayStart=" << arrayStart << ", arrayEnd=" << arrayEnd << std::endl;
        }
    } else {
        std::cout << "Warning: Invalid test format for " << name << std::endl;
        std::cout << "Expected format: {\"assignment_name\", [\"input1\", \"input2\"]}" << std::endl;
    }
}

// Main function that loads config.txt and uses helper functions to parse it
bool ConfigParser::loadConfig(const std::string& filename) {
    std::ifstream file(filename);
    if (!file.is_open()) {
        std::cout << "Error: Could not open config file: " << filename << std::endl;
        return false;
    }
    
    std::string line;
    std::string currentSection;
    int lineNumber = 0;
    
    while (std::getline(file, line)) {
        lineNumber++;
        std::cout << "DEBUG: Line " << lineNumber << ": '" << line << "'" << std::endl;
        
        line = trim(line);
        
        // Skip empty lines
        if (line.empty()) {
            std::cout << "DEBUG: Skipping empty line" << std::endl;
            continue;
        }
        
        // Check for section headers - Should only be 3 sections
        if (line.find("### ") == 0) {
            currentSection = trim(line.substr(4));
            std::cout << "Reading section: " << currentSection << std::endl;
            continue;
        }
        
        // Parse key-value pairs
        size_t equalPos = line.find(" = ");
        if (equalPos == std::string::npos) {
            std::cout << "DEBUG: No ' = ' found in line, skipping" << std::endl;
            continue;
        }
        
        std::string key = trim(line.substr(0, equalPos));
        std::string value = trim(line.substr(equalPos + 3));
        
        std::cout << "DEBUG: Current section: '" << currentSection << "'" << std::endl;
        std::cout << "DEBUG: Key: '" << key << "', Value: '" << value << "'" << std::endl;
        
        if (currentSection == "Assignments") {
            parseAssignment(key, value);
        } else if (currentSection == "Autograders") {
            parseAutograder(key, value);
        } else if (currentSection == "Tests") {
            parseTest(key, value);
        } else {
            std::cout << "DEBUG: Unknown section '" << currentSection << "'" << std::endl;
        }
    }
    
    file.close();
    
    std::cout << "DEBUG: Final counts - Assignments: " << assignments.size() 
              << ", Autograders: " << autograders.size() 
              << ", Tests: " << tests.size() << std::endl;
    
    return true;
}

// Functions to create objects from parsed key-value pairs
std::map<std::string, Autograder> ConfigParser::createAutograders() {
    std::map<std::string, Autograder> result;
    
    for (const auto& pair : autograders) {
        const AutograderConfig& config = pair.second;
        
        result[pair.first] = Autograder(config.outputItems, config.gradeValues, config.itemCount);
    }
    
    return result;
}

int ConfigParser::createAssignments(Assignment* assignmentArray, int maxAssignments) {
    std::map<std::string, Autograder> autograderMap = createAutograders();
    int count = 0;
    
    for (const auto& pair : assignments) {
        if (count >= maxAssignments) break;
        
        const AssignmentConfig& config = pair.second;
        
        auto autograderIt = autograderMap.find(config.autograderName);
        if (autograderIt == autograderMap.end()) {
            std::cout << "Warning: Autograder '" << config.autograderName 
                      << "' not found for assignment '" << config.name << "'" << std::endl;
            continue;
        }
        
        Date dueDate = parseDate(config.dueDate);
        assignmentArray[count] = Assignment(config.name, config.description, dueDate, autograderIt->second);
        count++;
    }
    
    return count;
}

// Getters for parsed configurations
std::map<std::string, TestConfig> ConfigParser::getTests() {
    return tests;
}

const std::map<std::string, AutograderConfig>& ConfigParser::getAutograderConfigs() const {
    return autograders;
}

const std::map<std::string, AssignmentConfig>& ConfigParser::getAssignmentConfigs() const {
    return assignments;
}

const std::map<std::string, TestConfig>& ConfigParser::getTestConfigs() const {
    return tests;
}