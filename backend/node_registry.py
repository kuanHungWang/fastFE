NODE_REGISTRY = {
    "abstract": {
        "ScheduleCreator": {
            "display_name": "Schedule Creator",
            "implementations": [
                "periodicScheduleNode",
            ]
        },
        "Model": {
            "display_name": "Model",
            "implementations": [
                "pricingModelNode"
            ]
        }
    },
    "concrete": {
        "periodicScheduleNode": {
            "display_name": "Periodic Schedule",
            "implements": "ScheduleCreator",
            "class_path": "backend.nodes.PeriodicScheduleCreatorNode",
            "parameters": {
                "startDate": {"type": "date", "default": "2025-01-01"},
                "endDate": {"type": "date", "default": "2026-01-01"},
                "frequency": {"type": "string", "default": "6M"}
            },
            "inputs": [],
            "outputs": [{"name": "output_schedule", "type": "ScheduleCreator"}]
        },
        "pricingModelNode": {
            "display_name": "Pricing Model",
            "implements": "Model",
            "class_path": "backend.nodes.PricingModelNode",
            "parameters": {},
            "inputs": [{"name": "schedule_input", "type": "ScheduleCreator"}],
            "outputs": [{"name": "price", "type": "float"}]
        }
    }
}
