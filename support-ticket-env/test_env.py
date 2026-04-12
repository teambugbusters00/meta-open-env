#!/usr/bin/env python
"""Quick test of the environment."""

from env import SupportTicketEnv, SupportAction, ActionType, TicketCategory, PriorityLevel

def main():
    """Test the env."""
    
    # Test 1: Reset
    print("=" * 60)
    print("TEST 1: Reset Environment")
    print("=" * 60)
    env = SupportTicketEnv()
    result = env.reset('categorize_ticket')
    print(f"✓ Reset successful")
    print(f"  - Observation keys: {list(result['observation'].keys())}")
    print(f"  - Tickets: {len(result['observation']['tickets'])}")
    print(f"  - Reward: {result['reward']}")
    print(f"  - Done: {result['done']}")
    print(f"  - Info: {result['info']}")
    
    # Test 2: Step - Categorize
    print("\n" + "=" * 60)
    print("TEST 2: Step - Categorize")
    print("=" * 60)
    
    tickets = result['observation']['tickets']
    if tickets:
        ticket = tickets[0]
        action = SupportAction(
            action_type=ActionType.CATEGORIZE,
            ticket_id=ticket['id'],
            category=TicketCategory.TECHNICAL,
            priority=PriorityLevel.HIGH
        )
        
        step_result = env.step(action)
        print(f"✓ Step successful")
        print(f"  - Reward: {step_result['reward']}")
        print(f"  - Done: {step_result['done']}")
        print(f"  - Info: {step_result['info']}")
    
    # Test 3: Get State
    print("\n" + "=" * 60)
    print("TEST 3: Get State")
    print("=" * 60)
    
    state = env.get_state()
    if state:
        print(f"✓ State retrieved")
        print(f"  - Task: {state.task_id}")
        print(f"  - Score: {state.score}")
        print(f"  - Current step: {state.current_step}")
        print(f"  - Total actions: {state.total_actions}")
        print(f"  - Correct actions: {state.correct_actions}")
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    main()
