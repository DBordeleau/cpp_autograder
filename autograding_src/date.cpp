/*
This class represents a date with year, month, and day attributes.
It is used for assignment due dates and submission dates.
*/

#include "date.h"

Date::Date(int year, int month, int day) {
    this->year = year;
    this->month = month;
    this->day = day;
}

// Note that submissions will not be accepted if the submission date is after the due date.
// The default date is set to January 1, 1901 to avoid accidental acceptance of late submissions.
Date::Date() {
    year = 1901;
    month = 1;
    day = 1;
}

// Returns a formatted string representation of the date in "YYYY-MM-DD" format.
std::string Date::toString() const {
    char buffer[11];
    snprintf(buffer, sizeof(buffer), "%04d-%02d-%02d", year, month, day);
    return std::string(buffer);
}

// Returns true if this date is the same as the passed date. 
// Useful for lessThan function.
bool Date::equals(const Date& d) const {
    return (year == d.year && month == d.month && day == d.day);
}

// Returns true if this date is earlier than the passed date.
bool Date::lessThan(const Date& d) const {
    if (year < d.year) return true;
    if (year > d.year) return false;
    if (month < d.month) return true;
    if (month > d.month) return false;
    return day < d.day;
}