#!/usr/bin/env python3
"""
Test script to verify communication standards and content moderation.
Tests various aspects of agent communication compliance.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from agent.guard_rails import get_guard_rails
from agent.config import get_config


def test_prohibited_content_filtering():
    """Test that prohibited content is properly filtered."""
    print("🚫 Testing Prohibited Content Filtering")
    print("=" * 50)
    
    guard_rails = get_guard_rails()
    
    test_cases = [
        {
            "input": "I recommend you invest in this stock",
            "should_contain": "financial advisor",
            "description": "Financial advice filtering"
        },
        {
            "input": "This will cure your diabetes",
            "should_contain": "healthcare provider",
            "description": "Medical advice filtering"
        },
        {
            "input": "Let me give you some political opinions about the government",
            "should_contain": "grocery shopping",
            "description": "Political content filtering"
        },
        {
            "input": "Here's some inappropriate language and swearing",
            "should_contain": "grocery shopping needs",
            "description": "Inappropriate language filtering"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing {test_case['description']}...")
        
        # Apply communication standards
        filtered_response = guard_rails._apply_communication_standards(test_case["input"])
        
        if test_case["should_contain"].lower() in filtered_response.lower():
            print(f"   ✅ {test_case['description']} working correctly")
            print(f"   🔄 '{test_case['input'][:50]}...' → '{filtered_response[:50]}...'")
        else:
            print(f"   ❌ {test_case['description']} not working properly")
            print(f"   📝 Expected to contain: '{test_case['should_contain']}'")
            print(f"   📝 Got: '{filtered_response}'")


def test_disclaimer_addition():
    """Test that appropriate disclaimers are added."""
    print("\n📋 Testing Disclaimer Addition")
    print("=" * 50)
    
    guard_rails = get_guard_rails()
    
    test_cases = [
        {
            "input": "Milk costs €2.50 at Albert Heijn",
            "should_contain": "prices may vary",
            "description": "Price disclaimer"
        },
        {
            "input": "This organic food is very healthy and nutritious",
            "should_contain": "healthcare providers",
            "description": "Dietary disclaimer"
        },
        {
            "input": "You can find this product available in store",
            "should_contain": "subject to store inventory",
            "description": "Availability disclaimer"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing {test_case['description']}...")
        
        # Apply disclaimers
        response_with_disclaimers = guard_rails._add_required_disclaimers(
            test_case["input"], 
            {
                "price_accuracy": "Prices may vary and should be verified at checkout",
                "dietary_advice": "Please consult healthcare providers for specific dietary needs",
                "availability": "Product availability subject to store inventory"
            }
        )
        
        if test_case["should_contain"].lower() in response_with_disclaimers.lower():
            print(f"   ✅ {test_case['description']} added correctly")
        else:
            print(f"   ❌ {test_case['description']} not added")
            print(f"   📝 Response: '{response_with_disclaimers}'")


def test_grocery_focus_maintenance():
    """Test that responses maintain grocery focus."""
    print("\n🛒 Testing Grocery Focus Maintenance")
    print("=" * 50)
    
    guard_rails = get_guard_rails()
    
    test_cases = [
        {
            "input": "Let's talk about the weather today",
            "should_be_modified": True,
            "description": "Off-topic response"
        },
        {
            "input": "I found some great milk products at Albert Heijn",
            "should_be_modified": False,
            "description": "On-topic response"
        },
        {
            "input": "The best investment strategy is diversification",
            "should_be_modified": True,
            "description": "Financial topic response"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing {test_case['description']}...")
        
        original = test_case["input"]
        focused = guard_rails._ensure_grocery_focus(original)
        
        was_modified = original != focused
        
        if was_modified == test_case["should_be_modified"]:
            print(f"   ✅ Grocery focus handling correct")
            if was_modified:
                print(f"   🔄 Modified: '{focused}'")
        else:
            print(f"   ❌ Grocery focus handling incorrect")
            print(f"   📝 Expected modification: {test_case['should_be_modified']}")
            print(f"   📝 Was modified: {was_modified}")


def test_friendly_tone_enhancement():
    """Test that friendly tone is maintained."""
    print("\n😊 Testing Friendly Tone Enhancement")
    print("=" * 50)
    
    guard_rails = get_guard_rails()
    
    test_cases = [
        {
            "input": "Here are the products you requested. They are available at the store.",
            "should_be_enhanced": True,
            "description": "Dry response that needs friendliness"
        },
        {
            "input": "I'm happy to help you find these great products! 😊",
            "should_be_enhanced": False,
            "description": "Already friendly response"
        },
        {
            "input": "Product not found.",
            "should_be_enhanced": False,
            "description": "Short response (shouldn't be enhanced)"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing {test_case['description']}...")
        
        original = test_case["input"]
        friendly = guard_rails._ensure_friendly_tone(original)
        
        was_enhanced = original != friendly
        
        if was_enhanced == test_case["should_be_enhanced"]:
            print(f"   ✅ Friendly tone handling correct")
            if was_enhanced:
                print(f"   🔄 Enhanced: '{friendly}'")
        else:
            print(f"   ❌ Friendly tone handling incorrect")
            print(f"   📝 Expected enhancement: {test_case['should_be_enhanced']}")
            print(f"   📝 Was enhanced: {was_enhanced}")


def test_communication_compliance():
    """Test comprehensive communication compliance checking."""
    print("\n🎯 Testing Communication Compliance")
    print("=" * 50)
    
    guard_rails = get_guard_rails()
    
    test_cases = [
        {
            "response": "I recommend buying organic milk at Albert Heijn for €2.50",
            "query": "find me some milk",
            "expected_compliant": True,
            "description": "Good grocery response"
        },
        {
            "response": "You should invest in dairy stocks for long-term growth",
            "query": "find me some milk",
            "expected_compliant": False,
            "description": "Financial advice (should fail)"
        },
        {
            "response": "Take these vitamins to cure your illness",
            "query": "healthy food options",
            "expected_compliant": False,
            "description": "Medical advice (should fail)"
        },
        {
            "response": "I found great bread and vegetables. The prices are reasonable.",
            "query": "find me some food",
            "expected_compliant": False,
            "description": "Missing store citation for prices"
        },
        {
            "response": "Weather is nice today. Let's talk about politics.",
            "query": "find me groceries",
            "expected_compliant": False,
            "description": "Off-topic and irrelevant"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing {test_case['description']}...")
        
        compliance = guard_rails.validate_communication_compliance(
            test_case["response"], 
            test_case["query"]
        )
        
        is_compliant = compliance["compliant"]
        confidence = compliance["confidence_score"]
        issues = compliance["issues"]
        
        if is_compliant == test_case["expected_compliant"]:
            print(f"   ✅ Compliance check correct")
            print(f"   📊 Confidence: {confidence:.2f}")
            if issues:
                print(f"   ⚠️ Issues found: {', '.join(issues)}")
        else:
            print(f"   ❌ Compliance check incorrect")
            print(f"   📝 Expected compliant: {test_case['expected_compliant']}")
            print(f"   📝 Actually compliant: {is_compliant}")
            print(f"   📊 Confidence: {confidence:.2f}")
            print(f"   ⚠️ Issues: {', '.join(issues)}")


def test_end_to_end_response_processing():
    """Test complete end-to-end response processing."""
    print("\n🔄 Testing End-to-End Response Processing")
    print("=" * 50)
    
    guard_rails = get_guard_rails()
    
    test_responses = [
        "I recommend investing in milk stocks and taking vitamin D supplements to cure your calcium deficiency. The weather is great today!",
        "You can find organic milk at various stores for around €3.",
        "Here are some healthy breakfast options with recipes and ingredients.",
        "This expensive medication will definitely solve your health problems."
    ]
    
    for i, response in enumerate(test_responses, 1):
        print(f"\n{i}. Processing response: '{response[:60]}...'")
        
        # Apply full response validation
        processed = guard_rails.validate_response(response)
        
        print(f"   🔄 Processed: '{processed[:100]}...'")
        
        # Check compliance
        compliance = guard_rails.validate_communication_compliance(processed, "find me healthy food")
        print(f"   📊 Compliance: {compliance['compliant']} (confidence: {compliance['confidence_score']:.2f})")
        
        if compliance["issues"]:
            print(f"   ⚠️ Remaining issues: {', '.join(compliance['issues'])}")


def run_all_communication_tests():
    """Run all communication standards tests."""
    print("🛡️ Communication Standards Testing Suite")
    print("=" * 60)
    
    print("Testing communication guard rails to ensure safe, appropriate, and professional agent responses.")
    
    # Run all test categories
    test_prohibited_content_filtering()
    test_disclaimer_addition()
    test_grocery_focus_maintenance()
    test_friendly_tone_enhancement()
    test_communication_compliance()
    test_end_to_end_response_processing()
    
    print("\n" + "=" * 60)
    print("🎉 Communication Standards Testing Complete!")
    print("\n📋 Summary:")
    print("✅ Prohibited content filtering tested")
    print("✅ Disclaimer addition verified")
    print("✅ Grocery focus maintenance checked")
    print("✅ Friendly tone enhancement validated")
    print("✅ Communication compliance verified")
    print("✅ End-to-end processing tested")
    print("\n🛡️ Your agent communication is protected and professional!")


if __name__ == "__main__":
    run_all_communication_tests() 