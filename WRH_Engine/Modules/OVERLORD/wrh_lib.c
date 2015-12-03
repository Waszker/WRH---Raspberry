#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <signal.h>
#include "common.h"
#include "wrh_lib.h"

static enum module_type module_types[] = { SCENARIO, DHT, CAMERA, MOTION, SOCKET };
static int modules_number = sizeof(module_types) / sizeof(enum module_type);

// https://trello.com/c/1oOLJIQW/60-module-type
static command commands[] = {
    { { NULL }, { "/usr/bin/python2.7", "-m", "WRH_Engine.ScenarioManager.ScenarioManager", NULL } },
    { { NULL }, { NULL } },
    { { NULL }, { "/usr/bin/python2.7", "-m", "WRH_Engine.Modules.CAMERA.camera", NULL } },
    { { NULL }, { "/usr/bin/python2.7", "-m", "WRH_Engine.Modules.MOVEMENT.MOVEMENT", NULL } },
    { { NULL }, { "/usr/bin/python2.7", "-m", "WRH_Engine.Modules.WIFISOCKET.WIFISOCKET", NULL } },
    { { NULL }, { "./lcd2.py", NULL } },
    { { NULL }, { "/bin/stunnel", "./stunnel.conf", NULL } },
};

int module_type_to_int(enum module_type type)
{
    int i;

    for(i = 0; i < sizeof(module_types); i++)
        if(module_types[i] == type) break;

    return (i < modules_number ? i : -1);
}

enum module_type int_to_module_type(int number)
{
    enum module_type type;

    if(number > modules_number) type = UNDEFINED;
    else type = module_types[number];

    return type;
}

enum module_type get_module_type_from_config_line(char* line)
{
    int number = 0;
    int i = 0;

    while(line[i] != ';')
    {
        number = number*10 + (line[i] - '0');
        i++;
    }

    return int_to_module_type(number);
}

pid_t start_service(command* pcommand)
{
    pid_t ppid;
    sigset_t mask;

    switch(ppid = fork())
    {
        case 0:
            printf("Starting %s\n", pcommand->arg[0]);
            set_signal_behaviour(SIG_UNBLOCK, &mask, 2, SIGINT, SIGCHLD);
            execve(pcommand->arg[0], pcommand->arg, pcommand->env);
            perror("execve");
            exit(EXIT_FAILURE);
            break;

        case -1:
            ERR("Problem forking");
            break;
    }

    return ppid;
}

pid_t start_module(enum module_type type, char* argument_from_file)
{
    command command_to_copy = commands[module_type_to_int(type)];
    command* command_to_use = (command*)safe_malloc(sizeof(command));
    int i, was_file_argument_added = 0;

    for(i = 0; i < MAX_ENV_COUNT; i++) {
        command_to_use->env[i] = command_to_copy.env[i];
    }
    for(i = 0; i < MAX_ARGUMENT_COUNT; i++) {
        command_to_use->arg[i] = command_to_copy.arg[i];
        if(NULL == command_to_copy.arg[i] && !was_file_argument_added)
        {
            command_to_use->arg[i] = argument_from_file;
            was_file_argument_added = 1;
        }
    }

    pid_t pid = start_service(command_to_use);

    free(command_to_use);
    return pid;
}
