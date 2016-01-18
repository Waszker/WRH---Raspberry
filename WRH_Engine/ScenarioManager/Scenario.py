
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
