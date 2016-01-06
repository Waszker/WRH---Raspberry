
class Scenario:

    def __init__(self, json_scenario):
        self.id = int(json_scenario["Id"])
        self.device_id = int(json_scenario["DeviceId"])
        self.condition = int(json_scenario["Condition"])
        self.action = int(json_scenario["Action"])
        self.value_int = int(json_scenario["ValueInt"])
        self.value_string = str(json_scenario["ValueString"])
        self.name = str(json_scenario["Name"])
        self.priority = int(json_scenario["Priority"])
        self.condition_module_id = int(json_scenario["ConditionModuleId"])
        self.action_module_id = int(json_scenario["ActionModuleId"])
        self.start_date = str(json_scenario["StartDate"])
        self.end_date = str(json_scenario["EndDate"])
        self.recurring = int(json_scenario["Recurring"])

    def __init__(self, id, device_id, condition, action, value_int, value_string, name, priority, condition_module_id,
                 action_module_id, start_date, end_date, recurring):
        self.id = id
        self.device_id = device_id
        self.condition = condition
        self.action = action
        self.value_int = value_int
        self.value_string = value_string
        self.name = name
        self.priority = priority
        self.condition_module_id = condition_module_id
        self.action_module_id = action_module_id
        self.start_date = start_date
        self.end_date = end_date
        self.recurring = recurring