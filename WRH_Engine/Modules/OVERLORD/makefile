# Name of the program
NAME=program

# Compiler to use
CC=gcc

# Flags to use
CFLAGS=-Wall -Werror -g -O3 -c

# Specify files
FILES=program.o wrh_lib.o common.o

all: $(NAME)

$(NAME): $(FILES)
	$(CC) $(FILES) -o $(NAME)

prgr.o: program.c
	$(CC) $(CFLAGS) program.c -o program.o

wrh_lib.o: wrh_lib.c
	$(CC) $(CFLAGS) wrh_lib.c -o wrh_lib.o

common.o: common.c
	$(CC) $(CFLAGS) common.c -o common.o

clean:
	rm -f *.o $(NAME)
