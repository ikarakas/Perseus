#!/usr/bin/env python3
# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Helper script to find Docker images and containers
"""

import subprocess
import json

def find_docker_images():
    """Find all Docker images containing 'open-webui'"""
    print("🔍 Finding Docker images containing 'open-webui'...")
    
    try:
        # Get all images
        result = subprocess.run(['docker', 'images', '--format', 'json'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            images = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    image_data = json.loads(line)
                    repo = image_data.get('Repository', '')
                    tag = image_data.get('Tag', '')
                    if 'open-webui' in repo.lower():
                        images.append(f"{repo}:{tag}")
            
            if images:
                print(f"✅ Found {len(images)} matching images:")
                for img in images:
                    print(f"   - {img}")
                return images
            else:
                print("❌ No images found matching 'open-webui'")
        else:
            print(f"❌ Error running docker images: {result.stderr}")
    
    except FileNotFoundError:
        print("❌ Docker command not found. Is Docker installed and running?")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return []

def find_running_containers():
    """Find running containers containing 'open-webui'"""
    print("\n🔍 Finding running containers containing 'open-webui'...")
    
    try:
        # Get running containers
        result = subprocess.run(['docker', 'ps', '--format', 'json'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            containers = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    container_data = json.loads(line)
                    image = container_data.get('Image', '')
                    names = container_data.get('Names', '')
                    if 'open-webui' in image.lower() or 'open-webui' in names.lower():
                        containers.append({
                            'image': image,
                            'name': names,
                            'status': container_data.get('Status', '')
                        })
            
            if containers:
                print(f"✅ Found {len(containers)} running containers:")
                for container in containers:
                    print(f"   - Name: {container['name']}")
                    print(f"     Image: {container['image']}")
                    print(f"     Status: {container['status']}")
                return containers
            else:
                print("❌ No running containers found matching 'open-webui'")
        else:
            print(f"❌ Error running docker ps: {result.stderr}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return []

def suggest_analysis_commands(images, containers):
    """Suggest SBOM analysis commands"""
    print("\n🚀 Suggested SBOM analysis commands:")
    print("=" * 50)
    
    if images:
        print("\nFor Docker images:")
        for img in images[:3]:  # Show max 3 suggestions
            print(f"\n# Analyze image: {img}")
            print(f"./sbom-cli.sh analyze-docker {img}")
            print(f"# OR via curl:")
            print(f'curl -X POST http://localhost:8080/analyze/docker \\')
            print(f'  -H "Content-Type: application/json" \\')
            print(f'  -d \'{{"type":"docker","location":"{img}"}}\'')
    
    if containers:
        print("\nFor running containers (use the image name):")
        for container in containers[:3]:  # Show max 3 suggestions
            img = container['image']
            print(f"\n# Analyze container '{container['name']}' (image: {img})")
            print(f"./sbom-cli.sh analyze-docker {img}")

if __name__ == "__main__":
    print("Docker Image/Container Finder for SBOM Analysis")
    print("=" * 50)
    
    images = find_docker_images()
    containers = find_running_containers()
    
    if images or containers:
        suggest_analysis_commands(images, containers)
    else:
        print("\n💡 Tips:")
        print("1. Make sure Docker Desktop is running")
        print("2. Check if open-webui container is running: docker ps")
        print("3. Check all images: docker images | grep open-webui")
        print("4. You can also analyze any Docker image by full name:")
        print("   Example: ./sbom-cli.sh analyze-docker ghcr.io/open-webui/open-webui:latest")