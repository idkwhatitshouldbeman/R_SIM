import React, { useState, useRef, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('builder');
  const [selectedComponent, setSelectedComponent] = useState(null);
  const [rocketComponents, setRocketComponents] = useState([]);
  const [rocketWeight, setRocketWeight] = useState(0);
  const [rocketCG, setRocketCG] = useState(0);
  const [inputValues, setInputValues] = useState({});
  const [draggedComponent, setDraggedComponent] = useState(null);
  const [dragOverIndex, setDragOverIndex] = useState(null);
  const [hoveredComponent, setHoveredComponent] = useState(null);
  const [zoom, setZoom] = useState(1);
  const canvasRef = useRef(null);
  
  // Simulation state
  const [openSections, setOpenSections] = useState({
    cfd: false,
    atmosphere: false,
    boundaries: false,
    mesh: false,
    analysis: false
  });
  
  const [simulationConfig, setSimulationConfig] = useState({
    // CFD Solver Settings
    solverType: 'pimpleFoam',
    turbulenceModel: 'LES',
    timeStep: 0.001,
    maxTime: 30,
    writeInterval: 100,
    
    // Atmospheric Conditions
    launchAltitude: 0,
    temperature: 15,
    pressure: 101325,
    humidity: 50,
    windSpeed: 0,
    windDirection: 0,
    
    // Boundary Conditions
    inletVelocity: 0,
    outletPressure: 101325,
    wallCondition: 'noSlip',
    domainSize: 10,
    
    // Mesh Settings
    baseCellSize: 0.01,
    boundaryLayerCells: 5,
    refinementLevel: 'medium',
    meshQuality: 0.3,
    
    // Analysis Settings
    calculateDrag: true,
    calculateLift: true,
    calculatePressure: true,
    calculateVelocity: true,
    outputFormat: 'vtk'
  });
  
  const [simulationRunning, setSimulationRunning] = useState(false);
  const [simulationStatus, setSimulationStatus] = useState(null);

  const addComponent = (type) => {
    console.log('Adding component:', type); // Debug log
    
    // Find the last body tube to attach fins and rail buttons to
    let attachedToComponent = null;
    if (type === 'Fins' || type === 'Rail Button') {
      const bodyComponents = rocketComponents.filter(comp => 
        ['Body Tube', 'Transition'].includes(comp.type)
      );
      if (bodyComponents.length > 0) {
        attachedToComponent = bodyComponents[bodyComponents.length - 1].id;
      }
    }
    
    // Count existing components of this type for better naming
    const existingCount = rocketComponents.filter(comp => comp.type === type).length;
    
    const newComponent = {
      id: Date.now(),
      type,
      name: `${type} ${existingCount + 1}`,
      length: type === 'Transition' ? 30 : type === 'Nose Cone' ? 40 : type === 'Fins' ? 0 : 60,
      diameter: type === 'Transition' ? 20 : 20,
      topDiameter: type === 'Transition' ? 20 : 20,
      bottomDiameter: type === 'Transition' ? 15 : 20,
      lengthInput: type === 'Transition' ? '30' : type === 'Nose Cone' ? '40' : type === 'Fins' ? '0' : '60',
      diameterInput: type === 'Transition' ? '20' : '20',
      topDiameterInput: type === 'Transition' ? '20' : '20',
      bottomDiameterInput: type === 'Transition' ? '15' : '20',
      noseShape: type === 'Nose Cone' ? 'conical' : null,
      tipLength: type === 'Nose Cone' ? 15 : null,
      finShape: type === 'Fins' ? 'rectangular' : null,
      finCount: type === 'Fins' ? 4 : null,
      finHeight: type === 'Fins' ? 25 : null,
      finWidth: type === 'Fins' ? 15 : null,
      finThickness: type === 'Fins' ? 2 : null,
      finSweep: type === 'Fins' ? 0 : null,
      railButtonHeight: type === 'Rail Button' ? 8 : null,
      railButtonWidth: type === 'Rail Button' ? 4 : null,
      railButtonOffset: type === 'Rail Button' ? 2 : null,
      attachedToComponent: attachedToComponent
    };
    console.log('New component:', newComponent); // Debug log
    setRocketComponents([...rocketComponents, newComponent]);
  };

  const updateComponent = (id, field, value) => {
    setRocketComponents(components => {
      const updated = components.map(comp =>
        comp.id === id ? { ...comp, [field]: value } : comp
      );
      
      // Only clean up if we're updating an attachment field
      if (field === 'attachedToComponent') {
        return cleanupOrphanedComponents(updated);
      }
      return updated;
    });
  };

  // Function to clean up orphaned components
  const cleanupOrphanedComponents = (components) => {
    return components.filter(comp => {
      if ((comp.type === 'Fins' || comp.type === 'Rail Button') && comp.attachedToComponent) {
        // Check if the attached component still exists
        const attachedExists = components.some(c => c.id === comp.attachedToComponent);
        if (!attachedExists) {
          console.log(`Removing orphaned ${comp.type.toLowerCase()} ${comp.name} - attached component no longer exists`);
          return false; // Remove this component
        }
      }
      return true; // Keep this component
    });
  };

  const updateSimulationConfig = (field, value) => {
    setSimulationConfig(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const startSimulation = async () => {
    setSimulationRunning(true);
    setSimulationStatus({
      status: 'Initializing...',
      progress: 0,
      message: 'Setting up simulation environment'
    });
    
    try {
      const response = await fetch('http://localhost:5000/api/simulation/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          rocketComponents,
          rocketWeight,
          rocketCG,
          simulationConfig
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to start simulation');
      }
      
      const data = await response.json();
      console.log('Simulation started:', data);
      
      // Start polling for status updates
      pollSimulationStatus();
      
    } catch (error) {
      console.error('Error starting simulation:', error);
      setSimulationStatus({
        status: 'Error',
        message: error.message
      });
      setSimulationRunning(false);
    }
  };

  const stopSimulation = async () => {
    try {
      await fetch('http://localhost:5000/api/simulation/stop', {
        method: 'POST'
      });
      setSimulationRunning(false);
      setSimulationStatus(null);
    } catch (error) {
      console.error('Error stopping simulation:', error);
    }
  };

  const generateMesh = async () => {
    setSimulationStatus({
      status: 'Generating Mesh...',
      progress: 0,
      message: 'Creating mesh from rocket geometry'
    });
    
    try {
      const response = await fetch('http://localhost:5000/api/simulation/mesh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          rocketComponents,
          simulationConfig
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to generate mesh');
      }
      
      const data = await response.json();
      console.log('Mesh generated:', data);
      
      setSimulationStatus({
        status: 'Mesh Complete',
        progress: 100,
        message: `Mesh generated with ${data.cellCount} cells`
      });
      
    } catch (error) {
      console.error('Error generating mesh:', error);
      setSimulationStatus({
        status: 'Error',
        message: error.message
      });
    }
  };

  const pollSimulationStatus = async () => {
    const pollInterval = setInterval(async () => {
      if (!simulationRunning) {
        clearInterval(pollInterval);
        return;
      }
      
      try {
        const response = await fetch('http://localhost:5000/api/simulation/status');
        if (response.ok) {
          const status = await response.json();
          setSimulationStatus(status);
          
          if (status.status === 'Complete' || status.status === 'Error') {
            setSimulationRunning(false);
            clearInterval(pollInterval);
          }
        }
      } catch (error) {
        console.error('Error polling simulation status:', error);
      }
    }, 1000);
  };

  const handleNumberInput = (id, field, value) => {
    // Update local input state immediately
    setInputValues(prev => ({
      ...prev,
      [`${id}-${field}`]: value
    }));
    
    // Update the actual component value when valid
    if (value === '' || !isNaN(parseFloat(value))) {
      const numValue = value === '' ? 0 : parseFloat(value) || 0;
      updateComponent(id, field, numValue);
    }
  };



  const handleTransitionInput = (id, field, value) => {
    console.log('Transition input:', id, field, value); // Debug log
    
    // Update local input state immediately
    setInputValues(prev => ({
      ...prev,
      [`${id}-${field}`]: value
    }));
    
    // Always update the component value
    const numValue = value === '' ? 0 : parseFloat(value) || 0;
    console.log('Updating component:', field, numValue); // Debug log
    updateComponent(id, field, numValue);
  };

  const deleteComponent = (id) => {
    setRocketComponents(components => {
      // Remove the component and any components that depend on it
      const filtered = components.filter(comp => comp.id !== id);
      
      // Clean up orphaned components (fins and rail buttons attached to deleted body tubes)
      const cleaned = filtered.filter(comp => {
        if ((comp.type === 'Fins' || comp.type === 'Rail Button') && comp.attachedToComponent) {
          // Check if the attached component still exists
          const attachedExists = filtered.some(c => c.id === comp.attachedToComponent);
          if (!attachedExists) {
            console.log(`Removing orphaned ${comp.type.toLowerCase()} ${comp.name} - attached component no longer exists`);
            return false; // Remove this component
          }
        }
        return true; // Keep this component
      });
      
      return cleaned;
    });
    
    if (selectedComponent?.id === id) {
      setSelectedComponent(null);
    }
  };

  const moveComponent = (id, direction) => {
    const index = rocketComponents.findIndex(comp => comp.id === id);
    if (index === -1) return;
    
    const newComponents = [...rocketComponents];
    if (direction === 'up' && index > 0) {
      [newComponents[index], newComponents[index - 1]] = [newComponents[index - 1], newComponents[index]];
    } else if (direction === 'down' && index < newComponents.length - 1) {
      [newComponents[index], newComponents[index + 1]] = [newComponents[index + 1], newComponents[index]];
    }
    setRocketComponents(cleanupOrphanedComponents(newComponents));
  };

  // Drag and drop handlers
  const handleDragStart = (e, component) => {
    console.log('Drag start:', component.name, component.type, component.id);
    setDraggedComponent(component);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', component.id);
    e.dataTransfer.setData('application/json', JSON.stringify(component));
    e.stopPropagation(); // Prevent event bubbling
  };

  const handleDragOver = (e, index) => {
    e.preventDefault();
    e.stopPropagation();
    
    console.log('Drag over index:', index, 'draggedComponent:', draggedComponent?.name);
    
    // Get the body components to find the correct index
    const bodyComponents = rocketComponents.filter(comp => 
      ['Nose Cone', 'Body Tube', 'Transition'].includes(comp.type)
    );
    const dropTarget = bodyComponents[index];
    
    if ((draggedComponent?.type === 'Fins' || draggedComponent?.type === 'Rail Button') && ['Body Tube', 'Transition'].includes(dropTarget?.type)) {
      e.dataTransfer.dropEffect = 'copy'; // Show copy effect for connecting
      console.log('Setting copy effect for attachment connection');
    } else {
      e.dataTransfer.dropEffect = 'move'; // Show move effect for reordering
      console.log('Setting move effect for reordering');
    }
    
    setDragOverIndex(index);
  };

  const handleDragLeave = (e) => {
    console.log('Drag leave');
    setDragOverIndex(null);
    e.stopPropagation();
  };

  const handleDrop = (e, dropIndex) => {
    e.preventDefault();
    e.stopPropagation();
    
    console.log('Drop on index:', dropIndex, 'draggedComponent:', draggedComponent?.name);
    
    if (!draggedComponent) {
      console.log('No dragged component');
      return;
    }

    const dragIndex = rocketComponents.findIndex(comp => comp.id === draggedComponent.id);
    if (dragIndex === -1) {
      console.log('Drag index not found');
      return;
    }

    // Get the body components to find the correct drop target
    const bodyComponents = rocketComponents.filter(comp => 
      ['Nose Cone', 'Body Tube', 'Transition'].includes(comp.type)
    );
    const dropTarget = bodyComponents[dropIndex];
    
    console.log('Drop target:', dropTarget?.name, dropTarget?.type);
    
    if ((draggedComponent.type === 'Fins' || draggedComponent.type === 'Rail Button') && ['Body Tube', 'Transition'].includes(dropTarget?.type)) {
      // Connect the attachment to the body tube
      console.log('Connecting attachment to body tube');
      try {
        const newComponents = [...rocketComponents];
        newComponents[dragIndex] = {
          ...draggedComponent,
          attachedToComponent: dropTarget.id
        };
        setRocketComponents(cleanupOrphanedComponents(newComponents));
        console.log('Attachment connected successfully');
      } catch (error) {
        console.error('Error connecting attachment:', error);
      }
    } else {
      // Regular reordering
      console.log('Reordering components');
      try {
        const newComponents = [...rocketComponents];
        const [removed] = newComponents.splice(dragIndex, 1);
        newComponents.splice(dropIndex, 0, removed);
        setRocketComponents(cleanupOrphanedComponents(newComponents));
        console.log('Components reordered successfully');
      } catch (error) {
        console.error('Error reordering components:', error);
      }
    }

    setDraggedComponent(null);
    setDragOverIndex(null);
  };

  const handleDragEnd = (e) => {
    console.log('Drag end');
    setDraggedComponent(null);
    setDragOverIndex(null);
    e.stopPropagation();
  };

  const drawRocketDiagram = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const rect = canvas.getBoundingClientRect();
    
    // Set canvas size to match display size
    canvas.width = rect.width;
    canvas.height = rect.height;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Apply zoom transformation
    ctx.save();
    ctx.translate(canvas.width / 2, canvas.height / 2);
    ctx.scale(zoom, zoom);
    ctx.translate(-canvas.width / 2, -canvas.height / 2);

    // Get body components only
    const bodyComponents = rocketComponents.filter(comp => 
      ['Nose Cone', 'Body Tube', 'Transition'].includes(comp.type)
    );

    if (bodyComponents.length === 0) return;

    // Calculate total height and center everything
    const totalHeight = bodyComponents.reduce((sum, comp) => sum + (comp.length || 60), 0);
    const startY = (canvas.height - totalHeight) / 2;
    const centerX = canvas.width / 2;

    let currentY = startY;

    // Smart diameter updates - only update if values are actually different to prevent loops
    bodyComponents.forEach((component, index) => {
      if (component.type === 'Transition') {
        const componentAbove = index > 0 ? bodyComponents[index - 1] : null;
        const componentBelow = index < bodyComponents.length - 1 ? bodyComponents[index + 1] : null;
        
        if (componentAbove) {
          const expectedTopDiameter = componentAbove.diameter || 20;
          if (component.topDiameter !== expectedTopDiameter) {
            updateComponent(component.id, 'topDiameter', expectedTopDiameter);
          }
        }
        
        if (componentBelow) {
          const expectedBottomDiameter = componentBelow.diameter || 20;
          if (component.bottomDiameter !== expectedBottomDiameter) {
            updateComponent(component.id, 'bottomDiameter', expectedBottomDiameter);
          }
        }
      } else if (component.type === 'Nose Cone') {
        const componentBelow = index < bodyComponents.length - 1 ? bodyComponents[index + 1] : null;
        
        if (componentBelow) {
          const expectedBottomDiameter = componentBelow.diameter || 20;
          if (component.bottomDiameter !== expectedBottomDiameter) {
            updateComponent(component.id, 'bottomDiameter', expectedBottomDiameter);
          }
        }
      }
    });

    bodyComponents.forEach((component) => {
      const height = component.length || 60;
      
      if (component.type === 'Nose Cone') {
        const bottomDiameter = component.bottomDiameter || component.diameter || 20;
        const noseShape = component.noseShape || 'conical';
        const tipLength = component.tipLength || 15;
        
        ctx.fillStyle = '#8B4513';
        ctx.strokeStyle = '#654321';
        ctx.lineWidth = 2;
        
        if (noseShape === 'conical') {
          // Draw conical nose cone
          const x = centerX - bottomDiameter / 2;
          
          ctx.beginPath();
          ctx.moveTo(centerX, currentY);
          ctx.lineTo(x, currentY + height);
          ctx.lineTo(x + bottomDiameter, currentY + height);
          ctx.closePath();
          ctx.fill();
          ctx.stroke();
        } else if (noseShape === 'ogive') {
          // Draw ogive nose cone (elliptical)
          const x = centerX - bottomDiameter / 2;
          const radius = bottomDiameter / 2;
          
          ctx.beginPath();
          ctx.ellipse(centerX, currentY + height, radius, height, 0, 0, Math.PI, true);
          ctx.lineTo(x, currentY + height);
          ctx.lineTo(x + bottomDiameter, currentY + height);
          ctx.closePath();
          ctx.fill();
          ctx.stroke();
        } else if (noseShape === 'parabolic') {
          // Draw parabolic nose cone (corrected to point upward)
          const x = centerX - bottomDiameter / 2;
          const radius = bottomDiameter / 2;
          
          ctx.beginPath();
          ctx.moveTo(centerX, currentY);
          
          // Draw parabolic curve (inverted to point upward)
          for (let i = 0; i <= height; i += 2) {
            const t = i / height;
            const curveRadius = radius * (1 - (1 - t) * (1 - t));
            const y = currentY + i;
            const x1 = centerX - curveRadius;
            
            if (i === 0) {
              ctx.moveTo(x1, y);
            } else {
              ctx.lineTo(x1, y);
            }
          }
          
          // Complete the shape
          for (let i = height; i >= 0; i -= 2) {
            const t = i / height;
            const curveRadius = radius * (1 - (1 - t) * (1 - t));
            const y = currentY + i;
            const x2 = centerX + curveRadius;
            ctx.lineTo(x2, y);
          }
          
          ctx.closePath();
          ctx.fill();
          ctx.stroke();
        } else if (noseShape === 'stepped') {
          // Draw stepped nose cone (improved design)
          const x = centerX - bottomDiameter / 2;
          const baseHeight = height * 0.4;
          const midHeight = height * 0.35;
          const tipHeight = height * 0.25;
          
          // Base section (widest)
          ctx.fillRect(x, currentY + height - baseHeight, bottomDiameter, baseHeight);
          ctx.strokeRect(x, currentY + height - baseHeight, bottomDiameter, baseHeight);
          
          // Middle section (medium width)
          const midDiameter = bottomDiameter * 0.75;
          const midX = centerX - midDiameter / 2;
          const midY = currentY + height - baseHeight - midHeight;
          ctx.fillRect(midX, midY, midDiameter, midHeight);
          ctx.strokeRect(midX, midY, midDiameter, midHeight);
          
          // Tip section (conical)
          const tipDiameter = midDiameter * 0.6;
          const tipX = centerX - tipDiameter / 2;
          const tipY = currentY + height - baseHeight - midHeight - tipHeight;
          
          ctx.beginPath();
          ctx.moveTo(centerX, currentY);
          ctx.lineTo(tipX, tipY);
          ctx.lineTo(tipX + tipDiameter, tipY);
          ctx.closePath();
          ctx.fill();
          ctx.stroke();
        }
        
        // Highlight if selected
        if (selectedComponent?.id === component.id) {
          ctx.strokeStyle = '#00FF00';
          ctx.lineWidth = 3;
          ctx.setLineDash([5, 5]);
          ctx.stroke();
          ctx.setLineDash([]);
        }
      } else if (component.type === 'Body Tube') {
        // Draw body tube as rectangle
        const diameter = component.diameter || 20;
        const x = centerX - diameter / 2;
        
        ctx.fillStyle = '#8B4513';
        ctx.strokeStyle = '#654321';
        ctx.lineWidth = 2;
        ctx.fillRect(x, currentY, diameter, height);
        ctx.strokeRect(x, currentY, diameter, height);
        
        // Add cylindrical shading
        ctx.fillStyle = 'rgba(255, 255, 255, 0.2)';
        ctx.fillRect(x + 2, currentY + 2, diameter - 4, height - 4);
        
        // Highlight if selected
        if (selectedComponent?.id === component.id) {
          ctx.strokeStyle = '#00FF00';
          ctx.lineWidth = 3;
          ctx.setLineDash([5, 5]);
          ctx.strokeRect(x, currentY, diameter, height);
          ctx.setLineDash([]);
        }
      } else if (component.type === 'Transition') {
        // Draw transition as trapezoid using top and bottom diameters
        const topDiameter = component.topDiameter || 20;
        const bottomDiameter = component.bottomDiameter || 20;
        

        
        ctx.fillStyle = '#8B4513';
        ctx.strokeStyle = '#654321';
        ctx.lineWidth = 2;
        
        ctx.beginPath();
        ctx.moveTo(centerX - topDiameter / 2, currentY);
        ctx.lineTo(centerX + topDiameter / 2, currentY);
        ctx.lineTo(centerX + bottomDiameter / 2, currentY + height);
        ctx.lineTo(centerX - bottomDiameter / 2, currentY + height);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
        
        // Highlight if selected
        if (selectedComponent?.id === component.id) {
          ctx.strokeStyle = '#00FF00';
          ctx.lineWidth = 3;
          ctx.setLineDash([5, 5]);
          ctx.stroke();
          ctx.setLineDash([]);
        }
      }

      currentY += height;
    });

    // Draw fins if any fin components exist
    const finComponents = rocketComponents.filter(comp => comp.type === 'Fins');
    if (finComponents.length > 0 && ctx) {
      finComponents.forEach(finComponent => {
        drawFins(ctx, finComponent, centerX, canvas.height);
      });
    }
    
    // Draw rail buttons if any rail button components exist
    const railButtonComponents = rocketComponents.filter(comp => comp.type === 'Rail Button');
    if (railButtonComponents.length > 0 && ctx) {
      railButtonComponents.forEach(railButtonComponent => {
        drawRailButtons(ctx, railButtonComponent, centerX, canvas.height);
      });
    }
    
    // Restore canvas context after zoom transformation
    ctx.restore();
  };





  const drawFins = (ctx, finComponent, centerX, canvasHeight) => {
    try {
      const finShape = finComponent.finShape || 'rectangular';
      const finCount = Math.max(3, Math.min(8, finComponent.finCount || 4));
      const finHeight = Math.max(5, finComponent.finHeight || 25);
      const finWidth = Math.max(5, finComponent.finWidth || 15);
      const finThickness = Math.max(0.5, finComponent.finThickness || 2);
      const finSweep = Math.max(0, finComponent.finSweep || 0);
      
      // Find the component that fins are attached to
      const attachedComponentId = finComponent.attachedToComponent;
      let attachedComponent = null;
      
      if (attachedComponentId) {
        // Find the specific component fins are attached to
        attachedComponent = rocketComponents.find(comp => comp.id === attachedComponentId);
      }
      
      // If no specific attachment, find the last body tube
      if (!attachedComponent) {
        const bodyComponents = rocketComponents.filter(comp => 
          ['Nose Cone', 'Body Tube', 'Transition'].includes(comp.type)
        );
        if (bodyComponents.length === 0) return;
        attachedComponent = bodyComponents[bodyComponents.length - 1];
      }
      
      // Calculate position relative to the attached component
      const bodyComponents = rocketComponents.filter(comp => 
        ['Nose Cone', 'Body Tube', 'Transition'].includes(comp.type)
      );
      const totalHeight = bodyComponents.reduce((sum, comp) => sum + (comp.length || 60), 0);
      const startY = (canvasHeight - totalHeight) / 2;
      
      // Find the Y position of the attached component
      let attachedComponentY = startY;
      for (const comp of bodyComponents) {
        if (comp.id === attachedComponent.id) {
          break;
        }
        attachedComponentY += comp.length || 60;
      }
      
      // Position fins at the bottom of the attached component
      const baseFinY = attachedComponentY + (attachedComponent.length || 60);
      const bodyDiameter = attachedComponent.diameter || 20;
      const bodyRadius = bodyDiameter / 2;
    
    ctx.fillStyle = '#8B4513';
    ctx.strokeStyle = '#654321';
    ctx.lineWidth = 1;
    
    // Draw fins as clustered horizontal blocks (like the image description)
    const numBlocks = Math.min(finCount * 2, 8); // 7-8 blocks as described
    
    for (let i = 0; i < numBlocks; i++) {
      // Deterministic positioning around the base (no Math.random())
      const baseAngle = (i * 2 * Math.PI / numBlocks);
      const angleVariation = Math.sin(i * 1.5) * 0.3; // Deterministic variation
      const angle = baseAngle + angleVariation;
      const distance = bodyRadius + (Math.sin(i * 2.3) * 0.3 + 0.5) * finWidth; // Extended distance
      const finX = centerX + distance * Math.cos(angle);
      const finY = baseFinY + (Math.sin(i * 1.7) * 0.15 + 0.15) * finHeight * 0.3;
      
      // Only draw fins that are in front of the rocket (visible)
      if (finX > centerX - bodyRadius) {
        // Deterministic fin dimensions (larger and more visible)
        const blockWidth = finWidth * (0.8 + Math.sin(i * 3.1) * 0.3);
        const blockHeight = finThickness * (1.2 + Math.sin(i * 2.7) * 0.4);
        const rotation = Math.sin(i * 1.9) * 0.2; // Slightly more rotation
        
        ctx.save();
        ctx.translate(finX, finY);
        ctx.rotate(rotation);
        
        // Draw horizontal block
        ctx.fillRect(-blockWidth/2, -blockHeight/2, blockWidth, blockHeight);
        ctx.strokeRect(-blockWidth/2, -blockHeight/2, blockWidth, blockHeight);
        
        ctx.restore();
      }
    }
    } catch (error) {
      console.error('Error drawing fins:', error);
    }
  };



  const drawRailButtons = (ctx, railButtonComponent, centerX, canvasHeight) => {
    try {
      const railButtonHeight = Math.max(2, Math.min(20, railButtonComponent.railButtonHeight || 8));
      const railButtonWidth = Math.max(1, Math.min(10, railButtonComponent.railButtonWidth || 4));
      const railButtonOffset = Math.max(0, Math.min(10, railButtonComponent.railButtonOffset || 2));
      
      // Find the component that rail buttons are attached to
      const attachedComponentId = railButtonComponent.attachedToComponent;
      let attachedComponent = null;
      
      if (attachedComponentId) {
        // Find the specific component rail buttons are attached to
        attachedComponent = rocketComponents.find(comp => comp.id === attachedComponentId);
      }
      
      // If no specific attachment, find the last body tube
      if (!attachedComponent) {
        const bodyComponents = rocketComponents.filter(comp => 
          ['Nose Cone', 'Body Tube', 'Transition'].includes(comp.type)
        );
        if (bodyComponents.length === 0) return;
        attachedComponent = bodyComponents[bodyComponents.length - 1];
      }
      
      // Calculate position relative to the attached component
      const bodyComponents = rocketComponents.filter(comp => 
        ['Nose Cone', 'Body Tube', 'Transition'].includes(comp.type)
      );
      const totalHeight = bodyComponents.reduce((sum, comp) => sum + (comp.length || 60), 0);
      const startY = (canvasHeight - totalHeight) / 2;
      
      // Find the Y position of the attached component
      let attachedComponentY = startY;
      for (const comp of bodyComponents) {
        if (comp.id === attachedComponent.id) {
          break;
        }
        attachedComponentY += comp.length || 60;
      }
      
      // Position rail buttons at the middle of the attached component
      const railButtonY = attachedComponentY + (attachedComponent.length || 60) / 2;
      const bodyDiameter = attachedComponent.diameter || 20;
      const bodyRadius = bodyDiameter / 2;
    
      ctx.fillStyle = '#8B4513';
      ctx.strokeStyle = '#654321';
      ctx.lineWidth = 1;
      
      // Draw one rail button on the right side only
      const railButtonX = centerX + bodyRadius + railButtonOffset;
      
      ctx.save();
      ctx.translate(railButtonX, railButtonY);
      
      // Draw rail button as a small rectangle
      ctx.fillRect(-railButtonWidth/2, -railButtonHeight/2, railButtonWidth, railButtonHeight);
      ctx.strokeRect(-railButtonWidth/2, -railButtonHeight/2, railButtonWidth, railButtonHeight);
      
      ctx.restore();
    } catch (error) {
      console.error('Error drawing rail buttons:', error);
    }
  };

  useEffect(() => {
    drawRocketDiagram();
  }, [rocketComponents, selectedComponent]);



  // Initialize input values when component is selected
  useEffect(() => {
    if (selectedComponent) {
      setInputValues(prev => ({
        ...prev,
        [`${selectedComponent.id}-length`]: selectedComponent.length.toString(),
        [`${selectedComponent.id}-diameter`]: selectedComponent.diameter.toString(),
        [`${selectedComponent.id}-topDiameter`]: selectedComponent.topDiameter?.toString() || selectedComponent.diameter.toString(),
        [`${selectedComponent.id}-bottomDiameter`]: selectedComponent.bottomDiameter?.toString() || selectedComponent.diameter.toString(),
        [`${selectedComponent.id}-noseShape`]: selectedComponent.noseShape || 'conical',
        [`${selectedComponent.id}-tipLength`]: selectedComponent.tipLength?.toString() || '15',
        [`${selectedComponent.id}-finShape`]: selectedComponent.finShape || 'rectangular',
        [`${selectedComponent.id}-finCount`]: selectedComponent.finCount?.toString() || '4',
        [`${selectedComponent.id}-finHeight`]: selectedComponent.finHeight?.toString() || '25',
        [`${selectedComponent.id}-finWidth`]: selectedComponent.finWidth?.toString() || '15',
        [`${selectedComponent.id}-finThickness`]: selectedComponent.finThickness?.toString() || '2',
        [`${selectedComponent.id}-finSweep`]: selectedComponent.finSweep?.toString() || '0',
        [`${selectedComponent.id}-attachedToComponent`]: selectedComponent.attachedToComponent || ''
      }));
    }
  }, [selectedComponent]);

  const handleCanvasClick = (event) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const centerX = canvas.width / 2;

    const bodyComponents = rocketComponents.filter(comp => 
      ['Nose Cone', 'Body Tube', 'Transition'].includes(comp.type)
    );

    if (bodyComponents.length === 0) return;

    const totalHeight = bodyComponents.reduce((sum, comp) => sum + (comp.length || 60), 0);
    const startY = (canvas.height - totalHeight) / 2;

    let currentY = startY;
    let clickedComponent = null;

    bodyComponents.forEach((component) => {
      const diameter = component.diameter || 20;
      const height = component.length || 60;
      const componentX = centerX - diameter / 2;

      if (x >= componentX && x <= componentX + diameter && 
          y >= currentY && y <= currentY + height) {
        clickedComponent = component;
      }
      currentY += height;
    });

    setSelectedComponent(clickedComponent);
  };

  return (
    <div className="app-container">
      <nav className="tabs-nav">
        <button 
          className={`tab-button ${activeTab === 'builder' ? 'active' : ''}`}
          onClick={() => setActiveTab('builder')}
        >
          Rocket Builder
        </button>
        <button 
          className={`tab-button ${activeTab === 'setup' ? 'active' : ''}`}
          onClick={() => setActiveTab('setup')}
        >
          Simulation Setup
        </button>
        <button 
          className={`tab-button ${activeTab === 'control' ? 'active' : ''}`}
          onClick={() => setActiveTab('control')}
        >
          Control Code
        </button>
        <button 
          className={`tab-button ${activeTab === 'simulation' ? 'active' : ''}`}
          onClick={() => setActiveTab('simulation')}
        >
          Simulation Run
        </button>
        <button 
          className={`tab-button ${activeTab === 'results' ? 'active' : ''}`}
          onClick={() => setActiveTab('results')}
        >
          Results
        </button>
      </nav>

      <main className="main-content">
        {activeTab === 'simulation' && (
          <div className="simulation-run-layout">
            <div className="simulation-header">
              <h2>🚀 Ready to Launch Your Simulation!</h2>
              <p>Your rocket is configured and ready for CFD analysis. Click the button below to start the OpenFOAM simulation.</p>
            </div>
            
            <div className="simulation-controls">
              <div className="control-panel">
                <h3>Simulation Status</h3>
                <div className="status-indicator">
                  {simulationRunning ? (
                    <div className="running">
                      <span className="status-dot running"></span>
                      Simulation Running...
                    </div>
                  ) : (
                    <div className="ready">
                      <span className="status-dot ready"></span>
                      Ready to Run
                    </div>
                  )}
                </div>
                
                <div className="action-buttons">
                  {!simulationRunning ? (
                    <button 
                      className="btn-primary"
                      onClick={startSimulation}
                      disabled={simulationRunning}
                    >
                      🚀 Start Simulation
                    </button>
                  ) : (
                    <button 
                      className="btn-secondary"
                      onClick={stopSimulation}
                      disabled={!simulationRunning}
                    >
                      ⏹️ Stop Simulation
                    </button>
                  )}
                  
                  <button 
                    className="btn-secondary"
                    onClick={generateMesh}
                    disabled={simulationRunning}
                  >
                    🔧 Generate Mesh
                  </button>
                </div>
              </div>
              
              <div className="progress-panel">
                <h3>Progress</h3>
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: simulationRunning ? '45%' : '0%' }}></div>
                </div>
                <div className="progress-text">
                  {simulationRunning ? 'Mesh generation and solver running...' : 'Click Start to begin'}
                </div>
              </div>
            </div>
            
            <div className="simulation-info">
              <div className="info-card">
                <h4>📊 What This Will Do</h4>
                <ul>
                  <li>Generate computational mesh from your rocket design</li>
                  <li>Run OpenFOAM LES simulation with compressible flow</li>
                  <li>Calculate aerodynamic forces and pressure distribution</li>
                  <li>Analyze flight characteristics and stability</li>
                  <li>Support active control systems (fins, thrust vectoring)</li>
                </ul>
              </div>
              
              <div className="info-card">
                <h4>⏱️ Expected Duration</h4>
                <p>Based on your configuration, this simulation should complete in approximately <strong>5-15 minutes</strong> depending on mesh complexity and solver settings.</p>
              </div>
            </div>
            
            {/* Simulation Status Display */}
            {simulationStatus && (
              <div className="simulation-status-display">
                <h3>📊 Live Simulation Status</h3>
                <div className="status-content">
                  <div className="status-item">
                    <strong>Status:</strong> {simulationStatus.status}
                  </div>
                  {simulationStatus.progress && (
                    <div className="status-item">
                      <strong>Progress:</strong> {simulationStatus.progress}%
                    </div>
                  )}
                  {simulationStatus.currentTime && (
                    <div className="status-item">
                      <strong>Current Time:</strong> {simulationStatus.currentTime}s
                    </div>
                  )}
                  {simulationStatus.message && (
                    <div className="status-item">
                      <strong>Message:</strong> {simulationStatus.message}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
        
        {activeTab === 'builder' && (
          <div className="rocket-builder-layout">
            {/* Left Panel - Rocket Structure & Properties */}
            <div className="left-panel">
              <div className="structure-section">
                <div className="panel-header">
                  <h3>Rocket Structure</h3>
                </div>
                <div className="component-tree" key={rocketComponents.map(c => `${c.id}-${c.attachedToComponent}`).join('-')}>
                  <div className="tree-item">
                    <span className="tree-label">Rocket</span>
                  </div>
                  {/* Render body components first, then show their attached fins */}
                  {rocketComponents.filter(comp => 
                    ['Nose Cone', 'Body Tube', 'Transition'].includes(comp.type)
                  ).map((component, index) => {
                    // Check if this component has fins or rail buttons attached to it
                    const attachedFins = rocketComponents.filter(comp => 
                      comp.type === 'Fins' && comp.attachedToComponent === component.id
                    );
                    const attachedRailButtons = rocketComponents.filter(comp => 
                      comp.type === 'Rail Button' && comp.attachedToComponent === component.id
                    );
                    

                    
                    return (
                      <div key={component.id}>
                        <div 
                          className={`tree-item ${selectedComponent?.id === component.id ? 'selected' : ''} ${draggedComponent?.id === component.id ? 'dragging' : ''} ${dragOverIndex === index ? (draggedComponent?.type === 'Fins' && ['Body Tube', 'Transition'].includes(component.type) ? 'dragover connectable' : 'dragover') : ''}`}
                          style={{ cursor: draggedComponent?.type === 'Fins' && ['Body Tube', 'Transition'].includes(component.type) ? 'copy' : 'grab' }}
                          onClick={() => setSelectedComponent(component)}
                          onMouseEnter={() => setHoveredComponent(component.id)}
                          onMouseLeave={() => setHoveredComponent(null)}
                          draggable
                          onDragStart={(e) => handleDragStart(e, component)}
                          onDragOver={(e) => handleDragOver(e, index)}
                          onDragLeave={handleDragLeave}
                          onDrop={(e) => handleDrop(e, index)}
                          onDragEnd={handleDragEnd}
                        >
                          <span className="tree-arrow">→</span>
                          <span className="tree-label">{component.name}</span>
                          {hoveredComponent === component.id && (
                            <button 
                              className="delete-btn"
                              onClick={(e) => {
                                e.stopPropagation();
                                deleteComponent(component.id);
                              }}
                              title="Delete component"
                            >
                              ×
                            </button>
                          )}
                        </div>
                        
                        {/* Show attached fins as sub-items */}
                        {attachedFins.map((fin, finIndex) => (
                          <div 
                            key={fin.id}
                            className={`tree-item sub-item ${selectedComponent?.id === fin.id ? 'selected' : ''} ${draggedComponent?.id === fin.id ? 'dragging' : ''}`}
                            onClick={() => setSelectedComponent(fin)}
                            onMouseEnter={() => setHoveredComponent(fin.id)}
                            onMouseLeave={() => setHoveredComponent(null)}
                            draggable
                            onDragStart={(e) => handleDragStart(e, fin)}
                            onDragOver={(e) => handleDragOver(e, index)}
                            onDragLeave={handleDragLeave}
                            onDrop={(e) => handleDrop(e, index)}
                            onDragEnd={handleDragEnd}
                          >
                            <span className="tree-arrow">  →</span>
                            <span className="tree-label">{fin.name}</span>
                            {hoveredComponent === fin.id && (
                              <button 
                                className="delete-btn"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  deleteComponent(fin.id);
                                }}
                                title="Delete component"
                              >
                                ×
                              </button>
                            )}
                          </div>
                        ))}
                        
                        {/* Show attached rail buttons as sub-items */}
                        {attachedRailButtons.map((railButton, railIndex) => (
                          <div 
                            key={railButton.id}
                            className={`tree-item sub-item ${selectedComponent?.id === railButton.id ? 'selected' : ''} ${draggedComponent?.id === railButton.id ? 'dragging' : ''}`}
                            onClick={() => setSelectedComponent(railButton)}
                            onMouseEnter={() => setHoveredComponent(railButton.id)}
                            onMouseLeave={() => setHoveredComponent(null)}
                            draggable
                            onDragStart={(e) => handleDragStart(e, railButton)}
                            onDragOver={(e) => handleDragOver(e, index)}
                            onDragLeave={handleDragLeave}
                            onDrop={(e) => handleDrop(e, index)}
                            onDragEnd={handleDragEnd}
                          >
                            <span className="tree-arrow">  →</span>
                            <span className="tree-label">{railButton.name}</span>
                            {hoveredComponent === railButton.id && (
                              <button 
                                className="delete-btn"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  deleteComponent(railButton.id);
                                }}
                                title="Delete component"
                              >
                                ×
                              </button>
                            )}
                          </div>
                        ))}
                      </div>
                    );
                  })}
                  
                  {/* Show any unattached fins and rail buttons at the bottom */}
                  {rocketComponents.filter(comp => 
                    (comp.type === 'Fins' || comp.type === 'Rail Button') && !comp.attachedToComponent
                  ).map((component, index) => (
                    <div 
                      key={component.id}
                      className={`tree-item ${selectedComponent?.id === component.id ? 'selected' : ''} ${draggedComponent?.id === component.id ? 'dragging' : ''}`}
                      onClick={() => setSelectedComponent(component)}
                      onMouseEnter={() => setHoveredComponent(component.id)}
                      onMouseLeave={() => setHoveredComponent(null)}
                      draggable
                      onDragStart={(e) => handleDragStart(e, component)}
                      onDragOver={(e) => {
                        // For unattached components, allow dropping on any body component
                        const bodyComponents = rocketComponents.filter(comp => 
                          ['Body Tube', 'Transition'].includes(comp.type)
                        );
                        if (bodyComponents.length > 0) {
                          handleDragOver(e, bodyComponents.length - 1); // Drop on last body component
                        }
                      }}
                      onDragLeave={handleDragLeave}
                      onDrop={(e) => {
                        // For unattached components, drop on last body component
                        const bodyComponents = rocketComponents.filter(comp => 
                          ['Body Tube', 'Transition'].includes(comp.type)
                        );
                        if (bodyComponents.length > 0) {
                          handleDrop(e, bodyComponents.length - 1); // Drop on last body component
                        }
                      }}
                      onDragEnd={handleDragEnd}
                    >
                      <span className="tree-arrow">→</span>
                      <span className="tree-label">{component.name} (Unattached)</span>
                      {hoveredComponent === component.id && (
                        <button 
                          className="delete-btn"
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteComponent(component.id);
                          }}
                          title="Delete component"
                        >
                          ×
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="properties-section">
                <div className="panel-header">
                  <h3>Rocket Properties</h3>
                </div>
                <div className="property-fields">
                  <div className="property-field">
                    <label>Total Mass (g):</label>
                    <input 
                      type="text" 
                      value={rocketWeight}
                      onChange={(e) => setRocketWeight(e.target.value === '' ? 0 : parseFloat(e.target.value) || 0)}
                      placeholder="Enter mass"
                    />
                  </div>
                  <div className="property-field">
                    <label>Center of Gravity (cm):</label>
                    <input 
                      type="text" 
                      value={rocketCG}
                      onChange={(e) => setRocketCG(e.target.value === '' ? 0 : parseFloat(e.target.value) || 0)}
                      placeholder="Enter CG"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Middle Panel - Rocket Diagram */}
            <div className="middle-panel" onClick={() => setSelectedComponent(null)}>
              <div className="rocket-diagram-container">
                <div className="view-controls">
                  <div className="control-group centered">
                    <button onClick={() => {
                      setZoom(zoom - 0.1);
                      // Manually trigger redraw after zoom change
                      setTimeout(() => drawRocketDiagram(), 0);
                    }}>-</button>
                    <span>Zoom: {Math.round(zoom * 100)}%</span>
                    <button onClick={() => {
                      setZoom(zoom + 0.1);
                      // Manually trigger redraw after zoom change
                      setTimeout(() => drawRocketDiagram(), 0);
                    }}>+</button>
                  </div>
                </div>
                
                <div className="rocket-diagram">
                  <canvas 
                    ref={canvasRef}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleCanvasClick(e);
                    }}
                    style={{ 
                      width: '100%',
                      height: '100%'
                    }}
                  />
                </div>
              </div>
            </div>

            {/* Right Panel - Component Selection or Configuration */}
            <div className="right-panel">
              {selectedComponent ? (
                <div className="configuration-panel" key={selectedComponent.id}>
                  <div className="panel-header">
                    <h3>Configuration: {selectedComponent.name}</h3>
                    <button 
                      className="close-btn"
                      onClick={() => setSelectedComponent(null)}
                    >
                      ×
                    </button>
                  </div>
                  
                  <div className="component-config">
                    
                    <div className="config-fields">
                      <div className="config-field">
                        <label>Length (cm):</label>
                        <input 
                          type="text" 
                          value={inputValues[`${selectedComponent.id}-length`] !== undefined ? inputValues[`${selectedComponent.id}-length`] : selectedComponent.length}
                          onChange={(e) => handleNumberInput(selectedComponent.id, 'length', e.target.value)}
                          placeholder="Enter length"
                        />
                      </div>
                      {selectedComponent.type === 'Transition' ? (
                        <>
                          <div className="config-field">
                            <label>Top Diameter (cm):</label>
                            <div className="auto-value">
                              {selectedComponent.topDiameter || 'Auto'}
                            </div>
                            <small>Automatically matches component above</small>
                          </div>
                          <div className="config-field">
                            <label>Bottom Diameter (cm):</label>
                            <div className="auto-value">
                              {selectedComponent.bottomDiameter || 'Auto'}
                            </div>
                            <small>Automatically matches component below</small>
                          </div>
                        </>
                      ) : selectedComponent.type === 'Nose Cone' ? (
                        <>
                          <div className="config-field">
                            <label>Bottom Diameter (cm):</label>
                            <div className="auto-value">
                              {selectedComponent.bottomDiameter || 'Auto'}
                            </div>
                            <small>Automatically matches component below</small>
                          </div>
                          <div className="config-field">
                            <label>Nose Shape:</label>
                            <select 
                              value={inputValues[`${selectedComponent.id}-noseShape`] || 'conical'}
                              onChange={(e) => {
                                setInputValues(prev => ({
                                  ...prev,
                                  [`${selectedComponent.id}-noseShape`]: e.target.value
                                }));
                                updateComponent(selectedComponent.id, 'noseShape', e.target.value);
                              }}
                            >
                              <option value="conical">Conical</option>
                              <option value="ogive">Ogive (Elliptical)</option>
                              <option value="parabolic">Parabolic</option>
                              <option value="stepped">Stepped</option>
                            </select>
                          </div>

                                                  </>
                        ) : selectedComponent.type === 'Fins' ? (
                          <>
                            <div className="config-field">
                              <label>Fin Shape:</label>
                              <select 
                                value={inputValues[`${selectedComponent.id}-finShape`] || 'rectangular'}
                                onChange={(e) => {
                                  setInputValues(prev => ({
                                    ...prev,
                                    [`${selectedComponent.id}-finShape`]: e.target.value
                                  }));
                                  updateComponent(selectedComponent.id, 'finShape', e.target.value);
                                }}
                              >
                                <option value="rectangular">Rectangular</option>
                                <option value="triangular">Triangular</option>
                                <option value="trapezoidal">Trapezoidal</option>
                                <option value="swept">Swept</option>
                              </select>
                            </div>
                            <div className="config-field">
                              <label>Number of Fins:</label>
                              <select 
                                value={inputValues[`${selectedComponent.id}-finCount`] || '4'}
                                onChange={(e) => {
                                  setInputValues(prev => ({
                                    ...prev,
                                    [`${selectedComponent.id}-finCount`]: e.target.value
                                  }));
                                  updateComponent(selectedComponent.id, 'finCount', parseInt(e.target.value));
                                }}
                              >
                                <option value="3">3</option>
                                <option value="4">4</option>
                                <option value="6">6</option>
                                <option value="8">8</option>
                              </select>
                            </div>
                            <div className="config-field">
                              <label>Fin Height (cm):</label>
                              <input 
                                type="text" 
                                value={inputValues[`${selectedComponent.id}-finHeight`] || '25'}
                                onChange={(e) => handleNumberInput(selectedComponent.id, 'finHeight', e.target.value)}
                                placeholder="Enter height"
                              />
                            </div>
                            <div className="config-field">
                              <label>Fin Width (cm):</label>
                              <input 
                                type="text" 
                                value={inputValues[`${selectedComponent.id}-finWidth`] || '15'}
                                onChange={(e) => handleNumberInput(selectedComponent.id, 'finWidth', e.target.value)}
                                placeholder="Enter width"
                              />
                            </div>
                            <div className="config-field">
                              <label>Fin Thickness (cm):</label>
                              <input 
                                type="text" 
                                value={inputValues[`${selectedComponent.id}-finThickness`] || '2'}
                                onChange={(e) => handleNumberInput(selectedComponent.id, 'finThickness', e.target.value)}
                                placeholder="Enter thickness"
                              />
                            </div>
                            {selectedComponent.finShape === 'swept' && (
                              <div className="config-field">
                                <label>Sweep Distance (cm):</label>
                                <input 
                                  type="text" 
                                  value={inputValues[`${selectedComponent.id}-finSweep`] || '0'}
                                  onChange={(e) => handleNumberInput(selectedComponent.id, 'finSweep', e.target.value)}
                                  placeholder="Enter sweep"
                                />
                              </div>
                            )}
                            <div className="config-field">
                              <label>Attach to Component:</label>
                              <select 
                                value={selectedComponent.attachedToComponent || ''}
                                onChange={(e) => {
                                  const newValue = e.target.value || null;
                                  updateComponent(selectedComponent.id, 'attachedToComponent', newValue);
                                }}
                              >
                                <option value="">Auto (Last Body Tube)</option>
                                {rocketComponents.filter(comp => 
                                  ['Body Tube', 'Transition'].includes(comp.type)
                                ).map(comp => (
                                  <option key={comp.id} value={comp.id}>
                                    {comp.name}
                                  </option>
                                ))}
                              </select>
                            </div>
                          </>
                        ) : selectedComponent.type === 'Rail Button' ? (
                          <>
                            <div className="config-field">
                              <label>Rail Button Height (cm):</label>
                              <input 
                                type="text" 
                                value={inputValues[`${selectedComponent.id}-railButtonHeight`] || '8'}
                                onChange={(e) => handleNumberInput(selectedComponent.id, 'railButtonHeight', e.target.value)}
                                placeholder="Enter height"
                              />
                            </div>
                            <div className="config-field">
                              <label>Rail Button Width (cm):</label>
                              <input 
                                type="text" 
                                value={inputValues[`${selectedComponent.id}-railButtonWidth`] || '4'}
                                onChange={(e) => handleNumberInput(selectedComponent.id, 'railButtonWidth', e.target.value)}
                                placeholder="Enter width"
                              />
                            </div>
                            <div className="config-field">
                              <label>Offset from Body (cm):</label>
                              <input 
                                type="text" 
                                value={inputValues[`${selectedComponent.id}-railButtonOffset`] || '2'}
                                onChange={(e) => handleNumberInput(selectedComponent.id, 'railButtonOffset', e.target.value)}
                                placeholder="Enter offset"
                              />
                            </div>
                            <div className="config-field">
                              <label>Attach to Component:</label>
                              <select 
                                value={selectedComponent.attachedToComponent || ''}
                                onChange={(e) => {
                                  const newValue = e.target.value || null;
                                  updateComponent(selectedComponent.id, 'attachedToComponent', newValue);
                                }}
                              >
                                <option value="">Auto (Last Body Tube)</option>
                                {rocketComponents.filter(comp => 
                                  ['Body Tube', 'Transition'].includes(comp.type)
                                ).map(comp => (
                                  <option key={comp.id} value={comp.id}>
                                    {comp.name}
                                  </option>
                                ))}
                              </select>
                            </div>
                          </>
                        ) : (
                          <div className="config-field">
                            <label>Diameter (cm):</label>
                            <input 
                              type="text" 
                              value={inputValues[`${selectedComponent.id}-diameter`] !== undefined ? inputValues[`${selectedComponent.id}-diameter`] : selectedComponent.diameter}
                              onChange={(e) => handleNumberInput(selectedComponent.id, 'diameter', e.target.value)}
                              placeholder="Enter diameter"
                            />
                          </div>
                        )}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="add-components-panel">
                  <div className="panel-header">
                    <h3>Add Components</h3>
                  </div>
                  
                  <div className="component-categories">
                    <div className="category">
                      <h4>Body Components</h4>
                      <div className="component-grid">
                        <button className="component-btn" onClick={() => addComponent('Nose Cone')}>
                          <div className="component-icon nose-cone"></div>
                          Nose Cone
                        </button>
                        <button className="component-btn" onClick={() => addComponent('Body Tube')}>
                          <div className="component-icon body-tube"></div>
                          Body Tube
                        </button>
                        <button className="component-btn" onClick={() => addComponent('Transition')}>
                          <div className="component-icon transition"></div>
                          Transition
                        </button>
                      </div>
                    </div>
                    
                    <div className="category">
                      <h4>Fins & Attachments</h4>
                      <div className="component-grid">
                        <button className="component-btn" onClick={() => addComponent('Fins')}>
                          <div className="component-icon fins"></div>
                          Fins
                        </button>
                        <button className="component-btn" onClick={() => addComponent('Rail Button')}>
                          <div className="component-icon rail-button"></div>
                          Rail Button
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
        
        {activeTab === 'setup' && (
          <div className="tab-content">
            <h2>Simulation Setup</h2>
            
            <div className="simulation-sections">
              {/* CFD Solver Settings */}
              <div className="simulation-section">
                <div className="section-header" onClick={() => setOpenSections(prev => ({...prev, cfd: !prev.cfd}))}>
                  <h3>CFD Solver Settings</h3>
                  <span className="toggle-icon">{openSections.cfd ? '▼' : '▶'}</span>
                </div>
                {openSections.cfd && (
                  <div className="section-content">
                    <div className="parameter-grid">
                      <div className="parameter-group">
                        <label>Solver Type:</label>
                        <select 
                          value={simulationConfig.solverType} 
                          onChange={(e) => updateSimulationConfig('solverType', e.target.value)}
                        >
                          <option value="pimpleFoam">PIMPLE (Compressible)</option>
                          <option value="interFoam">InterFoam (Multiphase)</option>
                          <option value="rhoPimpleFoam">RhoPimpleFoam (Density-based)</option>
                        </select>
                      </div>
                      
                      <div className="parameter-group">
                        <label>Turbulence Model:</label>
                        <select 
                          value={simulationConfig.turbulenceModel} 
                          onChange={(e) => updateSimulationConfig('turbulenceModel', e.target.value)}
                        >
                          <option value="kEpsilon">k-ε (RANS)</option>
                          <option value="kOmega">k-ω (RANS)</option>
                          <option value="LES">Large Eddy Simulation (LES)</option>
                          <option value="DES">Detached Eddy Simulation (DES)</option>
                        </select>
                      </div>
                      
                      <div className="parameter-group">
                        <label>Time Step (s):</label>
                        <input 
                          type="number" 
                          value={simulationConfig.timeStep} 
                          onChange={(e) => updateSimulationConfig('timeStep', parseFloat(e.target.value))}
                          step="0.001"
                          min="0.001"
                        />
                      </div>
                      
                      <div className="parameter-group">
                        <label>Max Simulation Time (s):</label>
                        <input 
                          type="number" 
                          value={simulationConfig.maxTime} 
                          onChange={(e) => updateSimulationConfig('maxTime', parseFloat(e.target.value))}
                          step="1"
                          min="1"
                        />
                      </div>
                      
                      <div className="parameter-group">
                        <label>Write Interval:</label>
                        <input 
                          type="number" 
                          value={simulationConfig.writeInterval} 
                          onChange={(e) => updateSimulationConfig('writeInterval', parseInt(e.target.value))}
                          step="1"
                          min="1"
                        />
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Atmospheric Conditions */}
              <div className="simulation-section">
                <div className="section-header" onClick={() => setOpenSections(prev => ({...prev, atmosphere: !prev.atmosphere}))}>
                  <h3>Atmospheric Conditions</h3>
                  <span className="toggle-icon">{openSections.atmosphere ? '▼' : '▶'}</span>
                </div>
                {openSections.atmosphere && (
                  <div className="section-content">
                    <div className="parameter-grid">
                      <div className="parameter-group">
                        <label>Launch Altitude (m):</label>
                        <input 
                          type="number" 
                          value={simulationConfig.launchAltitude} 
                          onChange={(e) => updateSimulationConfig('launchAltitude', parseFloat(e.target.value))}
                          step="1"
                          min="0"
                        />
                      </div>
                      
                      <div className="parameter-group">
                        <label>Temperature (°C):</label>
                        <input 
                          type="number" 
                          value={simulationConfig.temperature} 
                          onChange={(e) => updateSimulationConfig('temperature', parseFloat(e.target.value))}
                          step="0.1"
                          min="-50"
                          max="50"
                        />
                      </div>
                      
                      <div className="parameter-group">
                        <label>Pressure (Pa):</label>
                        <input 
                          type="number" 
                          value={simulationConfig.pressure} 
                          onChange={(e) => updateSimulationConfig('pressure', parseFloat(e.target.value))}
                          step="100"
                          min="10000"
                          max="150000"
                        />
                      </div>
                      
                      <div className="parameter-group">
                        <label>Humidity (%):</label>
                        <input 
                          type="number" 
                          value={simulationConfig.humidity} 
                          onChange={(e) => updateSimulationConfig('humidity', parseFloat(e.target.value))}
                          step="1"
                          min="0"
                          max="100"
                        />
                      </div>
                      
                      <div className="parameter-group">
                        <label>Wind Speed (m/s):</label>
                        <input 
                          type="number" 
                          value={simulationConfig.windSpeed} 
                          onChange={(e) => updateSimulationConfig('windSpeed', parseFloat(e.target.value))}
                          step="0.1"
                          min="0"
                          max="50"
                        />
                      </div>
                      
                      <div className="parameter-group">
                        <label>Wind Direction (°):</label>
                        <input 
                          type="number" 
                          value={simulationConfig.windDirection} 
                          onChange={(e) => updateSimulationConfig('windDirection', parseFloat(e.target.value))}
                          step="1"
                          min="0"
                          max="360"
                        />
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Boundary Conditions */}
              <div className="simulation-section">
                <div className="section-header" onClick={() => setOpenSections(prev => ({...prev, boundaries: !prev.boundaries}))}>
                  <h3>Boundary Conditions</h3>
                  <span className="toggle-icon">{openSections.boundaries ? '▼' : '▶'}</span>
                </div>
                {openSections.boundaries && (
                  <div className="section-content">
                    <div className="parameter-grid">
                      <div className="parameter-group">
                        <label>Inlet Velocity (m/s):</label>
                        <input 
                          type="number" 
                          value={simulationConfig.inletVelocity} 
                          onChange={(e) => updateSimulationConfig('inletVelocity', parseFloat(e.target.value))}
                          step="0.1"
                          min="0"
                        />
                      </div>
                      
                      <div className="parameter-group">
                        <label>Outlet Pressure (Pa):</label>
                        <input 
                          type="number" 
                          value={simulationConfig.outletPressure} 
                          onChange={(e) => updateSimulationConfig('outletPressure', parseFloat(e.target.value))}
                          step="100"
                        />
                      </div>
                      
                      <div className="parameter-group">
                        <label>Wall Condition:</label>
                        <select 
                          value={simulationConfig.wallCondition} 
                          onChange={(e) => updateSimulationConfig('wallCondition', e.target.value)}
                        >
                          <option value="noSlip">No-Slip</option>
                          <option value="slip">Slip</option>
                          <option value="partialSlip">Partial Slip</option>
                        </select>
                      </div>
                      
                      <div className="parameter-group">
                        <label>Domain Size (m):</label>
                        <input 
                          type="number" 
                          value={simulationConfig.domainSize} 
                          onChange={(e) => updateSimulationConfig('domainSize', parseFloat(e.target.value))}
                          step="0.1"
                          min="1"
                        />
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Mesh Settings */}
              <div className="simulation-section">
                <div className="section-header" onClick={() => setOpenSections(prev => ({...prev, mesh: !prev.mesh}))}>
                  <h3>Mesh Generation</h3>
                  <span className="toggle-icon">{openSections.mesh ? '▼' : '▶'}</span>
                </div>
                {openSections.mesh && (
                  <div className="section-content">
                    <div className="parameter-grid">
                      <div className="parameter-group">
                        <label>Base Cell Size (m):</label>
                        <input 
                          type="number" 
                          value={simulationConfig.baseCellSize} 
                          onChange={(e) => updateSimulationConfig('baseCellSize', parseFloat(e.target.value))}
                          step="0.001"
                          min="0.001"
                        />
                      </div>
                      
                      <div className="parameter-group">
                        <label>Boundary Layer Cells:</label>
                        <input 
                          type="number" 
                          value={simulationConfig.boundaryLayerCells} 
                          onChange={(e) => updateSimulationConfig('boundaryLayerCells', parseInt(e.target.value))}
                          step="1"
                          min="3"
                          max="20"
                        />
                      </div>
                      
                      <div className="parameter-group">
                        <label>Refinement Level:</label>
                        <select 
                          value={simulationConfig.refinementLevel} 
                          onChange={(e) => updateSimulationConfig('refinementLevel', e.target.value)}
                        >
                          <option value="coarse">Coarse</option>
                          <option value="medium">Medium</option>
                          <option value="fine">Fine</option>
                          <option value="veryFine">Very Fine</option>
                        </select>
                      </div>
                      
                      <div className="parameter-group">
                        <label>Mesh Quality Threshold:</label>
                        <input 
                          type="number" 
                          value={simulationConfig.meshQuality} 
                          onChange={(e) => updateSimulationConfig('meshQuality', parseFloat(e.target.value))}
                          step="0.01"
                          min="0.1"
                          max="1.0"
                        />
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Analysis Settings */}
              <div className="simulation-section">
                <div className="section-header" onClick={() => setOpenSections(prev => ({...prev, analysis: !prev.analysis}))}>
                  <h3>Analysis & Output</h3>
                  <span className="toggle-icon">{openSections.analysis ? '▼' : '▶'}</span>
                </div>
                {openSections.analysis && (
                  <div className="section-content">
                    <div className="parameter-grid">
                      <div className="parameter-group">
                        <label>Calculate Drag Coefficient:</label>
                        <input 
                          type="checkbox" 
                          checked={simulationConfig.calculateDrag} 
                          onChange={(e) => updateSimulationConfig('calculateDrag', e.target.checked)}
                        />
                      </div>
                      
                      <div className="parameter-group">
                        <label>Calculate Lift Coefficient:</label>
                        <input 
                          type="checkbox" 
                          checked={simulationConfig.calculateLift} 
                          onChange={(e) => updateSimulationConfig('calculateLift', e.target.checked)}
                        />
                      </div>
                      
                      <div className="parameter-group">
                        <label>Calculate Pressure Distribution:</label>
                        <input 
                          type="checkbox" 
                          checked={simulationConfig.calculatePressure} 
                          onChange={(e) => updateSimulationConfig('calculatePressure', e.target.checked)}
                        />
                      </div>
                      
                      <div className="parameter-group">
                        <label>Calculate Velocity Field:</label>
                        <input 
                          type="checkbox" 
                          checked={simulationConfig.calculateVelocity} 
                          onChange={(e) => updateSimulationConfig('calculateVelocity', e.target.checked)}
                        />
                      </div>
                      
                      <div className="parameter-group">
                        <label>Output Format:</label>
                        <select 
                          value={simulationConfig.outputFormat} 
                          onChange={(e) => updateSimulationConfig('outputFormat', e.target.value)}
                        >
                          <option value="vtk">VTK</option>
                          <option value="ensight">EnSight</option>
                          <option value="foam">OpenFOAM Native</option>
                        </select>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>


          </div>
        )}
        
        {activeTab === 'control' && (
          <div className="tab-content">
            <h2>Control Code</h2>
            <p>Content will go here...</p>
          </div>
        )}
        
        {activeTab === 'results' && (
          <div className="tab-content">
            <h2>Results</h2>
            <p>Content will go here...</p>
          </div>
        )}
      </main>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
