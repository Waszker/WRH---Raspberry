#ifndef _COMMON_H
#define _COMMON_H
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <signal.h>

#define ERR(src)    (fprintf(stderr, "%s:%d\n", __FILE__, __LINE__),\
                    perror(src), kill(0, SIGKILL), exit(EXIT_FAILURE))

# define TEMP_FAILURE_RETRY(expression) \
   (__extension__ \
     ({ long int __result; \
        do __result = (long int) (expression); \
        while (__result == -1L && errno == EINTR); \
        __result; }))

volatile sig_atomic_t _sig_No;

void sig_handler(int signo);
void set_signal_handler(int, void(*)(int));
sigset_t set_signal_behaviour(int, sigset_t*, int, ...);
FILE* open_file(char*, char*);
void* safe_malloc(size_t);
char* read_file_line(FILE*);

#endif
