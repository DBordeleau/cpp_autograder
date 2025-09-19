#ifndef CONFIG_H
#define CONFIG_H

#include <string>
#include <map>
#include "assignment.h"
#include "autograder.h"
#include "date.h"

#define MAX_OUTPUT_ITEMS 50 // Limit for output items to check and grade
#define MAX_INPUT_ITEMS 50
#define MAX_ASSIGNMENTS 20

struct AutograderConfig {
    std::string name;
    std::string outputItems[MAX_OUTPUT_ITEMS];
    int gradeValues[MAX_OUTPUT_ITEMS];
    int itemCount;
};

struct AssignmentConfig {
    std::string name;
    std::string description;
    std::string dueDate;
    std::string autograderName;
};

struct TestConfig {
    std::string name;
    std::string assignmentName;
    std::string inputs[MAX_INPUT_ITEMS];
    int inputCount;
};

class ConfigParser {
private:
    std::map<std::string, AutograderConfig> autograders;
    std::map<std::string, AssignmentConfig> assignments;
    std::map<std::string, TestConfig> tests;
    
    // Helper functions
    std::string trim(const std::string& str);
    int parseStringList(const std::string& listStr, std::string* outputArray, int maxItems);
    int parseIntList(const std::string& listStr, int* outputArray, int maxItems);
    Date parseDate(const std::string& dateStr);
    
    // Parsing methods
    void parseAssignment(const std::string& name, const std::string& value);
    void parseAutograder(const std::string& name, const std::string& value);
    void parseTest(const std::string& name, const std::string& value);
    
public:
    bool loadConfig(const std::string& filename);
    
    // Create objects from parsed config
    int createAssignments(Assignment* assignmentArray, int maxAssignments);
    std::map<std::string, Autograder> createAutograders();
    std::map<std::string, TestConfig> getTests();
    
    // Getters
    const std::map<std::string, AutograderConfig>& getAutograderConfigs() const;
    const std::map<std::string, AssignmentConfig>& getAssignmentConfigs() const;
    const std::map<std::string, TestConfig>& getTestConfigs() const;
};

#endif