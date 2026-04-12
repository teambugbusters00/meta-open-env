#!/usr/bin/env python
"""Test server endpoints."""

import asyncio
import json
from httpx import AsyncClient

async def test_server():
    """Test all server endpoints."""
    
    base_url = "http://localhost:8000"
    
    async with AsyncClient() as client:
        print("=" * 60)
        print("TESTING SERVER ENDPOINTS")
        print("=" * 60)
        
        # Test 1: Health
        print("\n1. Testing /health endpoint...")
        try:
            response = await client.get(f"{base_url}/health")
            print(f"   ✓ Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   - Status: {data.get('status')}")
                print(f"   - Environment: {data.get('environment')}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # Test 2: Metadata
        print("\n2. Testing /metadata endpoint...")
        try:
            response = await client.get(f"{base_url}/metadata")
            print(f"   ✓ Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   - Name: {data.get('name')}")
                print(f"   - Version: {data.get('version')}")
                print(f"   - Tasks: {len(data.get('tasks', []))}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # Test 3: Tasks
        print("\n3. Testing /tasks endpoint...")
        try:
            response = await client.get(f"{base_url}/tasks")
            print(f"   ✓ Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                tasks = data.get("tasks", [])
                print(f"   - Task count: {len(tasks)}")
                for task in tasks:
                    print(f"     • {task.get('id')}: {task.get('name')}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # Test 4: Graders
        print("\n4. Testing /graders endpoint...")
        try:
            response = await client.get(f"{base_url}/graders")
            print(f"   ✓ Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                graders = data.get("graders", [])
                print(f"   - Grader count: {len(graders)}")
                for grader in graders[:3]:
                    print(f"     • {grader.get('id')}: {grader.get('name')}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # Test 5: Schema
        print("\n5. Testing /schema endpoint...")
        try:
            response = await client.get(f"{base_url}/schema")
            print(f"   ✓ Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   - Has 'action' schema: {'action' in data}")
                print(f"   - Has 'observation' schema: {'observation' in data}")
                print(f"   - Has 'state' schema: {'state' in data}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # Test 6: Root
        print("\n6. Testing / endpoint...")
        try:
            response = await client.get(f"{base_url}/")
            print(f"   ✓ Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   - Name: {data.get('name')}")
                print(f"   - Endpoints: {list(data.get('endpoints', {}).keys())}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        print("\n" + "=" * 60)
        print("✅ Server endpoint tests completed!")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_server())
