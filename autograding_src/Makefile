OBJECTS = assignment.o autograder.o date.o submission.o mark.o tests.o grader.o config.o main.o

autograder: $(OBJECTS)
	clang++ -std=c++20 $(OBJECTS) -o autograder

assignment.o: assignment.cpp assignment.h date.h autograder.h submission.h
	clang++ -std=c++20 -c assignment.cpp

autograder.o: autograder.cpp autograder.h mark.h
	clang++ -std=c++20 -c autograder.cpp

date.o: date.cpp date.h
	clang++ -std=c++20 -c date.cpp

submission.o: submission.cpp submission.h mark.h date.h
	clang++ -std=c++20 -c submission.cpp

mark.o: mark.cpp mark.h
	clang++ -std=c++20 -c mark.cpp

tests.o: tests.cpp tests.h
	clang++ -std=c++20 -c tests.cpp

grader.o: grader.cpp grader.h assignment.h tests.h
	clang++ -std=c++20 -c grader.cpp

config.o: config.cpp config.h assignment.h tests.h
	clang++ -std=c++20 -c config.cpp

main.o: main.cpp grader.h assignment.h
	clang++ -std=c++20 -c main.cpp

clean:
	rm -f *.o autograder