import unittest
from datetime import datetime, timedelta
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
from spaceone.monitoring.manager.alert_manager import AlertManager
from spaceone.monitoring.manager.event_manager import EventManager
from spaceone.monitoring.model.event_model import Event
from spaceone.monitoring.info.alert_info import *
from spaceone.monitoring.model.alert_model import *
from test.factory.alert_factory import AlertFactory


class TestMetricService(unittest.TestCase):

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
        alert_vos = Alert.objects.filter()  # TODO : QUESTION
        alert_vos.delete()

    def _new_iter(self):
        return

    # TODO : QUESTION How to put factory generated data??? && how to put object
    @patch.object(EventManager, 'list_events', return_value=[{"event_id": "event-94b6c77645d7", "alert_id": "alert-b7726200f8c2"}, {"event_id": "event-94b6c77645s4", "alert_id": "alert-b7726200f8c2"}])
    @patch.object(EventManager, 'update_event_by_vo', return_value=({"event_id": "event-94b6c77645d7", "event_key": "296e44a16d1b10936f9d8587ce40efdc","alert_id": "alert-b0fd7e69691e"}))
    @patch.object(AlertManager, 'merge_alerts', return_value=Alert())
    def test_merge_alerts(self, mock_merge_alerts, *args):
        '''
        merge_to_alert_vo = AlertFactory()
        one_alert_vo = AlertFactory()
        two_alert_vo = AlertFactory()

        one_alert_dict = one_alert_vo.to_dict()
        two_alert_dict = two_alert_vo.to_dict()
        '''

        alert_one = {
        "alert_id": "alert-b0fd7e69691e",
        "title": "AWS SNS Parsing ERROR",
        "state": "TRIGGERED",
        "description": "TypeError(\"'NoneType' object is not iterable\")",
        "urgency": "HIGH",
        "severity": "CRITICAL",
        "resource": {},
        "additional_info": {}
        }

        alert_two = {
            "alert_id": "alert-b0fd7e696913",
            "title": "AWS SNS Parsing ERROR2",
            "state": "TRIGGERED",
            "description": "TypeError(\"'NoneType' object is not iterable\")",
            "urgency": "HIGH",
            "severity": "CRITICAL",
            "resource": {},
            "additional_info": {}
        }

        alerts = [alert_one, alert_two]
        merge_to = 'alert-b0fd7e69691e'

        mock_merge_alerts.return_value = {
        'results': [{
        "alert_id": "alert-b0fd7e69691e",
        "title": "AWS SNS Parsing ERROR",
        "state": "TRIGGERED",
        "description": "TypeError(\"'NoneType' object is not iterable\")",
        "urgency": "HIGH",
        "severity": "CRITICAL",
        "resource": {},
        "additional_info": {}}]
        }

        params = {
            'merge_to': merge_to,
            'alerts': alerts,
            'domain_id': self.domain_id
        }

        self.transaction.method = 'merge'
        alert_svc = AlertService(transaction=self.transaction)
        alert_data_info = alert_svc.merge(params.copy())

        # print_data(alert_data_info, 'test_alert_merge')
        print(f'alert_data_info: {alert_data_info}')
        # AlertInfo(alert_data_info['results'][0])

        self.assertEqual(params['merge_to'], alert_data_info['results'][0]['alert_id'])


if __name__ == "__main__":
    unittest.main(testRunner=RichTestRunner)
