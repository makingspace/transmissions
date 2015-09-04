from django.core.cache import cache
import contextlib
import time


@contextlib.contextmanager
def lock(key, timeout=5000):
    """
    A simple context manager that raises the passed exception
    if a lock can't be acquired.
    """

    lock_id = 'lock-transmission-{0}'.format(key)
    acquire_lock = lambda: cache.add(lock_id, 1, timeout)
    release_lock = lambda: cache.delete(lock_id)

    waited, hops = 0, 10
    while not acquire_lock():
        time.sleep(float(hops) / 1000.0)
        waited += hops
        if waited > timeout:
            raise RuntimeError('Lock could not be acquired after {}ms'.format(waited))

    try:
        yield
    finally:
        release_lock()
