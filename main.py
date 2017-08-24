"""Utilize all available cores to process a list of work."""
import multiprocessing as mp
import threading
import queue
from time import sleep

try:
    NUMB_PROCESSES = mp.cpu_count()
except NotImplementedError:
    NUMB_PROCESSES = 1
NUMB_THREADS_PER_PROCESS = 8
Q = mp.Queue()


class CustomThread(threading.Thread):
    """This functions the same as the inherited Thread
    class except with added semaphore parameter, which
    always releases the semaphore when the thread is done.
    """
    def __init__(self, semaphore=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._semaphore = semaphore

    def run(self):
        try:
            if self._target:
                self._target(*self._args, **self._kwargs)
        finally:
            if self._semaphore:
                self._semaphore.release()
            del self._target, self._args, self._kwargs


def do_work(i, process_name):
    """Do the heavy processing."""
    sleep(0.5)
    print('Process Number: {}, value: {}'.format(
        process_name,i*i))


def populate_queue():
    """Fill up the queue with work to do.
    Additional work will not be added."""
    for x in range(10000):
        Q.put(x)


def run_threads(p_name, semaphore):
    """As long as there are items on the queue,
    i.e. work to do, then we keep threading."""
    while not Q.empty():
        semaphore.acquire()
        try:
            i = Q.get(timeout=1)
        except queue.Empty:
            break
        CustomThread(
            target=do_work, daemon=1,
            args=(i,p_name), semaphore=semaphore
        ).start()


def start_processes():
    """Initialize the queue with work and start
    a number of process (defined above). With
    each process, we create a bounded semaphore
    to control the number of active threads
    per process."""
    populate_queue()
    process_list = []
    for x in range(NUMB_PROCESSES):
        semaphore = threading.BoundedSemaphore(
            NUMB_THREADS_PER_PROCESS)
        # pass the semaphore to the target func
        p = mp.Process(
            target=run_threads,
            args=(x,semaphore,), name=str(x)
        )
        process_list.append(p)
        p.start()
    for process in process_list:
        # make sure all processes have completed
        process.join()

if __name__ == '__main__':
    start_processes()
