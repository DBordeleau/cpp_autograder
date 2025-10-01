/*
Parses the config.txt file and creates the necessary objects/database entries.
*/

#include "config.h"
#include <iostream>
#include <fstream>
#include <sstream>
#include <algorithm>

std::string ConfigParser::trim(const std::string& str) {
    size_t first = str.find_first_not_of(" \t\r\n");
    if (std::string::npos == first) {
        return str;
    }
    size_t last = str.find_last_not_of(" \t\r\n");
    return str.substr(first, (last - first + 1));
}

int ConfigParser::parseStringList(const std::string& listStr, std::string* outputArray, int maxItems) {
    int count = 0;
    size_t start = listStr.find('[');
    size_t end = listStr.find(']');
    
    if (start == std::string::npos || end == std::string::npos) {
        return 0;
    }
    
    std::string content = listStr.substr(start + 1, end - start - 1);
    std::stringstream ss(content);
    std::string item;
    
    while (std::getline(ss, item, ',') && count < maxItems) {
        item = trim(item);
        // Remove quotes
        if (item.front() == '"' && item.back() == '"') {
            item = item.substr(1, item.length() - 2);
        }
        outputArray[count++] = item;
    }
    
    return count;
}

int ConfigParser::parseIntList(const std::string& listStr, int* outputArray, int maxItems) {
    int count = 0;
    size_t start = listStr.find('[');
    size_t end = listStr.find(']');
    
    if (start == std::string::npos || end == std::string::npos) {
        return 0;
    }
    
    std::string content = listStr.substr(start + 1, end - start - 1);
    std::stringstream ss(content);
    std::string item;
    
    while (std::getline(ss, item, ',') && count < maxItems) {
        item = trim(item);
        outputArray[count++] = std::stoi(item);
    }
    
    return count;
}

Date ConfigParser::parseDate(const std::string& dateStr) {
    // Parse YYYY-MM-DD format
    std::string cleanDate = dateStr;
    // Remove quotes if present
    if (cleanDate.front() == '"' && cleanDate.back() == '"') {
        cleanDate = cleanDate.substr(1, cleanDate.length() - 2);
    }
    
    std::stringstream ss(cleanDate);
    std::string year, month, day;
    
    std::getline(ss, year, '-');
    std::getline(ss, month, '-');
    std::getline(ss, day);
    
    return Date(std::stoi(day), std::stoi(month), std::stoi(year));
}

void ConfigParser::parseAssignment(const std::string& name, const std::string& value) {
    AssignmentConfig config;
    config.name = name;
    
    // Parse {"description", "date", "autograder"}
    size_t start = value.find('{');
    size_t end = value.find('}');
    
    if (start != std::string::npos && end != std::string::npos) {
        std::string content = value.substr(start + 1, end - start - 1);
        std::stringstream ss(content);
        std::string item;
        
        int index = 0;
        while (std::getline(ss, item, ',') && index < 3) {
            item = trim(item);
            if (item.front() == '"' && item.back() == '"') {
                item = item.substr(1, item.length() - 2);
            }
            
            switch (index) {
                case 0: config.description = item; break;
                case 1: config.dueDate = item; break;
                case 2: config.autograderName = item; break;
            }
            index++;
        }
    }
    
    assignments[name] = config;
}

void ConfigParser::parseAutograder(const std::string& name, const std::string& value) {
    AutograderConfig config;
    config.name = name;
    config.itemCount = 0;
    
    // Parse {["output1", "output2"], [val1, val2]}
    size_t start = value.find('{');
    size_t end = value.find('}');
    
    if (start != std::string::npos && end != std::string::npos) {
        std::string content = value.substr(start + 1, end - start - 1);
        
        // Find the two arrays
        size_t firstArrayStart = content.find('[');
        size_t firstArrayEnd = content.find(']');
        size_t secondArrayStart = content.find('[', firstArrayEnd);
        size_t secondArrayEnd = content.find(']', secondArrayStart);
        
        if (firstArrayStart != std::string::npos && firstArrayEnd != std::string::npos) {
            std::string outputsStr = content.substr(firstArrayStart, firstArrayEnd - firstArrayStart + 1);
            config.itemCount = parseStringList(outputsStr, config.outputItems, MAX_OUTPUT_ITEMS);
        }
        
        if (secondArrayStart != std::string::npos && secondArrayEnd != std::string::npos) {
            std::string valuesStr = content.substr(secondArrayStart, secondArrayEnd - secondArrayStart + 1);
            parseIntList(valuesStr, config.gradeValues, config.itemCount);
        }
    }
    
    autograders[name] = config;
}

void ConfigParser::parseTest(const std::string& name, const std::string& value) {
    TestConfig config;
    config.name = name;
    config.inputCount = 0;
    
    // Parse {"assignment", ["input1", "input2"]}
    size_t start = value.find('{');
    size_t end = value.find('}');
    
    if (start != std::string::npos && end != std::string::npos) {
        std::string content = value.substr(start + 1, end - start - 1);
        
        // Find assignment name (first item before comma)
        size_t commaPos = content.find(',');
        if (commaPos != std::string::npos) {
            std::string assignmentStr = trim(content.substr(0, commaPos));
            if (assignmentStr.front() == '"' && assignmentStr.back() == '"') {
                assignmentStr = assignmentStr.substr(1, assignmentStr.length() - 2);
            }
            config.assignmentName = assignmentStr;
            
            // Parse inputs array
            std::string inputsStr = trim(content.substr(commaPos + 1));
            config.inputCount = parseStringList(inputsStr, config.inputs, MAX_INPUT_ITEMS);
        }
    }
    
    tests[name] = config;
}

bool ConfigParser::loadConfig(const std::string& filename) {
    std::ifstream file(filename);
    if (!file.is_open()) {
        std::cerr << "Cannot open config file: " << filename << std::endl;
        return false;
    }
    
    std::string line;
    std::string currentSection = "";
    int lineNumber = 0;
    
    std::cerr << "DEBUG: Starting to read config file..." << std::endl;
    
    while (std::getline(file, line)) {
        lineNumber++;
        std::cerr << "DEBUG: Line " << lineNumber << ": '" << line << "'" << std::endl;
        
        line = trim(line);
        std::cerr << "DEBUG: Trimmed line: '" << line << "'" << std::endl;
        
        // Skip empty lines
        if (line.empty()) {
            std::cerr << "DEBUG: Skipping empty line" << std::endl;
            continue;
        }
        
        // Check for section headers
        if (line.find("### Assignments") != std::string::npos) {
            currentSection = "assignments";
            std::cerr << "DEBUG: Found assignments section" << std::endl;
            continue;
        }
        if (line.find("### Autograders") != std::string::npos) {
            currentSection = "autograders";
            std::cerr << "DEBUG: Found autograders section" << std::endl;
            continue;
        }
        if (line.find("### Tests") != std::string::npos) {
            currentSection = "tests";
            std::cerr << "DEBUG: Found tests section" << std::endl;
            continue;
        }
        
        // Parse assignment lines (name = value)
        size_t equalPos = line.find('=');
        if (equalPos != std::string::npos) {
            std::string name = trim(line.substr(0, equalPos));
            std::string value = trim(line.substr(equalPos + 1));
            
            std::cerr << "DEBUG: Found assignment line - Name: '" << name << "', Value: '" << value << "', Section: '" << currentSection << "'" << std::endl;
            
            if (currentSection == "assignments") {
                std::cerr << "DEBUG: Parsing assignment: " << name << std::endl;
                parseAssignment(name, value);
            } else if (currentSection == "autograders") {
                std::cerr << "DEBUG: Parsing autograder: " << name << std::endl;
                parseAutograder(name, value);
            } else if (currentSection == "tests") {
                std::cerr << "DEBUG: Parsing test: " << name << std::endl;
                parseTest(name, value);
            } else {
                std::cerr << "DEBUG: No current section set for line: " << line << std::endl;
            }
        } else {
            std::cerr << "DEBUG: No '=' found in line: " << line << std::endl;
        }
    }
    
    file.close();
    
    std::cerr << "DEBUG: Finished reading config file" << std::endl;
    std::cerr << "DEBUG: Final counts - Assignments: " << assignments.size() << ", Autograders: " << autograders.size() << ", Tests: " << tests.size() << std::endl;
    
    return true;
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

#ifndef CONFIG_PARSER_MAIN

int ConfigParser::createAssignments(Assignment* assignmentArray, int maxAssignments) {
    int count = 0;
    
    // map of autograders
    std::map<std::string, Autograder> autograderMap = createAutograders();
    
    for (const auto& pair : assignments) {
        if (count >= maxAssignments) break;
        
        const auto& config = pair.second;
        Date dueDate = parseDate(config.dueDate);
        
        auto autograderIt = autograderMap.find(config.autograderName);
        if (autograderIt != autograderMap.end()) {
            assignmentArray[count] = Assignment(config.name, config.description, dueDate, autograderIt->second);
        } else {
            assignmentArray[count] = Assignment(config.name, config.description, dueDate, Autograder());
        }
        count++;
    }
    return count;
}

std::map<std::string, Autograder> ConfigParser::createAutograders() {
    std::map<std::string, Autograder> result;
    
    for (const auto& pair : autograders) {
        const auto& config = pair.second;
        Autograder autograder(config.outputItems, config.gradeValues, config.itemCount);
        result[pair.first] = autograder;
    }
    
    return result;
}

std::map<std::string, TestConfig> ConfigParser::getTests() {
    return tests;
}

#endif 

#ifdef CONFIG_PARSER_MAIN
int main() {
    ConfigParser parser;
    
    std::cerr << "DEBUG: Starting config parser..." << std::endl;
    std::cerr << "DEBUG: Attempting to load config.txt..." << std::endl;
    
    if (!parser.loadConfig("../config.txt")) {
        std::cerr << "Failed to load config" << std::endl;
        return 1;
    }
    
    std::cerr << "DEBUG: Config loaded successfully" << std::endl;
    
    const auto& autograders = parser.getAutograderConfigs();
    const auto& assignments = parser.getAssignmentConfigs();
    const auto& tests = parser.getTestConfigs();
    
    std::cerr << "DEBUG: Found " << autograders.size() << " autograders" << std::endl;
    std::cerr << "DEBUG: Found " << assignments.size() << " assignments" << std::endl;
    std::cerr << "DEBUG: Found " << tests.size() << " tests" << std::endl;
    
    // Output JSON format for Python to parse
    std::cout << "{" << std::endl;
    
    // Output autograders
    std::cout << "  \"autograders\": {" << std::endl;
    bool first = true;
    for (const auto& pair : autograders) {
        if (!first) std::cout << "," << std::endl;
        const auto& config = pair.second;
        std::cout << "    \"" << pair.first << "\": {" << std::endl;
        std::cout << "      \"outputs\": [";
        for (int i = 0; i < config.itemCount; ++i) {
            if (i > 0) std::cout << ", ";
            std::cout << "\"" << config.outputItems[i] << "\"";
        }
        std::cout << "]," << std::endl;
        std::cout << "      \"weights\": [";
        for (int i = 0; i < config.itemCount; ++i) {
            if (i > 0) std::cout << ", ";
            std::cout << config.gradeValues[i];
        }
        std::cout << "]" << std::endl;
        std::cout << "    }";
        first = false;
    }
    std::cout << std::endl << "  }," << std::endl;
    
    // Output assignments
    std::cout << "  \"assignments\": {" << std::endl;
    first = true;
    for (const auto& pair : assignments) {
        if (!first) std::cout << "," << std::endl;
        const auto& config = pair.second;
        std::cout << "    \"" << pair.first << "\": {" << std::endl;
        std::cout << "      \"description\": \"" << config.description << "\"," << std::endl;
        std::cout << "      \"due_date\": \"" << config.dueDate << "\"," << std::endl;
        std::cout << "      \"autograder\": \"" << config.autograderName << "\"" << std::endl;
        std::cout << "    }";
        first = false;
    }
    std::cout << std::endl << "  }," << std::endl;
    
    // Output tests
    std::cout << "  \"tests\": {" << std::endl;
    first = true;
    for (const auto& pair : tests) {
        if (!first) std::cout << "," << std::endl;
        const auto& config = pair.second;
        std::cout << "    \"" << pair.first << "\": {" << std::endl;
        std::cout << "      \"assignment\": \"" << config.assignmentName << "\"," << std::endl;
        std::cout << "      \"inputs\": [";
        for (int i = 0; i < config.inputCount; ++i) {
            if (i > 0) std::cout << ", ";
            std::cout << "\"" << config.inputs[i] << "\"";
        }
        std::cout << "]" << std::endl;
        std::cout << "    }";
        first = false;
    }
    std::cout << std::endl << "  }" << std::endl;
    
    std::cout << "}" << std::endl;
    
    std::cerr << "DEBUG: JSON output complete" << std::endl;
    
    return 0;
}
#endif