import React, { useState, useRef, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  // API Configuration - works for both local development and Netlify production
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5011';
  const GCP_FUNCTION_URL = import.meta.env.VITE_GCP_FUNCTION_URL || 'https://us-central1-centered-scion-471523-a4.cloudfunctions.net/rocket-cfd-simulator';
  
  // Use local backend for now since Cloud Function deployment is having issues
  const SIMULATION_API_URL = import.meta.env.PROD ? 'https://us-central1-centered-scion-471523-a4.cloudfunctions.net/rocket-cfd-simulator' : 'http://localhost:5011';
  
  // Comprehensive Debug Logging (only log once)
  if (!window.apiConfigLogged) {
    console.log('🔧 API Configuration:', {
      isProduction: import.meta.env.PROD,
      apiBaseUrl: API_BASE_URL,
      gcpFunctionUrl: GCP_FUNCTION_URL,
      simulationApiUrl: SIMULATION_API_URL,
      environment: import.meta.env.MODE,
      nodeEnv: import.meta.env.NODE_ENV
    });
    window.apiConfigLogged = true;
  }

  // Google Cloud Status Check
  const checkGoogleCloudStatus = async () => {
    console.log('☁️ === GOOGLE CLOUD STATUS CHECK ===');
    
    try {
      // Test 1: Check if GCP Function URL is reachable
      console.log('🔍 Test 1: Checking GCP Function URL reachability...');
      const healthUrl = `${GCP_FUNCTION_URL}/health`;
      console.log('📍 Health check URL:', healthUrl);
      
      const healthResponse = await fetch(healthUrl, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });
      
      console.log('📡 Health response status:', healthResponse.status);
      console.log('📡 Health response headers:', Object.fromEntries(healthResponse.headers.entries()));
      
      if (healthResponse.ok) {
        const healthData = await healthResponse.json();
        console.log('✅ GCP Function is ACTIVE and responding!');
        console.log('📊 Health data:', healthData);
        return { status: 'active', data: healthData };
      } else {
        console.log('❌ GCP Function returned error:', healthResponse.status);
        const errorText = await healthResponse.text();
        console.log('📄 Error response:', errorText.substring(0, 200));
        return { status: 'error', error: healthResponse.status };
      }
    } catch (error) {
      console.log('💥 GCP Function connection failed:', error.message);
      console.log('🔍 Error details:', {
        name: error.name,
        message: error.message,
        stack: error.stack?.substring(0, 300)
      });
      return { status: 'offline', error: error.message };
    }
  };

  // Test 2: Check Netlify proxy
  const checkNetlifyProxy = async () => {
    console.log('🌐 === NETLIFY PROXY CHECK ===');
    
    try {
      const proxyUrl = '/api/health';
      console.log('📍 Proxy URL:', proxyUrl);
      
      const proxyResponse = await fetch(proxyUrl, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });
      
      console.log('📡 Proxy response status:', proxyResponse.status);
      console.log('📡 Proxy response headers:', Object.fromEntries(proxyResponse.headers.entries()));
      
      if (proxyResponse.ok) {
        try {
          const proxyData = await proxyResponse.json();
          console.log('✅ Netlify proxy is working!');
          console.log('📊 Proxy data:', proxyData);
          return { status: 'active', data: proxyData };
        } catch (jsonError) {
          console.log('⚠️ Netlify proxy returned non-JSON response (likely HTML)');
          // This is expected in production since we're using Google Cloud Function directly
          return { status: 'bypassed', error: 'Using direct Google Cloud Function' };
        }
      } else {
        console.log('❌ Netlify proxy returned error:', proxyResponse.status);
        const errorText = await proxyResponse.text();
        console.log('📄 Proxy error response:', errorText.substring(0, 200));
        return { status: 'error', error: proxyResponse.status };
      }
    } catch (error) {
      console.log('💥 Netlify proxy connection failed:', error.message);
      return { status: 'offline', error: error.message };
    }
  };

  // Test 3: Check local backend (if in development)
  const checkLocalBackend = async () => {
    if (import.meta.env.PROD) {
      console.log('🏠 Skipping local backend check (production mode)');
      return { status: 'skipped' };
    }
    
    console.log('🏠 === LOCAL BACKEND CHECK ===');
    
    try {
      const localUrl = `${API_BASE_URL}/health`;
      console.log('📍 Local backend URL:', localUrl);
      
      const localResponse = await fetch(localUrl, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });
      
      console.log('📡 Local backend response status:', localResponse.status);
      
      if (localResponse.ok) {
        const localData = await localResponse.json();
        console.log('✅ Local backend is running!');
        console.log('📊 Local backend data:', localData);
        return { status: 'active', data: localData };
      } else {
        console.log('❌ Local backend returned error:', localResponse.status);
        return { status: 'error', error: localResponse.status };
      }
    } catch (error) {
      console.log('💥 Local backend connection failed:', error.message);
      return { status: 'offline', error: error.message };
    }
  };

  // Run all status checks
  const runAllStatusChecks = async () => {
    console.log('🚀 === COMPREHENSIVE SYSTEM STATUS CHECK ===');
    console.log('⏰ Timestamp:', new Date().toISOString());
    
    const results = {
      gcp: await checkGoogleCloudStatus(),
      netlify: await checkNetlifyProxy(),
      local: await checkLocalBackend()
    };
    
    console.log('📊 === FINAL STATUS SUMMARY ===');
    console.log('☁️ Google Cloud Function:', results.gcp.status);
    console.log('🌐 Netlify Proxy:', results.netlify.status);
    console.log('🏠 Local Backend:', results.local.status);
    
    // Overall system status
    const hasWorkingBackend = results.gcp.status === 'active' || 
                             results.netlify.status === 'active' || 
                             results.netlify.status === 'bypassed' || 
                             results.local.status === 'active';
    
    // Check if Netlify proxy is returning HTML (function not deployed)
    const netlifyProxyIssue = results.netlify.status === 'html_response';
    
    console.log('🎯 Overall System Status:', hasWorkingBackend ? '✅ READY' : '❌ NOT READY');
    
    if (!hasWorkingBackend) {
      console.log('⚠️ WARNING: No backend services are available!');
      console.log('🔧 Troubleshooting steps:');
      console.log('1. Deploy Google Cloud Function: py deploy_gcp_function.py');
      console.log('2. Start local backend: py backend/f_backend.py');
      console.log('3. Check Netlify proxy configuration');
    }
    
    if (netlifyProxyIssue) {
      console.log('🔍 DIAGNOSIS: Netlify proxy is working but Google Cloud Function is not deployed');
      console.log('💡 SOLUTION: The function needs to be deployed to Google Cloud');
      console.log('📋 COMMAND: py deploy_gcp_function.py');
    }
    
    return results;
  };

  // Run status checks on component mount
  React.useEffect(() => {
    runAllStatusChecks();
  }, []);

  // Calculate total rocket length from components
  const calculateRocketLength = () => {
    return rocketComponents.reduce((total, component) => {
      return total + (component.length || 0);
    }, 0);
  };

  const calculateRocketCG = () => {
    if (rocketComponents.length === 0) return 0;
    
    let totalMoment = 0;
    let totalWeight = 0;
    let currentPosition = 0;
    
    // Calculate CG from bottom of rocket
    rocketComponents.forEach(component => {
      const componentLength = component.length || 0;
      const componentWeight = component.weight || 10; // Default weight in grams
      const componentCG = currentPosition + (componentLength / 2);
      
      totalMoment += componentWeight * componentCG;
      totalWeight += componentWeight;
      currentPosition += componentLength;
    });
    
    return totalWeight > 0 ? totalMoment / totalWeight : 0;
  };

  const calculateRocketWeight = () => {
    return rocketComponents.reduce((total, component) => {
      return total + (component.weight || 10); // Default 10g per component
    }, 0);
  };
  
  const [activeTab, setActiveTab] = useState('builder');
  const [tabDirection, setTabDirection] = useState('right');
  
  // Tab switching with animation
  const switchTab = (newTab) => {
    const tabOrder = ['builder', 'setup', 'control', 'simulation', 'results'];
    const currentIndex = tabOrder.indexOf(activeTab);
    const newIndex = tabOrder.indexOf(newTab);
    
    if (newIndex > currentIndex) {
      setTabDirection('right');
    } else {
      setTabDirection('left');
    }
    
    setActiveTab(newTab);
  };

  const [selectedComponent, setSelectedComponent] = useState(null);
  const [clickTimeout, setClickTimeout] = useState(null);
  const [rocketComponents, setRocketComponents] = useState([]);

  // Handle click/double-click for components
  const handleComponentClick = (component, isDoubleClick = false) => {
    console.log('🖱️ Component Click:', component.name, isDoubleClick ? '(DOUBLE)' : '(SINGLE)');
    
    if (isDoubleClick) {
      // Clear any pending single click
      if (clickTimeout) {
        clearTimeout(clickTimeout);
        setClickTimeout(null);
      }
      // Double click - open config
      setSelectedComponent(component);
    } else {
      // Single click - select component
      setSelectedComponent(component);
      
      // Set timeout to detect if this becomes a double click
      const timeout = setTimeout(() => {
        // This was just a single click, no double click followed
        console.log('🖱️ Single click confirmed for:', component.name);
      }, 300);
      setClickTimeout(timeout);
    }
  };
  const [rocketWeight, setRocketWeight] = useState(0);
  const [rocketCG, setRocketCG] = useState(0);
  const [cgReference, setCgReference] = useState('bottom'); // 'bottom' or 'top'
  const [inputValues, setInputValues] = useState({});
  const [draggedComponent, setDraggedComponent] = useState(null);
  const [dragOverIndex, setDragOverIndex] = useState(null);
  const [hoveredComponent, setHoveredComponent] = useState(null);
  const [zoom, setZoom] = useState(1.5); // Default zoom 150%
  const canvasRef = useRef(null);
  const fileInputRef = useRef(null);
  const configFileInputRef = useRef(null);
  const finFileInputRef = useRef(null);
  
  // Simulation state
  const [openSections, setOpenSections] = useState({
    cfd: true,
    atmosphere: true,
    boundaries: true,
    mesh: true,
    analysis: true
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
    outputFormat: 'vtk',
    
    // Active Fin Control Settings (simplified)
    activeFinControl: 'disabled',
    motorPower: 50, // Watts
    maxAngle: 15, // degrees
    responseSpeed: 10, // Hz
    
    // CFD Settings (moved from active fin control)
    cfdTimeStep: 0.01,
    controlUpdateRate: 100,
    finDeflectionLimit: 15, // degrees
    controlGains: {
      kp: 1.0,  // Proportional gain
      ki: 0.1,  // Integral gain
      kd: 0.05  // Derivative gain
    },
    
    // Control Code
    controlCode: `// Active Fin Control Algorithm
// This code runs in real-time during CFD simulation
// Available variables: attitude, velocity, position, target_trajectory
// Output: fin_deflections (array of 4 fin angles in degrees)

function calculateFinDeflections(cfdData, targetTrajectory) {
    // Extract CFD feedback data
    const attitude = cfdData.attitude;        // [roll, pitch, yaw] in degrees
    const velocity = cfdData.velocity;        // [vx, vy, vz] in m/s
    const position = cfdData.position;        // [x, y, z] in meters
    const angularVelocity = cfdData.angularVelocity; // [wx, wy, wz] in rad/s
    
    // Target trajectory
    const targetPitch = targetTrajectory.pitch;
    const targetYaw = targetTrajectory.yaw;
    
    // Control gains
    const kp = 1.0;  // Proportional gain
    const ki = 0.1;  // Integral gain  
    const kd = 0.05; // Derivative gain
    
    // Calculate errors
    const pitchError = targetPitch - attitude[1];
    const yawError = targetYaw - attitude[2];
    
    // PID control for pitch (fins 1&3)
    const pitchControl = kp * pitchError + ki * integralError + kd * derivativeError;
    
    // PID control for yaw (fins 2&4)  
    const yawControl = kp * yawError + ki * integralError + kd * derivativeError;
    
    // Calculate fin deflections (4 fins)
    const finDeflections = [
        pitchControl,  // Fin 1 (top)
        yawControl,    // Fin 2 (right)
        -pitchControl, // Fin 3 (bottom) 
        -yawControl    // Fin 4 (left)
    ];
    
    return finDeflections;
}`
  });
  
  const [simulationRunning, setSimulationRunning] = useState(false);
  const [simulationStatus, setSimulationStatus] = useState(null);
  const [currentSimulationId, setCurrentSimulationId] = useState(null);
  const [simulationResults, setSimulationResults] = useState(null);
  const simulationRunningRef = useRef(false);
  
  // Split point and separation features
  const [splitPoint, setSplitPoint] = useState(null);
  const [separationEnabled, setSeparationEnabled] = useState(false);
  const [stlProcessing, setStlProcessing] = useState(false);
  const [finMaterial, setFinMaterial] = useState('carbon_fiber'); // Default fin material
  
  // Motor search state
  const [showMotorSearch, setShowMotorSearch] = useState(false);
  const [motorSearchResults, setMotorSearchResults] = useState([]);
  const [motorSearchQuery, setMotorSearchQuery] = useState('');
  const [selectedMotor, setSelectedMotor] = useState(null);
  
  // Motor search function (mock for now - will integrate with ThrustCurve API)
  const searchMotors = async (query) => {
    console.log('🔍 Searching for motors:', query);
    
    if (!query.trim()) {
      setMotorSearchResults([]);
      return;
    }
    
    // Mock motor data - in production this would come from ThrustCurve API
    const mockMotors = [
      {
        id: 'estes-c6-5',
        manufacturer: 'Estes',
        model: 'C6-5',
        impulse: 'C',
        thrust: 6.0,
        burnTime: 1.6,
        totalImpulse: 10.0,
        delay: 5,
        weight: 16.8,
        diameter: 18,
        length: 70
      },
      {
        id: 'aerotech-e30-4',
        manufacturer: 'AeroTech',
        model: 'E30-4',
        impulse: 'E',
        thrust: 30.0,
        burnTime: 0.8,
        totalImpulse: 24.0,
        delay: 4,
        weight: 62.0,
        diameter: 18,
        length: 70
      },
      {
        id: 'estes-d12-5',
        manufacturer: 'Estes',
        model: 'D12-5',
        impulse: 'D',
        thrust: 12.0,
        burnTime: 1.2,
        totalImpulse: 14.4,
        delay: 5,
        weight: 24.0,
        diameter: 18,
        length: 70
      }
    ];
    
    // Filter motors based on query
    const filtered = mockMotors.filter(motor => 
      motor.manufacturer.toLowerCase().includes(query.toLowerCase()) ||
      motor.model.toLowerCase().includes(query.toLowerCase()) ||
      motor.impulse.toLowerCase().includes(query.toLowerCase())
    );
    
    setMotorSearchResults(filtered);
  };
  
  // Custom notification system
  const [notifications, setNotifications] = useState([]);
  const [currentWeatherNotification, setCurrentWeatherNotification] = useState(null);
  
  const showNotification = (message, type = 'info', autoRemove = true) => {
    const id = Date.now();
    const notification = { id, message, type };
    setNotifications(prev => [...prev, notification]);
    
    // Auto-remove after 4 seconds only if autoRemove is true
    if (autoRemove) {
      setTimeout(() => {
        setNotifications(prev => prev.filter(n => n.id !== id));
      }, 4000);
    }
    
    return id; // Return the notification ID for manual removal
  };
  
  const removeNotification = (id) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  // Weather condition information
  const weatherInfo = {
    sunny: {
      title: "☀️ Sunny Day Conditions",
      description: "Clear skies with minimal wind. Perfect for stable rocket launches with predictable flight paths.",
      conditions: "• Temperature: 25°C\n• Wind Speed: 2 m/s\n• Humidity: 30%\n• Pressure: 101325 Pa\n• Turbulence: k-ε model for steady conditions"
    },
    rainy: {
      title: "🌧️ Rainy Day Conditions", 
      description: "Wet weather with moderate wind. Rain affects air density and can impact rocket performance.",
      conditions: "• Temperature: 12°C\n• Wind Speed: 8 m/s\n• Humidity: 85%\n• Pressure: 100500 Pa\n• Turbulence: k-ω model for moisture effects"
    },
    windy: {
      title: "💨 High Wind Conditions",
      description: "Strong winds create challenging launch conditions. Requires advanced turbulence modeling.",
      conditions: "• Temperature: 18°C\n• Wind Speed: 20 m/s\n• Humidity: 45%\n• Pressure: 101000 Pa\n• Turbulence: LES model for wind effects"
    },
    stormy: {
      title: "⛈️ Stormy Weather Conditions",
      description: "Extreme weather with high winds and low pressure. Most challenging conditions for rocket launches.",
      conditions: "• Temperature: 8°C\n• Wind Speed: 35 m/s\n• Humidity: 95%\n• Pressure: 99500 Pa\n• Turbulence: DES model for complex flows"
    }
  };

  const showWeatherInfo = (weatherType) => {
    const info = weatherInfo[weatherType];
    if (info) {
      // Remove any existing weather notification
      if (currentWeatherNotification) {
        removeNotification(currentWeatherNotification);
      }
      
      // Show new weather notification without auto-remove
      const notificationId = showNotification(`${info.title}\n\n${info.description}\n\n${info.conditions}`, 'info', false);
      setCurrentWeatherNotification(notificationId);
    }
  };

  const hideWeatherInfo = () => {
    if (currentWeatherNotification) {
      removeNotification(currentWeatherNotification);
      setCurrentWeatherNotification(null);
    }
  };

  // Variable information for tooltips
  const variableInfo = {
    solver: "How the simulation calculates air flow around your rocket:\n\n• PIMPLE (Compressible): Good for most rockets, handles air compression effects well\n• InterFoam (Multiphase): For rockets with water or other fluids, more complex\n• RhoPimpleFoam (Density-based): Best for high-speed rockets, most accurate but slower",
    turbulenceModel: "How the simulation handles air turbulence (swirling air):\n\n• k-ε (RANS): Fast and simple, good for basic rocket shapes\n• k-ω (RANS): Better for detailed surfaces, medium speed\n• LES (Large Eddy): Very accurate for complex flows, slower\n• DES (Detached Eddy): Best for rockets with lots of details, slowest but most precise",
    timeStep: "How often the simulation updates. Smaller values = more accurate but slower. Typical range: 0.0001-0.01 seconds.",
    maxTime: "How long to simulate the rocket flight. Longer times show more of the flight but take longer to calculate.",
    temperature: "Air temperature around the rocket. Hotter air is thinner, affecting how the rocket moves through it.",
    pressure: "Air pressure at launch height. Higher altitude = lower pressure. Affects how dense the air is.",
    windSpeed: "How fast the wind is blowing. Higher wind = more force pushing on the rocket.",
    windDirection: "Which way the wind is blowing. 0° = North, 90° = East, 180° = South, 270° = West.",
    humidity: "How much water is in the air. More humidity = slightly denser air, affecting rocket performance.",
    domainSize: "How big the simulation area is around the rocket. Bigger area = more accurate but slower.",
    cellSize: "How detailed the simulation grid is. Smaller cells = more accurate but much slower.",
    meshQuality: "How good the simulation grid quality is. Lower numbers = better quality but takes longer to create.",
    inletVelocity: "How fast air enters the simulation area. Usually 0 for stationary rockets, or wind speed for moving rockets.",
    outletPressure: "Air pressure at the exit of the simulation area. Usually atmospheric pressure (101325 Pa).",
    wallCondition: "How air behaves when it hits the rocket surface:\n\n• No-Slip: Air sticks to the surface (most realistic)\n• Slip: Air slides freely (less realistic but faster)\n• Partial Slip: Somewhere in between"
  };

  const showVariableInfo = (variableType) => {
    const info = variableInfo[variableType];
    if (info) {
      // Remove any existing variable notification
      if (currentWeatherNotification) {
        removeNotification(currentWeatherNotification);
      }
      
      // Show new variable notification without auto-remove
      const notificationId = showNotification(info, 'info', false);
      setCurrentWeatherNotification(notificationId);
    }
  };

  const hideVariableInfo = () => {
    if (currentWeatherNotification) {
      removeNotification(currentWeatherNotification);
      setCurrentWeatherNotification(null);
    }
  };

  // Add click handler to hide notifications when clicking anywhere outside variable items
  const handleDocumentClick = (e) => {
    // Only hide if clicking outside of variable items and preset buttons
    if (!e.target.closest('.variable-item') && !e.target.closest('.preset-btn')) {
      if (currentWeatherNotification) {
        removeNotification(currentWeatherNotification);
        setCurrentWeatherNotification(null);
      }
    }
  };

  // Add document click listener
  React.useEffect(() => {
    document.addEventListener('click', handleDocumentClick);
    return () => {
      document.removeEventListener('click', handleDocumentClick);
    };
  }, [currentWeatherNotification]);

  // Validation functions for simulation parameters
  const validateParameter = (param, value) => {
    switch (param) {
      case 'solverType':
        return ['pimpleFoam', 'interFoam', 'rhoPimpleFoam'].includes(value);
      case 'turbulenceModel':
        return ['kEpsilon', 'kOmega', 'LES', 'DES'].includes(value);
      case 'timeStep':
        const ts = parseFloat(value);
        return !isNaN(ts) && ts > 0 && ts <= 0.1;
      case 'maxTime':
        const mt = parseFloat(value);
        return !isNaN(mt) && mt > 0 && mt <= 1000;
      case 'temperature':
        const temp = parseFloat(value);
        return !isNaN(temp) && temp >= -50 && temp <= 50;
      case 'pressure':
        const press = parseFloat(value);
        return !isNaN(press) && press >= 50000 && press <= 120000;
      case 'windSpeed':
        const ws = parseFloat(value);
        return !isNaN(ws) && ws >= 0 && ws <= 100;
      case 'windDirection':
        const wd = parseFloat(value);
        return !isNaN(wd) && wd >= 0 && wd < 360;
      case 'humidity':
        const hum = parseFloat(value);
        return !isNaN(hum) && hum >= 0 && hum <= 100;
      case 'domainSize':
        const ds = parseFloat(value);
        return !isNaN(ds) && ds >= 5 && ds <= 100;
      case 'baseCellSize':
        const cs = parseFloat(value);
        return !isNaN(cs) && cs >= 0.001 && cs <= 0.1;
      case 'meshQuality':
        const mq = parseFloat(value);
        return !isNaN(mq) && mq >= 0.1 && mq <= 1.0;
      default:
        return true;
    }
  };

  const updateSimulationParameter = (param, value) => {
    const isValid = validateParameter(param, value);
    
    setSimulationConfig(prev => ({
      ...prev,
      [param]: value
    }));

    // Show validation feedback
    if (!isValid) {
      showNotification(`Warning: ${param} value may be outside recommended range`, 'warning');
    }
  };

  const addComponent = (type) => {
    console.log('🔧 addComponent called with type:', type);
    
    // Find the last body tube to attach fins to
    let attachedToComponent = null;
    if (type === 'Fins' || type === 'Motor') {
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
      length: type === 'Transition' ? 30 : type === 'Nose Cone' ? 40 : type === 'Fins' ? 0 : type === 'Rail Button' ? 8 : type === 'Motor' ? 70 : 60,
      diameter: type === 'Transition' ? 20 : type === 'Rail Button' ? 4 : type === 'Motor' ? 18 : 20,
      topDiameter: type === 'Transition' ? 20 : type === 'Rail Button' ? 4 : type === 'Motor' ? 18 : 20,
      bottomDiameter: type === 'Transition' ? 15 : type === 'Rail Button' ? 4 : type === 'Motor' ? 18 : 20,
      lengthInput: type === 'Transition' ? '30' : type === 'Nose Cone' ? '40' : type === 'Fins' ? '0' : type === 'Rail Button' ? '8' : type === 'Motor' ? '70' : '60',
      diameterInput: type === 'Transition' ? '20' : type === 'Rail Button' ? '4' : type === 'Motor' ? '18' : '20',
      topDiameterInput: type === 'Transition' ? '20' : type === 'Rail Button' ? '4' : type === 'Motor' ? '18' : '20',
      bottomDiameterInput: type === 'Transition' ? '15' : type === 'Rail Button' ? '4' : type === 'Motor' ? '18' : '20',
      noseShape: type === 'Nose Cone' ? 'conical' : null,
      tipLength: type === 'Nose Cone' ? 15 : null,
      finShape: type === 'Fins' ? 'rectangular' : null,
      finCount: type === 'Fins' ? 4 : null,
      finHeight: type === 'Fins' ? 25 : null,
      finWidth: type === 'Fins' ? 15 : null,
      finThickness: type === 'Fins' ? 2 : null,
      finSweep: type === 'Fins' ? 0 : null,
      material: type === 'Fins' ? finMaterial : null,
      railButtonHeight: type === 'Rail Button' ? 8 : null,
      railButtonWidth: type === 'Rail Button' ? 4 : null,
      railButtonOffset: type === 'Rail Button' ? 2 : null,
         // Motor properties
         motorType: type === 'Motor' ? 'Estes' : null,
         motorModel: type === 'Motor' ? 'C6-5' : null,
         motorImpulse: type === 'Motor' ? 'C' : null,
         motorThrust: type === 'Motor' ? 6 : null,
         motorBurnTime: type === 'Motor' ? 1.6 : null,
         motorTotalImpulse: type === 'Motor' ? 10 : null,
         motorDelay: type === 'Motor' ? 5 : null,
         motorWeight: type === 'Motor' ? 16.8 : null,
         // Motor attachment (similar to fins)
         attachedToComponent: type === 'Motor' ? null : (type === 'Fins' ? attachedToComponent : null)
    };
    console.log('🔧 Adding new component:', newComponent);
    setRocketComponents([...rocketComponents, newComponent]);
    console.log('🔧 Component added successfully. Total components:', rocketComponents.length + 1);
  };

  const addMotorFromSearch = (motorData) => {
    const existingCount = rocketComponents.filter(comp => comp.type === 'Motor').length;
    
    // Find body tubes for motor attachment
    const bodyTubes = rocketComponents.filter(comp => 
      ['Body Tube', 'Transition'].includes(comp.type)
    );
    
    let attachedToComponent = null;
    if (bodyTubes.length > 0) {
      // Auto-attach to the last body tube (bottom of rocket)
      attachedToComponent = bodyTubes[bodyTubes.length - 1].id;
    }
    
    const newMotor = {
      id: Date.now(),
      type: 'Motor',
      name: `${motorData.manufacturer} ${motorData.model}`,
      length: motorData.length,
      diameter: motorData.diameter,
      topDiameter: motorData.diameter,
      bottomDiameter: motorData.diameter,
      lengthInput: motorData.length.toString(),
      diameterInput: motorData.diameter.toString(),
      topDiameterInput: motorData.diameter.toString(),
      bottomDiameterInput: motorData.diameter.toString(),
      // Motor properties from search
      motorType: motorData.manufacturer,
      motorModel: motorData.model,
      motorImpulse: motorData.impulse,
      motorThrust: motorData.thrust,
      motorBurnTime: motorData.burnTime,
      motorTotalImpulse: motorData.totalImpulse,
      motorDelay: motorData.delay,
      motorWeight: motorData.weight,
      motorPropellant: motorData.propellant,
      motorCertification: motorData.certification,
      motorPrice: motorData.price,
      motorId: motorData.id,
      // Motor attachment
      attachedToComponent: attachedToComponent
    };
    
    setRocketComponents([...rocketComponents, newMotor]);
    setShowMotorSearch(false);
    setSelectedMotor(null);
    
    if (attachedToComponent) {
      const attachedComponent = rocketComponents.find(comp => comp.id === attachedToComponent);
      showNotification(`Motor added and attached to ${attachedComponent?.name}`, 'success');
    } else {
      showNotification(`Motor added: ${motorData.manufacturer} ${motorData.model}`, 'success');
    }
  };

  const importSTL = (event) => {
    const file = event.target.files[0];
    if (file && file.name.toLowerCase().endsWith('.stl')) {
      console.log('📁 STL Import:', file.name, `(${(file.size/1024).toFixed(1)}KB)`);
      
      const reader = new FileReader();
      reader.onload = (e) => {
        const stlContent = e.target.result;
        
        // Process the STL to clean it up
        const processedSTL = processSTL(stlContent);
        
        // Calculate dimensions first
        const dimensions = calculateSTLDimensions(processedSTL);
        
        // Create a rocket component from the STL file
        const stlRocket = {
          id: Date.now(),
          type: 'Imported Rocket',
          name: file.name.replace('.stl', ''),
          stlData: processedSTL,
          originalStlData: stlContent,
          fileName: file.name,
          fileSize: file.size,
          // Calculate dimensions from STL data
          length: dimensions.length,
          diameter: dimensions.diameter,
          topDiameter: dimensions.diameter,
          bottomDiameter: dimensions.diameter,
          lengthInput: dimensions.length.toString(),
          diameterInput: dimensions.diameter.toString(),
          topDiameterInput: dimensions.diameter.toString(),
          bottomDiameterInput: dimensions.diameter.toString(),
          noseShape: null,
          tipLength: null,
          finShape: null,
          finCount: null,
          finHeight: null,
          finWidth: null,
          finThickness: null,
          finSweep: null,
          railButtonHeight: null,
          railButtonWidth: null,
          railButtonOffset: null,
          attachedToComponent: null
        };
        
        console.log('✅ STL Rocket Created:', dimensions);
        
        // Replace all existing components with the imported STL rocket
        setRocketComponents([stlRocket]);
        
        // Update rocket properties based on STL dimensions
        const weight = Math.round(dimensions.volume * 2.7); // Default to aluminum density
        const cg = dimensions.length / 2;
        
        // Ensure we have valid values
        if (isFinite(weight) && weight > 0) {
          setRocketWeight(weight);
        } else {
          setRocketWeight(100); // Default weight
        }
        
        if (isFinite(cg) && cg > 0) {
          setRocketCG(cg);
        } else {
          setRocketCG(25); // Default CG
        }
        
        console.log('📊 Rocket Properties Updated:', { weight: `${weight}g`, cg: `${cg.toFixed(1)}cm` });
        
        // Show success message
        showNotification(`STL imported successfully! Rocket: ${stlRocket.name}, Length: ${dimensions.length} units, Diameter: ${dimensions.diameter} units`, 'success');
      };
      reader.readAsText(file);
    } else {
      showNotification('Please select a valid STL file', 'warning');
    }
    
    // Reset the file input
    event.target.value = '';
  };

  const processSTL = (stlContent) => {
    try {
      // Parse STL content
      const lines = stlContent.split('\n');
      const vertices = [];
      const faces = [];
      let currentFace = [];
      
      // Extract vertices and faces from STL
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        
        if (line.startsWith('vertex')) {
          const parts = line.split(' ');
          const x = parseFloat(parts[1]);
          const y = parseFloat(parts[2]);
          const z = parseFloat(parts[3]);
          currentFace.push([x, y, z]);
          
          if (currentFace.length === 3) {
            faces.push([...currentFace]);
            vertices.push(...currentFace);
            currentFace = [];
          }
        }
      }
      
      // Remove duplicate vertices and create clean mesh
      const uniqueVertices = removeDuplicateVertices(vertices);
      const cleanedFaces = createCleanFaces(faces, uniqueVertices);
      
      // Fill holes and gaps
      const filledMesh = fillHolesAndGaps(cleanedFaces, uniqueVertices);
      
      // Generate cleaned STL content
      return generateCleanSTL(filledMesh.vertices, filledMesh.faces);
      
    } catch (error) {
      console.error('Error processing STL:', error);
      return stlContent; // Return original if processing fails
    }
  };

  const removeDuplicateVertices = (vertices) => {
    const unique = [];
    const seen = new Set();
    
    for (const vertex of vertices) {
      const key = `${vertex[0].toFixed(6)},${vertex[1].toFixed(6)},${vertex[2].toFixed(6)}`;
      if (!seen.has(key)) {
        seen.add(key);
        unique.push(vertex);
      }
    }
    
    return unique;
  };

  const createCleanFaces = (faces, uniqueVertices) => {
    // Remove faces with zero area or degenerate triangles
    return faces.filter(face => {
      const [v1, v2, v3] = face;
      const area = calculateTriangleArea(v1, v2, v3);
      return area > 0.0001; // Minimum area threshold
    });
  };

  const calculateTriangleArea = (v1, v2, v3) => {
    const a = Math.sqrt(
      Math.pow(v2[0] - v1[0], 2) + 
      Math.pow(v2[1] - v1[1], 2) + 
      Math.pow(v2[2] - v1[2], 2)
    );
    const b = Math.sqrt(
      Math.pow(v3[0] - v2[0], 2) + 
      Math.pow(v3[1] - v2[1], 2) + 
      Math.pow(v3[2] - v2[2], 2)
    );
    const c = Math.sqrt(
      Math.pow(v1[0] - v3[0], 2) + 
      Math.pow(v1[1] - v3[1], 2) + 
      Math.pow(v1[2] - v3[2], 2)
    );
    
    const s = (a + b + c) / 2;
    return Math.sqrt(s * (s - a) * (s - b) * (s - c));
  };

  const fillHolesAndGaps = (faces, vertices) => {
    // Find boundary edges (edges that appear only once)
    const edgeCount = new Map();
    
    for (const face of faces) {
      for (let i = 0; i < 3; i++) {
        const v1 = face[i];
        const v2 = face[(i + 1) % 3];
        const edge = [v1, v2].sort((a, b) => 
          a[0] !== b[0] ? a[0] - b[0] : 
          a[1] !== b[1] ? a[1] - b[1] : a[2] - b[2]
        );
        const edgeKey = `${edge[0]},${edge[1]}`;
        edgeCount.set(edgeKey, (edgeCount.get(edgeKey) || 0) + 1);
      }
    }
    
    // Find boundary edges (appear only once)
    const boundaryEdges = [];
    for (const [edgeKey, count] of edgeCount) {
      if (count === 1) {
        const [v1Str, v2Str] = edgeKey.split(',');
        const v1 = v1Str.split(',').map(Number);
        const v2 = v2Str.split(',').map(Number);
        boundaryEdges.push([v1, v2]);
      }
    }
    
    // Create new faces to fill holes
    const newFaces = [...faces];
    
    // Simple hole filling: create triangles from boundary edges
    for (let i = 0; i < boundaryEdges.length - 2; i++) {
      const v1 = boundaryEdges[i][0];
      const v2 = boundaryEdges[i + 1][0];
      const v3 = boundaryEdges[i + 2][0];
      
      // Check if this creates a valid triangle
      const area = calculateTriangleArea(v1, v2, v3);
      if (area > 0.0001) {
        newFaces.push([v1, v2, v3]);
      }
    }
    
    return { vertices, faces: newFaces };
  };

  const generateCleanSTL = (vertices, faces) => {
    let stlContent = 'solid cleaned_mesh\n';
    
    for (const face of faces) {
      // Calculate face normal
      const [v1, v2, v3] = face;
      const normal = calculateFaceNormal(v1, v2, v3);
      
      stlContent += `  facet normal ${normal[0]} ${normal[1]} ${normal[2]}\n`;
      stlContent += '    outer loop\n';
      stlContent += `      vertex ${v1[0]} ${v1[1]} ${v1[2]}\n`;
      stlContent += `      vertex ${v2[0]} ${v2[1]} ${v2[2]}\n`;
      stlContent += `      vertex ${v3[0]} ${v3[1]} ${v3[2]}\n`;
      stlContent += '    endloop\n';
      stlContent += '  endfacet\n';
    }
    
    stlContent += 'endsolid cleaned_mesh\n';
    return stlContent;
  };

  const calculateFaceNormal = (v1, v2, v3) => {
    const ux = v2[0] - v1[0];
    const uy = v2[1] - v1[1];
    const uz = v2[2] - v1[2];
    
    const vx = v3[0] - v1[0];
    const vy = v3[1] - v1[1];
    const vz = v3[2] - v1[2];
    
    const nx = uy * vz - uz * vy;
    const ny = uz * vx - ux * vz;
    const nz = ux * vy - uy * vx;
    
    const length = Math.sqrt(nx * nx + ny * ny + nz * nz);
    return [nx / length, ny / length, nz / length];
  };

  // Redraw canvas when rocket components change
  useEffect(() => {
    drawRocketDiagram();
  }, [rocketComponents, zoom]);

  // Redraw canvas when switching back to builder tab
  useEffect(() => {
    if (activeTab === 'builder') {
      console.log('🔄 Switching to builder tab - redrawing rocket');
      setTimeout(() => {
        drawRocketDiagram();
      }, 100); // Small delay to ensure DOM is ready
    }
  }, [activeTab]);



  const loadPresetConfig = (presetType) => {
    const presets = {
      sunny: {
        solverType: 'pimpleFoam',
        turbulenceModel: 'kEpsilon',
        timeStep: 0.001,
        maxTime: 30,
        writeInterval: 100,
        launchAltitude: 0,
        temperature: 25,
        pressure: 101325,
        humidity: 30,
        windSpeed: 2,
        windDirection: 0,
        inletVelocity: 0,
        outletPressure: 101325,
        wallCondition: 'noSlip',
        domainSize: 10,
        baseCellSize: 0.01,
        boundaryLayerCells: 5,
        refinementLevel: 'medium',
        meshQuality: 0.3,
        calculateDrag: true,
        calculateLift: true,
        calculatePressure: true,
        calculateVelocity: true,
        outputFormat: 'vtk'
      },
      rainy: {
        solverType: 'interFoam',
        turbulenceModel: 'kOmega',
        timeStep: 0.0008,
        maxTime: 35,
        writeInterval: 120,
        launchAltitude: 0,
        temperature: 12,
        pressure: 100500,
        humidity: 85,
        windSpeed: 8,
        windDirection: 45,
        inletVelocity: 0,
        outletPressure: 100500,
        wallCondition: 'noSlip',
        domainSize: 12,
        baseCellSize: 0.008,
        boundaryLayerCells: 6,
        refinementLevel: 'medium',
        meshQuality: 0.25,
        calculateDrag: true,
        calculateLift: true,
        calculatePressure: true,
        calculateVelocity: true,
        outputFormat: 'vtk'
      },
      windy: {
        solverType: 'pimpleFoam',
        turbulenceModel: 'LES',
        timeStep: 0.0005,
        maxTime: 40,
        writeInterval: 100,
        launchAltitude: 0,
        temperature: 18,
        pressure: 101000,
        humidity: 45,
        windSpeed: 20,
        windDirection: 90,
        inletVelocity: 0,
        outletPressure: 101000,
        wallCondition: 'noSlip',
        domainSize: 15,
        baseCellSize: 0.006,
        boundaryLayerCells: 7,
        refinementLevel: 'high',
        meshQuality: 0.2,
        calculateDrag: true,
        calculateLift: true,
        calculatePressure: true,
        calculateVelocity: true,
        outputFormat: 'ensight'
      },
      stormy: {
        solverType: 'rhoPimpleFoam',
        turbulenceModel: 'DES',
        timeStep: 0.0003,
        maxTime: 25,
        writeInterval: 80,
        launchAltitude: 0,
        temperature: 8,
        pressure: 99500,
        humidity: 95,
        windSpeed: 35,
        windDirection: 180,
        inletVelocity: 0,
        outletPressure: 99500,
        wallCondition: 'noSlip',
        domainSize: 18,
        baseCellSize: 0.004,
        boundaryLayerCells: 8,
        refinementLevel: 'high',
        meshQuality: 0.15,
        calculateDrag: true,
        calculateLift: true,
        calculatePressure: true,
        calculateVelocity: true,
        outputFormat: 'ensight'
      }
    };

    if (presets[presetType]) {
      setSimulationConfig(presets[presetType]);
      showNotification(`${presetType.replace('_', ' ').toUpperCase()} configuration loaded!`, 'success');
    }
  };

  const saveSimulationConfig = () => {
    const configData = JSON.stringify(simulationConfig, null, 2);
    const blob = new Blob([configData], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `rocket_simulation_config_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showNotification('Configuration saved successfully!', 'success');
  };

  const loadSimulationConfig = () => {
    configFileInputRef.current.click();
  };

  const handleConfigFileLoad = (event) => {
    const file = event.target.files[0];
    if (file && file.name.toLowerCase().endsWith('.json')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const config = JSON.parse(e.target.result);
          setSimulationConfig(config);
          showNotification('Configuration loaded successfully!', 'success');
        } catch (error) {
          showNotification('Error loading configuration file. Please check the file format.', 'error');
        }
      };
      reader.readAsText(file);
    }
    event.target.value = '';
  };

  const resetSimulationConfig = () => {
    setSimulationConfig({
      solverType: 'pimpleFoam',
        turbulenceModel: 'LES',
        timeStep: 0.001,
        maxTime: 30,
        writeInterval: 100,
        launchAltitude: 0,
        temperature: 15,
        pressure: 101325,
        humidity: 50,
        windSpeed: 0,
        windDirection: 0,
        inletVelocity: 0,
        outletPressure: 101325,
        wallCondition: 'noSlip',
        domainSize: 10,
        baseCellSize: 0.01,
        boundaryLayerCells: 5,
        refinementLevel: 'medium',
        meshQuality: 0.3,
        calculateDrag: true,
        calculateLift: true,
        calculatePressure: true,
        calculateVelocity: true,
        outputFormat: 'vtk'
      });
      showNotification('Configuration reset to defaults!', 'info');
  };

  const importFins = (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    const fileName = file.name.toLowerCase();
    const isSTL = fileName.endsWith('.stl');
    const isDXF = fileName.endsWith('.dxf');
    
    if (!isSTL && !isDXF) {
      showNotification('Please select a valid STL or DXF file for fins', 'warning');
      event.target.value = '';
      return;
    }
    
    console.log('📁 Fin Import:', file.name, `(${isSTL ? 'STL' : 'DXF'})`);
    
    const reader = new FileReader();
    reader.onload = (e) => {
      const fileContent = e.target.result;
      
      try {
        let finData;
        let finDimensions;
        
        if (isSTL) {
          // Process STL file
          const processedSTL = processSTL(fileContent);
          finData = processedSTL;
          finDimensions = calculateSTLDimensions(processedSTL);
        } else {
          // Process DXF file
          finData = fileContent;
          finDimensions = parseDXFFins(fileContent);
        }
        
        // Create fin component with imported data
        const importedFin = {
          id: Date.now(),
          type: 'Imported Fins',
          name: `Imported Fins ${rocketComponents.filter(c => c.type === 'Imported Fins').length + 1}`,
          finData: finData,
          fileName: file.name,
          fileType: isSTL ? 'STL' : 'DXF',
          material: finMaterial,
          // Fin properties
          finCount: 4, // Default, can be adjusted
          finHeight: finDimensions.height || 25,
          finWidth: finDimensions.width || 15,
          finThickness: finDimensions.thickness || 2,
          finSweep: 0,
          // Dimensions for display
          length: finDimensions.thickness || 2,
          diameter: finDimensions.width || 15,
          topDiameter: finDimensions.width || 15,
          bottomDiameter: finDimensions.width || 15,
          lengthInput: (finDimensions.thickness || 2).toString(),
          diameterInput: (finDimensions.width || 15).toString(),
          topDiameterInput: (finDimensions.width || 15).toString(),
          bottomDiameterInput: (finDimensions.width || 15).toString(),
          // Other properties
          noseShape: null,
          tipLength: null,
          finShape: 'custom',
          railButtonHeight: null,
          railButtonWidth: null,
          railButtonOffset: null,
          attachedToComponent: null
        };
        
        console.log('✅ Fin Imported:', importedFin.name);
        
        // Add to existing components
        setRocketComponents(prev => [...prev, importedFin]);
        
        // Show success message
        showNotification(`Fins imported successfully! File: ${file.name}, Material: ${finMaterial}, Dimensions: ${finDimensions.width || 'N/A'} × ${finDimensions.height || 'N/A'} × ${finDimensions.thickness || 'N/A'}`, 'success');
        
      } catch (error) {
        console.error('Error importing fins:', error);
        showNotification('Error importing fins. Please check the file format and try again.', 'error');
      }
    };
    
    if (isSTL) {
      reader.readAsText(file);
    } else {
      reader.readAsText(file);
    }
    
    // Reset the file input
    event.target.value = '';
  };

  const parseDXFFins = (dxfContent) => {
    try {
      // Basic DXF parsing for fin dimensions
      const lines = dxfContent.split('\n');
      let minX = Infinity, maxX = -Infinity;
      let minY = Infinity, maxY = -Infinity;
      let minZ = Infinity, maxZ = -Infinity;
      
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        if (line === '10' && i + 1 < lines.length) { // X coordinate
          const x = parseFloat(lines[i + 1]);
          if (!isNaN(x)) {
            minX = Math.min(minX, x);
            maxX = Math.max(maxX, x);
          }
        } else if (line === '20' && i + 1 < lines.length) { // Y coordinate
          const y = parseFloat(lines[i + 1]);
          if (!isNaN(y)) {
            minY = Math.min(minY, y);
            maxY = Math.max(maxY, y);
          }
        } else if (line === '30' && i + 1 < lines.length) { // Z coordinate
          const z = parseFloat(lines[i + 1]);
          if (!isNaN(z)) {
            minZ = Math.min(minZ, z);
            maxZ = Math.max(maxZ, z);
          }
        }
      }
      
      const width = Math.abs(maxX - minX);
      const height = Math.abs(maxY - minY);
      const thickness = Math.abs(maxZ - minZ);
      
      return {
        width: Math.round(width * 100) / 100,
        height: Math.round(height * 100) / 100,
        thickness: Math.round(thickness * 100) / 100
      };
    } catch (error) {
      console.error('Error parsing DXF:', error);
      return { width: 15, height: 25, thickness: 2 };
    }
  };

  const calculateSTLDimensions = (stlContent) => {
    try {
      const lines = stlContent.split('\n');
      let minX = Infinity, maxX = -Infinity;
      let minY = Infinity, maxY = -Infinity;
      let minZ = Infinity, maxZ = -Infinity;
      let vertexCount = 0;
      
      for (const line of lines) {
        if (line.trim().startsWith('vertex')) {
          const parts = line.trim().split(' ');
          if (parts.length >= 4) {
            const x = parseFloat(parts[1]);
            const y = parseFloat(parts[2]);
            const z = parseFloat(parts[3]);
            
            if (!isNaN(x) && !isNaN(y) && !isNaN(z)) {
              minX = Math.min(minX, x);
              maxX = Math.max(maxX, x);
              minY = Math.min(minY, y);
              maxY = Math.max(maxY, y);
              minZ = Math.min(minZ, z);
              maxZ = Math.max(maxZ, z);
              vertexCount++;
            }
          }
        }
      }
      
      // Check if we found valid vertices
      if (vertexCount === 0 || minX === Infinity || maxX === -Infinity) {
        console.warn('No valid vertices found in STL, using defaults');
        return { length: 50, diameter: 20, volume: 15708 };
      }
      
      const length = Math.abs(maxZ - minZ);
      const diameter = Math.max(Math.abs(maxX - minX), Math.abs(maxY - minY));
      const volume = length * Math.PI * Math.pow(diameter / 2, 2);
      
      console.log('📐 STL Dimensions:', `${length.toFixed(1)}×${diameter.toFixed(1)}cm (${vertexCount} vertices)`);
      
      return {
        length: Math.round(length * 100) / 100,
        diameter: Math.round(diameter * 100) / 100,
        volume: Math.round(volume * 100) / 100
      };
    } catch (error) {
      console.error('Error calculating STL dimensions:', error);
      return { length: 50, diameter: 20, volume: 15708 };
    }
  };

  const drawSTLRocket = (ctx, stlComponent) => {
    if (!stlComponent || !stlComponent.stlData) return;
    
    try {
      const dimensions = calculateSTLDimensions(stlComponent.stlData);
      const centerX = ctx.canvas.width / 2;
      const centerY = ctx.canvas.height / 2;
      
      // Scale factors for display
      const scaleX = (ctx.canvas.width * 0.6) / dimensions.diameter;
      const scaleY = (ctx.canvas.height * 0.6) / dimensions.length;
      const scale = Math.min(scaleX, scaleY) * zoom;
      
      // Draw rocket body
      ctx.fillStyle = '#6b4c3e';
      ctx.strokeStyle = '#333';
      ctx.lineWidth = 2;
      
      const rocketWidth = dimensions.diameter * scale;
      const rocketHeight = dimensions.length * scale;
      
      // Draw main body
      ctx.fillRect(centerX - rocketWidth/2, centerY - rocketHeight/2, rocketWidth, rocketHeight);
      ctx.strokeRect(centerX - rocketWidth/2, centerY - rocketHeight/2, rocketWidth, rocketHeight);
      
      // Draw nose cone
      ctx.beginPath();
      ctx.moveTo(centerX, centerY - rocketHeight/2);
      ctx.lineTo(centerX - rocketWidth/2, centerY - rocketHeight/2 + rocketWidth/2);
      ctx.lineTo(centerX + rocketWidth/2, centerY - rocketHeight/2 + rocketWidth/2);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
      
      // Add label
      ctx.fillStyle = '#333';
      ctx.font = '14px -apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", "Oxygen", "Ubuntu", "Cantarell", "Fira Sans", "Droid Sans", "Helvetica Neue", sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(stlComponent.name, centerX, centerY + rocketHeight/2 + 20);
      ctx.fillText(`${dimensions.length.toFixed(1)} × ${dimensions.diameter.toFixed(1)}`, centerX, centerY + rocketHeight/2 + 40);
      
    } catch (error) {
      console.error('Error drawing STL rocket:', error);
    }
  };

  const updateComponent = (id, field, value) => {
    console.log('🔄 updateComponent called:', { id, field, value });
    setRocketComponents(components => {
      console.log('🔄 Before update - components:', components.map(c => ({ id: c.id, name: c.name, [field]: c[field] })));
      const updated = components.map(comp =>
        comp.id === id ? { ...comp, [field]: value } : comp
      );
      console.log('🔄 After update - components:', updated.map(c => ({ id: c.id, name: c.name, [field]: c[field] })));
      
      // Update selectedComponent if it's the same component being updated
      if (selectedComponent && selectedComponent.id === id) {
        const updatedSelectedComponent = updated.find(comp => comp.id === id);
        if (updatedSelectedComponent) {
          console.log('🔄 Updating selectedComponent:', updatedSelectedComponent);
          setSelectedComponent(updatedSelectedComponent);
        }
      }
      
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
      if (comp.type === 'Fins' && comp.attachedToComponent) {
        // Check if the attached component still exists
        const attachedExists = components.some(c => c.id === comp.attachedToComponent);
        if (!attachedExists) {
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

  // Active Fin Control API Functions
  const updateActiveFinControlConfig = async (configData) => {
    try {
      const response = await fetch(`${SIMULATION_API_URL}/api/active-fin-control/config`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(configData)
      });
      const result = await response.json();
      if (result.success) {
        console.log('✅ Active fin control config updated');
      } else {
        console.error('Failed to update config:', result.error);
      }
    } catch (error) {
      console.error('Error updating active fin control config:', error);
    }
  };

  const startActiveFinControl = async () => {
    try {
      const response = await fetch(`${SIMULATION_API_URL}/api/active-fin-control/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      const result = await response.json();
      if (result.success) {
        console.log('🚀 Active fin control started');
      } else {
        console.error('Failed to start active fin control:', result.error);
      }
    } catch (error) {
      console.error('Error starting active fin control:', error);
    }
  };

  const stopActiveFinControl = async () => {
    try {
      const response = await fetch(`${SIMULATION_API_URL}/api/active-fin-control/stop`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      const result = await response.json();
      if (result.success) {
        console.log('⏹️ Active fin control stopped');
      } else {
        console.error('Failed to stop active fin control:', result.error);
      }
    } catch (error) {
      console.error('Error stopping active fin control:', error);
    }
  };

  const testControlAlgorithm = async (testData) => {
    try {
      const response = await fetch(`${SIMULATION_API_URL}/api/active-fin-control/test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(testData)
      });
      const result = await response.json();
      if (result.success) {
        console.log('🧪 Control test result:', result.fin_deflections);
        return result.fin_deflections;
      } else {
        console.error('Failed to test control algorithm:', result.error);
        return null;
      }
    } catch (error) {
      console.error('Error testing control algorithm:', error);
      return null;
    }
  };

  const startSimulation = async () => {
    // Check if rocket has a motor
    const hasMotor = rocketComponents.some(comp => comp.type === 'Motor');
    if (!hasMotor) {
      showNotification('Please add a motor to your rocket before running simulation', 'error');
      return;
    }

    console.log('🚀 Starting simulation - setting simulationRunning to true');
    setSimulationRunning(true);
    simulationRunningRef.current = true;
    setSimulationStatus({
      status: 'Initializing...',
      progress: 0,
      message: 'Setting up simulation environment'
    });
    
    try {
      const fullUrl = `${SIMULATION_API_URL}/api/simulation/start`;
      console.log('🚀 Starting simulation with URL:', fullUrl);
      // Calculate actual values
      const actualWeight = calculateRocketWeight();
      const actualCG = calculateRocketCG();
      const totalHeight = calculateRocketLength();
      
      console.log('📊 Simulation data:', {
        rocketComponents: rocketComponents.length,
        rocketWeight: actualWeight,
        rocketCG: actualCG,
        totalHeight: totalHeight,
        simulationConfig: Object.keys(simulationConfig)
      });
      
      const response = await fetch(fullUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          rocketComponents,
          rocketWeight: actualWeight,
          rocketCG: actualCG,
          totalHeight: totalHeight,
          simulationConfig
        })
      });
      
      console.log('📡 Response received:', {
        status: response.status,
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries())
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ Simulation start failed:', {
          status: response.status,
          statusText: response.statusText,
          url: fullUrl,
          errorText: errorText.substring(0, 500) // Limit error text length
        });
        
        // Provide specific error messages based on status code
        if (response.status === 404) {
          throw new Error(`Simulation service not available (404). Please deploy the Google Cloud Function first.`);
        } else if (response.status === 500) {
          throw new Error(`Simulation service error (500). Check the backend logs.`);
        } else {
          throw new Error(`Failed to start simulation: ${response.status} ${response.statusText}`);
        }
      }
      
      const data = await response.json();
      console.log('🚀 Simulation started:', data.message);
      console.log('🆔 Simulation ID:', data.simulation_id);
      
      // Store simulation ID for status polling
      setCurrentSimulationId(data.simulation_id);
      
      // Start polling for status updates
      pollSimulationStatus(data.simulation_id);
      
    } catch (error) {
      console.error('💥 Error starting simulation:', {
        error: error.message,
        stack: error.stack,
        name: error.name,
        url: `${SIMULATION_API_URL}/api/simulation/start`,
        timestamp: new Date().toISOString()
      });
      setSimulationStatus({
        status: 'Error',
        message: error.message
      });
      setSimulationRunning(false);
      simulationRunningRef.current = false;
    }
  };

  const stopSimulation = async () => {
    try {
      console.log('🛑 Stopping simulation:', currentSimulationId);
      await fetch(`${SIMULATION_API_URL}/api/simulation/stop`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          simulation_id: currentSimulationId
        })
      });
      setSimulationRunning(false);
      simulationRunningRef.current = false;
      setSimulationStatus(null);
      setCurrentSimulationId(null);
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
      const response = await fetch(`${SIMULATION_API_URL}/api/simulation/mesh`, {
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
      console.log('🔧 Mesh generated:', data.message);
      
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

  const pollSimulationStatus = (simulationId) => {
    console.log('🔄 Starting status polling for simulation:', simulationId);
    console.log('📊 Current simulationRunning state:', simulationRunning);
    console.log('📊 Current simulationRunningRef:', simulationRunningRef.current);
    
    const pollInterval = setInterval(async () => {
      console.log('🔄 Polling check - simulationRunning:', simulationRunning);
      console.log('🔄 Polling check - simulationRunningRef:', simulationRunningRef.current);
      if (!simulationRunningRef.current) {
        console.log('🛑 Stopping status polling - simulation not running');
        clearInterval(pollInterval);
        return;
      }
      
      try {
        console.log('📊 Polling status for simulation:', simulationId);
        const response = await fetch(`${SIMULATION_API_URL}/api/simulation/status`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            simulation_id: simulationId
          })
        });
        
        console.log('📡 Status response:', response.status);
        
        if (response.ok) {
          const status = await response.json();
          console.log('📊 Status update:', status);
          setSimulationStatus(status);
          
          if (status.status === 'completed' || status.status === 'error' || status.status === 'stopped') {
            console.log('✅ Simulation finished with status:', status.status);
            setSimulationRunning(false);
            simulationRunningRef.current = false;
            clearInterval(pollInterval);
            
            // If simulation completed successfully, switch to results tab
            if (status.status === 'completed') {
              console.log('🎯 Switching to results tab and populating results');
              setActiveTab('results');
              // Store simulation results for display
              setSimulationResults({
                status: 'completed',
                progress: 100,
                message: status.message,
                elapsed_time: status.elapsed_time,
                rocket_components: status.rocket_components,
                rocket_weight: status.rocket_weight,
                rocket_cg: status.rocket_cg,
                totalHeight: status.totalHeight || calculateRocketLength(),
                simulation_id: simulationId,
                completed_at: new Date().toISOString(),
                // Include real simulation results
                results: status.results || null
              });
            }
          }
        } else {
          console.error('❌ Status check failed:', response.status, response.statusText);
        }
      } catch (error) {
        console.error('💥 Error polling simulation status:', error);
      }
    }, 2000); // Poll every 2 seconds
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
      
      // Clean up orphaned components (fins attached to deleted body tubes)
      const cleaned = filtered.filter(comp => {
        if (comp.type === 'Fins' && comp.attachedToComponent) {
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
    console.log('🖱️ Drag Start:', component.name, `(${component.type})`);
    
    // DIAGNOSTIC: Test drag start setup
    console.log('🧪 DragStart Test - DataTransfer Setup:', {
      effectAllowed: e.dataTransfer.effectAllowed,
      hasData: e.dataTransfer.getData('text/plain'),
      dataTypes: e.dataTransfer.types,
      files: e.dataTransfer.files.length,
      items: e.dataTransfer.items.length
    });
    
    setDraggedComponent(component);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', component.id);
    e.dataTransfer.setData('application/json', JSON.stringify(component));
    e.stopPropagation(); // Prevent event bubbling
  };

  const handleDragOver = (e, index) => {
    e.preventDefault();
    e.stopPropagation();
    
    // Get the body components to find the correct index
    const bodyComponents = rocketComponents.filter(comp => 
      ['Nose Cone', 'Body Tube', 'Transition'].includes(comp.type)
    );
    const dropTarget = bodyComponents[index];
    
    console.log('🔄 DragOver:', {
      index,
      dropTarget: dropTarget?.name,
      draggedComponent: draggedComponent?.name,
      dropEffect: e.dataTransfer?.dropEffect
    });
    
    // DIAGNOSTIC: Test drag over setup
    console.log('🧪 DragOver Test - Event Details:', {
      type: e.type,
      target: e.target.className,
      currentTarget: e.currentTarget.className,
      dataTransfer: {
        effectAllowed: e.dataTransfer?.effectAllowed,
        dropEffect: e.dataTransfer?.dropEffect,
        types: e.dataTransfer?.types,
        hasData: e.dataTransfer?.getData('text/plain')
      },
      isDefaultPrevented: e.defaultPrevented,
      isPropagationStopped: e.isPropagationStopped
    });
    
    if (draggedComponent?.type === 'Fins' && ['Body Tube', 'Transition'].includes(dropTarget?.type)) {
      e.dataTransfer.dropEffect = 'copy'; // Show copy effect for connecting
      console.log(`🎯 Ready to attach ${draggedComponent?.name} → ${dropTarget?.name}`);
    } else {
      e.dataTransfer.dropEffect = 'move'; // Show move effect for reordering
      console.log(`🔄 Ready to reorder ${draggedComponent?.name} to position ${index}`);
    }
    
    setDragOverIndex(index);
  };

  const handleDragLeave = (e) => {
    console.log('🚪 DragLeave');
    console.log('🚪 DragLeave Details:', {
      type: e.type,
      target: e.target.className,
      currentTarget: e.currentTarget.className,
      draggedComponent: draggedComponent?.name
    });
    
    // DIAGNOSTIC: Check if dragLeave is interfering with drop
    console.log('🧪 DragLeave Interference Test:', {
      hasDraggedComponent: !!draggedComponent,
      dragOverIndex: dragOverIndex,
      willClearDragOver: true,
      potentialIssue: 'DragLeave clearing dragOverIndex might prevent drop event'
    });
    
    // FIX: Don't clear dragOverIndex on dragLeave to prevent drop interference
    // setDragOverIndex(null); // COMMENTED OUT - This was causing the issue!
    e.stopPropagation();
  };

  const handleDrop = (e, dropIndex) => {
    e.preventDefault();
    e.stopPropagation();
    
    console.log('🎯 DROP EVENT:', draggedComponent?.name, '→ index', dropIndex);
    
    if (!draggedComponent) {
      console.log('❌ No dragged component found');
      return;
    }

    const dragIndex = rocketComponents.findIndex(comp => comp.id === draggedComponent.id);
    if (dragIndex === -1) {
      console.log('❌ Dragged component not found in rocketComponents');
      return;
    }

    // Get the body components to find the correct drop target
    const bodyComponents = rocketComponents.filter(comp => 
      ['Nose Cone', 'Body Tube', 'Transition'].includes(comp.type)
    );
    const dropTarget = bodyComponents[dropIndex];
    
    console.log('🎯 Drop Target:', dropTarget?.name, `(${dropTarget?.type})`);
    
    if (draggedComponent.type === 'Fins' && ['Body Tube', 'Transition'].includes(dropTarget?.type)) {
      // Connect the fins to the body tube
      console.log(`🔗 Attaching ${draggedComponent.name} → ${dropTarget.name}`);
      try {
        const newComponents = [...rocketComponents];
        newComponents[dragIndex] = {
          ...draggedComponent,
          attachedToComponent: dropTarget.id
        };
        setRocketComponents(cleanupOrphanedComponents(newComponents));
        console.log(`✅ SUCCESS: ${draggedComponent.name} attached to ${dropTarget.name}`);
        showNotification(`✅ ${draggedComponent.name} attached to ${dropTarget.name}`, 'success');
      } catch (error) {
        console.error('Error connecting fins:', error);
        showNotification(`❌ Error attaching fins: ${error.message}`, 'error');
      }
    } else {
      // Regular reordering
      console.log(`🔄 Reordering ${draggedComponent.name} to position ${dropIndex}`);
      try {
        const newComponents = [...rocketComponents];
        const [removed] = newComponents.splice(dragIndex, 1);
        newComponents.splice(dropIndex, 0, removed);
        setRocketComponents(cleanupOrphanedComponents(newComponents));
        console.log(`✅ SUCCESS: ${draggedComponent.name} reordered to position ${dropIndex}`);
      } catch (error) {
        console.error('Error reordering components:', error);
      }
    }

    setDraggedComponent(null);
    setDragOverIndex(null);
  };

  const handleDragEnd = (e) => {
    console.log('🖱️ Drag End');
    console.log('🖱️ Drag End Details:', {
      type: e.type,
      target: e.target.className,
      currentTarget: e.currentTarget.className,
      dataTransfer: e.dataTransfer?.effectAllowed,
      draggedComponent: draggedComponent?.name,
      dropEffect: e.dataTransfer?.dropEffect
    });
    
    // FALLBACK: If we have a dragged component and a dragOverIndex, but no drop event fired,
    // manually trigger the drop logic
    if (draggedComponent && dragOverIndex !== null) {
      console.log('🚨 FALLBACK: No drop event fired, manually triggering drop logic');
      console.log('🚨 Fallback Details:', {
        draggedComponent: draggedComponent.name,
        dragOverIndex: dragOverIndex,
        reason: 'Drop event never fired, using dragEnd as fallback'
      });
      
      // Manually call handleDrop with the current dragOverIndex
      setTimeout(() => {
        handleDrop(e, dragOverIndex);
      }, 0);
    }
    
    setDraggedComponent(null);
    setDragOverIndex(null);
    e.stopPropagation();
  };

  // Global drop handler to catch any missed drops
  const handleGlobalDrop = (e) => {
    console.log('🌍 Global Drop Event:', e.type);
    console.log('🌍 Global Drop Details:', {
      type: e.type,
      target: e.target.className,
      currentTarget: e.currentTarget.className,
      dataTransfer: e.dataTransfer?.effectAllowed,
      draggedComponent: draggedComponent?.name
    });
    e.preventDefault();
    e.stopPropagation();
  };

  // COMPREHENSIVE DRAG & DROP DIAGNOSTICS
  const runDragDropDiagnostics = () => {
    console.log('🔍 === DRAG & DROP DIAGNOSTICS ===');
    
    // Test 1: Check if draggedComponent state is properly set
    console.log('🧪 Test 1 - DraggedComponent State:', {
      draggedComponent: draggedComponent,
      isNull: draggedComponent === null,
      isUndefined: draggedComponent === undefined,
      hasName: draggedComponent?.name,
      hasType: draggedComponent?.type
    });
    
    // Test 2: Check if dragOverIndex is properly set
    console.log('🧪 Test 2 - DragOverIndex State:', {
      dragOverIndex: dragOverIndex,
      isNull: dragOverIndex === null,
      isUndefined: dragOverIndex === undefined,
      isNumber: typeof dragOverIndex === 'number'
    });
    
    // Test 3: Check rocketComponents array
    console.log('🧪 Test 3 - RocketComponents Array:', {
      length: rocketComponents.length,
      hasFins: rocketComponents.some(c => c.type === 'Fins'),
      finsComponents: rocketComponents.filter(c => c.type === 'Fins').map(f => ({id: f.id, name: f.name, attachedTo: f.attachedToComponent})),
      bodyComponents: rocketComponents.filter(c => ['Body Tube', 'Transition'].includes(c.type)).map(b => ({id: b.id, name: b.name, type: b.type}))
    });
    
    // Test 4: Check if event handlers are properly bound
    console.log('🧪 Test 4 - Event Handler Functions:', {
      handleDragStart: typeof handleDragStart,
      handleDragOver: typeof handleDragOver,
      handleDragLeave: typeof handleDragLeave,
      handleDrop: typeof handleDrop,
      handleDragEnd: typeof handleDragEnd
    });
    
    // Test 5: Check browser drag and drop support
    console.log('🧪 Test 5 - Browser Support:', {
      hasDataTransfer: 'DataTransfer' in window,
      hasDragEvent: 'DragEvent' in window,
      hasFileReader: 'FileReader' in window,
      userAgent: navigator.userAgent.includes('Chrome') ? 'Chrome' : navigator.userAgent.includes('Firefox') ? 'Firefox' : 'Other'
    });
    
    // Test 6: Check if preventDefault is working
    console.log('🧪 Test 6 - Event Prevention:', {
      note: 'This test requires manual drag operation to verify preventDefault is working'
    });
    
    // Test 7: Check if stopPropagation is working
    console.log('🧪 Test 7 - Event Propagation:', {
      note: 'This test requires manual drag operation to verify stopPropagation is working'
    });
    
    // Test 8: Check if dataTransfer is properly set
    console.log('🧪 Test 8 - DataTransfer Setup:', {
      note: 'This test requires manual drag operation to verify dataTransfer is working'
    });
    
    // Test 9: Check if drop zones are properly configured
    console.log('🧪 Test 9 - Drop Zone Configuration:', {
      note: 'This test requires manual drag operation to verify drop zones are working'
    });
    
    // Test 10: Check if React re-renders are interfering
    console.log('🧪 Test 10 - React Re-render Issues:', {
      note: 'This test requires manual drag operation to verify React is not interfering'
    });
    
    console.log('🔍 === END DIAGNOSTICS ===');
  };

  // Run diagnostics on component mount
  React.useEffect(() => {
    runDragDropDiagnostics();
  }, []);

  const drawRocketDiagram = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const rect = canvas.getBoundingClientRect();
    
    // Set canvas size to match display size with high DPI support
    const devicePixelRatio = window.devicePixelRatio || 1;
    canvas.width = rect.width * devicePixelRatio;
    canvas.height = rect.height * devicePixelRatio;
    canvas.style.width = rect.width + 'px';
    canvas.style.height = rect.height + 'px';
    
    // Scale context to match device pixel ratio
    ctx.scale(devicePixelRatio, devicePixelRatio);
    
    // Improve rendering quality
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';

    // Clear canvas
    ctx.clearRect(0, 0, rect.width, rect.height);
    
    // Apply zoom transformation
    ctx.save();
    ctx.translate(rect.width / 2, rect.height / 2);
    ctx.scale(zoom, zoom);
    ctx.translate(-rect.width / 2, -rect.height / 2);

    // Check if we have an imported STL rocket
    const stlRocket = rocketComponents.find(comp => comp.type === 'Imported Rocket');
    
    if (stlRocket) {
      // Draw STL rocket
      drawSTLRocket(ctx, stlRocket);
      return;
    }
    
    // Get body components only (for built rockets)
    const bodyComponents = rocketComponents.filter(comp => 
      ['Nose Cone', 'Body Tube', 'Transition', 'Rail Button', 'Motor'].includes(comp.type)
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
      } else if (component.type === 'Rail Button') {
        // Draw rail button as a small rectangular component
        const diameter = component.diameter || 20;
        const x = centerX - diameter / 2;
        
        ctx.fillStyle = '#8B4513';
        ctx.strokeStyle = '#654321';
        ctx.lineWidth = 2;
        ctx.fillRect(x, currentY, diameter, height);
        ctx.strokeRect(x, currentY, diameter, height);
        
        // Add rail button detail
        ctx.fillStyle = '#654321';
        const railWidth = component.railButtonWidth || 4;
        const railHeight = component.railButtonHeight || 8;
        const railX = centerX + diameter / 2 + (component.railButtonOffset || 2);
        const railY = currentY + height / 2 - railHeight / 2;
        
        ctx.fillRect(railX, railY, railWidth, railHeight);
        ctx.strokeRect(railX, railY, railWidth, railHeight);
        
        // Highlight if selected
        if (selectedComponent?.id === component.id) {
          ctx.strokeStyle = '#00FF00';
          ctx.lineWidth = 3;
          ctx.setLineDash([5, 5]);
          ctx.strokeRect(x, currentY, diameter, height);
          ctx.setLineDash([]);
        }
      } else if (component.type === 'Motor') {
        // Draw motor as a simple cylindrical component
        const diameter = component.diameter || 18;
        const x = centerX - diameter / 2;
        
        // Motor body (darker color to distinguish from body tubes)
        ctx.fillStyle = '#2C3E50';
        ctx.strokeStyle = '#1A252F';
        ctx.lineWidth = 2;
        ctx.fillRect(x, currentY, diameter, height);
        ctx.strokeRect(x, currentY, diameter, height);
        
        // Simple motor label
        ctx.fillStyle = '#FFFFFF';
        ctx.font = '10px Arial';
        ctx.textAlign = 'center';
        const motorModel = component.motorModel || 'Motor';
        ctx.fillText(motorModel, centerX, currentY + height / 2);
        
        // Highlight if selected
        if (selectedComponent?.id === component.id) {
          ctx.strokeStyle = '#00FF00';
          ctx.lineWidth = 3;
          ctx.setLineDash([5, 5]);
          ctx.strokeRect(x, currentY, diameter, height);
          ctx.setLineDash([]);
        }
      }

      currentY += height;
    });

    // Draw fins using parametric shape system
    const finComponents = rocketComponents.filter(comp => comp.type === 'Fins');
    if (finComponents.length > 0) {
      finComponents.forEach(finComponent => {
      const finShape = finComponent.finShape || 'rectangular';
      const finCount = Math.max(3, Math.min(8, finComponent.finCount || 4));
      const finHeight = Math.max(5, finComponent.finHeight || 25);
      const finWidth = Math.max(5, finComponent.finWidth || 15);
      const finThickness = Math.max(0.5, finComponent.finThickness || 2);
        const finOffset = finComponent.finOffset || 0; // Offset from bottom of attached component
      
      // Find the component that fins are attached to
      const attachedComponentId = finComponent.attachedToComponent;
      let attachedComponent = null;
      
      if (attachedComponentId) {
        attachedComponent = rocketComponents.find(comp => comp.id === attachedComponentId);
      }
      
      // If no specific attachment, find the last body tube
      if (!attachedComponent) {
        const bodyComponents = rocketComponents.filter(comp => 
          ['Nose Cone', 'Body Tube', 'Transition', 'Rail Button', 'Motor'].includes(comp.type)
        );
        if (bodyComponents.length === 0) return;
        attachedComponent = bodyComponents[bodyComponents.length - 1];
      }
      
      // Calculate position relative to the attached component
      const bodyComponents = rocketComponents.filter(comp => 
        ['Nose Cone', 'Body Tube', 'Transition', 'Rail Button', 'Motor'].includes(comp.type)
      );
      const totalHeight = bodyComponents.reduce((sum, comp) => sum + (comp.length || 60), 0);
      const startY = (canvas.height - totalHeight) / 2;
      
      // Find the position of the attached component
      let attachedComponentBottomY = startY + totalHeight; // Default to bottom of rocket
      let currentY = startY;
      
      for (const comp of bodyComponents) {
        const compHeight = comp.length || 60;
        if (comp.id === attachedComponent.id) {
          // Found the attached component - its bottom is currentY + compHeight
          attachedComponentBottomY = currentY + compHeight;
          break;
        }
        currentY += compHeight;
      }
      
      const bodyDiameter = attachedComponent.diameter || 20;
      const bodyRadius = bodyDiameter / 2;
    
      // Calculate fin position with offset from the bottom of the attached component
      // finY represents the CENTER of the fin horizontally extending from the body tube
      const finY = attachedComponentBottomY - finOffset;
      
      // Debug logging for fin positioning (reduced frequency)
      if (Math.random() < 0.1) { // Only log 10% of the time
        console.log('🎯 Fin Positioning Debug:', {
          finComponent: finComponent.name,
          attachedTo: attachedComponent.name,
          attachedComponentBottomY: attachedComponentBottomY,
          finOffset: finOffset,
          finalFinY: finY,
          startY: startY,
          totalHeight: totalHeight
        });
      }
        
        // Draw horizontal fins extending outward from the body tube
        // Only draw left and right fins (visible from side view)
    
    ctx.fillStyle = '#8B4513';
    ctx.strokeStyle = '#654321';
    ctx.lineWidth = 1;
    
        // Position fins centered on the attachment point
        const finTopY = finY - finHeight/2; // Top of fin
        const finBottomY = finY + finHeight/2; // Bottom of fin
        
        // Right fin (extends to the right)
        const rightFinStartX = centerX + bodyRadius;
        const rightFinEndX = centerX + bodyRadius + finWidth;
        
        ctx.beginPath();
        ctx.moveTo(rightFinStartX, finTopY);
        ctx.lineTo(rightFinEndX, finTopY);
        ctx.lineTo(rightFinEndX, finBottomY);
        ctx.lineTo(rightFinStartX, finBottomY);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
        
        // Left fin (extends to the left)
        const leftFinStartX = centerX - bodyRadius;
        const leftFinEndX = centerX - bodyRadius - finWidth;
        
        ctx.beginPath();
        ctx.moveTo(leftFinStartX, finTopY);
        ctx.lineTo(leftFinEndX, finTopY);
        ctx.lineTo(leftFinEndX, finBottomY);
        ctx.lineTo(leftFinStartX, finBottomY);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
      });
    }
    
    // Draw split lines if separation is enabled
    if (separationEnabled && splitPoint) {
      const splitComponent = rocketComponents.find(comp => comp.id === splitPoint);
      if (splitComponent) {
        // Find the Y position of the split point
        let splitY = startY;
        const bodyComponents = rocketComponents.filter(comp => 
          ['Nose Cone', 'Body Tube', 'Transition', 'Rail Button', 'Motor'].includes(comp.type)
        );
        
        for (const component of bodyComponents) {
          if (component.id === splitPoint) {
            // Draw split line at the bottom of this component
            splitY += component.length || 60;
            break;
          }
          splitY += component.length || 60;
        }
        
        // Draw separation line
        ctx.strokeStyle = '#FF0000';
        ctx.lineWidth = 3;
        ctx.setLineDash([10, 5]);
        
        // Draw horizontal line across the rocket
        const maxDiameter = Math.max(...bodyComponents.map(comp => comp.diameter || 20));
        const lineStartX = centerX - maxDiameter / 2 - 10;
        const lineEndX = centerX + maxDiameter / 2 + 10;
        
        ctx.beginPath();
        ctx.moveTo(lineStartX, splitY);
        ctx.lineTo(lineEndX, splitY);
        ctx.stroke();
        
        // Add "SEPARATION" label
        ctx.fillStyle = '#FF0000';
        ctx.font = 'bold 12px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('SEPARATION', centerX, splitY - 5);
        
        ctx.setLineDash([]);
      }
    }
    
    // Restore canvas context after zoom transformation
        ctx.restore();
  };





  // drawFins function removed - fins will not be displayed on the main screen

  // Parametric Shape System - Define points for each shape type
  const SHAPE_DEFINITIONS = {
    // Nose Cone Shapes
    'conical': {
      pointCount: 3,
      points: (length, diameter) => [
        { x: 0, y: 0 }, // Tip
        { x: diameter/2, y: length }, // Base right
        { x: -diameter/2, y: length }  // Base left
      ]
    },
    'ogive': {
      pointCount: 8,
      points: (length, diameter) => {
        const points = [];
        const radius = diameter/2;
        for (let i = 0; i < 8; i++) {
          const angle = (i * Math.PI) / 7; // 0 to π
          const x = radius * Math.cos(angle);
          const y = length * (1 - Math.cos(angle/2)); // Ogive curve
          points.push({ x, y });
        }
        return points;
      }
    },
    'parabolic': {
      pointCount: 6,
      points: (length, diameter) => {
        const points = [];
        const radius = diameter/2;
        for (let i = 0; i < 6; i++) {
          const t = i / 5; // 0 to 1
          const x = radius * (1 - t);
          const y = length * t * t; // Parabolic curve
          points.push({ x, y });
        }
        return points;
      }
    },

    // Body Tube Shapes
    'cylinder': {
      pointCount: 4,
      points: (length, diameter) => [
        { x: -diameter/2, y: 0 }, // Top left
        { x: diameter/2, y: 0 },  // Top right
        { x: diameter/2, y: length }, // Bottom right
        { x: -diameter/2, y: length }  // Bottom left
      ]
    },

    // Transition Shapes
    'conical_transition': {
      pointCount: 4,
      points: (length, topDiameter, bottomDiameter) => [
        { x: -topDiameter/2, y: 0 }, // Top left
        { x: topDiameter/2, y: 0 },  // Top right
        { x: bottomDiameter/2, y: length }, // Bottom right
        { x: -bottomDiameter/2, y: length }  // Bottom left
      ]
    },
    'curved_transition': {
      pointCount: 6,
      points: (length, topDiameter, bottomDiameter) => {
        const points = [];
        const topRadius = topDiameter/2;
        const bottomRadius = bottomDiameter/2;
        for (let i = 0; i < 6; i++) {
          const t = i / 5; // 0 to 1
          const radius = topRadius + (bottomRadius - topRadius) * t;
          const x = radius;
          const y = length * t;
          points.push({ x, y });
          if (i > 0) points.push({ x: -radius, y: length * t });
        }
        return points;
      }
    },

    // Fin Shapes - All oriented to extend outward from rocket body
    'rectangular_fin': {
      pointCount: 4,
      points: (height, width, thickness) => [
        { x: 0, y: 0 }, // Root leading edge (attached to rocket)
        { x: width, y: 0 }, // Tip leading edge
        { x: width, y: height }, // Tip trailing edge
        { x: 0, y: height }  // Root trailing edge
      ]
    },
    'trapezoidal_fin': {
      pointCount: 4,
      points: (height, rootWidth, tipWidth, thickness) => [
        { x: 0, y: 0 }, // Root leading edge (attached to rocket)
        { x: tipWidth, y: 0 }, // Tip leading edge (narrower)
        { x: tipWidth, y: height }, // Tip trailing edge
        { x: rootWidth, y: height }  // Root trailing edge (wider)
      ]
    },
    'elliptical_fin': {
      pointCount: 12,
      points: (height, width, thickness) => {
        const points = [];
        const a = width/2; // Semi-major axis (horizontal)
        const b = height/2; // Semi-minor axis (vertical)
        for (let i = 0; i < 12; i++) {
          const angle = (i * Math.PI) / 11; // 0 to π
          const x = a * Math.cos(angle);
          const y = b * Math.sin(angle);
          points.push({ x, y });
        }
        return points;
      }
    },
    'delta_fin': {
      pointCount: 3,
      points: (height, width, thickness) => [
        { x: 0, y: 0 }, // Root leading edge (attached to rocket)
        { x: width, y: 0 }, // Tip leading edge
        { x: width/2, y: height }  // Trailing edge center (pointed)
      ]
    }
  };

  // Function to draw any parametric shape
  const drawParametricShape = (ctx, shapeType, variables, position = {x: 0, y: 0}, color = '#8B4513') => {
    const shapeDef = SHAPE_DEFINITIONS[shapeType];
    if (!shapeDef) {
      console.error(`Unknown shape type: ${shapeType}`);
      return;
    }

    const points = shapeDef.points(...variables);
        
        ctx.save();
    ctx.translate(position.x, position.y);
    ctx.fillStyle = color;
    ctx.strokeStyle = '#654321';
    ctx.lineWidth = 1;
    
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    for (let i = 1; i < points.length; i++) {
      ctx.lineTo(points[i].x, points[i].y);
    }
    ctx.closePath();
    
    ctx.fill();
    ctx.stroke();
        ctx.restore();
  };

  // Function to get shape variables from component
  const getShapeVariables = (component) => {
    switch (component.type) {
      case 'Nose Cone':
        return [component.length || 60, component.diameter || 20];
      case 'Body Tube':
        return [component.length || 60, component.diameter || 20];
      case 'Transition':
        return [component.length || 30, component.diameter || 20, component.bottomDiameter || 15];
      case 'Fins':
        return [component.finHeight || 25, component.finWidth || 15, component.finThickness || 2];
      default:
        return [];
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
        [`${selectedComponent.id}-material`]: selectedComponent.material || 'carbon_fiber',
        [`${selectedComponent.id}-attachedToComponent`]: selectedComponent.attachedToComponent || ''
      }));
    }
  }, [selectedComponent]);

  const handleCanvasClick = (event) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    console.log('🖱️ Canvas click detected - zoom level:', zoom);
    
    const rect = canvas.getBoundingClientRect();
    let x = event.clientX - rect.left;
    let y = event.clientY - rect.top;
    
    console.log('🖱️ Raw click coordinates:', { x, y });
    
    // Transform coordinates to account for zoom
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    
    // Apply inverse zoom transformation
    x = (x - centerX) / zoom + centerX;
    y = (y - centerY) / zoom + centerY;
    
    console.log('🖱️ Transformed coordinates:', { x, y, zoom });

    const bodyComponents = rocketComponents.filter(comp => 
      ['Nose Cone', 'Body Tube', 'Transition'].includes(comp.type)
    );

    if (bodyComponents.length === 0) return;

    const totalHeight = bodyComponents.reduce((sum, comp) => sum + (comp.length || 60), 0);
    const startY = (rect.height - totalHeight) / 2;

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
    <div 
      className="app-container"
      onDrop={handleGlobalDrop}
      onDragOver={(e) => e.preventDefault()}
      onMouseUp={(e) => {
        // Reduced logging - only log on specific events
        if (e.target.classList.contains('component') || e.target.closest('.component')) {
          console.log('🌍 Global Mouse Up on component');
        }
      }}
    >
      {/* Custom Notifications */}
      <div className="notifications-container">
        {notifications.map(notification => (
          <div 
            key={notification.id} 
            className={`notification notification-${notification.type}`}
            onClick={() => removeNotification(notification.id)}
          >
            <div className="notification-content">
              <span className="notification-message">{notification.message}</span>
              <button className="notification-close">&times;</button>
            </div>
          </div>
        ))}
      </div>
      
      <nav className="tabs-nav">
        <button 
          className={`tab-button ${activeTab === 'builder' ? 'active' : ''}`}
          onClick={() => switchTab('builder')}
        >
          Rocket Builder
        </button>
        <button 
          className={`tab-button ${activeTab === 'setup' ? 'active' : ''}`}
          onClick={() => switchTab('setup')}
        >
          Simulation Setup
        </button>
        <button 
          className={`tab-button ${activeTab === 'control' ? 'active' : ''}`}
          onClick={() => switchTab('control')}
        >
          Control Code
        </button>
        <button 
          className={`tab-button ${activeTab === 'simulation' ? 'active' : ''}`}
          onClick={() => switchTab('simulation')}
        >
          Simulation Run
        </button>
        <button 
          className={`tab-button ${activeTab === 'results' ? 'active' : ''}`}
          onClick={() => switchTab('results')}
        >
          Results
        </button>
      </nav>

      <main className="main-content">
        {activeTab === 'simulation' && (
          <div key="simulation" className={`simulation-run-container tab-content slide-in-${tabDirection}`}>
            {!simulationRunning ? (
              <div className="simulation-ready">
                <div className="launch-header">
                  <h1>🚀 Ready to Launch</h1>
                  <p>Your rocket is configured and ready for CFD analysis</p>
            </div>
            
                    <button 
                  className="launch-button"
                      onClick={startSimulation}
                    >
                  <span className="button-icon">🚀</span>
                  <span className="button-text">Start Simulation</span>
                    </button>
                    
                    <button 
                      onClick={runAllStatusChecks}
                      className="debug-status-btn"
                      style={{
                        marginLeft: '10px',
                        padding: '8px 16px',
                        backgroundColor: '#6366f1',
                        color: 'white',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '12px'
                      }}
                    >
                      🔍 Check System Status
                    </button>
                
                <div className="simulation-info">
                  <div className="info-item">
                    <span className="info-icon">⏱️</span>
                    <span>Expected duration: 5-15 minutes</span>
                </div>
                </div>
                </div>
            ) : (
              <div className="simulation-running">
                <div className="loading-animation">
                  <div className="rocket-loader">
                    <div className="rocket">🚀</div>
                    <div className="trail"></div>
              </div>
            </div>
            
                <div className="simulation-status">
                  <h2>{simulationStatus?.status || 'Initializing...'}</h2>
                  <p>{simulationStatus?.message || 'Setting up simulation environment...'}</p>
              </div>
              
                <div className="progress-container">
                  <div className="progress-bar">
                    <div 
                      className="progress-fill" 
                      style={{ width: `${simulationStatus?.progress || 0}%` }}
                    ></div>
                  </div>
                  <div className="progress-text">
                    {simulationStatus?.progress || 0}% Complete
              </div>
            </div>
            
                <div className="simulation-details">
                  <div className="detail-item">
                    <span className="detail-label">Status:</span>
                    <span className="detail-value">{simulationStatus?.status || 'Initializing'}</span>
                  </div>
                  {simulationStatus?.iteration_count && (
                    <div className="detail-item">
                      <span className="detail-label">Iterations:</span>
                      <span className="detail-value">{simulationStatus.iteration_count}</span>
                    </div>
                  )}
                  {simulationStatus?.cell_count && (
                    <div className="detail-item">
                      <span className="detail-label">Mesh Cells:</span>
                      <span className="detail-value">{simulationStatus.cell_count.toLocaleString()}</span>
                    </div>
                  )}
                    </div>
                
                <button 
                  className="stop-button"
                  onClick={stopSimulation}
                >
                  <span className="button-icon">⏹️</span>
                  <span className="button-text">Stop Simulation</span>
                </button>
              </div>
            )}
          </div>
        )}
        
        {activeTab === 'builder' && (
          <div key="builder" className={`rocket-builder-layout tab-content slide-in-${tabDirection}`}>
            {/* Left Panel - Rocket Structure & Properties */}
            <div className="left-panel">
              <div className="structure-section">
                <div className="panel-header">
                  <h3>Rocket Structure</h3>
                  <button 
                    className="add-split-btn"
                    onClick={() => {
                      console.log('Adding split point');
                      // Find body tubes and transitions for split point selection
                      const bodyComponents = rocketComponents.filter(comp => 
                        ['Body Tube', 'Transition'].includes(comp.type)
                      );
                      
                      if (bodyComponents.length < 2) {
                        showNotification('Need at least 2 body components to add a split point', 'warning');
                        return;
                      }
                      
                      // Show split point selection modal or dropdown
                      const splitOptions = bodyComponents.map((comp, index) => ({
                        id: comp.id,
                        name: `${comp.name} (${comp.type})`,
                        position: index
                      }));
                      
                      console.log('Available split points:', splitOptions);
                      showNotification('Split point functionality ready - select a component to split at', 'info');
                    }}
                    style={{
                      padding: '4px 8px',
                      fontSize: '12px',
                      backgroundColor: '#ef4444',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    Add Split
                  </button>
                </div>
                
                {/* Rocket Properties Panel - Moved up for better visibility */}
                <div className="properties-section expanded" style={{ marginTop: '10px', marginBottom: '10px', border: '1px solid #e5e7eb', borderRadius: '8px', backgroundColor: 'rgba(255, 255, 255, 0.95)' }}>
                  <div className="panel-header" style={{ backgroundColor: 'rgba(255, 255, 255, 0.9)', color: '#374151' }}>
                    <h3>🚀 Rocket Properties</h3>
                  </div>
                  <div className="property-fields">
                    <div className="property-field">
                      <label>Total Mass (g):</label>
                      <input 
                        type="number" 
                        value={rocketWeight}
                        onChange={(e) => setRocketWeight(e.target.value === '' ? 0 : parseFloat(e.target.value) || 0)}
                        placeholder="Enter mass"
                        min="0"
                        step="0.1"
                      />
                    </div>
                    
                    <div className="property-field">
                      <label>Center of Gravity (cm):</label>
                      <div className="cg-input-group">
                        <input 
                          type="number" 
                          value={rocketCG}
                          onChange={(e) => setRocketCG(e.target.value === '' ? 0 : parseFloat(e.target.value) || 0)}
                          placeholder="Enter CG"
                          min="0"
                          step="0.1"
                        />
                        <div className="cg-reference-toggle">
                          <label className="toggle-label">
                            <input 
                              type="checkbox" 
                              checked={cgFromNose}
                              onChange={(e) => setCgFromNose(e.target.checked)}
                            />
                            From nose
                          </label>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="component-tree" key={rocketComponents.map(c => `${c.id}-${c.attachedToComponent}`).join('-')}>
                  <div className="tree-item">
                    <span className="tree-label">Rocket</span>
                  </div>
                  {/* Render body components first, then show their attached fins and motors */}
                  {rocketComponents.filter(comp => 
                    ['Nose Cone', 'Body Tube', 'Transition', 'Rail Button'].includes(comp.type)
                  ).map((component, index) => {
                    // Check if this component has fins attached to it
                    const attachedFins = rocketComponents.filter(comp => 
                      comp.type === 'Fins' && comp.attachedToComponent === component.id
                    );
                    if (attachedFins.length > 0) {
                      console.log(`🔗 ${component.name} has ${attachedFins.length} attached fins`);
                    }
                    
                    // Check if this component has motors attached to it
                    const attachedMotors = rocketComponents.filter(comp => 
                      comp.type === 'Motor' && comp.attachedToComponent === component.id
                    );
                    if (attachedMotors.length > 0) {
                      console.log(`🚀 ${component.name} has ${attachedMotors.length} attached motors`);
                    }

                    

                    
                    return (
                      <div key={component.id}>
                        <div 
                          className={`tree-item ${selectedComponent?.id === component.id ? 'selected' : ''} ${draggedComponent?.id === component.id ? 'dragging' : ''} ${dragOverIndex === index ? (draggedComponent?.type === 'Fins' && ['Body Tube', 'Transition'].includes(component.type) ? 'dragover connectable' : 'dragover') : ''}`}
                          style={{ 
                            cursor: draggedComponent?.type === 'Fins' && ['Body Tube', 'Transition'].includes(component.type) ? 'copy' : 'grab',
                            backgroundColor: dragOverIndex === index && draggedComponent?.type === 'Fins' ? 'rgba(0, 255, 0, 0.2)' : 'transparent',
                            border: '2px solid transparent',
                            position: 'relative',
                            minHeight: '40px'
                          }}
                          onClick={() => setSelectedComponent(component)}
                          onMouseEnter={() => setHoveredComponent(component.id)}
                          onMouseLeave={() => setHoveredComponent(null)}
                          draggable
                          onDragStart={(e) => handleDragStart(e, component)}
                          onDragOver={(e) => {
                            console.log('🔄 Component DragOver:', component.name, 'index', index);
                            e.preventDefault(); // This is crucial for drop zones to work!
                            e.stopPropagation();
                            
                            // Set drop effect based on component type
                            if (draggedComponent?.type === 'Fins' && ['Body Tube', 'Transition'].includes(component.type)) {
                              e.dataTransfer.dropEffect = 'copy'; // Show copy effect for connecting fins
                            } else {
                              e.dataTransfer.dropEffect = 'move'; // Show move effect for reordering
                            }
                            
                            handleDragOver(e, index);
                          }}
                          onDragLeave={handleDragLeave}
                          onDrop={(e) => {
                            console.log('🎯 DROP EVENT FIRED on', component.name, 'index', index);
                            console.log('🎯 Drop event details:', {
                              type: e.type,
                              target: e.target.className,
                              currentTarget: e.currentTarget.className,
                              dataTransfer: e.dataTransfer?.effectAllowed
                            });
                            e.preventDefault();
                            e.stopPropagation();
                            handleDrop(e, index);
                          }}
                          onDragEnd={(e) => {
                            console.log('🎯 Component DragEnd on', component.name, 'index', index);
                            e.preventDefault();
                            e.stopPropagation();
                            handleDragEnd(e);
                          }}
                          onDragEnter={(e) => {
                            console.log('🚪 DragEnter:', component.name, 'index', index);
                            e.preventDefault();
                            e.stopPropagation();
                          }}
                          onMouseUp={(e) => {
                            console.log('🖱️ Mouse Up on', component.name, 'index', index);
                            console.log('🖱️ Mouse Up Details:', {
                              type: e.type,
                              target: e.target.className,
                              currentTarget: e.currentTarget.className,
                              draggedComponent: draggedComponent?.name
                            });
                          }}
                          data-drop-target="true"
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
                            onClick={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                              handleComponentClick(fin, false);
                            }}
                            onDoubleClick={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                              handleComponentClick(fin, true);
                            }}
                            onMouseEnter={() => setHoveredComponent(fin.id)}
                            onMouseLeave={() => setHoveredComponent(null)}
                            // Temporarily disable dragging to test double-click
                            // draggable
                            // onDragStart={(e) => handleDragStart(e, fin)}
                            // onDragEnd={handleDragEnd}
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
                        
                        {/* Show attached motors as sub-items */}
                        {attachedMotors.map((motor, motorIndex) => (
                          <div 
                            key={motor.id}
                            className={`tree-item sub-item ${selectedComponent?.id === motor.id ? 'selected' : ''} ${draggedComponent?.id === motor.id ? 'dragging' : ''}`}
                            onClick={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                              handleComponentClick(motor, false);
                            }}
                            onDoubleClick={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                              handleComponentClick(motor, true);
                            }}
                            onMouseEnter={() => setHoveredComponent(motor.id)}
                            onMouseLeave={() => setHoveredComponent(null)}
                          >
                            <span className="tree-arrow">🚀</span>
                            <span className="tree-label">{motor.name}</span>
                            {hoveredComponent === motor.id && (
                              <button 
                                className="delete-btn"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  deleteComponent(motor.id);
                                }}
                                title="Delete motor"
                              >
                                ×
                              </button>
                            )}
                          </div>
                        ))}

                      </div>
                    );
                  })}
                  
                  {/* Show any unattached fins at the bottom */}
                  {rocketComponents.filter(comp => 
                    comp.type === 'Fins' && !comp.attachedToComponent
                  ).map((component, index) => (
                    <div 
                      key={component.id}
                      className={`tree-item ${selectedComponent?.id === component.id ? 'selected' : ''} ${draggedComponent?.id === component.id ? 'dragging' : ''}`}
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        handleComponentClick(component, false);
                      }}
                      onDoubleClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        handleComponentClick(component, true);
                      }}
                      onMouseEnter={() => setHoveredComponent(component.id)}
                      onMouseLeave={() => setHoveredComponent(null)}
                      // Temporarily disable dragging to test double-click
                      // draggable
                      // onDragStart={(e) => handleDragStart(e, component)}
                                                onDragOver={(e) => {
                            // For unattached fins, allow dropping on any body component
                            const bodyComponents = rocketComponents.filter(comp => 
                              ['Body Tube', 'Transition'].includes(comp.type)
                            );
                            if (bodyComponents.length > 0) {
                              handleDragOver(e, bodyComponents.length - 1); // Drop on last body component
                            }
                          }}
                          onDragLeave={handleDragLeave}
                          onDrop={(e) => {
                            // For unattached fins, drop on last body component
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
                              <label>Fin Material:</label>
                              <select 
                                value={inputValues[`${selectedComponent.id}-material`] || selectedComponent.material || 'carbon_fiber'} 
                                onChange={(e) => {
                                  setInputValues(prev => ({
                                    ...prev,
                                    [`${selectedComponent.id}-material`]: e.target.value
                                  }));
                                  updateComponent(selectedComponent.id, 'material', e.target.value);
                                }}
                              >
                                <option value="carbon_fiber">Carbon Fiber (1.6 g/cm³)</option>
                                <option value="fiberglass">Fiberglass (1.8 g/cm³)</option>
                                <option value="aluminum">Aluminum (2.7 g/cm³)</option>
                                <option value="balsa">Balsa Wood (0.12 g/cm³)</option>
                                <option value="plywood">Plywood (0.6 g/cm³)</option>
                                <option value="plastic">Plastic (1.2 g/cm³)</option>
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
                            <div className="config-field">
                              <label>Fin Offset (cm):</label>
                              <input 
                                type="text" 
                                value={inputValues[`${selectedComponent.id}-finOffset`] || '0'}
                                onChange={(e) => handleNumberInput(selectedComponent.id, 'finOffset', e.target.value)}
                                placeholder="Enter offset from bottom"
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

                            {/* Active Fins Configuration */}
                            <div className="config-section">
                              <h4>Active Fins</h4>
                              <div className="config-field">
                                <label>Enable Active Control:</label>
                                {console.log('🔍 Rendering Active Fins Checkbox:', {
                                  selectedComponent: selectedComponent?.name,
                                  activeFinsEnabled: selectedComponent?.activeFinsEnabled,
                                  componentId: selectedComponent?.id
                                })}
                                <input 
                                  type="checkbox" 
                                  checked={selectedComponent.activeFinsEnabled || false}
                                  onChange={(e) => {
                                    console.log('🔘 Active Fins Checkbox Clicked:', e.target.checked);
                                    console.log('🔘 Checkbox Event Details:', {
                                      type: e.type,
                                      target: e.target.type,
                                      checked: e.target.checked,
                                      componentId: selectedComponent.id
                                    });
                                    updateComponent(selectedComponent.id, 'activeFinsEnabled', e.target.checked);
                                  }}
                                  onClick={(e) => {
                                    console.log('🔘 Active Fins Checkbox onClick:', e.target.checked);
                                    e.stopPropagation();
                                  }}
                                />
                              </div>
                              
                              {selectedComponent.activeFinsEnabled && (
                                <>
                                  <div className="config-field">
                                    <label>Motor Power (W):</label>
                                    <input 
                                      type="text" 
                                      value={inputValues[`${selectedComponent.id}-motorPower`] || selectedComponent.motorPower || '50'}
                                      onChange={(e) => handleNumberInput(selectedComponent.id, 'motorPower', e.target.value)}
                                      placeholder="Enter motor power"
                                    />
                                  </div>
                                  
                                  <div className="config-field">
                                    <label>Max Deflection Angle (°):</label>
                                    <input 
                                      type="text" 
                                      value={inputValues[`${selectedComponent.id}-maxDeflectionAngle`] || selectedComponent.maxDeflectionAngle || '15'}
                                      onChange={(e) => handleNumberInput(selectedComponent.id, 'maxDeflectionAngle', e.target.value)}
                                      placeholder="Enter max angle"
                                    />
                                  </div>
                                  
                                  <div className="config-field">
                                    <label>Response Speed (Hz):</label>
                                    <input 
                                      type="text" 
                                      value={inputValues[`${selectedComponent.id}-responseSpeed`] || selectedComponent.responseSpeed || '10'}
                                      onChange={(e) => handleNumberInput(selectedComponent.id, 'responseSpeed', e.target.value)}
                                      placeholder="Enter response frequency"
                                    />
                                  </div>
                                  
                                </>
                              )}
                            </div>
                          </>
                        ) : selectedComponent.type === 'Rail Button' ? (
                          <>
                            <div className="config-field">
                              <label>Length (cm):</label>
                              <input 
                                type="text" 
                                value={inputValues[`${selectedComponent.id}-length`] !== undefined ? inputValues[`${selectedComponent.id}-length`] : selectedComponent.length}
                                onChange={(e) => handleNumberInput(selectedComponent.id, 'length', e.target.value)}
                                placeholder="Enter length"
                              />
                            </div>
                            <div className="config-field">
                              <label>Diameter (cm):</label>
                              <input 
                                type="text" 
                                value={inputValues[`${selectedComponent.id}-diameter`] !== undefined ? inputValues[`${selectedComponent.id}-diameter`] : selectedComponent.diameter}
                                onChange={(e) => handleNumberInput(selectedComponent.id, 'diameter', e.target.value)}
                                placeholder="Enter diameter"
                              />
                            </div>
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
                          </>
                        ) : selectedComponent.type === 'Motor' ? (
                          <>
                            <div className="config-field">
                              <label>Motor Model:</label>
                              <input 
                                type="text"
                                value={selectedComponent.motorModel || ''}
                                onChange={(e) => updateComponent(selectedComponent.id, 'motorModel', e.target.value)}
                                placeholder="Enter motor model"
                              />
                            </div>
                            <div className="config-field">
                              <label>Motor Type:</label>
                              <input 
                                type="text"
                                value={selectedComponent.motorType || ''}
                                onChange={(e) => updateComponent(selectedComponent.id, 'motorType', e.target.value)}
                                placeholder="Enter motor type"
                              />
                            </div>
                            <div className="config-field">
                              <label>Thrust (N):</label>
                              <input 
                                type="number"
                                value={selectedComponent.motorThrust || ''}
                                onChange={(e) => updateComponent(selectedComponent.id, 'motorThrust', parseFloat(e.target.value) || 0)}
                                placeholder="Enter thrust"
                              />
                            </div>
                            <div className="config-field">
                              <label>Burn Time (s):</label>
                              <input 
                                type="number"
                                value={selectedComponent.motorBurnTime || ''}
                                onChange={(e) => updateComponent(selectedComponent.id, 'motorBurnTime', parseFloat(e.target.value) || 0)}
                                placeholder="Enter burn time"
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
                        <button className="component-btn" onClick={() => addComponent('Rail Button')}>
                          <div className="component-icon rail-button"></div>
                          Rail Button
                        </button>
                      </div>
                    </div>
                    
                    <div className="category">
                      <h4>Fins</h4>
                      <div className="component-grid">
                        <button className="component-btn" onClick={() => addComponent('Fins')}>
                          <div className="component-icon fins"></div>
                          Fins
                        </button>
                        <button className="component-btn import-btn" onClick={() => finFileInputRef.current.click()}>
                          <div className="component-icon import-icon"></div>
                          Import Fins
                        </button>
                        <input
                          ref={finFileInputRef}
                          type="file"
                          accept=".stl,.dxf"
                          onChange={importFins}
                          style={{ display: 'none' }}
                        />
                      </div>
                    </div>
                    
                    <div className="category">
                      <h4>Motors</h4>
                      <div className="component-grid">
                        <button className="component-btn" onClick={() => {
                          console.log('🔧 Motor button clicked - opening search modal');
                          console.log('🔍 Current showMotorSearch state:', showMotorSearch);
                          setShowMotorSearch(true);
                          console.log('🔍 Set showMotorSearch to true');
                        }}>
                          <div className="component-icon motor"></div>
                          Motor
                        </button>
                      </div>
                    </div>
                    
                    <div className="category">
                      <div className="component-grid full-width">
                        <button className="component-btn stl-import-btn full-width-btn" onClick={() => fileInputRef.current.click()}>
                          <div className="component-icon stl-icon"></div>
                          Import STL
                        </button>
                        <input
                          ref={fileInputRef}
                          type="file"
                          accept=".stl"
                          onChange={importSTL}
                          style={{ display: 'none' }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
        
        {activeTab === 'setup' && (
          <div key="setup" className={`tab-content slide-in-${tabDirection}`}>
            {/* Weather Condition Presets */}
            <div className="preset-configs">
              <h3>Weather Conditions</h3>
              <div className="preset-buttons">
                <button 
                  className="preset-btn sunny" 
                  onClick={() => loadPresetConfig('sunny')}
                  onMouseEnter={() => showWeatherInfo('sunny')}
                  onMouseLeave={() => hideWeatherInfo()}
                  title="Click to load sunny day configuration"
                >
                  ☀️ Sunny Day
                </button>
                <button 
                  className="preset-btn rainy" 
                  onClick={() => loadPresetConfig('rainy')}
                  onMouseEnter={() => showWeatherInfo('rainy')}
                  onMouseLeave={() => hideWeatherInfo()}
                  title="Click to load rainy day configuration"
                >
                  🌧️ Rainy Day
                </button>
                <button 
                  className="preset-btn windy" 
                  onClick={() => loadPresetConfig('windy')}
                  onMouseEnter={() => showWeatherInfo('windy')}
                  onMouseLeave={() => hideWeatherInfo()}
                  title="Click to load high wind configuration"
                >
                  💨 High Wind
                </button>
                <button 
                  className="preset-btn stormy" 
                  onClick={() => loadPresetConfig('stormy')}
                  onMouseEnter={() => showWeatherInfo('stormy')}
                  onMouseLeave={() => hideWeatherInfo()}
                  title="Click to load stormy weather configuration"
                >
                  ⛈️ Stormy Weather
                </button>
              </div>
            </div>
            
            {/* Configuration Management */}
            <div className="config-management">
              <div className="config-actions">
                <button className="config-btn save" onClick={saveSimulationConfig}>
                  Save Config
                </button>
                <button className="config-btn load" onClick={loadSimulationConfig}>
                  Load Config
                </button>
                <button className="config-btn reset" onClick={resetSimulationConfig}>
                  Reset to Defaults
                </button>
              </div>
              <input
                type="file"
                accept=".json"
                onChange={handleConfigFileLoad}
                style={{ display: 'none' }}
                ref={configFileInputRef}
              />
            </div>
            
            {/* Frequently Changed Variables */}
            <div className="frequent-variables">
              <h3>Frequent Variables</h3>
              <div className="variables-grid">
                <div className="variable-group">
                  <label>Launch Altitude (m):</label>
                  <input 
                    type="number"
                    value={simulationConfig.launchAltitude} 
                    onChange={(e) => updateSimulationConfig('launchAltitude', parseFloat(e.target.value))}
                    step="10"
                    min="0"
                    max="10000"
                  />
                </div>

                <div className="variable-group">
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
                
                <div className="variable-group">
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
                
                <div className="variable-group">
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

                <div className="variable-group">
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
            
                <div className="variable-group">
                  <label>Active Fin Control:</label>
                        <select 
                    value={simulationConfig.activeFinControl} 
                    onChange={(e) => updateSimulationConfig('activeFinControl', e.target.value)}
                  >
                    <option value="disabled">Disabled</option>
                    <option value="enabled">Enabled</option>
                    <option value="test">Test Mode</option>
                        </select>
                      </div>
                      
                      </div>
                    </div>

                  </div>
                )}
        
        {activeTab === 'control' && (
          <div key="control" className={`tab-content slide-in-${tabDirection}`}>
            <h2>Active Fin Control System</h2>
            
            {/* Control System Status */}
            <div className="control-status">
              <div className="status-indicator">
                <span className={`status-dot ${simulationConfig.activeFinControl === 'enabled' ? 'active' : 'inactive'}`}></span>
                <span>Control System: {simulationConfig.activeFinControl === 'enabled' ? 'ACTIVE' : 'INACTIVE'}</span>
                </div>
              <div className="control-params">
                <span>Update Rate: {simulationConfig.controlUpdateRate} Hz</span>
                <span>CFD Time Step: {simulationConfig.cfdTimeStep}s</span>
                <span>Fin Limit: ±{simulationConfig.finDeflectionLimit}°</span>
                      </div>
                      </div>
                      
            {/* Control Code Editor */}
            <div className="control-code-section">
              <h3>Control Algorithm</h3>
              <div className="code-editor-container">
                <textarea
                  className="control-code-editor"
                  value={simulationConfig.controlCode}
                  onChange={(e) => updateSimulationConfig('controlCode', e.target.value)}
                  placeholder="// Active Fin Control Algorithm
// This code runs in real-time during CFD simulation
// Available variables: attitude, velocity, position, target_trajectory
// Output: fin_deflections (array of 4 fin angles in degrees)

function calculateFinDeflections(cfdData, targetTrajectory) {
    // Extract CFD feedback data
    const attitude = cfdData.attitude;        // [roll, pitch, yaw] in degrees
    const velocity = cfdData.velocity;        // [vx, vy, vz] in m/s
    const position = cfdData.position;        // [x, y, z] in meters
    const angularVelocity = cfdData.angularVelocity; // [wx, wy, wz] in rad/s
    
    // Target trajectory
    const targetPitch = targetTrajectory.pitch;
    const targetYaw = targetTrajectory.yaw;
    
    // Control gains
    const kp = 1.0;  // Proportional gain
    const ki = 0.1;  // Integral gain  
    const kd = 0.05; // Derivative gain
    
    // Calculate errors
    const pitchError = targetPitch - attitude[1];
    const yawError = targetYaw - attitude[2];
    
    // PID control for pitch (fins 1&3)
    const pitchControl = kp * pitchError + ki * integralError + kd * derivativeError;
    
    // PID control for yaw (fins 2&4)  
    const yawControl = kp * yawError + ki * integralError + kd * derivativeError;
    
    // Calculate fin deflections (4 fins)
    const finDeflections = [
        pitchControl,  // Fin 1 (top)
        yawControl,    // Fin 2 (right)
        -pitchControl, // Fin 3 (bottom) 
        -yawControl    // Fin 4 (left)
    ];
    
    // Apply deflection limits
    const maxDeflection = 15; // degrees
    for (let i = 0; i < finDeflections.length; i++) {
        finDeflections[i] = Math.max(-maxDeflection, Math.min(maxDeflection, finDeflections[i]));
    }
    
    return finDeflections;
}"
                  rows={25}
                  cols={80}
                        />
                      </div>
                      
              <div className="control-actions">
                <button 
                  className="btn btn-primary"
                  onClick={() => updateActiveFinControlConfig(simulationConfig)}
                >
                  Save Control Code
                </button>
                <button 
                  className="btn btn-secondary"
                  onClick={() => testControlAlgorithm({
                    attitude: [0, 5, 0], // 5 degree pitch error
                    velocity: [0, 0, 0],
                    position: [0, 0, 0],
                    angular_velocity: [0, 0, 0],
                    target_trajectory: {pitch: 0, yaw: 0}
                  })}
                >
                  Test Algorithm
                </button>
                <button 
                  className="btn btn-success"
                  onClick={startActiveFinControl}
                >
                  Start Co-Simulation
                </button>
                      </div>
                      </div>
                      
            {/* Real-time Feedback Display */}
            <div className="feedback-display">
              <h3>Real-time CFD Feedback</h3>
              <div className="feedback-grid">
                <div className="feedback-item">
                  <label>Attitude (deg):</label>
                  <span id="attitude-display">Roll: 0.0, Pitch: 0.0, Yaw: 0.0</span>
                      </div>
                <div className="feedback-item">
                  <label>Velocity (m/s):</label>
                  <span id="velocity-display">Vx: 0.0, Vy: 0.0, Vz: 0.0</span>
                    </div>
                <div className="feedback-item">
                  <label>Fin Deflections (deg):</label>
                  <span id="fin-display">Fin1: 0.0, Fin2: 0.0, Fin3: 0.0, Fin4: 0.0</span>
                  </div>
                <div className="feedback-item">
                  <label>Control Error:</label>
                  <span id="error-display">Pitch: 0.0°, Yaw: 0.0°</span>
              </div>
                </div>
                      </div>
            <p>Content will go here...</p>
                      </div>
        )}
        
        {activeTab === 'results' && (
          <div key="results" className={`results-container tab-content slide-in-${tabDirection}`} style={{ maxHeight: 'calc(100vh - 120px)', overflowY: 'auto' }}>
            <div className="results-header" style={{ padding: '10px 20px', marginBottom: '10px' }}>
              <h1 style={{ margin: '0 0 5px 0', fontSize: '24px' }}>📊 Simulation Results</h1>
              {simulationResults ? (
                <p style={{ margin: '0', fontSize: '14px', color: '#666' }}>Analysis and visualization of your rocket's performance</p>
              ) : (
                <p style={{ margin: '0', fontSize: '14px', color: '#666' }}>Run a simulation to see results</p>
              )}
            </div>
                      
            <div className="results-grid">
              {/* Performance Overview */}
              <div className="results-section performance-overview">
                <div className="section-header">
                  <h2>🚀 Performance Overview</h2>
                  <div className="section-status">
                    <span className="status-indicator">{simulationResults ? 'Completed' : 'No Data'}</span>
                      </div>
                    </div>
                <div className="performance-metrics">
                  <div className="metric-card">
                    <div className="metric-icon">🚀</div>
                    <div className="metric-content">
                      <h3>Max Altitude</h3>
                      <div className="metric-value">{simulationResults?.results ? `${Math.round(simulationResults.results.max_altitude || 0)} m` : '-- m'}</div>
                      <div className="metric-label">Peak flight height</div>
                  </div>
              </div>
                  <div className="metric-card">
                    <div className="metric-icon">⚡</div>
                    <div className="metric-content">
                      <h3>Max Velocity</h3>
                      <div className="metric-value">{simulationResults?.results ? `${Math.round(simulationResults.results.max_velocity || 0)} m/s` : '-- m/s'}</div>
                      <div className="metric-label">Peak flight speed</div>
                </div>
                      </div>
                  <div className="metric-card">
                    <div className="metric-icon">⏱️</div>
                    <div className="metric-content">
                      <h3>Flight Time</h3>
                      <div className="metric-value">{simulationResults?.results ? `${Math.round(simulationResults.results.total_flight_time || 0)} s` : '-- s'}</div>
                      <div className="metric-label">Total flight duration</div>
                    </div>
                  </div>
                  <div className="metric-card">
                    <div className="metric-icon">🎯</div>
                    <div className="metric-content">
                      <h3>Stability Margin</h3>
                      <div className="metric-value">{simulationResults?.results ? `${simulationResults.results.stability_margin || 0} cal` : '-- cal'}</div>
                      <div className="metric-label">Flight stability</div>
                    </div>
                  </div>
                </div>
                      </div>
                      
              {/* Aerodynamic Analysis */}
              <div className="results-section aerodynamic-analysis">
                <div className="section-header">
                  <h2>🌪️ Aerodynamic Analysis</h2>
                  <div className="section-actions">
                    <button className="action-btn">Export Data</button>
                  </div>
                </div>
                <div className="analysis-content">
                  <div className="analysis-chart">
                    <div className="chart-placeholder">
                      <div className="chart-icon">📊</div>
                      <h3>Force vs Time</h3>
                      <p>Drag, lift, and side forces over flight time</p>
                    </div>
                  </div>
                  <div className="analysis-stats">
                    <div className="stat-item">
                      <span className="stat-label">Max Drag Force</span>
                      <span className="stat-value">-- N</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">Max Lift Force</span>
                      <span className="stat-value">-- N</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">Drag Coefficient</span>
                      <span className="stat-value">--</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">Lift Coefficient</span>
                      <span className="stat-value">--</span>
                    </div>
                  </div>
                </div>
                      </div>
                      
              {/* Pressure Distribution */}
              <div className="results-section pressure-distribution">
                <div className="section-header">
                  <h2>💨 Pressure Distribution</h2>
                  <div className="section-actions">
                    <button className="action-btn">3D View</button>
                    <button className="action-btn">Export STL</button>
                  </div>
                </div>
                <div className="visualization-container">
                  <div className="pressure-visualization">
                    <div className="viz-placeholder">
                      <div className="viz-icon">🎨</div>
                      <h3>Pressure Field</h3>
                      <p>3D visualization of pressure distribution on rocket surface</p>
                    </div>
                  </div>
                  <div className="pressure-stats">
                    <div className="pressure-range">
                      <div className="range-label">Pressure Range</div>
                      <div className="range-values">
                        <span className="min-pressure">Min: -- Pa</span>
                        <span className="max-pressure">Max: -- Pa</span>
                      </div>
                    </div>
                    <div className="pressure-zones">
                      <div className="zone-item high-pressure">
                        <div className="zone-color"></div>
                        <span>High Pressure Zones</span>
                      </div>
                      <div className="zone-item low-pressure">
                        <div className="zone-color"></div>
                        <span>Low Pressure Zones</span>
                      </div>
                    </div>
                  </div>
                </div>
                      </div>
                      
              {/* Active Fin Control Results */}
              <div className="results-section fin-control-results">
                <div className="section-header">
                  <h2>🎛️ Active Fin Control</h2>
                  <div className="section-status">
                    <span className="status-indicator">Active</span>
                      </div>
                    </div>
                <div className="control-metrics">
                  <div className="control-chart">
                    <div className="chart-placeholder">
                      <div className="chart-icon">🎯</div>
                      <h3>Fin Deflections</h3>
                      <p>Real-time fin angle adjustments during flight</p>
                  </div>
                  </div>
                  <div className="control-stats">
                    <div className="stat-grid">
                      <div className="stat-item">
                        <span className="stat-label">Max Deflection</span>
                        <span className="stat-value">--°</span>
                      </div>
                      <div className="stat-item">
                        <span className="stat-label">Control Accuracy</span>
                        <span className="stat-value">--%</span>
                      </div>
                      <div className="stat-item">
                        <span className="stat-label">Corrections Made</span>
                        <span className="stat-value">--</span>
                      </div>
                      <div className="stat-item">
                        <span className="stat-label">Response Time</span>
                        <span className="stat-value">-- ms</span>
                      </div>
                    </div>
                  </div>
              </div>
            </div>

              {/* Trajectory Analysis */}
              <div className="results-section trajectory-analysis">
                <div className="section-header">
                  <h2>🛤️ Flight Trajectory</h2>
                  <div className="section-actions">
                    <button className="action-btn">Export Path</button>
                    <button className="action-btn">Compare</button>
          </div>
                </div>
                <div className="trajectory-content">
                  <div className="trajectory-plot">
                    <div className="plot-placeholder">
                      <div className="plot-icon">📈</div>
                      <h3>3D Flight Path</h3>
                      <p>Complete trajectory from launch to landing</p>
                    </div>
                  </div>
                  <div className="trajectory-data">
                    <div className="data-section">
                      <h4>Launch Parameters</h4>
                      <div className="data-grid">
                        <div className="data-item">
                          <span>Launch Angle</span>
                          <span>--°</span>
                        </div>
                        <div className="data-item">
                          <span>Initial Velocity</span>
                          <span>-- m/s</span>
                        </div>
                        <div className="data-item">
                          <span>Wind Effect</span>
                          <span>-- m/s</span>
                        </div>
                      </div>
                    </div>
                    <div className="data-section">
                      <h4>Landing Data</h4>
                      <div className="data-grid">
                        <div className="data-item">
                          <span>Landing Distance</span>
                          <span>-- m</span>
                        </div>
                        <div className="data-item">
                          <span>Landing Velocity</span>
                          <span>-- m/s</span>
                        </div>
                        <div className="data-item">
                          <span>Accuracy</span>
                          <span>-- m</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Motor Performance Analysis */}
              <div className="results-section motor-analysis">
                <div className="section-header">
                  <h2>🚀 Motor Performance</h2>
                  <div className="section-status">
                    <span className="status-indicator">{simulationResults?.results ? 'Analyzed' : 'No Data'}</span>
                  </div>
                </div>
                <div className="section-content">
                  {simulationResults?.results ? (
                    <div className="data-grid">
                      <div className="data-item">
                        <span>Motor Thrust</span>
                        <span>{Math.round(simulationResults.results.motor_thrust || 0)} N</span>
                      </div>
                      <div className="data-item">
                        <span>Burn Time</span>
                        <span>{simulationResults.results.motor_burn_time || 0} s</span>
                      </div>
                      <div className="data-item">
                        <span>Total Impulse</span>
                        <span>{Math.round((simulationResults.results.motor_thrust || 0) * (simulationResults.results.motor_burn_time || 0))} Ns</span>
                      </div>
                      <div className="data-item">
                        <span>Thrust-to-Weight</span>
                        <span>{((simulationResults.results.motor_thrust || 0) / ((simulationResults.rocket_weight || 1) / 1000)).toFixed(1)}</span>
                      </div>
                    </div>
                  ) : (
                    <div className="no-results-message">
                      <p>No motor performance data available. Run a simulation to see motor analysis.</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Aerodynamic Coefficients */}
              <div className="results-section aerodynamic-coefficients">
                <div className="section-header">
                  <h2>🌪️ Aerodynamic Coefficients</h2>
                  <div className="section-status">
                    <span className="status-indicator">{simulationResults?.results ? 'Calculated' : 'No Data'}</span>
                  </div>
                </div>
                <div className="section-content">
                  {simulationResults?.results ? (
                    <div className="data-grid">
                      <div className="data-item">
                        <span>Drag Coefficient (Cd)</span>
                        <span>{simulationResults.results.drag_coefficient || 0}</span>
                      </div>
                      <div className="data-item">
                        <span>Lift Coefficient (Cl)</span>
                        <span>{simulationResults.results.lift_coefficient || 0}</span>
                      </div>
                      <div className="data-item">
                        <span>Stability Margin</span>
                        <span>{simulationResults.results.stability_margin || 0} cal</span>
                      </div>
                      <div className="data-item">
                        <span>Center of Pressure</span>
                        <span>{Math.round((simulationResults.rocket_cg || 0) * 0.8)} mm</span>
                      </div>
                    </div>
                  ) : (
                    <div className="no-results-message">
                      <p>No aerodynamic data available. Run a simulation to see aerodynamic analysis.</p>
                    </div>
                  )}
                </div>
              </div>

              {/* CFD Analysis Results */}
              <div className="results-section cfd-analysis">
                <div className="section-header">
                  <h2>🔬 CFD Analysis Results</h2>
                  <div className="section-status">
                    <span className="status-indicator">{simulationResults?.results ? 'Available' : 'No Data'}</span>
                  </div>
                </div>
                <div className="section-content">
                  {simulationResults?.results ? (
                    <div className="data-grid">
                      <div className="data-item">
                        <span>Pressure Distribution</span>
                        <span>{simulationResults.results.pressure_distribution || 'Not Available'}</span>
                      </div>
                      <div className="data-item">
                        <span>Velocity Field</span>
                        <span>{simulationResults.results.velocity_field || 'Not Available'}</span>
                      </div>
                      <div className="data-item">
                        <span>Trajectory Data</span>
                        <span>{simulationResults.results.trajectory_data || 'Not Available'}</span>
                      </div>
                      <div className="data-item">
                        <span>Mesh Quality</span>
                        <span>High Resolution</span>
                      </div>
                    </div>
                  ) : (
                    <div className="no-results-message">
                      <p>No CFD analysis data available. Run a simulation to see computational fluid dynamics results.</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Data Export & Actions */}
              <div className="results-section data-export">
                <div className="section-header">
                  <h2>💾 Data Export</h2>
                  <div className="section-actions">
                    <button className="action-btn primary">Download All</button>
          </div>
                </div>
                <div className="export-options">
                  <div className="export-grid">
                    <div className="export-option">
                      <div className="export-icon">📊</div>
                      <h3>CSV Data</h3>
                      <p>Time-series data for analysis</p>
                      <button className="export-btn">Download</button>
                    </div>
                    <div className="export-option">
                      <div className="export-icon">🎥</div>
                      <h3>Animation</h3>
                      <p>Flight simulation video</p>
                      <button className="export-btn">Generate</button>
                    </div>
                    <div className="export-option">
                      <div className="export-icon">📋</div>
                      <h3>Report</h3>
                      <p>Complete analysis report</p>
                      <button className="export-btn">Generate</button>
                    </div>
                    <div className="export-option">
                      <div className="export-icon">🔧</div>
                      <h3>OpenFOAM</h3>
                      <p>Raw simulation files</p>
                      <button className="export-btn">Download</button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Results Status Bar */}
            <div className="results-status-bar">
              <div className="status-info">
                <span className="status-icon">ℹ️</span>
                {simulationResults ? (
                  <span>Simulation completed at {new Date(simulationResults.completed_at).toLocaleTimeString()} - ID: {simulationResults.simulation_id}</span>
                ) : (
                  <span>Run a simulation to see results</span>
                )}
              </div>
              <div className="status-actions">
                <button className="status-btn" onClick={() => setSimulationResults(null)}>Clear Results</button>
                <button className="status-btn primary" onClick={() => setActiveTab('simulation')}>Run New Simulation</button>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Motor Search Modal */}
      {console.log('🔍 Modal render check - showMotorSearch:', showMotorSearch)}
      {showMotorSearch && (
        <div className="modal-overlay" onClick={() => setShowMotorSearch(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Search Motors</h2>
              <button className="modal-close" onClick={() => setShowMotorSearch(false)}>×</button>
            </div>
            
            <div className="modal-body">
              <div className="search-input-group">
                <input
                  type="text"
                  placeholder="Search by manufacturer, model, or impulse class..."
                  value={motorSearchQuery}
                  onChange={(e) => {
                    setMotorSearchQuery(e.target.value);
                    searchMotors(e.target.value);
                  }}
                  className="search-input"
                />
                <button 
                  className="search-btn"
                  onClick={() => searchMotors(motorSearchQuery)}
                >
                  Search
                </button>
              </div>
              
              <div className="motor-results">
                {motorSearchResults.length > 0 ? (
                  <div className="motor-grid">
                    {motorSearchResults.map((motor) => (
                      <div key={motor.id} className="motor-card">
                        <div className="motor-header">
                          <h3>{motor.manufacturer} {motor.model}</h3>
                          <span className="impulse-class">{motor.impulse}</span>
                        </div>
                        <div className="motor-specs">
                          <div className="spec-row">
                            <span>Thrust:</span>
                            <span>{motor.thrust} N</span>
                          </div>
                          <div className="spec-row">
                            <span>Burn Time:</span>
                            <span>{motor.burnTime} s</span>
                          </div>
                          <div className="spec-row">
                            <span>Total Impulse:</span>
                            <span>{motor.totalImpulse} Ns</span>
                          </div>
                          <div className="spec-row">
                            <span>Weight:</span>
                            <span>{motor.weight} g</span>
                          </div>
                          <div className="spec-row">
                            <span>Diameter:</span>
                            <span>{motor.diameter} mm</span>
                          </div>
                          <div className="spec-row">
                            <span>Length:</span>
                            <span>{motor.length} mm</span>
                          </div>
                          <div className="spec-row">
                            <span>Propellant:</span>
                            <span>{motor.propellant}</span>
                          </div>
                          <div className="spec-row">
                            <span>Price:</span>
                            <span>${motor.price}</span>
                          </div>
                        </div>
                        <button 
                          className="add-motor-btn"
                          onClick={() => addMotorFromSearch(motor)}
                        >
                          Add Motor
                        </button>
                      </div>
                    ))}
                  </div>
                ) : motorSearchQuery ? (
                  <div className="no-results">
                    <p>No motors found for "{motorSearchQuery}"</p>
                    <p>Try searching for: Estes, AeroTech, C, D, E</p>
                  </div>
                ) : (
                  <div className="search-prompt">
                    <p>Enter a search term to find motors</p>
                    <p>Examples: "Estes C6", "AeroTech E30", "D12"</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
