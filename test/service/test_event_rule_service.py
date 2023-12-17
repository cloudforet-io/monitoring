import unittest

from unittest.mock import patch

from parameterized import parameterized
from mongoengine import connect, disconnect
from spaceone.core import config, utils
from spaceone.core.error import ERROR_INVALID_PARAMETER
from spaceone.core.transaction import Transaction
from spaceone.core.unittest.result import print_data
from spaceone.core.unittest.runner import RichTestRunner

from spaceone.monitoring.info import EventRuleInfo, EventRulesInfo, StatisticsInfo
from spaceone.monitoring.manager import IdentityManager
from spaceone.monitoring.model import EventRule
from spaceone.monitoring.service import EventRuleService
from test.factory.event_rule_factory import EventRuleFactory


def order_name_func(testcase_func, param_num, param):
    return f"{testcase_func.__name__}(order={parameterized.to_safe_name(str(param.args[0]))})"


def key_value_name_func(testcase_func, param_num, param):
    key = parameterized.to_safe_name(str(param.args[0]))
    value = parameterized.to_safe_name(str(param.args[1]))
    return f"{testcase_func.__name__}(key={key},value={value})"


class TestEventRuleService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config.init_conf(package="spaceone.monitoring")
        config.set_service_config()
        config.set_global(MOCK_MODE=True)
        connect("test", host="mongomock://localhost")

        cls.domain_id = utils.generate_id("domain")
        cls.transaction = Transaction(
            {"service": "monitoring", "api_class": "EventRule"}
        )
        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        disconnect()

    def tearDown(self, *args) -> None:
        print()
        print("(tearDown) ==> Delete all data_sources")
        event_rule_vos = EventRule.objects.filter()
        event_rule_vos.delete()

    @parameterized.expand(
        [["description", "test"], ["account", "1234567890"]],
        name_func=key_value_name_func,
    )
    @patch.object(
        IdentityManager,
        "get_project",
        return_value={"project_id": "project-xyz", "name": "Project X"},
    )
    def test_create_event_rule(self, key, value, *args):
        params = {
            "name": "aaa",
            "conditions": [{"key": key, "value": value, "operator": "contain"}],
            "conditions_policy": "ALL",
            "actions": {"add_additional_info": {}},
            "options": {},
            "project_id": "project-xyz",
            "tags": {},
            "domain_id": self.domain_id,
        }

        event_rule_svc = EventRuleService(transaction=self.transaction)
        event_rule_svc_vo = event_rule_svc.create(params.copy())

        print_data(event_rule_svc_vo.to_dict(), "test_create_event_rule")

        self.assertIsInstance(event_rule_svc_vo, EventRule)
        self.assertEqual(params["name"], event_rule_svc_vo.name)
        self.assertEqual(params["domain_id"], event_rule_svc_vo.domain_id)

    def test_update_event_rule(self):
        event_rule_vo = EventRuleFactory(domain_id=self.domain_id)

        condition = {"key": "title", "value": "new", "operator": "eq"}

        params = {
            "event_rule_id": event_rule_vo.event_rule_id,
            "conditions": [condition],
            "conditions_policy": "ALL",
            "actions": {"add_additional_info": {}},
            "options": {},
            "domain_id": event_rule_vo.domain_id,
        }

        self.transaction.method = "update"
        event_rule_svc = EventRuleService(transaction=self.transaction)
        update_event_rule_vo = event_rule_svc.update(params.copy())

        print_data(update_event_rule_vo.to_dict(), "test_update_event_rule")
        EventRuleInfo(update_event_rule_vo)

        self.assertIsInstance(update_event_rule_vo, EventRule)
        self.assertEqual(condition["key"], update_event_rule_vo.conditions[0].key)
        self.assertEqual(condition["value"], update_event_rule_vo.conditions[0].value)
        self.assertEqual(
            condition["operator"], update_event_rule_vo.conditions[0].operator
        )
        self.assertEqual(params["event_rule_id"], update_event_rule_vo.event_rule_id)
        self.assertEqual(params["domain_id"], update_event_rule_vo.domain_id)

    @parameterized.expand([[1], [2], [3]], name_func=order_name_func)
    def test_change_order_event_rule(self, current_order):
        event_rule_vos = EventRuleFactory.build_batch(10, domain_id=self.domain_id)
        list(map(lambda vo: vo.save(), event_rule_vos))
        target_event_rule_vo = event_rule_vos[0]

        params = {
            "event_rule_id": target_event_rule_vo.event_rule_id,
            "order": current_order,
            "domain_id": self.domain_id,
        }

        self.transaction.method = "change_order"
        event_rule_svc = EventRuleService(transaction=self.transaction)
        result = event_rule_svc.change_order(params)
        print_data(result.to_dict(), f"test_change_order(order={current_order})")

        self.assertIsInstance(result, EventRule)
        self.assertEqual(result.order, current_order)

    @parameterized.expand([[-1], [0]], name_func=order_name_func)
    def test_change_order_event_rule_less_than_or_equal_zero(self, current_order):
        event_rule_vos = EventRuleFactory.build_batch(5, domain_id=self.domain_id)
        list(map(lambda vo: vo.save(), event_rule_vos))
        target_event_rule_vo = event_rule_vos[2]

        params = {
            "event_rule_id": target_event_rule_vo.event_rule_id,
            "order": current_order,
            "domain_id": self.domain_id,
        }

        self.transaction.method = "change_order"
        event_rule_svc = EventRuleService(transaction=self.transaction)

        with self.assertRaises(ERROR_INVALID_PARAMETER):
            event_rule_svc.change_order(params)

    def test_change_order_event_rule_order_greater_than_highest_order(self):
        event_rule_vos = EventRuleFactory.build_batch(5, domain_id=self.domain_id)
        list(map(lambda vo: vo.save(), event_rule_vos))
        target_event_rule_vo = event_rule_vos[2]

        params = {
            "event_rule_id": target_event_rule_vo.event_rule_id,
            "order": 7,
            "domain_id": self.domain_id,
        }

        self.transaction.method = "change_order"
        event_rule_svc = EventRuleService(transaction=self.transaction)

        with self.assertRaises(ERROR_INVALID_PARAMETER):
            event_rule_svc.change_order(params)

    def test_delete_event_rule(self):
        event_rule_vo = EventRuleFactory(domain_id=self.domain_id)

        params = {
            "event_rule_id": event_rule_vo.event_rule_id,
            "domain_id": self.domain_id,
        }

        self.transaction.method = "delete"
        event_rule_svc = EventRuleService(transaction=self.transaction)
        result = event_rule_svc.delete(params)

        self.assertIsNone(result)

    def test_get_event_rule(self):
        event_rule_vo = EventRuleFactory(domain_id=self.domain_id)

        params = {
            "event_rule_id": event_rule_vo.event_rule_id,
            "domain_id": self.domain_id,
        }

        self.transaction.method = "get"
        event_rule_svc = EventRuleService(transaction=self.transaction)
        get_event_rule_vo = event_rule_svc.get(params)

        print_data(get_event_rule_vo.to_dict(), "test_get_event_rule")
        EventRuleInfo(get_event_rule_vo)

        self.assertIsInstance(get_event_rule_vo, EventRule)

    def test_list_event_rule(self):
        event_rule_vos = EventRuleFactory.build_batch(10, domain_id=self.domain_id)
        list(map(lambda vo: vo.save(), event_rule_vos))

        params = {
            "event_rule_id": event_rule_vos[0].event_rule_id,
            "domain_id": self.domain_id,
        }

        self.transaction.method = "list"
        event_rule_svc = EventRuleService(transaction=self.transaction)
        event_rule_svc_vos, total_count = event_rule_svc.list(params)
        EventRulesInfo(event_rule_svc_vos, total_count)

        self.assertEqual(len(event_rule_svc_vos), 1)
        self.assertIsInstance(event_rule_svc_vos[0], EventRule)
        self.assertEqual(total_count, 1)

    def test_stat_event_rule(self):
        event_rule_vos = EventRuleFactory.build_batch(10, domain_id=self.domain_id)
        list(map(lambda vo: vo.save(), event_rule_vos))

        params = {
            "domain_id": self.domain_id,
            "query": {"distinct": "event_rule_id", "page": {"start": 2, "limit": 3}},
        }

        self.transaction.method = "stat"
        event_rule_svc = EventRuleService(transaction=self.transaction)
        values = event_rule_svc.stat(params)
        StatisticsInfo(values)

        print_data(values, "test_stat_event_rule_distinct")


if __name__ == "__main__":
    unittest.main(testRunner=RichTestRunner)
