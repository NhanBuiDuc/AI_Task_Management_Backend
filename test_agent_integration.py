#!/usr/bin/env python
"""
Simple test script for LangChain agent integration
Run with: python test_agent_integration.py
"""

import requests
import json
import sys

API_BASE = 'http://localhost:8000/api'

def test_agent_health():
    """Test if agent is configured properly"""
    print("🔍 Testing agent health...")
    
    try:
        response = requests.get(f'{API_BASE}/agent-health/')
        data = response.json()
        
        print(f"Agent Status: {data['agent_status']}")
        print(f"OpenAI Configured: {data['openai_configured']}")
        
        if data['agent_status'] == 'healthy':
            print("✅ Agent is healthy and ready")
            return True
        else:
            print("❌ Agent has issues")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Django server. Run: python manage.py runserver")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_intention_processing():
    """Test intention processing with sample data"""
    print("\n🤖 Testing intention processing...")
    
    test_cases = [
        "learn Chinese 30 minutes daily, go to gym 3 times a week",
        "work on graduation thesis 2 hours daily, prepare CV",
        "read books about AI, practice coding interviews"
    ]
    
    for i, intentions in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Input: {intentions}")
        
        try:
            response = requests.post(
                f'{API_BASE}/process-intentions/',
                json={'intentions': intentions},
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 201:
                data = response.json()
                print(f"✅ Success: Created {len(data['data']['created_tasks'])} tasks")
                
                for task in data['data']['created_tasks']:
                    print(f"  📝 {task['name']} (Priority: {task['piority']}, Duration: {task['duration_in_minutes']}min)")
                
                print(f"📊 Feasibility Score: {data['data']['feasibility_score']}/10")
                print(f"⏱️ Total Time/Week: {data['data']['total_estimated_time_per_week']} minutes")
                
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")

def main():
    """Run all tests"""
    print("🚀 Starting LangChain Agent Integration Tests")
    print("=" * 50)
    
    # Test 1: Health check
    if not test_agent_health():
        print("\n❌ Health check failed. Fix configuration before proceeding.")
        sys.exit(1)
    
    # Test 2: Process intentions
    test_intention_processing()
    
    print("\n" + "=" * 50)
    print("🎉 Tests completed!")
    
if __name__ == "__main__":
    main()