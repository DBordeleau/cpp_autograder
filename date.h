#ifndef DATE_H
#define DATE_H

#include <string>

class Date {
private:
    int year;
    int month;
    int day;
public:
    Date(int year, int month, int day);
    Date();
    std::string toString() const; // Format: "YYYY-MM-DD"
    bool equals(const Date& d) const;
    bool lessThan(const Date& d) const;
};

#endif