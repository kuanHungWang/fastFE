# Node Developer Guide

This guide explains how to extend the application by adding new node types and new parameter types.

---

## Architecture Overview

The application is composed of a React frontend and a Python (FastAPI) backend.

- **Backend**: Defines the capabilities of all nodes, their parameters, and their execution logic.
- **Frontend**: Renders a graph-based UI. It dynamically generates the interface for nodes based on definitions provided by the backend.

---

## How to Add a New Node Type

Adding a new node (e.g., a "Shift Schedule Creator") involves two steps: defining its backend logic and registering it.

### 1. Define the Backend Logic

- **File**: `backend/nodes.py`
- **Action**: Create a new Python class that inherits from `Node`.
- **Details**:
  - The class name should be descriptive (e.g., `ShiftScheduleCreatorNode`).
  - You must implement the `execute` method. This method receives a dictionary of `inputs` from upstream nodes and must return a dictionary of its `outputs`.

**Example:**
```python
# In backend/nodes.py

class ShiftScheduleCreatorNode(Node):
    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        base_schedule = inputs.get('base_schedule_input')
        shift_period = self.data['parameters']['shiftPeriod']
        
        print(f"Shifting schedule '{base_schedule}' by {shift_period}")
        
        # In a real implementation, perform the date shift logic here
        new_schedule = f"{base_schedule} (shifted by {shift_period})"
        
        return {"output_schedule": new_schedule}
```

### 2. Register the Node

- **File**: `backend/node_registry.py`
- **Action**: Add a new entry to the `concrete` dictionary within the `NODE_REGISTRY`.
- **Details**:
  - **`display_name`**: The user-friendly name that will appear in the UI.
  - **`implements`**: The `abstract` type this node can fulfill (e.g., `ScheduleCreator`).
  - **`class_path`**: The full import path to the Python class you just created (e.g., `backend.nodes.ShiftScheduleCreatorNode`).
  - **`parameters`**: A dictionary defining the inputs the user can edit directly within the node. For each parameter, specify its `type` (e.g., 'string', 'date') and a `default` value.
  - **`inputs` / `outputs`**: Define the connection handles for the node.

**Example:**
```python
# In backend/node_registry.py, inside the 'concrete' dictionary

"shiftScheduleNode": {
    "display_name": "Shift Schedule",
    "implements": "ScheduleCreator",
    "class_path": "backend.nodes.ShiftScheduleCreatorNode",
    "parameters": {
        "shiftPeriod": {"type": "string", "default": "3D"}
    },
    "inputs": [{"name": "base_schedule_input", "type": "ScheduleCreator"}],
    "outputs": [{"name": "output_schedule", "type": "ScheduleCreator"}]
},
```

After restarting the backend server, the "Shift Schedule" option will automatically appear in the UI when a `ScheduleCreator` is needed.

---

## How to Add a New Parameter Type

If you need a new kind of UI control for a parameter (e.g., a number input with step buttons), follow these steps.

### 1. Create the React Input Component

- **Directory**: `frontend/src/components/` (or a new `inputs` subdirectory).
- **Action**: Create a new `.jsx` file for your component (e.g., `NumberInput.jsx`).
- **Details**: The component must accept `value` and `onChange` as props to work with the generic `ConcreteNode`.

**Example:**
```jsx
// In frontend/src/components/inputs/NumberInput.jsx

const NumberInput = ({ value, onChange }) => (
  <input 
    type="number" 
    style={{ width: '95%' }} 
    value={value} 
    onChange={onChange} 
  />
);

export default NumberInput;
```

### 2. Register the Input Component

- **File**: `frontend/src/components/ConcreteNode.jsx`
- **Action**: Import your new component and add it to the `InputComponentMap`.
- **Details**: The key should be the `type` string you will use in the `NODE_REGISTRY` (e.g., 'number').

**Example:**
```jsx
// In frontend/src/components/ConcreteNode.jsx

import StringInput from './inputs/StringInput';
import DateInput from './inputs/DateInput';
import NumberInput from './inputs/NumberInput'; // <-- Import new component

const InputComponentMap = {
  string: StringInput,
  date: DateInput,
  number: NumberInput, // <-- Add new entry
};
```

You can now use `"type": "number"` in your `NODE_REGISTRY` definitions, and the frontend will automatically render your new `NumberInput` component for that parameter.
