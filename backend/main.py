from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any

from fastapi import HTTPException

from .node_registry import NODE_REGISTRY
from .template_registry import TEMPLATE_REGISTRY
from .execution_engine import ExecutionEngine

app = FastAPI()

# Configure CORS to allow frontend to connect
origins = [
    "http://localhost:3000",  # Default for Create React App
    "http://localhost:5173", # Default for Vite
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Graph(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]

@app.get("/api/nodes")
async def get_nodes():
    """
    Returns the entire node registry to the frontend.
    """
    return NODE_REGISTRY

@app.get("/api/templates/{template_id}")
async def get_template(template_id: str):
    """
    Returns a specific graph template by its ID.
    """
    template = TEMPLATE_REGISTRY.get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template

@app.post("/api/execute")
async def execute_graph(graph: Graph):
    """
    Receives a graph for execution.
    Prototype: Prints the graph and returns a mock result.
    """
    if not graph.nodes:
        return {"status": "error", "message": "Graph is empty"}

    # Validate that all nodes are concrete
    for node in graph.nodes:
        if node.get('data', {}).get('isAbstract'):
            return {"status": "error", "message": f"Graph contains abstract node '{node.get('id')}'"}

    try:
        engine = ExecutionEngine(nodes=graph.nodes, edges=graph.edges)
        result = engine.execute()
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}
