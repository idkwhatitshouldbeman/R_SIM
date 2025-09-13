"""
GCP Integration for Active Fin Control System
Handles cloud CFD computations and real-time data synchronization
"""

import os
import json
import time
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests
from google.cloud import storage
from google.cloud import compute_v1
import google.auth

class GCPActiveFinManager:
    """Manages GCP integration for active fin control simulations"""
    
    def __init__(self, project_id: str, bucket_name: str, zone: str = "us-central1-a"):
        self.project_id = project_id
        self.bucket_name = bucket_name
        self.zone = zone
        
        # Initialize GCP clients
        self.storage_client = storage.Client(project=project_id)
        self.compute_client = compute_v1.InstancesClient()
        
        # Simulation state
        self.instance_name = None
        self.case_directory = None
        self.simulation_running = False
        
    def create_cfd_instance(self, instance_name: str, machine_type: str = "n1-standard-4") -> bool:
        """Create a GCP compute instance for CFD simulation"""
        try:
            # Check if instance already exists
            if self._instance_exists(instance_name):
                print(f"✅ Instance {instance_name} already exists")
                self.instance_name = instance_name
                return True
            
            # Create instance configuration
            instance_config = {
                "name": instance_name,
                "machine_type": f"zones/{self.zone}/machineTypes/{machine_type}",
                "disks": [{
                    "boot": True,
                    "auto_delete": True,
                    "initialize_params": {
                        "source_image": "projects/ubuntu-os-cloud/global/images/family/ubuntu-2004-lts",
                        "disk_size_gb": "50"
                    }
                }],
                "network_interfaces": [{
                    "access_configs": [{"type": "ONE_TO_ONE_NAT"}],
                    "network": f"projects/{self.project_id}/global/networks/default"
                }],
                "metadata": {
                    "items": [{
                        "key": "startup-script",
                        "value": self._get_startup_script()
                    }]
                },
                "tags": {
                    "items": ["cfd-simulation", "active-fin-control"]
                }
            }
            
            # Create the instance
            operation = self.compute_client.insert(
                project=self.project_id,
                zone=self.zone,
                instance_resource=instance_config
            )
            
            print(f"🚀 Creating CFD instance {instance_name}...")
            print(f"Operation: {operation.name}")
            
            self.instance_name = instance_name
            return True
            
        except Exception as e:
            print(f"❌ Error creating CFD instance: {e}")
            return False
    
    def _instance_exists(self, instance_name: str) -> bool:
        """Check if a compute instance exists"""
        try:
            self.compute_client.get(
                project=self.project_id,
                zone=self.zone,
                instance=instance_name
            )
            return True
        except:
            return False
    
    def _get_startup_script(self) -> str:
        """Get the startup script for CFD instance"""
        return """
#!/bin/bash
# Install OpenFOAM and dependencies
apt-get update
apt-get install -y wget curl build-essential

# Install OpenFOAM
wget -O - https://dl.openfoam.org/gpg.key | apt-key add -
add-apt-repository http://dl.openfoam.org/ubuntu
apt-get update
apt-get install -y openfoam2212-dev

# Install Python dependencies
apt-get install -y python3 python3-pip
pip3 install numpy scipy pandas trimesh

# Create simulation directory
mkdir -p /home/simulation
chown -R ubuntu:ubuntu /home/simulation

# Install our active fin control system
cd /home/simulation
git clone https://github.com/your-repo/active-fin-control.git || echo "Git repo not available"

echo "CFD instance setup complete"
"""
    
    def upload_case_to_gcp(self, local_case_dir: Path, remote_case_name: str) -> bool:
        """Upload OpenFOAM case to GCP storage"""
        try:
            bucket = self.storage_client.bucket(self.bucket_name)
            
            # Upload case files
            for file_path in local_case_dir.rglob("*"):
                if file_path.is_file():
                    # Create remote path
                    relative_path = file_path.relative_to(local_case_dir)
                    remote_path = f"{remote_case_name}/{relative_path}"
                    
                    # Upload file
                    blob = bucket.blob(remote_path)
                    blob.upload_from_filename(str(file_path))
                    print(f"📤 Uploaded {relative_path}")
            
            self.case_directory = remote_case_name
            print(f"✅ Case uploaded to GCP: {remote_case_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error uploading case to GCP: {e}")
            return False
    
    def download_case_from_gcp(self, remote_case_name: str, local_case_dir: Path) -> bool:
        """Download OpenFOAM case from GCP storage"""
        try:
            bucket = self.storage_client.bucket(self.bucket_name)
            blobs = bucket.list_blobs(prefix=f"{remote_case_name}/")
            
            for blob in blobs:
                # Create local file path
                relative_path = blob.name[len(remote_case_name)+1:]
                local_file_path = local_case_dir / relative_path
                
                # Create directory if needed
                local_file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Download file
                blob.download_to_filename(str(local_file_path))
                print(f"📥 Downloaded {relative_path}")
            
            print(f"✅ Case downloaded from GCP: {remote_case_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error downloading case from GCP: {e}")
            return False
    
    def start_cfd_simulation(self, case_name: str) -> bool:
        """Start CFD simulation on GCP instance"""
        try:
            if not self.instance_name:
                print("❌ No instance available")
                return False
            
            # Get instance IP
            instance_ip = self._get_instance_ip()
            if not instance_ip:
                print("❌ Could not get instance IP")
                return False
            
            # SSH command to start simulation
            ssh_command = f"""
            cd /home/simulation/{case_name}
            source /opt/openfoam2212/etc/bashrc
            pimpleFoam > simulation.log 2>&1 &
            echo $! > simulation.pid
            """
            
            # Execute via SSH
            result = subprocess.run([
                "gcloud", "compute", "ssh", self.instance_name,
                "--zone", self.zone,
                "--command", ssh_command
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.simulation_running = True
                print(f"✅ CFD simulation started on {instance_ip}")
                return True
            else:
                print(f"❌ Error starting simulation: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error starting CFD simulation: {e}")
            return False
    
    def stop_cfd_simulation(self) -> bool:
        """Stop CFD simulation on GCP instance"""
        try:
            if not self.instance_name:
                return True
            
            # SSH command to stop simulation
            ssh_command = """
            if [ -f simulation.pid ]; then
                kill $(cat simulation.pid) 2>/dev/null || true
                rm simulation.pid
            fi
            pkill -f pimpleFoam || true
            """
            
            # Execute via SSH
            result = subprocess.run([
                "gcloud", "compute", "ssh", self.instance_name,
                "--zone", self.zone,
                "--command", ssh_command
            ], capture_output=True, text=True)
            
            self.simulation_running = False
            print("⏹️ CFD simulation stopped")
            return True
            
        except Exception as e:
            print(f"❌ Error stopping CFD simulation: {e}")
            return False
    
    def get_simulation_status(self) -> Dict:
        """Get simulation status from GCP instance"""
        try:
            if not self.instance_name:
                return {"status": "no_instance", "running": False}
            
            # SSH command to check status
            ssh_command = """
            if [ -f simulation.pid ]; then
                if kill -0 $(cat simulation.pid) 2>/dev/null; then
                    echo "running"
                else
                    echo "stopped"
                fi
            else
                echo "stopped"
            fi
            """
            
            # Execute via SSH
            result = subprocess.run([
                "gcloud", "compute", "ssh", self.instance_name,
                "--zone", self.zone,
                "--command", ssh_command
            ], capture_output=True, text=True)
            
            status = result.stdout.strip()
            return {
                "status": status,
                "running": status == "running",
                "instance_ip": self._get_instance_ip()
            }
            
        except Exception as e:
            print(f"❌ Error getting simulation status: {e}")
            return {"status": "error", "running": False, "error": str(e)}
    
    def download_cfd_results(self, local_results_dir: Path) -> bool:
        """Download CFD results from GCP instance"""
        try:
            if not self.instance_name:
                return False
            
            # Create results directory
            local_results_dir.mkdir(parents=True, exist_ok=True)
            
            # Download postProcessing directory
            subprocess.run([
                "gcloud", "compute", "scp",
                "--recurse",
                f"{self.instance_name}:/home/simulation/{self.case_directory}/postProcessing",
                str(local_results_dir),
                "--zone", self.zone
            ], check=True)
            
            print("✅ CFD results downloaded")
            return True
            
        except Exception as e:
            print(f"❌ Error downloading CFD results: {e}")
            return False
    
    def _get_instance_ip(self) -> Optional[str]:
        """Get the external IP of the compute instance"""
        try:
            instance = self.compute_client.get(
                project=self.project_id,
                zone=self.zone,
                instance=self.instance_name
            )
            
            for network_interface in instance.network_interfaces:
                for access_config in network_interface.access_configs:
                    if access_config.nat_i_p:
                        return access_config.nat_i_p
            
            return None
            
        except Exception as e:
            print(f"❌ Error getting instance IP: {e}")
            return None
    
    def cleanup_resources(self):
        """Clean up GCP resources"""
        try:
            if self.instance_name:
                # Stop simulation
                self.stop_cfd_simulation()
                
                # Delete instance
                operation = self.compute_client.delete(
                    project=self.project_id,
                    zone=self.zone,
                    instance=self.instance_name
                )
                print(f"🗑️ Deleting instance {self.instance_name}")
                print(f"Operation: {operation.name}")
                
        except Exception as e:
            print(f"❌ Error cleaning up resources: {e}")

class GCPActiveFinIntegration:
    """Main integration class for GCP active fin control"""
    
    def __init__(self, project_id: str, bucket_name: str):
        self.gcp_manager = GCPActiveFinManager(project_id, bucket_name)
        self.local_case_dir = None
        self.remote_case_name = None
        
    def setup_simulation(self, local_case_dir: Path, case_name: str, 
                        instance_name: str = "cfd-simulation") -> bool:
        """Setup complete simulation on GCP"""
        try:
            # Create CFD instance
            if not self.gcp_manager.create_cfd_instance(instance_name):
                return False
            
            # Wait for instance to be ready
            print("⏳ Waiting for instance to be ready...")
            time.sleep(60)  # Wait 1 minute for startup
            
            # Upload case to GCP
            if not self.gcp_manager.upload_case_to_gcp(local_case_dir, case_name):
                return False
            
            self.local_case_dir = local_case_dir
            self.remote_case_name = case_name
            
            print("✅ GCP simulation setup complete")
            return True
            
        except Exception as e:
            print(f"❌ Error setting up GCP simulation: {e}")
            return False
    
    def start_simulation(self) -> bool:
        """Start the CFD simulation"""
        return self.gcp_manager.start_cfd_simulation(self.remote_case_name)
    
    def stop_simulation(self) -> bool:
        """Stop the CFD simulation"""
        return self.gcp_manager.stop_cfd_simulation()
    
    def get_status(self) -> Dict:
        """Get simulation status"""
        return self.gcp_manager.get_simulation_status()
    
    def download_results(self, results_dir: Path) -> bool:
        """Download simulation results"""
        return self.gcp_manager.download_cfd_results(results_dir)
    
    def cleanup(self):
        """Clean up all resources"""
        self.gcp_manager.cleanup_resources()

# Example usage
def create_gcp_integration(project_id: str, bucket_name: str) -> GCPActiveFinIntegration:
    """Create GCP integration for active fin control"""
    return GCPActiveFinIntegration(project_id, bucket_name)
