TEMPLATE_REGISTRY = {
    "default_template": {
        "nodes": [
            {
                "id": "schedule-creator-abstract-1",
                "type": "abstractNode",
                "position": {"x": 100, "y": 100},
                "data": {
                    "label": "Schedule Creator",
                    "abstractType": "ScheduleCreator",
                    "isAbstract": True
                }
            },
            {
                "id": "model-abstract-1",
                "type": "abstractNode",
                "position": {"x": 450, "y": 100},
                "data": {
                    "label": "Model",
                    "abstractType": "Model",
                    "isAbstract": True
                }
            }
        ],
        "edges": [
            {
                "id": "e1-2",
                "source": "schedule-creator-abstract-1",
                "target": "model-abstract-1",
                "sourceHandle": "output_schedule",
                "targetHandle": "schedule_input"
            }
        ]
    }
}
