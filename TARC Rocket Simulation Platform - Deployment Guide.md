# TARC Rocket Simulation Platform - Deployment Guide

## Overview
This is a comprehensive web-based rocket simulation platform designed for TARC (Team America Rocketry Challenge) with active control code testing, high-fidelity CFD simulation, and a futuristic user interface.

## Features Implemented

### ✅ Core Features
- **OpenRocket-style Rocket Builder**: Click-to-add components with visual design interface
- **High-Fidelity CFD Simulation**: Custom Python-based CFD solver with Navier-Stokes equations
- **C++ Control Code Integration**: Secure compilation and execution of user control algorithms
- **Motor Database**: 8 TARC-approved motors with realistic thrust curves
- **Environment Configuration**: Atmospheric modeling, wind profiles, launch sites
- **Interactive Results Visualization**: 2D/3D charts, performance metrics, real-time progress
- **Hardware Limitations Modeling**: Servo constraints, sensor noise, processing delays
- **Futuristic UI**: Beige/white theme with glass-morphism effects and 3D feel

### 🚀 Technical Architecture
- **Frontend**: React + Vite + Plotly.js for interactive visualizations
- **Backend**: Flask + SQLite for motor database + Custom CFD engine
- **Security**: Sandboxed C++ compilation with validation
- **Real-time**: WebSocket-like polling for simulation progress

## Local Deployment Instructions

### Prerequisites
- Node.js 20+ and pnpm
- Python 3.11+ with pip
- g++ compiler (build-essential)
- Ubuntu 22.04 or similar Linux environment

### 1. Backend Setup
```bash
cd rocket-sim-backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install flask flask-cors numpy scipy matplotlib sqlite3

# Start backend server
python src/main.py
```
Backend will run on: http://localhost:5000

### 2. Frontend Setup
```bash
cd rocket-sim-platform

# Install dependencies
pnpm install

# Development mode
pnpm run dev --host

# Production build
pnpm run build
pnpm run preview --host
```
Frontend will run on: http://localhost:5173 (dev) or http://localhost:4173 (production)

### 3. Access the Platform
Open your browser and navigate to the frontend URL. The platform includes:

1. **Rocket Builder Tab**: Design your rocket using the component library
2. **Simulation Setup Tab**: Configure environment and motor selection
3. **Control Code Tab**: Write and test your C++ control algorithms
4. **Results Tab**: View comprehensive simulation results and analysis

## Usage Workflow

### Step 1: Design Your Rocket
- Click components from the library to add them to your rocket
- Adjust component properties in the right panel
- View real-time statistics (length, diameter, mass)

### Step 2: Configure Environment
- Select launch site (NAR TARC Finals, Estes Field, etc.)
- Set atmospheric conditions (temperature, wind, humidity)
- Choose motor from TARC-approved database

### Step 3: Write Control Code
- Implement your C++ control algorithm
- Test compilation and hardware constraints
- Validate against safety restrictions

### Step 4: Run Simulation
- Click "Run Simulation" to start CFD analysis
- Monitor real-time progress with detailed iteration info
- Wait for completion (can take several minutes for high accuracy)

### Step 5: Analyze Results
- View interactive charts: trajectory, velocity, control deflections
- Examine 3D flight path with wind effects
- Review performance metrics and CFD-computed values

## API Endpoints

### Simulation
- `POST /api/simulation/start` - Start CFD simulation
- `GET /api/simulation/status` - Get simulation progress
- `GET /api/simulation/results` - Retrieve results

### Motor Database
- `GET /api/environment/motors` - List all motors
- `GET /api/environment/motors/{designation}` - Get specific motor
- `GET /api/environment/motors/{designation}/thrust` - Get thrust curve

### Environment
- `GET /api/environment/launch-sites` - Available launch sites
- `POST /api/environment/environment-config` - Create environment config
- `GET /api/environment/presets` - Environment presets

### Control Code
- `POST /api/control-code/compile` - Compile C++ code
- `POST /api/control-code/test` - Test with sample data

## File Structure

```
rocket-sim-platform/
├── src/
│   ├── components/
│   │   ├── RocketBuilder.jsx          # OpenRocket-style builder
│   │   ├── ControlCodeEditor.jsx      # C++ code editor
│   │   └── ResultsVisualization.jsx   # Interactive charts
│   ├── App.jsx                        # Main application
│   └── App.css                        # Futuristic styling
├── dist/                              # Production build
└── package.json

rocket-sim-backend/
├── src/
│   ├── cfd_engine.py                  # CFD simulation engine
│   ├── motor_database.py              # Motor database system
│   ├── environment_config.py          # Atmospheric modeling
│   ├── cpp_integration.py             # C++ code compilation
│   ├── routes/                        # API endpoints
│   └── main.py                        # Flask application
├── database/                          # SQLite databases
└── requirements.txt
```

## Performance Notes

- **CFD Simulation**: Can take 2-10 minutes depending on mesh resolution
- **Memory Usage**: ~500MB for typical simulations
- **Disk Space**: ~100MB for motor database and temporary files
- **Browser**: Chrome/Firefox recommended for best visualization performance

## Security Features

- **C++ Sandboxing**: Restricted compilation with forbidden operations blocked
- **Input Validation**: All user inputs validated and sanitized
- **Temporary Files**: Automatic cleanup of compiled programs
- **CORS Protection**: Configured for local development only

## Future Enhancements

- **Real CFD Integration**: OpenFOAM or SU2 integration for production use
- **Cloud Deployment**: Docker containerization for cloud hosting
- **User Accounts**: Save/load rocket designs and simulation results
- **Advanced Visualization**: VTK-based 3D flow field visualization
- **Competition Mode**: TARC-specific scoring and constraints

## Troubleshooting

### Common Issues

1. **Backend won't start**: Check if port 5000 is available
2. **C++ compilation fails**: Ensure g++ is installed (`sudo apt install build-essential`)
3. **Frontend build errors**: Clear node_modules and reinstall (`rm -rf node_modules && pnpm install`)
4. **Simulation hangs**: Check backend logs for CFD convergence issues

### Performance Optimization

1. **Reduce mesh resolution** for faster simulations during development
2. **Use production build** for better frontend performance
3. **Close other applications** to free up memory for CFD calculations

## Support

This platform was designed specifically for TARC rocket development and testing. The CFD simulation provides research-grade accuracy while maintaining usability for educational purposes.

For technical issues, check the browser console and backend logs for detailed error messages.

