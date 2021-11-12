import unittest
from unittest.mock import patch
from mongoengine import connect, disconnect
from spaceone.core.unittest.result import print_data
from spaceone.core.unittest.runner import RichTestRunner
from spaceone.core import config
from spaceone.core import utils
from spaceone.core.transaction import Transaction
from spaceone.monitoring.error import *
from spaceone.monitoring.model.data_source_model import DataSource
from spaceone.monitoring.service.alert_service import AlertService
from spaceone.monitoring.service.event_service import EventService
from spaceone.monitoring.manager.event_manager import EventManager
from spaceone.monitoring.manager.alert_manager import AlertManager
from spaceone.monitoring.manager.event_manager import EventManager
from spaceone.monitoring.model.event_model import Event
from spaceone.monitoring.info.alert_info import *
from spaceone.monitoring.model.alert_model import *
from test.factory.alert_factory import AlertFactory
from test.factory.event_factory import EventFactory


class TestAlertService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config.init_conf(package='spaceone.monitoring')
        config.set_service_config()
        config.set_global(MOCK_MODE=True)
        connect('test', host='mongomock://localhost')

        cls.domain_id = utils.generate_id('domain')
        cls.transaction = Transaction({
            'service': 'monitoring',
            'api_class': 'Alert'
        })
        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        disconnect()

    def tearDown(self, *args) -> None:
        print()
        print('(tearDown) ==> Delete all data_sources')
        alert_vos = Alert.objects.filter()
        alert_vos.delete()

    @patch.object(EventManager, 'list_events', return_value=[Event(event_id='event-1130a81e7b64', alert_id='alert-400c20b10a5c'), Event(event_id='event-1130a81e7b64')])
    @patch.object(EventManager, 'update_event_by_vo', return_value=Event(event_id='event-09729273f6c1', alert_id='alert-b02c18c373ae', event_type='ALERT'))
    @patch.object(AlertManager, 'merge_alerts', return_value=Alert())
    @patch.object(AlertManager, 'delete_alert')
    def test_merge_alerts(self, *args):
        alerts = ['alert-400c20b10a5c', 'alert-b02c18c373ae']
        merge_to = 'alert-b02c18c373ae'
        params = {
            'merge_to': merge_to,
            'alerts': alerts,
            'domain_id': self.domain_id
        }

        self.transaction.method = 'merge'
        alert_svc = AlertService(transaction=self.transaction)
        alert_data_info = alert_svc.merge(params.copy())
        AlertInfo(alert_data_info)

        # Test if updated event's id is equivalent with 'merge_to'
        event_vo = EventFactory(alert_id=alert_data_info['alert_id'])
        event_mgr = EventManager(transaction=self.transaction)
        update_event_params = {'alert_id': merge_to}
        updated_event = event_mgr.update_event_by_vo(self, params=update_event_params, event_vo=event_vo)

        self.assertEqual(updated_event.alert_id, merge_to)


if __name__ == "__main__":
    unittest.main(testRunner=RichTestRunner)
