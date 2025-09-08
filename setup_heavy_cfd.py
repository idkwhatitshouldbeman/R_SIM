#!/usr/bin/env python3
"""
Heavy CFD Setup Script
Sets up full OpenFOAM integration for professional-grade rocket simulations
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_system_requirements():
    """Check if system meets requirements for heavy CFD"""
    print("🔍 Checking system requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    
    # Check available memory (rough estimate)
    try:
        with open('/proc/meminfo', 'r') as f:
            meminfo = f.read()
            for line in meminfo.split('\n'):
                if 'MemTotal' in line:
                    mem_kb = int(line.split()[1])
                    mem_gb = mem_kb / 1024 / 1024
                    if mem_gb < 2:
                        print(f"⚠️  Low memory detected: {mem_gb:.1f}GB (recommended: 4GB+)")
                    else:
                        print(f"✅ Memory: {mem_gb:.1f}GB")
                    break
    except:
        print("⚠️  Could not check memory")
    
    print("✅ System requirements check completed")
    return True

def install_openfoam():
    """Install OpenFOAM for heavy CFD simulations"""
    print("🚀 Installing OpenFOAM...")
    
    try:
        # Check if OpenFOAM is already installed
        result = subprocess.run(['which', 'blockMesh'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ OpenFOAM already installed")
            return True
        
        # Install OpenFOAM
        print("📥 Installing OpenFOAM...")
        install_commands = [
            ['sudo', 'apt-get', 'update'],
            ['sudo', 'apt-get', 'install', '-y', 'software-properties-common'],
            ['wget', '-O', '-', 'https://dl.openfoam.org/gpg.key', '|', 'sudo', 'apt-key', 'add', '-'],
            ['sudo', 'add-apt-repository', 'http://dl.openfoam.org/ubuntu'],
            ['sudo', 'apt-get', 'update'],
            ['sudo', 'apt-get', 'install', '-y', 'openfoam8-dev']
        ]
        
        for cmd in install_commands:
            print(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Command failed: {result.stderr}")
                return False
        
        print("✅ OpenFOAM installation completed")
        return True
        
    except Exception as e:
        print(f"❌ OpenFOAM installation failed: {e}")
        return False

def setup_openfoam_environment():
    """Set up OpenFOAM environment variables"""
    print("🔧 Setting up OpenFOAM environment...")
    
    try:
        # Create OpenFOAM environment file
        openfoam_env_content = '''#!/bin/bash
# OpenFOAM Environment Setup
export FOAM_INSTALL_DIR=/opt/openfoam8
export FOAM_RUN=/opt/openfoam8/run
export FOAM_APPBIN=/opt/openfoam8/platforms/linux64GccDPInt32Opt/bin
export FOAM_LIBBIN=/opt/openfoam8/platforms/linux64GccDPInt32Opt/lib
export PATH=$FOAM_APPBIN:$PATH
export LD_LIBRARY_PATH=$FOAM_LIBBIN:$LD_LIBRARY_PATH
export WM_PROJECT=OpenFOAM
export WM_PROJECT_VERSION=8
export WM_THIRD_PARTY_DIR=/opt/openfoam8/ThirdParty
export WM_OPTIONS=64
export WM_ARCH=linux64
export WM_COMPILER=Gcc
export WM_COMPILER_ARCH=64
export WM_COMPILER_LIB_ARCH=64
export WM_MPLIB=SYSTEMOPENMPI
export WM_LABEL_SIZE=32
export WM_PRECISION_OPTION=DP
export WM_LABEL_OPTION=Int32
export WM_COMPILE_OPTION=Opt
export WM_DIR=/opt/openfoam8/wmake
export WM_PROJECT_USER_DIR=/opt/openfoam8/user
export FOAM_SIGFPE=""
export FOAM_COPYRIGHT="Copyright 2011-2024 OpenCFD Ltd."
export FOAM_LIBBIN=/opt/openfoam8/platforms/linux64GccDPInt32Opt/lib
export FOAM_APPBIN=/opt/openfoam8/platforms/linux64GccDPInt32Opt/bin
export FOAM_APP=/opt/openfoam8/applications
export FOAM_SRC=/opt/openfoam8/src
export FOAM_TUTORIALS=/opt/openfoam8/tutorials
export FOAM_ETC=/opt/openfoam8/etc
export FOAM_UTILITIES=/opt/openfoam8/applications/utilities
export FOAM_SOLVERS=/opt/openfoam8/applications/solvers
export FOAM_RUN=/opt/openfoam8/run
'''
        
        # Write environment file
        with open('openfoam_env.sh', 'w') as f:
            f.write(openfoam_env_content)
        
        # Make it executable
        os.chmod('openfoam_env.sh', 0o755)
        
        print("✅ OpenFOAM environment setup completed")
        return True
        
    except Exception as e:
        print(f"❌ Environment setup failed: {e}")
        return False

def create_openfoam_directories():
    """Create necessary OpenFOAM directories"""
    print("📁 Creating OpenFOAM directories...")
    
    try:
        # Create case directories
        directories = [
            'openfoam_cases',
            'openfoam_cases/templates',
            'openfoam_cases/results',
            'openfoam_cases/meshes'
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Created: {directory}")
        
        print("✅ OpenFOAM directories created")
        return True
        
    except Exception as e:
        print(f"❌ Directory creation failed: {e}")
        return False

def test_openfoam_installation():
    """Test OpenFOAM installation"""
    print("🧪 Testing OpenFOAM installation...")
    
    try:
        # Test blockMesh
        result = subprocess.run(['blockMesh', '-help'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ blockMesh test passed")
        else:
            print("❌ blockMesh test failed")
            return False
        
        # Test snappyHexMesh
        result = subprocess.run(['snappyHexMesh', '-help'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ snappyHexMesh test passed")
        else:
            print("❌ snappyHexMesh test failed")
            return False
        
        # Test pimpleFoam
        result = subprocess.run(['pimpleFoam', '-help'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ pimpleFoam test passed")
        else:
            print("❌ pimpleFoam test failed")
            return False
        
        print("✅ OpenFOAM installation test completed")
        return True
        
    except Exception as e:
        print(f"❌ OpenFOAM test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Heavy CFD Setup for Rocket Simulation Platform")
    print("=" * 60)
    
    try:
        # Check system requirements
        if not check_system_requirements():
            print("❌ System requirements not met")
            return 1
        
        # Install OpenFOAM
        if not install_openfoam():
            print("❌ OpenFOAM installation failed")
            return 1
        
        # Setup environment
        if not setup_openfoam_environment():
            print("❌ Environment setup failed")
            return 1
        
        # Create directories
        if not create_openfoam_directories():
            print("❌ Directory creation failed")
            return 1
        
        # Test installation
        if not test_openfoam_installation():
            print("❌ OpenFOAM test failed")
            return 1
        
        print("\n🎉 Heavy CFD setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Run the application: python backend/f_backend.py")
        print("2. Open your browser to: http://localhost:5000")
        print("3. Start building rockets and running heavy CFD simulations!")
        print("\n🔧 For Docker deployment:")
        print("1. Build the Docker image: docker build -t rocket-sim .")
        print("2. Run the container: docker run -p 5000:5000 rocket-sim")
        print("\n🌐 For Render deployment:")
        print("1. Push your code to GitHub")
        print("2. Connect your repository to Render")
        print("3. Deploy using the render.yaml configuration")
        
        return 0
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
