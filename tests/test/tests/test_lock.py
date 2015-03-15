import logging

from django.core.cache import cache
from django.test import TestCase
from transmissions.lock import lock

class LockTests(TestCase):

    def setUp(self):
        logging.disable(logging.WARNING)

    def test_simple(self):

        v = 1
        with lock('simple'):
            v = 2

        self.assertEqual(v, 2)

    def test_fail(self):

        v = 1
        key = 'fail'
        lock_id = 'lock-transmission-{0}'.format(key)
        cache.add(lock_id, 1, 200)
        with self.assertRaisesMessage(RuntimeError, 'Lock could not be acquired after 110ms'):
            with lock(key, 100):
                v = 2
        cache.delete(lock_id)

        self.assertEqual(v, 1)

