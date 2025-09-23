import { Handle, Position } from 'reactflow';

const nodeStyle = {
  border: '1px solid #777',
  borderRadius: '5px',
  padding: '10px',
  background: '#fff',
  width: '200px',
};

const labelStyle = {
  display: 'block',
  marginBottom: '5px',
  color: '#555',
  fontSize: '12px',
};

const inputStyle = {
  width: '95%',
  padding: '5px',
  border: '1px solid #ccc',
  borderRadius: '3px',
  marginBottom: '10px',
  fontSize: '14px',
};

// In a real app, these would be more complex components (e.g., a real date picker)
const StringInput = ({ value, onChange }) => (
  <input type="text" style={inputStyle} value={value} onChange={onChange} />
);

const DateInput = ({ value, onChange }) => (
  <input type="date" style={inputStyle} value={value} onChange={onChange} />
);

// --- This is the map you would extend to add new parameter types ---
const InputComponentMap = {
  string: StringInput,
  date: DateInput,
};

const ConcreteNode = ({ id, data }) => {
  const renderParameter = (paramName) => {
    const paramDef = data.definition.parameters[paramName];
    const paramType = paramDef.type;
    const InputComponent = InputComponentMap[paramType] || StringInput; // Default to string input

    return (
      <div key={paramName}>
        <label style={labelStyle}>{paramName}</label>
        <InputComponent
          value={data.parameters[paramName]}
          onChange={(e) => data.onParamChange(id, paramName, e.target.value)}
        />
      </div>
    );
  };

  return (
    <div style={nodeStyle}>
      <Handle type="target" position={Position.Left} />
      <strong>{data.label}</strong>
      <hr />
      <div style={{ marginTop: '10px' }}>
        {data.definition && data.definition.parameters &&
          Object.keys(data.definition.parameters).map(renderParameter)}
      </div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
};

export default ConcreteNode;
