
class Execution:

    def __init__(self, device_id, device_token, condition_value, action_value, timestamp, scenario_id, condition, action):
        self.device_id = device_id
        self.device_token = device_token
        self.condition_value = condition_value
        self.action_value = action_value
        self.timestamp = timestamp
        self.scenario_id = scenario_id
        self.condition = condition
        self.action = action