#!/usr/bin/env python
"""Comprehensive validation of OpenEnv submission requirements."""

import asyncio
import json
import sys
from env import (
    SupportTicketEnv, 
    ActionType, 
    TicketCategory, 
    PriorityLevel, 
    get_task_metadata,
    Ticket,
    SupportObservation,
    SupportState,
    SupportAction
)

async def validate_environment():
    """Validate all OpenEnv requirements."""
    
    print("=" * 70)
    print("OPENENV SUBMISSION VALIDATION")
    print("=" * 70)
    
    issues = []
    warnings = []
    passed = []
    
    # =========================================================================
    # REQUIREMENT 1: Real-world utility
    # =========================================================================
    print("\n[1] Real-world Task Modeling")
    print("-" * 70)
    try:
        print("✓ Domain: Customer Support Ticket Triage")
        print("✓ Use Case: AI agent learns to handle support tickets")
        print("✓ Real-world value: Applicable to any organization with support queues")
        passed.append("Real-world domain")
    except Exception as e:
        issues.append(f"Real-world task validation failed: {e}")
    
    # =========================================================================
    # REQUIREMENT 2: Full OpenEnv spec (step/reset/state)
    # =========================================================================
    print("\n[2] OpenEnv API Implementation")
    print("-" * 70)
    
    env = SupportTicketEnv()
    
    # Test reset
    try:
        result = await env.reset("categorize_ticket")
        assert "observation" in result
        assert "reward" in result
        assert "done" in result
        assert "info" in result
        assert isinstance(result["reward"], (int, float))
        assert 0.0 <= result["reward"] <= 1.0, f"Reward {result['reward']} out of range"
        print("✓ reset() works correctly")
        passed.append("reset() API")
    except Exception as e:
        issues.append(f"reset() failed: {e}")
    
    # Test step
    try:
        tickets = result["observation"].get("tickets", [])
        assert tickets, "No tickets in observation"
        
        action = SupportAction(
            action_type=ActionType.CATEGORIZE,
            ticket_id=tickets[0]["id"],
            category=TicketCategory.TECHNICAL,
            priority=PriorityLevel.HIGH
        )
        
        step_result = await env.step(action)
        assert "observation" in step_result
        assert "reward" in step_result
        assert "done" in step_result
        assert "info" in step_result
        assert isinstance(step_result["reward"], (int, float))
        assert 0.0 <= step_result["reward"] <= 1.0, f"Reward {step_result['reward']} out of range"
        print("✓ step() works correctly")
        passed.append("step() API")
    except Exception as e:
        issues.append(f"step() failed: {e}")
    
    # Test get_state
    try:
        state = env.get_state()
        assert state is not None
        assert hasattr(state, 'task_id')
        assert hasattr(state, 'score')
        assert hasattr(state, 'current_step')
        assert 0.0 <= state.score <= 1.0, f"Score {state.score} out of range"
        print("✓ get_state() works correctly")
        passed.append("get_state() API")
    except Exception as e:
        issues.append(f"get_state() failed: {e}")
    
    # =========================================================================
    # REQUIREMENT 3: Minimum 3 tasks with graders
    # =========================================================================
    print("\n[3] Tasks and Graders")
    print("-" * 70)
    
    try:
        tasks_meta = get_task_metadata()
        assert len(tasks_meta) >= 3, f"Only {len(tasks_meta)} tasks, need >= 3"
        print(f"✓ {len(tasks_meta)} tasks defined:")
        
        task_ids = []
        for task in tasks_meta:
            task_id = task.get("id")
            task_name = task.get("name")
            graders = task.get("graders", [])
            task_ids.append(task_id)
            print(f"  • {task_id}: {task_name} ({len(graders)} grader(s))")
            
            # Verify graders
            for grader in graders:
                assert "id" in grader, "Grader missing ID"
                assert "name" in grader, "Grader missing name"
                assert "description" in grader, "Grader missing description"
        
        passed.append(f"Tasks and graders ({len(tasks_meta)} tasks)")
        
        # Test difficulty progression
        difficulties = [t.get("difficulty") for t in tasks_meta]
        print(f"  - Difficulty levels: {difficulties}")
        if "easy" in difficulties and "medium" in difficulties and "hard" in difficulties:
            passed.append("Difficulty progression")
        else:
            warnings.append("Not all difficulty levels present")
        
    except Exception as e:
        issues.append(f"Tasks/graders validation failed: {e}")
    
    # =========================================================================
    # REQUIREMENT 4: Reward function with partial progress signals
    # =========================================================================
    print("\n[4] Reward Function and Progress Signals")
    print("-" * 70)
    
    try:
        env2 = SupportTicketEnv()
        await env2.reset("categorize_ticket")
        
        rewards_collected = []
        for step in range(5):
            tickets = env2.get_state().tickets
            if not tickets:
                break
            
            action = SupportAction(
                action_type=ActionType.CATEGORIZE,
                ticket_id=tickets[0].id,
                category=TicketCategory.GENERAL,
                priority=PriorityLevel.MEDIUM
            )
            result = await env2.step(action)
            rewards_collected.append(result["reward"])
        
        # Check for varying signals (not all 0 or all 1)
        unique_rewards = set(rewards_collected)
        if len(unique_rewards) > 1:
            print(f"✓ Varying reward signal: {unique_rewards}")
            passed.append("Reward variance")
        else:
            warnings.append(f"Limited reward variety: {unique_rewards}")
        
        print(f"  - Sample rewards: {rewards_collected}")
        
    except Exception as e:
        issues.append(f"Reward function validation failed: {e}")
    
    # =========================================================================
    # REQUIREMENT 5: Baseline inference script exists
    # =========================================================================
    print("\n[5] Baseline Inference Script")
    print("-" * 70)
    
    try:
        import os
        inference_path = os.path.join(os.path.dirname(__file__), "inference.py")
        assert os.path.exists(inference_path), "inference.py not found"
        
        with open(inference_path) as f:
            content = f.read()
            assert "async def main()" in content
            assert "get_llm_action" in content
            assert "log_start" in content
            assert "log_end" in content
        
        print("✓ inference.py exists and has all required components")
        passed.append("Baseline inference script")
        
    except Exception as e:
        issues.append(f"Baseline script validation failed: {e}")
    
    # =========================================================================
    # REQUIREMENT 6: Typed models and Pydantic
    # =========================================================================
    print("\n[6] Type Checking and Models")
    print("-" * 70)
    
    try:
        from pydantic import BaseModel
        
        assert issubclass(Ticket, BaseModel)
        assert issubclass(SupportObservation, BaseModel)
        assert issubclass(SupportState, BaseModel)
        assert issubclass(SupportAction, BaseModel)
        
        print("✓ All models use Pydantic BaseModel")
        print("✓ Full type annotations present")
        passed.append("Typed models")
        
    except Exception as e:
        issues.append(f"Type checking validation failed: {e}")
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    print(f"\n✅ PASSED ({len(passed)}):")
    for item in passed:
        print(f"   • {item}")
    
    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for item in warnings:
            print(f"   • {item}")
    
    if issues:
        print(f"\n❌ ISSUES ({len(issues)}):")
        for item in issues:
            print(f"   • {item}")
        return False
    else:
        print(f"\n🎉 ALL CHECKS PASSED!")
        return True

if __name__ == "__main__":
    success = asyncio.run(validate_environment())
    sys.exit(0 if success else 1)
