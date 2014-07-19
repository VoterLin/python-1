import pytest

import time
import threading

object_id = "python-unittest"

from Pubnub import Pubnub
p = Pubnub(
    publish_key="demo",
    subscribe_key="demo",
    origin="pubsub-beta.pubnub.com"
)

@pytest.fixture
def async(request):
    """Use py.test fixture black magic to create Event objects for each test."""
    return threading.Event()

class TestSimpleDataSync():
    data = {}

    def asyncTest(fn):
        """
        Decorator that creates an asynchronous test case with setup and teardown
        methods.
        """

        def decorator(self, async):
            self.setUp(async)
            try:
                fn(self, async)
            finally:
                self.tearDown(async)

        return decorator

    def setUp(self, async):
        """Initialize the DataSync object and its callback."""

        def callback(message, action_list):
            print "DataSync callback:", message, action_list
            self.data = message
            async.set()

        p.get_synced_object(object_id, callback)
        self.wait(async)

    def tearDown(self, async):
        """
        Python SDK will not exit because it spawns a subscribe thread that keeps
        the process active.

        Workaround; unsubscribe from all hidden DataSync channels and publish to
        the last channel to terminate the subscribe thread.
        """

        p.unsubscribe("pn_ds_" + object_id)
        p.unsubscribe("pn_ds_" + object_id + ".*")
        p.unsubscribe("pn_dstr_" + object_id)
        p.publish(channel="pn_dstr_" + object_id, message={ 'trans_id' : -1 })

    def wait(self, async):
        """
        Wait for the threading.Event object to be set, then clear it for any
        following async operations.
        """

        async.wait()
        async.clear()

    @asyncTest
    def test_set(self, async):
        """Set object data with PUT."""

        now = time.time()
        p.set(object_id, {
            "time" : now
        })
        self.wait(async)

        assert 'time' in self.data
        assert self.data['time'] == now

    @asyncTest
    def test_merge(self, async):
        """Update object data with PATCH."""

        now = time.time()
        p.merge(object_id, {
            "time" : now
        })
        self.wait(async)

        assert 'time' in self.data
        assert self.data['time'] == now

    @asyncTest
    def test_delete(self, async):
        """Delete object data with DELETE."""

        p.delete(object_id)
        self.wait(async)

        assert self.data == {}
