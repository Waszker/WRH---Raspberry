#ifndef _WRH_LIB_H
#define _WRH_LIB_H

#define MAX_ENV_COUNT 10
#define MAX_ARGUMENT_COUNT 10

enum module_type
{
    UNDEFINED,
    SCENARIO,
    DHT,
    CAMERA,
    MOTION,
    SOCKET
};

typedef struct command
{
    char* env[MAX_ENV_COUNT];   // environment-specific options
    char* arg[MAX_ARGUMENT_COUNT];  // arguments
} command;

/**************************************/
/*      FUNCTIONS                     */
/**************************************/

int module_type_to_int(enum module_type);
enum module_type int_to_module_type(int);
enum module_type get_module_type_from_config_line(char*);
pid_t start_module(enum module_type, char*);

#endif
