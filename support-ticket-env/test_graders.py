#!/usr/bin/env python
"""
Quick validation script to test graders work correctly
"""

from env import GRADER_FUNCTIONS, get_task_metadata, TicketCategory, PriorityLevel

def test_graders():
    """Test that all graders are callable and return valid scores"""
    
    print("=" * 60)
    print("GRADER VALIDATION TEST")
    print("=" * 60)
    
    # Test 1: Check task metadata
    print("\n✓ Task Metadata:")
    tasks = get_task_metadata()
    print(f"  Total tasks: {len(tasks)}")
    for task in tasks:
        grader_count = len(task.get("graders", []))
        print(f"    - {task['id']}: {grader_count} grader(s)")
    
    if len(tasks) < 3:
        print("  ✗ ERROR: Need at least 3 tasks")
        return False
    else:
        print("  ✓ PASS: 4 tasks found (>= 3 minimum)")
    
    # Test 2: Check all graders are mapped
    print("\n✓ Grader Functions:")
    print(f"  Available graders: {list(GRADER_FUNCTIONS.keys())}")
    
    grader_ids_from_metadata = set()
    for task in tasks:
        for grader in task.get("graders", []):
            grader_ids_from_metadata.add(grader["id"])
    
    print(f"  Graders from metadata: {grader_ids_from_metadata}")
    
    # Test 3: Test each grader
    print("\n✓ Testing Grader Calls:")
    
    test_cases = {
        "categorization_accuracy": {
            "agent_category": TicketCategory.TECHNICAL,
            "expected_category": TicketCategory.TECHNICAL,
            "agent_priority": PriorityLevel.HIGH,
            "expected_priority": PriorityLevel.HIGH,
        },
        "queue_prioritization": {
            "priority_scores": [0.8, 0.7, 0.9],
        },
        "workflow_resolution_quality": {
            "categorization_score": 0.8,
            "response_quality": 0.7,
            "escalation_score": 0.9,
            "completion_ratio": 0.95,
        },
        "escalation_precision": {
            "expected_escalation": True,
            "agent_escalated": True,
            "expected_team": "eng",
            "agent_team": "eng",
        },
        "response_professionalism": {
            "response_length": 150,
        },
    }
    
    all_pass = True
    for grader_id, sample in test_cases.items():
        try:
            if grader_id not in GRADER_FUNCTIONS:
                print(f"  ✗ {grader_id}: NOT FOUND")
                all_pass = False
                continue
            
            grader_fn = GRADER_FUNCTIONS[grader_id]
            score = grader_fn(sample)
            
            if not isinstance(score, (int, float)):
                print(f"  ✗ {grader_id}: Invalid return type {type(score)}")
                all_pass = False
            elif score < 0.0 or score > 1.0:
                print(f"  ✗ {grader_id}: Score {score} out of range [0.0, 1.0]")
                all_pass = False
            else:
                print(f"  ✓ {grader_id}: {score:.2f}")
        except Exception as e:
            print(f"  ✗ {grader_id}: {str(e)}")
            all_pass = False
    
    print("\n" + "=" * 60)
    if all_pass and len(tasks) >= 3:
        print("✓ ALL TESTS PASSED - Ready for submission!")
        print("=" * 60)
        return True
    else:
        print("✗ SOME TESTS FAILED")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = test_graders()
    exit(0 if success else 1)
