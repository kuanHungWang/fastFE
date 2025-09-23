# Solution 1: The Rapid Prototyping (Batteries-Included) Approach

This approach focuses on using powerful, existing libraries to get a functional prototype up and running as quickly as possible. It's great for validating the concept and iterating on features.

**Architecture Overview:**

*   **Frontend**: A React-based single-page application (SPA) using a dedicated graph library.
*   **Backend**: A Python FastAPI server to manage graph execution and data.
*   **Communication**: Standard REST API with JSON.

**Component Breakdown:**

1.  **Frontend (React + React Flow):**
    *   **Why React Flow?**: It's a highly popular, well-documented, and feature-rich library for building node-based UIs. It handles rendering, connections, panning, zooming, and provides helpers for custom nodes.
    *   **Implementation:**
        *   **Canvas**: Use the `<ReactFlow>` component as the main canvas.
        *   **Nodes**: Create custom React components for different node types (e.g., `DepositNode`, `SwapCurveNode`). These components will render the node's title, input fields for direct parameters, and connection handles (sources/targets).
        *   **Node Palette**: A sidebar lists all available nodes, categorized by type. Users can drag these onto the canvas.
        *   **Contextual Menu**: When a user drags a connection handle into an empty space, you can use React Flow's events to trigger a popup menu that suggests compatible nodes.
        *   **State Management**: Use a state management library like Zustand or Redux Toolkit to manage the graph's state (nodes, edges, global variables).

2.  **Backend (Python + FastAPI + Pydantic):**
    *   **Why FastAPI?**: It's a modern, high-performance Python web framework that uses Pydantic for data validation out-of-the-box. This makes defining and validating your node structures clean and robust.
    *   **Node Definition**:
        *   Define each node's parameters and logic using Pydantic models and simple Python functions. This is a more structured approach than using `Callable`.
        *   **Example Node Definition (`ir_template.py` style):**
            ```python
            from pydantic import BaseModel, Field
            import QuantLib as ql

            class SwapCurveInputs(BaseModel):
                deposits: list # This would be a more specific Pydantic model
                swaps: list    # representing deposit/swap data

            class SwapCurveNode:
                # Pydantic model defines the inputs from other nodes
                inputs: SwapCurveInputs 
                
                # Pydantic model can also define direct inputs
                day_count: str = Field(default="Thirty360", description="Day count convention")

                def execute(self) -> ql.YieldTermStructure:
                    # Node logic here...
                    # Use self.inputs.deposits, self.day_count, etc.
                    # ...
                    return yield_curve_handle
            ```
    *   **Execution Engine**:
        *   Implement a simple topological sort algorithm to determine the execution order of the nodes based on their connections.
        *   Create an `/execute` endpoint that receives the graph structure (nodes and edges) as JSON.
        *   The engine traverses the graph, executing each node's function and passing the output to the next connected node. It can also handle partial graph execution by identifying a subgraph ending at a specific node.

3.  **Serialization:**
    *   The frontend is responsible for generating a JSON representation of the graph (nodes with positions, edges, and global variable values).
    *   This JSON is sent to the backend for execution or can be saved to a file/database. React Flow provides helper functions (`toObject()`) that make this straightforward.

---

## Frontend-Backend Communication Flow

In this architecture, the **frontend is the "source of truth" for the graph's structure and UI state** (like node positions). The **backend is the "source of truth" for computation and business logic**.

### The Standard Interaction Flow

This covers actions like moving nodes, connecting them, and editing parameters.

1.  **User Manipulates the Graph (Frontend-Only)**
    *   A user drags a node, connects two nodes, or types a value into a node's parameter field (e.g., changing a date).
    *   The React Flow library captures this event and updates its internal state *entirely within the browser*.
    *   The UI updates instantly.
    *   **No backend communication happens at this stage.** This is key to making the interface feel fast and responsive.

2.  **User Triggers a Backend Action (e.g., "Run" or "Save")**
    *   The user decides they are ready to execute a calculation or save their work. They click a "Run" button on a specific node or a global "Save" button.

3.  **Frontend Sends a Request to the Backend**
    *   The frontend application serializes the *entire current state* of the graph into a clean JSON object. This object contains:
        *   A list of all nodes (with their ID, type, position, and parameter data).
        *   A list of all edges (describing the connections between nodes).
        *   Any global variables.
    *   It then sends this JSON payload via an HTTP POST request to a specific backend endpoint (e.g., `/api/execute` or `/api/save`).

4.  **Backend Processes the Request**
    *   The FastAPI backend receives the request.
    *   **For an `/execute` request:**
        *   It validates the incoming JSON using Pydantic models.
        *   It uses the list of nodes and edges to determine the correct order of execution (using a topological sort).
        *   It executes the Python functions for each node in sequence, passing the output of one node as the input to the next.
    *   **For a `/save` request:**
        *   It simply takes the JSON payload and saves it to a file or a database record.

5.  **Backend Sends a Response to the Frontend**
    *   **For an `/execute` request:** The backend sends back the *result* of the computation. This is typically a JSON object containing the final output value(s), any intermediate data you wish to display, and a status (e.g., `success` or `error`). It does **not** send the whole graph back.
    *   **For a `/save` request:** The backend sends back a simple confirmation message, perhaps with the ID of the saved graph (e.g., `{"status": "success", "graphId": "xyz-123"}`).

6.  **Frontend Updates the UI with the Result**
    *   The frontend receives the response from the backend.
    *   It might display the calculated result in a popup, a dedicated "output" panel, or by updating a specific field on the node that was executed. If there was an error, it would display an error message.

### Visualizing the Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend (React Flow)
    participant Backend (FastAPI)

    User->>Frontend: Drags Node A
    Note right of Frontend: UI updates instantly (no API call)

    User->>Frontend: Connects Node A to Node B
    Note right of Frontend: UI updates instantly (no API call)

    User->>Frontend: Clicks "Run" on Node B
    Frontend->>Backend: POST /api/execute (sends graph as JSON)
    activate Backend

    Backend->>Backend: 1. Validate Graph
    Backend->>Backend: 2. Determine Execution Order (A -> B)
    Backend->>Backend: 3. Execute Node A logic
    Backend->>Backend: 4. Execute Node B logic
    
    Backend-->>Frontend: 200 OK (sends result of Node B as JSON)
    deactivate Backend

    Frontend->>User: Display result from Node B

---

## Defining Edges: The Connections Between Nodes

Edges are the lines that connect your nodes, representing the flow of data and logic through your graph. In this architecture, an edge is a simple data structure that defines a directed connection between two specific points on two different nodes.

### How to Define an Edge

Following the convention used by libraries like React Flow, an edge is represented as a JSON object with five key properties:

1.  `id`: A unique string to identify the edge. React Flow can generate this automatically (e.g., `reactflow__edge-nodeA-output-nodeB-input`).
2.  `source`: The unique ID of the node where the edge starts.
3.  `target`: The unique ID of the node where the edge ends.
4.  `sourceHandle`: The specific ID of the **output point** (or "handle") on the `source` node.
5.  `targetHandle`: The specific ID of the **input point** (or "handle") on the `target` node.

Handles are the small connection dots you see on nodes in graph UIs. Using `sourceHandle` and `targetHandle` is vital because a single node can have multiple inputs and multiple outputs.

### Example from Your Code

Let's translate a line from your `ir_template.py` file into a graph representation.

**Code:**
```python
# curve is the output of create_usd_curve()
hw_model = HullWhiteModel(valuationDate, curve['curve'])
```

This single line implies two connections into the `HullWhiteModel` node. Let's assume we have three nodes in our graph:

*   A `ValuationDateNode` with ID `date-node-1`. It has one output handle named `date_output`.
*   A `UsdCurveNode` with ID `curve-node-1`. It has one output handle named `curve_output`.
*   A `HullWhiteModelNode` with ID `hw-model-1`. It has two input handles: `valuation_date_input` and `curve_input`.

The connections would be defined by these two edge objects in the JSON payload:

**Edge 1: Connecting the date**
```json
{
  "id": "edge-1",
  "source": "date-node-1",
  "target": "hw-model-1",
  "sourceHandle": "date_output",
  "targetHandle": "valuation_date_input"
}
```

**Edge 2: Connecting the curve**
```json
{
  "id": "edge-2",
  "source": "curve-node-1",
  "target": "hw-model-1",
  "sourceHandle": "curve_output",
  "targetHandle": "curve_input"
}
```

### How the Backend Uses This

When the backend receives the list of nodes and these edge objects, it can build a complete dependency graph.

1.  It knows that `hw-model-1` cannot be executed until its inputs (`valuation_date_input` and `curve_input`) are satisfied.
2.  It looks at the edges and sees that `valuation_date_input` is connected to `date-node-1` and `curve_input` is connected to `curve-node-1`.
3.  Therefore, it knows it must first execute `date-node-1` and `curve-node-1`.
4.  Once those are complete, it takes their results and feeds them as arguments to the `HullWhiteModelNode`'s execution function, mapping them correctly using the handle names.

This handle-based approach is extremely flexible and allows you to build complex nodes that consume and produce many different pieces of data, just like functions in a program.
