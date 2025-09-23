# Detailed Design Specification: Interactive Financial Modeler

This document outlines the detailed design for a graph-based financial modeling tool, incorporating the concepts of Abstract Nodes and Templates as described in the scenario.

---

## 1. Core Concepts & Data Models

The foundation of the system is a clear and extensible data model for representing nodes and graphs. The graph itself is a collection of `nodes` and `edges`.

### Node Data Model

We will introduce properties to distinguish between abstract and concrete nodes.

#### Abstract Node

An abstract node acts as a placeholder that defines an interface (i.e., the type of data it is expected to produce).

```json
{
  "id": "schedule-creator-abstract-1",
  "type": "abstractNode", 
  "position": { "x": 100, "y": 100 },
  "data": {
    "label": "Schedule Creator",
    "abstractType": "ScheduleCreator",
    "isAbstract": true
  }
}
```
- `type`: A generic type (`abstractNode`) for the frontend component, which will handle the special rendering (e.g., dotted border).
- `abstractType`: A key string identifying the interface (e.g., `ScheduleCreator`, `Model`, `Curve`). This is used to find compatible concrete nodes.

#### Concrete Node

A concrete node is a fully defined, executable unit of logic.

```json
{
  "id": "periodic-schedule-1",
  "type": "periodicScheduleNode",
  "position": { "x": 100, "y": 100 },
  "data": {
    "label": "Periodic Schedule",
    "implements": "ScheduleCreator",
    "isAbstract": false,
    "parameters": {
      "startDate": "2025-01-01",
      "endDate": "2026-01-01",
      "frequency": "6M"
    },
    "inputs": [{"name": "base_schedule", "type": "ScheduleCreator"}],
    "outputs": [{"name": "output_schedule", "type": "ScheduleCreator"}]
  }
}
```
- `type`: A specific type for the dedicated frontend component (`periodicScheduleNode`).
- `implements`: The `abstractType` this node can replace.
- `parameters`: In-node parameters that the user can edit directly.
- `inputs`/`outputs`: Defines the handles, their names, and the `abstractType` of data they accept/produce. This is crucial for type-checking connections.

### Template Data Model

A template is simply a graph JSON file that contains at least one node where `isAbstract` is `true`.

---

## 2. Backend Design (FastAPI + Pydantic)

The backend is responsible for defining node capabilities, validating graphs, and executing them.

### Node Registry

This is the most critical backend component for this workflow. It's a service or module that provides a complete dictionary of all available nodes and their relationships.

**Data Structure:**
```python
NODE_REGISTRY = {
    "ScheduleCreator": {
        "is_abstract": True,
        "implementations": [
            "PeriodicScheduleCreator",
            "ShiftScheduleCreator",
            "MergeScheduleCreator",
            # ...
        ]
    },
    "PeriodicScheduleCreator": {
        "is_abstract": False,
        "implements": "ScheduleCreator",
        "class": "path.to.PeriodicScheduleCreatorNode",
        "parameters": {
            "startDate": {"type": "date"},
            "endDate": {"type": "date"}
        },
        "inputs": [],
        "outputs": [{"name": "output", "type": "ScheduleCreator"}]
    },
    "ShiftScheduleCreator": {
        "is_abstract": False,
        "implements": "ScheduleCreator",
        "class": "path.to.ShiftScheduleCreatorNode",
        "parameters": {"shiftPeriod": {"type": "string"}},
        "inputs": [{"name": "base_schedule", "type": "ScheduleCreator"}],
        "outputs": [{"name": "output", "type": "ScheduleCreator"}]
    },
    # ... other nodes
}
```

### Pydantic Class Structure

We define a base class for all nodes and then inherit from it.

```python
from pydantic import BaseModel, Field
from typing import Dict, Any, List

class Node(BaseModel):
    id: str
    # ... other common fields

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

class PeriodicScheduleCreatorNode(Node):
    parameters: Dict[str, Any] # Defines startDate, endDate etc.

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        # Logic to create a periodic schedule
        schedule = # ...
        return {"output": schedule}
```

### API Endpoints

- `GET /api/nodes`
  - **Action**: Returns the entire `NODE_REGISTRY` as JSON. The frontend uses this to populate its menus and understand node relationships.
- `POST /api/execute`
  - **Action**: Receives a graph JSON. Before execution, it performs a crucial validation step: **it iterates through the nodes and rejects the request if any node has `isAbstract: true`**, returning a helpful error message.

### Connecting the Registry to Pydantic Classes: The Node Factory

A key question is: where is the link between an abstract type (like `ScheduleCreator`) and its concrete implementations (like `PeriodicScheduleCreator`) defined in the Pydantic classes? 

The answer is that this relationship is **not** defined within the Pydantic class structure itself. Instead, it is defined declaratively in the `NODE_REGISTRY` and acted upon by a **Node Factory**.

This approach decouples the node definitions (for the UI) from their execution logic (the Python code).

The **Node Factory** is a function responsible for creating an executable Pydantic object from the JSON data of a single node sent by the frontend.

Here is the workflow:

1. The `/api/execute` endpoint receives the graph and decides which node to run next.
2. It passes that node's JSON data to the `NodeFactory`.
3. The factory looks up the node's `type` in the `NODE_REGISTRY` to find the path to its implementation class (e.g., `"class": "path.to.PeriodicScheduleCreatorNode"`).
4. It dynamically imports this class, instantiates it with the node's data, and returns the executable object.

**Conceptual Code for a Node Factory:**
```python
import importlib
from .node_registry import NODE_REGISTRY # Your registry definition

def NodeFactory(node_data: dict):
    """
    Creates an executable Pydantic node object from its JSON representation.
    """
    node_type = node_data.get("type")
    
    # 1. Look up the node type in the registry
    registry_entry = NODE_REGISTRY.get(node_type)
    if not registry_entry:
        raise ValueError(f"Node type '{node_type}' not found in registry.")
        
    # 2. Get the path to the implementation class
    class_path_str = registry_entry.get("class")
    if not class_path_str:
        raise ValueError(f"Node type '{node_type}' has no implementation class defined.")

    # 3. Dynamically import the module and get the class
    module_path, class_name = class_path_str.rsplit('.', 1)
    try:
        module = importlib.import_module(module_path)
        NodeClass = getattr(module, class_name)
    except (ImportError, AttributeError):
        raise ImportError(f"Could not import class {class_name} from {module_path}")

    # 4. Instantiate the Pydantic class with the node's data
    # Pydantic will automatically validate the incoming data
    return NodeClass(**node_data['data'])
```

---

## 3. Frontend Design (React + React Flow)

The frontend is responsible for rendering the graph and managing all user interactions.

### Component Architecture

- **`GraphCanvas.js`**: The main component that wraps React Flow and manages the state of nodes and edges.
- **`AbstractNode.js`**: A single, reusable component for rendering all abstract nodes. It reads `data.label` for the title and has a special CSS class for the dotted border and a '+' icon.
- **`ConcreteNode.js`**: A single, generic component for rendering all concrete nodes. It dynamically generates the parameter editing UI by reading the node's definition from the `NODE_REGISTRY`. It will map parameter types (e.g., 'string', 'date', 'number') to specific input components (e.g., `<input type="text">`, a date picker, etc.). This makes the system highly extensible.
- **`NodeSelectorMenu.js`**: A pop-up menu component. It takes an `abstractType` as a prop and renders a list of compatible concrete nodes fetched from the backend's `/api/nodes` endpoint.

### State Management (Zustand or Redux)

The global state store will hold the `nodes` and `edges` arrays. Key actions will be defined to manipulate this state:

- `replaceNode(nodeId, newNodeData)`: This action finds a node by `nodeId`, removes it, and adds a new node in its place. It also intelligently reconnects the edges to the new node, preserving the graph's structure. This is the core of swapping an abstract node for a concrete one.
- `addNodeAndEdge(sourceNodeId, sourceHandle, newNodeData)`: Creates a new node and an edge connecting it from the specified source.

---

## 4. Scenario Walkthroughs

### Case 1: Replacing an Abstract Node

**Initial State**: User loads a template. The graph has `[AbstractScheduleCreator] -> [Model]`.

1.  **User Action**: Clicks the `AbstractScheduleCreator` node.
    - **Frontend**: The `onClick` handler in the `AbstractNode.js` component is triggered. It opens the `NodeSelectorMenu` component, passing it the prop `abstractType="ScheduleCreator"`.

2.  **User Action**: Selects `PeriodicScheduleCreator` from the pop-up menu.
    - **Frontend**: 
        1. The `NodeSelectorMenu`'s `onSelect` callback is fired.
        2. It calls the `replaceNode` state management action.
        3. The action replaces the abstract node object in the `nodes` array with a new concrete `PeriodicScheduleCreator` node object. The new node keeps the same ID and position but has `isAbstract: false` and default `parameters`.
        4. React Flow automatically re-renders, now showing the `PeriodicScheduleNode` component in place of the old abstract node.

3.  **User Action**: Fills in the `startDate`, `endDate`, etc. parameters.
    - **Frontend**: The input fields in the `PeriodicScheduleNode` component update the node's `data.parameters` in the main state.

4.  **User Action**: Clicks "Run".
    - **Frontend**: Serializes the graph (which now contains only concrete nodes) and sends it to `POST /api/execute`.
    - **Backend**: Validates that no nodes are abstract, executes the graph, and returns the result.

### Case 2: Creating a Node from a Handle

**Initial State**: User has just replaced `AbstractScheduleCreator` with `ShiftScheduleCreator`.

1.  **User Action**: Clicks and drags the input handle of the `ShiftScheduleCreator` node into a blank area of the canvas.
    - **Frontend**: React Flow's `onConnectStart` and `onConnectEnd` events are triggered. The code detects that the drag ended on the pane, not another handle. It gets the `sourceNodeId`, `sourceHandle`, and importantly, the **data type** required by that handle (from `nodes.data.inputs` which is `ScheduleCreator`).

2.  **System Action**: A pop-up menu appears.
    - **Frontend**: The event handler from step 1 opens the `NodeSelectorMenu`, passing it the required data type: `abstractType="ScheduleCreator"`.

3.  **User Action**: Selects `PeriodicScheduleCreator`.
    - **Frontend**:
        1. The `onSelect` callback is fired.
        2. It calls the `addNodeAndEdge` state management action.
        3. This action adds a new `PeriodicScheduleCreator` node to the `nodes` array and a new `edge` object to the `edges` array, connecting the `ShiftScheduleCreator`'s input to the new node's output.
        4. React Flow re-renders, showing the newly created node and the connection.

4.  **User Action**: Fills in parameters for the new `PeriodicScheduleCreator`, then clicks "Run".
    - **Frontend/Backend**: The flow proceeds exactly as in Case 1.
