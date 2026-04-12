#!/usr/bin/env python
"""Validate openenv.yaml grader structure"""

import yaml

with open('openenv.yaml', 'r') as f:
    config = yaml.safe_load(f)
    
tasks_with_graders = 0
for task in config.get('tasks', []):
    if 'graders' in task and task['graders']:
        tasks_with_graders += 1
        print(f"✓ Task '{task['id']}': {len(task['graders'])} grader(s)")
    else:
        print(f"✗ Task '{task['id']}': NO GRADERS")

print(f"\nTotal tasks with graders: {tasks_with_graders}")
if tasks_with_graders >= 3:
    print("✓ PASS - Ready for submission!")
else:
    print("✗ FAIL - Need at least 3 tasks with graders")
