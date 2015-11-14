#include <sys/sem.h>
#include <sys/shm.h>
#include <sys/types.h>
#include "common.h"
#include "ipc.h"

void init_semaphore(int sem, int start_value, int sem_num)
{
    semun init_union;
    init_union.val = start_value;
    if(-1 == semctl(sem, sem_num, SETVAL, init_union)) ERR("semtctl");
}

int create_semaphore(key_t key, int nsems, int semflg, int init_val)
{
    int semId, i;
    if((semId = semget(key, nsems, semflg)) < 0) ERR("semget");
    for(i = 0; i < nsems; i++) init_semaphore(semId, init_val, i);
    return semId;
}

void remove_semaphore(int sem)
{
    if(semctl(sem,0,IPC_RMID)<0) ERR("semctl");
}

void sem_operation(int sem, int sem_num, int value)
{
    struct sembuf buffer;
    buffer.sem_num = sem_num;
    buffer.sem_op = value;
    buffer.sem_flg = 0;
    if (TEMP_FAILURE_RETRY(semop(sem,&buffer,1)) == -1) ERR("semop");
}

void acquire_semaphore(int sem, int sem_num)
{
    sem_operation(sem, sem_num, -1);
}

void release_semaphore(int sem, int sem_num)
{
    sem_operation(sem, sem_num, 1);
}

int create_memory(key_t key, int nsems, int semflg)
{
    int shmdId;
    if((shmdId = shmget(IPC_PRIVATE, nsems, semflg)) < 0) ERR("semget");
    return shmdId;
}

void remove_memory(int* addr, int mem)
{
    if(-1 == shmdt(addr)) ERR("shmdt");
    if(shmctl(mem,0,IPC_RMID)<0) ERR("semctl");
}
