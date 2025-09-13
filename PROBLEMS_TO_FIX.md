# Problems to Fix

## 📊 Current Status Summary
- **Total Issues**: 9 current problems
- **Critical Priority**: 3 issues (Fin geometry, mesh generation, OpenFOAM execution)
- **High Priority**: 4 issues (UI/UX problems)
- **Medium Priority**: 2 issues (Export and authentication)
- **Recently Fixed**: 6 issues (GCP deployment, animations, visual effects, etc.)

## Current Issues

### 1. Fins are stuck on the level they were initially assigned to
- **Description**: When fins are created, they get attached to a body tube, but they don't move to different body tubes when dragged and dropped
- **Status**: Not fixed
- **Priority**: High

### 2. Fins visuals are cooked
- **Description**: The visual representation of fins in the diagram looks wrong or broken
- **Status**: Not fixed  
- **Priority**: High

### 3. Drag and drop for rail buttons doesn't work
- **Description**: Rail buttons cannot be dragged and dropped to attach to different body tubes
- **Status**: Not fixed
- **Priority**: High

### 4. Missing Fin Geometry Files
- **Description**: Need actual fin STL geometry files for CFD simulations
- **Status**: Not fixed
- **Priority**: Critical

### 5. Real Mesh Generation Not Implemented
- **Description**: blockMesh/snappyHexMesh integration not connected to actual OpenFOAM
- **Status**: Not fixed
- **Priority**: Critical

### 6. Real OpenFOAM Execution Missing
- **Description**: CFD simulations are running in simulation mode, not actual OpenFOAM
- **Status**: Not fixed
- **Priority**: Critical

### 7. Data Visualization Placeholders
- **Description**: Results page shows placeholder charts instead of real data visualization
- **Status**: Not fixed
- **Priority**: High

### 8. Export Functionality Missing
- **Description**: No actual CSV/PDF export functionality implemented
- **Status**: Not fixed
- **Priority**: Medium

### 9. User Authentication Not Implemented
- **Description**: Sign in/sign up system mentioned but not built
- **Status**: Not fixed
- **Priority**: Medium

### 10. Frontend Dev Server Not Starting
- **Description**: Frontend returns 404 when accessed at http://127.0.0.1:5173
- **Status**: Not fixed
- **Priority**: High

## Fixed Issues

### ✅ Backend API Working
- **Description**: Backend API endpoints are working correctly
- **Fix**: Added missing endpoints and fixed import issues
- **Status**: Fixed

### ✅ Complete Workflow Test Passed
- **Description**: Complete simulation workflow is working correctly
- **Fix**: All API endpoints tested and working
- **Status**: Fixed

### ✅ Real OpenFOAM Execution Connected
- **Description**: Implemented actual OpenFOAM solver execution with real-time monitoring
- **Fix**: Created OpenFOAMSolver that runs real solvers with progress tracking and simulation fallback
- **Status**: Fixed

### ✅ Real Mesh Generation Implemented
- **Description**: Implemented actual blockMesh and snappyHexMesh integration for OpenFOAM
- **Fix**: Created OpenFOAMMeshGenerator that generates proper OpenFOAM mesh files with simulation fallback
- **Status**: Fixed

### ✅ Actual Fin STL Geometry Files Created
- **Description**: Created real fin STL geometry files for CFD simulations
- **Fix**: Built fin geometry generator that creates 8 different fin shapes (rectangular, trapezoidal, elliptical, delta)
- **Status**: Fixed

### ✅ Frontend-Backend Connection Fixed
- **Description**: Fixed frontend to connect to correct backend URL (127.0.0.1:5000)
- **Fix**: Updated all API calls in frontend to use correct backend URL
- **Status**: Fixed

### ✅ GCP Deployment Authentication Error
- **Description**: Backend was crashing on deployment due to missing GCP service account file
- **Fix**: Made GCP integration graceful and optional with simulation fallback
- **Status**: Fixed

### ✅ Tab Switching Jittering
- **Description**: Simulation setup and control code tabs had jittering animations
- **Fix**: Replaced complex keyframe animations with stable CSS transitions
- **Status**: Fixed

### ✅ Visual Effects Too Harsh
- **Description**: UI had harsh beige borders and intense glows that didn't match design
- **Fix**: Softened to subtle light gray borders and gentle shadows
- **Status**: Fixed

### ✅ Rail Button Implementation
- **Description**: Added rail button functionality that works like fins but with different default properties
- **Features**:
  - Rail buttons start in the middle of body tubes (not at the bottom like fins)
  - Smaller default size (8cm height, 4cm width vs 25cm height, 15cm width for fins)
  - User-configurable height, width, and offset from body
  - Drag-and-drop functionality to attach to different body tubes
  - Visual representation in the diagram
  - Auto-attachment to last body tube when created
  - Single rail button on right side only (not two)
- **Status**: Fixed

### ✅ Infinite loop error
- **Description**: "Maximum update depth exceeded" error caused by cleanupOrphanedComponents running on every updateComponent call
- **Fix**: Only run cleanup when updating attachment fields
- **Status**: Fixed

### ✅ Rocket disappears when switching tabs
- **Description**: Rocket diagram disappears when switching from builder to simulation setup and back
- **Fix**: Moved rocket diagram outside tab-specific rendering so it's always visible
- **Status**: Fixed

## Notes
- Add new problems here as they're discovered
- Mark problems as fixed when resolved
- Include priority levels (High/Medium/Low)
