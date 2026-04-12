#!/usr/bin/env python
"""Integration test simulating OpenEnv validator checks."""

import asyncio
import json
import sys
from typing import Dict, Any, List

async def validate_integration():
    """Run integration tests."""
    
    print("=" * 70)
    print("INTEGRATION TEST - Simulating OpenEnv Validator")
    print("=" * 70)
    
    # Phase 1: Import and basic checks
    print("\n[PHASE 1] Module Import and Basic Checks")
    print("-" * 70)
    
    try:
        from env import (
            SupportTicketEnv,
            SupportAction,
            SupportObservation,
            SupportState,
            ActionType,
            TicketCategory,
            PriorityLevel,
            get_task_metadata,
            TicketGrader
        )
        print("✓ All modules imported successfully")
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False
    
    # Phase 2: Task metadata validation
    print("\n[PHASE 2] Task Metadata Validation")
    print("-" * 70)
    
    try:
        tasks = get_task_metadata()
        
        if len(tasks) < 3:
            print(f"✗ Need at least 3 tasks, found {len(tasks)}")
            return False
        
        print(f"✓ Found {len(tasks)} tasks")
        
        for task in tasks:
            # Check required fields
            required = ['id', 'name', 'description', 'difficulty', 'max_steps', 'success_threshold', 'graders']
            for field in required:
                if field not in task:
                    print(f"✗ Task {task.get('id')} missing {field}")
                    return False
            
            # Check graders
            if not task.get('graders'):
                print(f"✗ Task {task['id']} has no graders")
                return False
            
            print(f"  ✓ {task['id']}: {task['name']} ({len(task['graders'])} graders)")
        
    except Exception as e:
        print(f"✗ Task metadata validation failed: {e}")
        return False
    
    # Phase 3: Environment API validation
    print("\n[PHASE 3] Environment API Validation")
    print("-" * 70)
    
    try:
        env = SupportTicketEnv()
        
        # Test reset for each task
        for task_config in tasks:
            task_id = task_config['id']
            
            result = await env.reset(task_id)
            
            # Check result structure
            if not all(k in result for k in ['observation', 'reward', 'done', 'info']):
                print(f"✗ reset() missing required keys for {task_id}")
                return False
            
            # Check observation structure
            obs = result['observation']
            if not all(k in obs for k in ['tickets', 'current_step', 'max_steps', 'queue_status']):
                print(f"✗ observation missing required keys for {task_id}")
                return False
            
            # Check reward range
            if not (0.0 <= result['reward'] <= 1.0):
                print(f"✗ reset() reward out of range: {result['reward']}")
                return False
            
            print(f"  ✓ reset('{task_id}') valid")
        
        # Test step
        result = await env.reset('categorize_ticket')
        obs = result['observation']
        tickets = obs.get('tickets', [])
        
        if tickets:
            action = SupportAction(
                action_type=ActionType.CATEGORIZE,
                ticket_id=tickets[0]['id'],
                category=TicketCategory.TECHNICAL,
                priority=PriorityLevel.HIGH
            )
            
            step_result = await env.step(action)
            
            if not all(k in step_result for k in ['observation', 'reward', 'done', 'info']):
                print(f"✗ step() missing required keys")
                return False
            
            if not (0.0 <= step_result['reward'] <= 1.0):
                print(f"✗ step() reward out of range: {step_result['reward']}")
                return False
            
            print(f"  ✓ step() returns valid structure")
        
        # Test get_state
        state = env.get_state()
        if not state:
            print(f"✗ get_state() returned None")
            return False
        
        if not (0.0 <= state.score <= 1.0):
            print(f"✗ state.score out of range: {state.score}")
            return False
        
        print(f"  ✓ get_state() returns valid state")
        
    except Exception as e:
        print(f"✗ Environment API validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Phase 4: Grader validation
    print("\n[PHASE 4] Grader Validation")
    print("-" * 70)
    
    try:
        grader = TicketGrader()
        
        # Test categorization grader
        score = grader.grade_categorization(
            TicketCategory.TECHNICAL,
            TicketCategory.TECHNICAL,
            PriorityLevel.HIGH,
            PriorityLevel.HIGH
        )
        if not (0.0 <= score <= 1.0):
            print(f"✗ grade_categorization out of range: {score}")
            return False
        print(f"  ✓ grade_categorization valid (perfect match: {score})")
        
        # Test response grader
        score = grader.grade_response(
            "Thank you for reporting this issue. We will troubleshoot and fix it.",
            TicketCategory.TECHNICAL
        )
        if not (0.0 <= score <= 1.0):
            print(f"✗ grade_response out of range: {score}")
            return False
        print(f"  ✓ grade_response valid (score: {score:.2f})")
        
        # Test escalation grader
        score = grader.grade_escalation(
            PriorityLevel.CRITICAL,
            "Production system outage requiring immediate senior response",
            "senior_support"
        )
        if not (0.0 <= score <= 1.0):
            print(f"✗ grade_escalation out of range: {score}")
            return False
        print(f"  ✓ grade_escalation valid (score: {score:.2f})")
        
    except Exception as e:
        print(f"✗ Grader validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Phase 5: Multi-episode consistency
    print("\n[PHASE 5] Multi-Episode Consistency")
    print("-" * 70)
    
    try:
        scores = []
        for i in range(3):
            env = SupportTicketEnv()
            result = await env.reset('categorize_ticket')
            
            # Take 3-5 random actions
            for _ in range(3):
                tickets = env.get_state().tickets
                if tickets:
                    action = SupportAction(
                        action_type=ActionType.CATEGORIZE,
                        ticket_id=tickets[0].id,
                        category=TicketCategory.GENERAL,
                        priority=PriorityLevel.MEDIUM
                    )
                    result = await env.step(action)
                    if result.get('done'):
                        break
            
            state = env.get_state()
            scores.append(state.score)
        
        print(f"  ✓ Multi-episode test passed (scores: {[f'{s:.2f}' for s in scores]})")
        
    except Exception as e:
        print(f"✗ Multi-episode test failed: {e}")
        return False
    
    # Success
    print("\n" + "=" * 70)
    print("✅ ALL INTEGRATION TESTS PASSED!")
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = asyncio.run(validate_integration())
    sys.exit(0 if success else 1)
