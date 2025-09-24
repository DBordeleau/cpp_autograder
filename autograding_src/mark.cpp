/*
Mark class is associated with every submission. It holds the mark value and the out of value.
The mark value is calculated by the autograder based on the submission's output.
The out of value is the sum of every element in the autograder's gradeValues array.
*/

#include "mark.h"

Mark::Mark(int markValue, int outOf) {
    this->markValue = markValue;
    this->outOf = outOf;
}

Mark::Mark() {
    markValue = 0;
    outOf = 100;
}

int Mark::getMark() const {
    return markValue;
}

int Mark::getOutOf() const {
    return outOf;
}

// Set the mark value and out of value.
// Return true if successful, false if invalid values.
bool Mark::setMark(int markValue, int outOf) {
    if (outOf <= 0 || markValue < 0 || markValue > outOf) {
        return false;
    }
    this->markValue = markValue;
    this->outOf = outOf;
    return true;
}

std::string Mark::print() {
    return std::to_string(markValue) + "/" + std::to_string(outOf);
}