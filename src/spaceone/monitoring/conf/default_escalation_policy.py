DEFAULT_ESCALATION_POLICY = {
    'name': 'Default',
    'is_default': True,
    'rules': [
        {
            'notification_level': 'ALL',
            'escalate_minutes': 0
        }
    ],
    'repeat_count': 0,
    'finish_condition': 'ACKNOWLEDGED',
    'scope': 'GLOBAL'
}
