NODE_REGISTRY = {
    "abstract": {
        "ScheduleCreator": {
            "display_name": "Schedule Creator",
            "implementations": [
                "periodicScheduleNode",
            ],
            "inputs": [],
            "outputs": [{"name": "output_schedule", "type": "Schedule"}]
        },
        "Model": {
            "display_name": "Model",
            "implementations": [
                "pricingModelNode"
            ],
            "inputs": [{"name": "schedule_input", "type": "Schedule"}],
            "outputs": [{"name": "price", "type": "string"}]
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
            "outputs": [{"name": "output_schedule", "type": "Schedule"}]
        },
        "pricingModelNode": {
            "display_name": "Pricing Model",
            "implements": "Model",
            "class_path": "backend.nodes.PricingModelNode",
            "parameters": {},
            "inputs": [{"name": "schedule_input", "type": "Schedule"}],
            "outputs": [{"name": "price", "type": "string"}]
        }
    }
}
