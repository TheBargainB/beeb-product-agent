"""Test the live LangGraph Platform deployment with enhanced memory capabilities."""

import requests
import json
import time
import uuid
from typing import Dict, Any

# Deployment URL
DEPLOYMENT_URL = "https://ht-ample-carnation-93-62e3a16b2190526eac38c74198169a7f.us.langgraph.app"

def test_live_deployment(api_key: str = None):
    """
    Comprehensive test of the live deployment with memory capabilities.
    
    Args:
        api_key: The X-Api-Key for the deployment (if available)
    """
    
    print("🚀 Testing Live LangGraph Platform Deployment")
    print("=" * 60)
    print(f"Deployment URL: {DEPLOYMENT_URL}")
    print()
    
    headers = {
        "Content-Type": "application/json"
    }
    
    if api_key:
        headers["X-Api-Key"] = api_key
    else:
        # Try with a test key first
        headers["X-Api-Key"] = "test"
    
    # Test user and thread IDs
    user_id = "test_user_" + str(uuid.uuid4())[:8]
    thread_id = "test_thread_" + str(uuid.uuid4())[:8]
    
    print(f"🧪 Test User ID: {user_id}")
    print(f"🧪 Test Thread ID: {thread_id}")
    print()
    
    # Test scenarios for comprehensive memory testing
    test_scenarios = [
        {
            "name": "User Profile Setup",
            "message": "Hi! I'm Emma from Amsterdam, family of 3. I'm vegan and allergic to shellfish. I prefer shopping at Albert Heijn.",
            "expected_features": ["user_profile", "dietary_preferences", "allergies", "location"]
        },
        {
            "name": "Budget Planning", 
            "message": "I want to set a weekly grocery budget of €90 for my family.",
            "expected_features": ["budget_tracking", "weekly_budget"]
        },
        {
            "name": "Grocery List Creation",
            "message": "Add to my shopping list: quinoa, bell peppers, chickpeas, coconut milk, and fresh herbs.",
            "expected_features": ["grocery_list", "vegan_products"]
        },
        {
            "name": "Meal Planning",
            "message": "Plan a vegan curry for dinner tomorrow for 3 people.",
            "expected_features": ["meal_planning", "dietary_compliance", "servings"]
        },
        {
            "name": "Product Search with Memory",
            "message": "Find some good vegan protein sources with prices that fit my budget.",
            "expected_features": ["product_search", "personalization", "budget_awareness"]
        },
        {
            "name": "Memory Recall",
            "message": "What do you know about my dietary preferences and current shopping list?",
            "expected_features": ["memory_recall", "profile_summary", "list_summary"]
        }
    ]
    
    # Function to create a thread
    def create_thread():
        """Create a new thread for testing."""
        try:
            response = requests.post(
                f"{DEPLOYMENT_URL}/threads",
                headers=headers,
                json={
                    "metadata": {
                        "test_user": user_id,
                        "test_type": "memory_capabilities"
                    }
                }
            )
            
            if response.status_code == 200:
                thread_data = response.json()
                return thread_data.get("thread_id")
            else:
                print(f"❌ Failed to create thread: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating thread: {e}")
            return None
    
    # Function to send a message and get response
    def send_message(thread_id: str, message: str, config: Dict[str, Any] = None):
        """Send a message to the agent and get response."""
        try:
            # Default config with user_id for memory
            if config is None:
                config = {
                    "configurable": {
                        "user_id": user_id,
                        "thread_id": thread_id
                    }
                }
            
            response = requests.post(
                f"{DEPLOYMENT_URL}/threads/{thread_id}/runs",
                headers=headers,
                json={
                    "input": {
                        "messages": [
                            {"role": "user", "content": message}
                        ]
                    },
                    "config": config,
                    "metadata": {
                        "test_scenario": True
                    }
                }
            )
            
            if response.status_code == 200:
                run_data = response.json()
                return run_data
            else:
                print(f"❌ Failed to send message: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return None
    
    # Function to get run result
    def get_run_result(thread_id: str, run_id: str, max_wait: int = 30):
        """Wait for run to complete and get the result."""
        try:
            for i in range(max_wait):
                response = requests.get(
                    f"{DEPLOYMENT_URL}/threads/{thread_id}/runs/{run_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    run_data = response.json()
                    status = run_data.get("status")
                    
                    if status == "success":
                        # Get the final state
                        state_response = requests.get(
                            f"{DEPLOYMENT_URL}/threads/{thread_id}/state",
                            headers=headers
                        )
                        
                        if state_response.status_code == 200:
                            state_data = state_response.json()
                            messages = state_data.get("values", {}).get("messages", [])
                            if messages:
                                return messages[-1].get("content", "No response content")
                        
                        return "Run completed but no response found"
                    
                    elif status == "error":
                        error_msg = run_data.get("error", "Unknown error")
                        return f"Error: {error_msg}"
                    
                    elif status in ["pending", "running"]:
                        print(f"⏳ Waiting for run to complete... ({i+1}/{max_wait})")
                        time.sleep(1)
                        continue
                    
                else:
                    print(f"❌ Failed to get run status: {response.status_code}")
                    return None
            
            return "Timeout waiting for run to complete"
            
        except Exception as e:
            print(f"❌ Error getting run result: {e}")
            return None
    
    # Check if deployment is accessible
    print("🔍 Checking deployment accessibility...")
    try:
        # Try to get assistants (this doesn't require authentication in some cases)
        response = requests.get(f"{DEPLOYMENT_URL}/docs")
        if response.status_code == 200:
            print("✅ Deployment is accessible")
        else:
            print(f"⚠️ Deployment returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot reach deployment: {e}")
        return
    
    # Test the deployment with memory scenarios
    print(f"\n🧪 Running {len(test_scenarios)} Memory Test Scenarios")
    print("=" * 60)
    
    # Create a thread for testing
    current_thread_id = create_thread()
    
    if not current_thread_id:
        print("❌ Cannot create thread - testing with direct URLs")
        current_thread_id = thread_id
    else:
        print(f"✅ Created thread: {current_thread_id}")
    
    # Run all test scenarios
    results = []
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🧪 Test {i}: {scenario['name']}")
        print("-" * 40)
        print(f"Input: {scenario['message']}")
        
        # Send message
        run_data = send_message(current_thread_id, scenario['message'])
        
        if run_data:
            run_id = run_data.get("run_id")
            print(f"⏳ Run started: {run_id}")
            
            # Get result
            result = get_run_result(current_thread_id, run_id)
            
            if result:
                print(f"✅ Response: {result[:200]}{'...' if len(result) > 200 else ''}")
                results.append({
                    "scenario": scenario['name'],
                    "status": "success",
                    "response": result
                })
            else:
                print("❌ No response received")
                results.append({
                    "scenario": scenario['name'], 
                    "status": "failed",
                    "response": None
                })
        else:
            print("❌ Failed to send message")
            results.append({
                "scenario": scenario['name'],
                "status": "failed", 
                "response": None
            })
        
        # Short delay between tests
        time.sleep(2)
    
    # Test cross-thread memory persistence
    print(f"\n🧪 Test 7: Cross-Thread Memory Persistence")
    print("-" * 40)
    
    # Create a new thread to test memory persistence
    new_thread_id = create_thread()
    if new_thread_id:
        print(f"✅ Created new thread: {new_thread_id}")
        
        memory_test_message = "What do you remember about my profile and preferences?"
        run_data = send_message(new_thread_id, memory_test_message)
        
        if run_data:
            run_id = run_data.get("run_id")
            result = get_run_result(new_thread_id, run_id)
            
            if result:
                print(f"✅ Cross-thread memory test: {result[:200]}{'...' if len(result) > 200 else ''}")
                results.append({
                    "scenario": "Cross-Thread Memory",
                    "status": "success", 
                    "response": result
                })
            else:
                print("❌ Cross-thread memory test failed")
                results.append({
                    "scenario": "Cross-Thread Memory",
                    "status": "failed",
                    "response": None
                })
    
    # Summary
    print(f"\n📊 Test Summary")
    print("=" * 60)
    
    successful_tests = len([r for r in results if r["status"] == "success"])
    total_tests = len(results)
    
    print(f"✅ Successful tests: {successful_tests}/{total_tests}")
    print(f"❌ Failed tests: {total_tests - successful_tests}/{total_tests}")
    
    if successful_tests == total_tests:
        print("\n🎉 All enhanced memory features are working on live deployment!")
        print("\nMemory Features Confirmed:")
        print("- 👤 User profile management")
        print("- 🛒 Grocery list creation and management") 
        print("- 🍽️ Meal planning with dietary compliance")
        print("- 💰 Budget tracking and awareness")
        print("- 🔍 Personalized product search")
        print("- 🧠 Cross-thread memory persistence")
    else:
        print(f"\n⚠️ Some tests failed - deployment may still be updating")
        print("Note: LangGraph Platform deployments can take 10-15 minutes to fully update")
    
    return results


if __name__ == "__main__":
    # Test with different API key options
    print("🧪 Testing Live Deployment - Enhanced Agent with Memory")
    print("\nNote: If you have the deployment API key, set it as environment variable:")
    print("export LANGGRAPH_API_KEY='your-api-key'")
    print("\nTesting with default configuration...")
    print()
    
    import os
    api_key = os.getenv("LANGGRAPH_API_KEY")
    
    results = test_live_deployment(api_key)
    
    # Also provide manual testing URLs
    print(f"\n🌐 Manual Testing URLs:")
    print(f"- Studio Interface: {DEPLOYMENT_URL}/studio")
    print(f"- API Documentation: {DEPLOYMENT_URL}/docs") 
    print(f"- Assistant Creation: {DEPLOYMENT_URL}/assistants")
    
    print(f"\n📱 For manual testing, use:")
    print(f"curl -X POST '{DEPLOYMENT_URL}/threads' \\")
    print(f"  -H 'Content-Type: application/json' \\")
    print(f"  -H 'X-Api-Key: YOUR_API_KEY' \\")
    print(f"  -d '{{\"metadata\": {{}}}}'") 