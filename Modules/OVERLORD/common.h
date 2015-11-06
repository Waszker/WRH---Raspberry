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
#endif
