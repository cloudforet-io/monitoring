import unittest
from datetime import datetime, timedelta
from unittest.mock import patch
from mongoengine import connect, disconnect

from spaceone.core.unittest.result import print_data
from spaceone.core.unittest.runner import RichTestRunner
from spaceone.core import config
from spaceone.core import utils
from spaceone.core.transaction import Transaction
from spaceone.monitoring.manager.event_manager import EventManager
from spaceone.monitoring.model.event_model import *
from test.factory.event_factory import EventFactory


class TestEventManager(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config.init_conf(package='spaceone.monitoring')
        config.set_service_config()
        config.set_global(MOCK_MODE=True)
        connect('test', host='mongomock://localhost')

        cls.domain_id = utils.generate_id('domain')
        cls.transaction = Transaction({
            'service': 'monitoring',
            'api_class': 'Event'
        })
        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        disconnect()

    def tearDown(self, *args) -> None:
        print()
        print('(tearDown) ==> Delete all data_sources')
        event_vos = Event.objects.filter()
        event_vos.delete()

    def test_update_event_by_vo(self):
        test_event = EventFactory(alert_id='alert-400c20b10a5c',  domain_id='domain-58010aa2e451', event_type='ALERT')
        merge_to = 'alert-b02c18c373ae'
        event_params = {'alert_id': merge_to}

        self.transaction.method = 'update'
        event_mgr = EventManager(transaction=self.transaction)
        updated_event_info = event_mgr.update_event_by_vo(event_params.copy(), event_vo=test_event)

        print(f'event_data_returned_info: {updated_event_info}')
        self.assertEqual(merge_to, updated_event_info.alert_id)


if __name__ == "__main__":
    unittest.main(testRunner=RichTestRunner)
