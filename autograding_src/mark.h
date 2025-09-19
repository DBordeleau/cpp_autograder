#ifndef MARK_H
#define MARK_H

#include <string>
#include <iostream>

class Mark {
private:
    int markValue;
    int outOf;
public:
    Mark();
    Mark(int markValue, int outOf);
    bool setMark(int markValue, int outOf);
    std::string print();
};

#endif