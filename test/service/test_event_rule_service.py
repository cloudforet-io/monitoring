import unittest

from unittest.mock import patch

from mongoengine import connect, disconnect
from spaceone.core import config, utils
from spaceone.core.transaction import Transaction
from spaceone.core.unittest.result import print_data

from spaceone.monitoring.info import EventRuleInfo, EventRulesInfo
from spaceone.monitoring.manager import IdentityManager
from spaceone.monitoring.model import EventRule
from spaceone.monitoring.service import EventRuleService
from test.factory.event_rule_factory import EventRuleFactory


class TestEventRuleService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config.init_conf(package='spaceone.monitoring')
        config.set_service_config()
        config.set_global(MOCK_MODE=True)
        connect('test', host='mongomock://localhost')

        cls.domain_id = utils.generate_id('domain')
        cls.transaction = Transaction({
            'service': 'monitoring',
            'api_class': 'EventRule'
        })
        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        disconnect()

    def tearDown(self, *args) -> None:
        print()
        print('(tearDown) ==> Delete all data_sources')
        event_rule_vos = EventRule.objects.filter()
        event_rule_vos.delete()

    @patch.object(IdentityManager, 'get_project', return_value={'project_id': 'project-xyz', 'name': 'Project X'})
    def test_create_event_rule(self, *args):
        params = {
            'name': 'aaa',
            'conditions': [
                {
                    "key": "description",
                    "value": "test",
                    "operator": "contain"
                }
            ],
            'conditions_policy': "ALL",
            'actions': {
                "add_additional_info": {}
            },
            'options': {},
            'project_id': 'project-xyz',
            'tags': {},
            'domain_id': self.domain_id
        }

        event_rule_svc = EventRuleService(transaction=self.transaction)
        event_rule_svc_vo = event_rule_svc.create(params.copy())

        print_data(event_rule_svc_vo.to_dict(), 'test_create_event_rule')

        self.assertIsInstance(event_rule_svc_vo, EventRule)
        self.assertEqual(params['name'], event_rule_svc_vo.name)
        self.assertEqual(params['domain_id'], event_rule_svc_vo.domain_id)

    def test_update_event_rule(self):
        event_rule_vo = EventRuleFactory(domain_id=self.domain_id)

        # TODO: Have to change condition factory
        condition = {
            'key': 'title',
            'value': 'new',
            'operator': 'eq'
        }

        params = {
            "event_rule_id": event_rule_vo.event_rule_id,
            "conditions": [
                condition
            ],
            "conditions_policy": "ALL",
            "actions": {"add_additional_info": {}},
            "options": {},
            "domain_id": event_rule_vo.domain_id
        }

        self.transaction.method = 'update'
        event_rule_svc = EventRuleService(transaction=self.transaction)
        update_event_rule_vo = event_rule_svc.update(params.copy())

        print_data(update_event_rule_vo.to_dict(), 'test_update_event_rule')
        EventRuleInfo(update_event_rule_vo)

        self.assertIsInstance(update_event_rule_vo, EventRule)
        self.assertEqual(condition['key'], update_event_rule_vo.conditions[0].key)
        self.assertEqual(condition['value'], update_event_rule_vo.conditions[0].value)
        self.assertEqual(condition['operator'], update_event_rule_vo.conditions[0].operator)
        self.assertEqual(params['event_rule_id'], update_event_rule_vo.event_rule_id)
        self.assertEqual(params['domain_id'], update_event_rule_vo.domain_id)

    def test_change_order_event_rule(self):
        pass
        # event_rule_vo = EventRuleFactory(domain_id=self.domain_id)
        # event_rule_vo.order = 3
        # params = {
        #     'event_rule_id': event_rule_vo.event_rule_id,
        #     'order': 3,
        #     'domain_id': self.domain_id
        # }
        #
        # self.transaction.method = 'update'
        # event_rule_svc = EventRuleService(transaction=self.transaction)
        # changed_oder_event_rule_vo = event_rule_svc.change_order(params)
        #
        # self.assertIsInstance(changed_oder_event_rule_vo, EventRule)



    def test_delete_event_rule(self):
        event_rule_vo = EventRuleFactory(domain_id=self.domain_id)

        params = {
            'event_rule_id': event_rule_vo.event_rule_id,
            'domain_id': self.domain_id
        }

        self.transaction.method = 'delete'
        event_rule_svc = EventRuleService(transaction=self.transaction)
        result = event_rule_svc.delete(params)

        self.assertIsNone(result)

    def test_get_event_rule(self):
        event_rule_vo = EventRuleFactory(domain_id=self.domain_id)

        params = {
            'event_rule_id': event_rule_vo.event_rule_id,
            'domain_id': self.domain_id
        }

        self.transaction.method = 'get'
        event_rule_svc = EventRuleService(transaction=self.transaction)
        get_event_rule_vo = event_rule_svc.get(params)

        print_data(get_event_rule_vo.to_dict(), 'test_get_event_rule')
        EventRuleInfo(get_event_rule_vo)

        self.assertIsInstance(get_event_rule_vo, EventRule)

    def test_list_event_rule(self):
        event_rule_vos = EventRuleFactory.build_batch(10, domain_id=self.domain_id)
        list(map(lambda vo: vo.save(), event_rule_vos))

        params = {
            'event_rule_id': event_rule_vos[0].event_rule_id,
            'domain_id': self.domain_id
        }

        self.transaction.method = 'list'
        event_rule_svc = EventRuleService(transaction=self.transaction)
        event_rule_svc_vos, total_count = event_rule_svc.list(params)
        EventRulesInfo(event_rule_svc_vos, total_count)

        self.assertEqual(len(event_rule_svc_vos), 1)
        self.assertIsInstance(event_rule_svc_vos[0], EventRule)
        self.assertEqual(total_count, 1)
