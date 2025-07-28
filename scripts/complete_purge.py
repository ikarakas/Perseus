#!/usr/bin/env python3
# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Complete system purge with volume reset option
"""

import requests
import subprocess
import sys
import time
import json

def complete_purge_api():
    """Call the API complete purge endpoint"""
    print("🔥 Executing API complete purge...")
    try:
        response = requests.delete(
            'http://localhost:8000/api/v1/dashboard/purge-everything?confirm=DESTROY-ALL-DATA',
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API purge completed!")
            print(f"   Deleted: {sum(result.get('purged', {}).values())} total records")
            return True
        else:
            print(f"❌ API purge failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ API purge error: {e}")
        return False

def volume_reset():
    """Reset Docker volumes completely"""
    print("\n🔄 Resetting Docker volumes...")
    try:
        # Stop containers and remove volumes
        print("   Stopping containers and removing volumes...")
        subprocess.run(['docker', 'compose', 'down', '-v'], check=True, capture_output=True)
        
        # Start containers with fresh volumes
        print("   Starting fresh containers...")
        subprocess.run(['docker', 'compose', 'up', '-d'], check=True, capture_output=True)
        
        # Wait for services
        print("   Waiting for services to start...")
        time.sleep(20)
        
        # Check health
        try:
            response = requests.get('http://localhost:8000/health', timeout=10)
            if response.status_code == 200:
                print("✅ Volume reset completed! Services are healthy.")
                return True
            else:
                print("⚠️  Services may still be starting...")
                return True
        except:
            print("⚠️  Services may still be starting...")
            return True
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Volume reset failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Volume reset error: {e}")
        return False

def main():
    print("🚨 COMPLETE SYSTEM PURGE")
    print("=========================")
    print("\nOptions:")
    print("  1. Database purge only (keeps Docker volumes)")
    print("  2. Complete reset (database + Docker volumes)")
    print("")
    
    try:
        choice = input("Select option (1 or 2): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n❌ No input available or interrupted. Using default option 2 (complete reset)")
        choice = "2"
    
    if choice == "1":
        print("\n🎯 Database purge only...")
        success = complete_purge_api()
        if success:
            print("\n🎉 Database purge completed!")
            print("Note: Docker volumes are preserved. Data will persist across container restarts.")
    
    elif choice == "2":
        print("\n🎯 Complete reset (database + volumes)...")
        print("⚠️  This will restart Docker containers!")
        
        try:
            confirm = input("Are you sure? (type 'yes'): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n❌ No input available. Auto-confirming complete reset...")
            confirm = "yes"
        
        if confirm.lower() == 'yes':
            # First try API purge (optional, since volumes will be wiped anyway)
            complete_purge_api()
            
            # Then reset volumes
            success = volume_reset()
            if success:
                print("\n🎉 COMPLETE RESET SUCCESSFUL!")
                print("\n   🌐 Dashboard: http://localhost:8000/dashboard/enhanced")
                print("   📊 API Docs:  http://localhost:8000/docs")
        else:
            print("❌ Operation cancelled")
    
    else:
        print("❌ Invalid option")
        sys.exit(1)

if __name__ == "__main__":
    main()