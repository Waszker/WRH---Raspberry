#ifndef _IPC_H
#define _IPC_H

typedef union semun
{
    int val;
    struct semid_ds *buf;
    unsigned short *array;
    struct seminfo *_buf;
} semun;

void init_semaphore(int, int, int);
int create_semaphore(key_t, int, int, int);
void remove_semaphore(int);
void sem_operation(int, int, int);
void acquire_semaphore(int, int);
void release_semaphore(int, int);
int create_memory(key_t, int, int);
void remove_memory(int*, int);
#endif
