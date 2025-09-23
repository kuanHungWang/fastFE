import { useState } from 'react';

const menuStyle = {
  position: 'absolute',
  background: 'white',
  border: '1px solid #ddd',
  borderRadius: '5px',
  boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
  zIndex: 10,
};

const baseItemStyle = {
  padding: '10px 20px',
  cursor: 'pointer',
};

const hoverItemStyle = {
  ...baseItemStyle,
  background: '#f0f0f0',
};

const NodeSelectorMenu = ({ top, left, options, onSelect }) => {
  const [hoveredItem, setHoveredItem] = useState(null);

  return (
    <div style={{ ...menuStyle, top, left }}>
      {options.map((option) => (
        <div
          key={option.id}
          style={hoveredItem === option.id ? hoverItemStyle : baseItemStyle}
          onMouseDown={() => onSelect(option.id)} // use onMouseDown to not lose focus
          onMouseEnter={() => setHoveredItem(option.id)}
          onMouseLeave={() => setHoveredItem(null)}
        >
          {option.label}
        </div>
      ))}
    </div>
  );
};

export default NodeSelectorMenu;
