#include <signal.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "common.h"

void sig_handler(int signo)
{
    _sig_No = signo;
}

void set_signal_handler(int signo, void (*f)(int))
{
    struct sigaction action;
    memset(&action, 0, sizeof(struct sigaction));
    action.sa_handler = f;
    if(-1 == sigaction(signo, &action, NULL)) ERR("sigaction");
}

sigset_t set_signal_behaviour(int behaviour, sigset_t* set, int num_of_signals, ...)
{
    int i;
    sigset_t oldmask;
    va_list arguments;
    va_start(arguments, num_of_signals);

    sigemptyset(set);
    for(i = 0; i < num_of_signals; i++)
        sigaddset(set, (int)va_arg(arguments, int));
    va_end(arguments);

    if(-1 == sigprocmask(behaviour, set, &oldmask)) ERR("sigprocmask");

    return oldmask;
}

FILE* open_file(char* filename, char* mode)
{
    FILE* file = fopen(filename, mode);
    if(NULL == file) ERR("fopen");
    return file;
}

void* safe_malloc(size_t size)
{
    void* mem = malloc(size);
    if(NULL == mem) ERR("malloc");
    return mem;
}

char* read_file_line(FILE* file)
{
    char* buffer = NULL;
    size_t len = 0;
    ssize_t read;
    read = getline(&buffer, &len, file);
    if(-1 == read) buffer = NULL;
    return buffer;
}
