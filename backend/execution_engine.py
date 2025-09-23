import importlib
from typing import List, Dict, Any
from collections import deque

from .node_registry import NODE_REGISTRY

def NodeFactory(node_data: Dict[str, Any]):
    """
    Creates an executable Pydantic node object from its JSON representation.
    """
    node_type = node_data.get("type")
    registry_entry = NODE_REGISTRY['concrete'].get(node_type)
    if not registry_entry:
        raise ValueError(f"Node type '{node_type}' not found in concrete registry.")

    class_path_str = registry_entry.get("class_path")
    if not class_path_str:
        raise ValueError(f"Node type '{node_type}' has no implementation class defined.")

    module_path, class_name = class_path_str.rsplit('.', 1)
    try:
        module = importlib.import_module(module_path)
        NodeClass = getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        raise ImportError(f"Could not import class {class_name} from {module_path}: {e}")

    return NodeClass(**node_data)

class ExecutionEngine:
    def __init__(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]):
        self.nodes = {node['id']: node for node in nodes}
        self.edges = edges
        self.adjacency = {node_id: [] for node_id in self.nodes}
        self.in_degree = {node_id: 0 for node_id in self.nodes}
        self._build_graph()

    def _build_graph(self):
        for edge in self.edges:
            source, target = edge['source'], edge['target']
            self.adjacency[source].append(target)
            self.in_degree[target] += 1

    def topological_sort(self) -> List[str]:
        queue = deque([node_id for node_id in self.nodes if self.in_degree[node_id] == 0])
        sorted_order = []
        while queue:
            node_id = queue.popleft()
            sorted_order.append(node_id)
            for neighbor in self.adjacency[node_id]:
                self.in_degree[neighbor] -= 1
                if self.in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(sorted_order) != len(self.nodes):
            raise Exception("Graph has a cycle!")
        return sorted_order

    def execute(self):
        sorted_nodes = self.topological_sort()
        results = {}
        final_node_output = None

        for node_id in sorted_nodes:
            node_data = self.nodes[node_id]
            
            # Gather inputs for the current node
            inputs = {}
            for edge in self.edges:
                if edge['target'] == node_id:
                    source_node_id = edge['source']
                    source_handle = edge.get('sourceHandle') # e.g., 'output_schedule'
                    target_handle = edge.get('targetHandle') # e.g., 'schedule_input'
                    
                    if source_node_id in results and source_handle in results[source_node_id]:
                        inputs[target_handle] = results[source_node_id][source_handle]

            # Instantiate and execute the node
            node_instance = NodeFactory(node_data)
            node_output = node_instance.execute(inputs)
            results[node_id] = node_output
            final_node_output = node_output # Keep track of the last output

        return final_node_output
