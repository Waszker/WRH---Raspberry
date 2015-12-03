#define _GNU_SOURCE
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <sys/wait.h>
#include "common.h"
#include "wrh_lib.h"

#define CONFIGURATION_FILE ".wrh.config"

typedef struct process {
    enum module_type type;
    pid_t pid;
    char* arguments_from_config;
} process;


void start_subprocesses(process* processes, int processes_number)
{
    int i;

    for(i = 0; i < processes_number; i++)
        processes[i].pid = start_module(processes[i].type,
                processes[i].arguments_from_config);
}

void stop_all_services(process* processes, int processes_number)
{
    int i;
    printf("Ending subprocesses\n");
    for(i = 0; i < 10; i++)
        kill(processes[i].pid, SIGINT); // do not check for errors here!
    while(TEMP_FAILURE_RETRY(wait(NULL)) > 0);
    printf("Ended life of all children\n");
    exit(EXIT_SUCCESS);
}

void restart_stopped_child(process* processes, int processes_number)
{
    pid_t pid;
    int i;
    while(1)
    {
        pid = waitpid(0, NULL, WNOHANG);
        if(0 == pid) break;
        if(ECHILD == errno) ERR("waitpid");

        for(i = 0; i < processes_number; i++)
            if(pid == processes[i].pid)
            {
                processes[i].pid = start_module(processes[i].type,
                        processes[i].arguments_from_config);
            }
    }
}

void fill_processes_details(process* processes, int processes_number, FILE* config)
{
    int line_number = 0;
    char* buffer;

    while((buffer = read_file_line(config)) != NULL)
    {
        if(++line_number == 1) continue;
        processes[line_number - 2].type = get_module_type_from_config_line(buffer);
        processes[line_number - 2].arguments_from_config = buffer;
    }
}

int get_number_of_lines_in_config(FILE* config)
{
    int c;
    int lines_number = 0;

    while(EOF != (c = fgetc(config))) {
        if('\n' == (char)c) lines_number++;
    }
    fseek(config, 0, SEEK_SET);

    return lines_number;
}

/*
 * Configuration sanity check should be done in Python module
 * so when starting this procedure we have 100% good configuration file
 */
int main()
{
    /* Variables */
    sigset_t mask;
    FILE* config_file = open_file(CONFIGURATION_FILE, "r");

    /* Get number of modules */
    printf("Program start\n");
    int number_of_modules = get_number_of_lines_in_config(config_file);
    number_of_modules--; // because first line is not module line
    if(0 == number_of_modules)
    {
        printf("No modules registered. Nothing to do, exiting.");
        exit(EXIT_SUCCESS);
    }
    printf("Number of registered modules: %d\n", number_of_modules);

    /* Setting child signal handler */
    set_signal_handler(SIGINT, sig_handler);
    set_signal_handler(SIGCHLD, sig_handler);

    /* Setting signal mask */
    set_signal_behaviour(SIG_UNBLOCK, &mask, 2, SIGINT, SIGCHLD);
    mask = set_signal_behaviour(SIG_BLOCK, &mask, 2, SIGINT, SIGCHLD);

    /* Start subprocesses */
    printf("Starting server\n");
    process* subprocesses = (process*)safe_malloc(number_of_modules * sizeof(process));
    fill_processes_details(subprocesses, number_of_modules, config_file);
    fclose(config_file); // TODO: Check for errors
    start_subprocesses(subprocesses, number_of_modules);

    /* Wait for signal */
    while(1)
    {
        sigsuspend(&mask);
        switch(_sig_No)
        {
            case SIGCHLD:
                restart_stopped_child(subprocesses, number_of_modules);
                break;

            case SIGINT:
                stop_all_services(subprocesses, number_of_modules);
                break;
        }
    }

    return 0;
}
