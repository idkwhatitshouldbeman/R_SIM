# Problems to Fix

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

## Fixed Issues

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

## Fixed Issues

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
