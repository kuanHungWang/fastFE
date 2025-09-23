import { useState, useCallback, useEffect } from 'react';
import ReactFlow, {
  Controls,
  Background,
  Panel,
  applyNodeChanges,
  applyEdgeChanges,
  Handle,
  Position,
} from 'reactflow';
import axios from 'axios';

// Import components
import ConcreteNode from './components/ConcreteNode';
import NodeSelectorMenu from './components/NodeSelectorMenu';

// Import React Flow styles
import 'reactflow/dist/style.css';

// Custom component for our abstract nodes
const AbstractNode = ({ data }) => {
  return (
    <div style={{
      border: '2px dashed #aaa',
      borderRadius: '5px',
      padding: '10px 20px',
      background: '#f0f0f0',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      width: '150px',
    }}>
      <Handle type="target" position={Position.Left} />
      <strong>{data.label}</strong>
      <Handle type="source" position={Position.Right} />
    </div>
  );
};


function App() {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [nodeRegistry, setNodeRegistry] = useState(null);
  const [menu, setMenu] = useState({ visible: false, top: 0, left: 0, options: [], context: null });
  const [nodeTypes, setNodeTypes] = useState({ abstractNode: AbstractNode });

  const onNodesChange = useCallback((changes) => setNodes((nds) => applyNodeChanges(changes, nds)), [setNodes]);
  const onEdgesChange = useCallback((changes) => setEdges((eds) => applyEdgeChanges(changes, eds)), [setEdges]);

  const updateNodeParameter = (nodeId, paramName, value) => {
    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === nodeId) {
          // Create a new data object with the updated parameter
          const newData = {
            ...node.data,
            parameters: {
              ...node.data.parameters,
              [paramName]: value,
            },
          };
          return { ...node, data: newData };
        }
        return node;
      })
    );
  };

  // Load the node registry and the initial template
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/nodes');
        const registry = response.data;
        setNodeRegistry(registry);

        // Dynamically build the nodeTypes mapping
        const concreteTypes = Object.keys(registry.concrete).reduce((acc, typeId) => {
          acc[typeId] = ConcreteNode;
          return acc;
        }, {});
        setNodeTypes(prev => ({ ...prev, ...concreteTypes }));

        // Fetch the default template
        const templateResponse = await axios.get('http://localhost:8000/api/templates/default_template');
        const template = templateResponse.data;

        setNodes(template.nodes);
        setEdges(template.edges);
      } catch (error) {
        console.error("Failed to load node registry:", error);
      }
    };
    loadInitialData();
  }, []);

  const onNodeClick = useCallback((event, node) => {
    event.stopPropagation();
    if (!nodeRegistry || !node.data.isAbstract) return;

    const pane = event.target.closest('.react-flow__pane');
    const paneRect = pane.getBoundingClientRect();

    const implementations = nodeRegistry.abstract[node.data.abstractType].implementations;
    const options = implementations.map(implId => ({
      id: implId,
      label: nodeRegistry.concrete[implId].display_name,
    }));

    setMenu({
      visible: true,
      top: event.clientY - paneRect.top,
      left: event.clientX - paneRect.left,
      options,
      context: { nodeId: node.id, nodePos: node.position },
    });
  }, [nodeRegistry]);

  const replaceNode = (selectedTypeId) => {
    const { nodeId, nodePos } = menu.context;
    const concreteNodeDef = nodeRegistry.concrete[selectedTypeId];

    // Create default parameters from the registry definition
    const defaultParams = Object.entries(concreteNodeDef.parameters).reduce((acc, [key, val]) => {
      acc[key] = val.default;
      return acc;
    }, {});

    const newNode = {
      id: nodeId, // Reuse the ID
      type: selectedTypeId, // Use the specific type for the backend
      position: nodePos, // Keep the position
      data: {
        label: concreteNodeDef.display_name,
        implements: concreteNodeDef.implements,
        isAbstract: false,
        parameters: defaultParams,
        onParamChange: updateNodeParameter,
        definition: concreteNodeDef, // Pass the full definition for dynamic rendering
      },
    };

    setNodes((nds) => nds.map((n) => (n.id === nodeId ? newNode : n)));
    setMenu({ visible: false, ...menu });
  };

  const onRun = async () => {
    try {
      const response = await axios.post('http://localhost:8000/api/execute', { nodes, edges });
      const { status, result, message } = response.data;
      if (status === 'success') {
        alert('Execution successful!\nResult: ' + JSON.stringify(result));
      } else {
        alert('Execution failed:\n' + message);
      }
    } catch (error) {
      alert('An error occurred while running the execution: ' + error.message);
    }
  };

  console.log('Rendering with nodes:', nodes);

  return (
    <div style={{ width: '100vw', height: '100vh' }} onClick={() => setMenu({ ...menu, visible: false })}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        fitView
      >
        <Panel position="top-right">
          <button onClick={onRun} style={{ padding: '10px 20px', fontSize: '16px' }}>Run</button>
        </Panel>
        <Controls />
        <Background />
      </ReactFlow>
      {menu.visible && <NodeSelectorMenu {...menu} onSelect={replaceNode} />}
    </div>
  );
}

export default App;
