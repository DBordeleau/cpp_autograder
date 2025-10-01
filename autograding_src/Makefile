CXX = g++
CXXFLAGS = -std=c++20 -Wall -Wextra
LDFLAGS = -lsqlite3

OBJECTS = assignment.o autograder.o date.o submission.o mark.o tests.o grader.o config.o main.o

all: autograder config_parser

autograder: $(OBJECTS)
	$(CXX) $(CXXFLAGS) $(OBJECTS) -o autograder $(LDFLAGS)

config_parser: config_parser.o date.o
	$(CXX) $(CXXFLAGS) config_parser.o date.o -o config_parser

# Special rule for config_parser.o with the CONFIG_PARSER_MAIN macro
config_parser.o: config.cpp config.h
	$(CXX) $(CXXFLAGS) -DCONFIG_PARSER_MAIN -c config.cpp -o config_parser.o

assignment.o: assignment.cpp assignment.h date.h autograder.h submission.h
	$(CXX) $(CXXFLAGS) -c assignment.cpp

autograder.o: autograder.cpp autograder.h mark.h
	$(CXX) $(CXXFLAGS) -c autograder.cpp

date.o: date.cpp date.h
	$(CXX) $(CXXFLAGS) -c date.cpp

submission.o: submission.cpp submission.h mark.h date.h
	$(CXX) $(CXXFLAGS) -c submission.cpp

mark.o: mark.cpp mark.h
	$(CXX) $(CXXFLAGS) -c mark.cpp

tests.o: tests.cpp tests.h
	$(CXX) $(CXXFLAGS) -c tests.cpp

grader.o: grader.cpp grader.h assignment.h tests.h
	$(CXX) $(CXXFLAGS) -c grader.cpp

config.o: config.cpp config.h assignment.h tests.h
	$(CXX) $(CXXFLAGS) -c config.cpp

main.o: main.cpp grader.h assignment.h
	$(CXX) $(CXXFLAGS) -c main.cpp

clean:
	rm -f *.o autograder config_parser