#define _GNU_SOURCE
#include <errno.h>
#include <signal.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>

#define ERR(src)    (fprintf(stderr, "%s:%d\n", __FILE__, __LINE__),\
                    perror(src), kill(0, SIGKILL), exit(EXIT_FAILURE))
#define NUMBER_OF_EXECS     4

typedef struct command
{
    char* env[5];
    char* arg[10];
} command;

volatile sig_atomic_t _is_ending;
volatile sig_atomic_t _sig_No;

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

void start_service(command* pcommand, pid_t* ppid)
{
    sigset_t mask;
    switch(*ppid = fork())
    {
        case 0:
            set_signal_behaviour(SIG_UNBLOCK, &mask, 2, SIGINT, SIGCHLD);
            execve(pcommand->arg[0], pcommand->arg, pcommand->env);
            break;

        case -1:
            ERR("Problem forking");
            break;
    }
}

void start_subprocesses(command commands[], pid_t subprocesses[])
{
    int i;
    for(i = 0; i < NUMBER_OF_EXECS; i++)
        start_service(&commands[i], &subprocesses[i]);
}

void stop_all_services(pid_t subprocesses[])
{
    int i;
    for(i = 0; i < NUMBER_OF_EXECS; i++)
        kill(subprocesses[i], SIGINT); // do not check for errors here!
    while(TEMP_FAILURE_RETRY(wait(NULL)) > 0);
    printf("Ended life of all children\n");
    exit(EXIT_SUCCESS);
}

void restart_stopped_child(command commands[], pid_t subprocesses[])
{
    pid_t pid;
    int i;
    while(1)
    {
        pid = waitpid(0, NULL, WNOHANG);
        if(0 == pid) break;
        if(ECHILD == errno) ERR("waitpid");

        for(i = 0; i < NUMBER_OF_EXECS; i++)
            if(pid == subprocesses[i] && i != 3)
            {
                printf("Program %s has stopped. Restarting.\n", commands[i].arg[0]);
                start_service(&commands[i], &subprocesses[i]);
            }
    }
}

int main()
{
    /* Variables */
    int i;
    sigset_t mask;
    pid_t subprocesses[NUMBER_OF_EXECS];
    command commands[] = {
        { { "LD_LIBRARY_PATH=/usr/lib/", NULL }, { "/bin/mjpg_streamer",  "-i",
            "input_uvc.so -n -q 50 -f 1", "-o",
            "output_http.so -p 8080 -c login:password", NULL } },
        { { NULL }, { "./server.py", NULL } },
        { { NULL }, { "./lcd2.py", NULL } },
        { { NULL }, { "/bin/stunnel", "./stunnel.conf", NULL } },
    };
    _is_ending = 0;

    // TODO: Should signals go first?
    /* Start processes first, then block signals */
    printf("Starting server\n");
    start_subprocesses(commands, subprocesses);

    /* Setting signal handlers */
    set_signal_handler(SIGINT, sig_handler);
    set_signal_handler(SIGCHLD, sig_handler);

    /* Setting signal mask */
    set_signal_behaviour(SIG_UNBLOCK, &mask, 2, SIGINT, SIGCHLD);
    mask = set_signal_behaviour(SIG_BLOCK, &mask, 2, SIGINT, SIGCHLD);

    /* Wait for signal */
    while(1)
    {
        sigsuspend(&mask);
        switch(_sig_No)
        {
            case SIGCHLD:
                restart_stopped_child(commands, subprocesses);
                break;

            case SIGINT:
                stop_all_services(subprocesses);
                break;
        }
    }

    return 0;
}
