"""
Hugging Face Spaces App Entry Point
This file is used when deploying to HF Spaces with Gradio interface.
"""

import os
import gradio as gr
import asyncio
import json
from typing import Dict, Any

from env import SupportTicketEnv, SupportAction


# ============================================================================
# Environment Setup
# ============================================================================

env = SupportTicketEnv()
env_state = None


# ============================================================================
# Gradio Interface Functions
# ============================================================================

def reset_environment(task_id: str) -> str:
    """Reset the environment and return initial observation"""
    global env_state
    
    async def _reset():
        global env_state
        result = await env.reset(task_id)
        env_state = result
        return result
    
    result = asyncio.run(_reset())
    observation = result.get("observation", {})
    
    # Format tickets for display
    tickets_info = ""
    for ticket in observation.get("tickets", []):
        tickets_info += f"""
**Ticket ID**: {ticket.get('id', 'N/A')}
- **From**: {ticket.get('customer_name', 'N/A')} ({ticket.get('customer_email', 'N/A')})
- **Subject**: {ticket.get('subject', 'N/A')}
- **Content**: {ticket.get('content', 'N/A')[:100]}...
- **Status**: {ticket.get('status', 'N/A')}
"""
        if ticket.get('category'):
            tickets_info += f"- **Category**: {ticket.get('category')}\n"
        if ticket.get('priority'):
            tickets_info += f"- **Priority**: {ticket.get('priority')}\n"
        tickets_info += "\n"
    
    return f"""
### Environment Reset Successfully!

**Task**: {task_id}
**Max Steps**: {observation.get('max_steps', 'N/A')}
**Instructions**: {observation.get('instructions', 'N/A')}

### Current Tickets:
{tickets_info}

**Queue Status**: {observation.get('queue_status', {})}
**Available Actions**: {', '.join(observation.get('available_actions', []))}
"""


def take_action(action_json: str) -> str:
    """Execute an action and return the result"""
    global env_state
    
    if env_state is None:
        return "Error: Environment not initialized. Please reset first."
    
    try:
        action_dict = json.loads(action_json)
        
        # Validate required fields
        if "action_type" not in action_dict:
            return "Error: 'action_type' is required in the action."
        
        async def _step():
            action = SupportAction(**action_dict)
            result = await env.step(action)
            return result
        
        result = asyncio.run(_step())
        observation = result.get("observation", {})
        reward = result.get("reward", 0.0)
        done = result.get("done", False)
        info = result.get("info", {})
        
        # Format result
        output = f"""
### Action Result

**Reward**: {reward:.2f}
**Done**: {done}
**Result**: {info.get('action_result', 'N/A')}
**Current Score**: {info.get('current_score', 0.0):.3f}

### Updated Tickets:
"""
        
        for ticket in observation.get("tickets", []):
            output += f"""
**Ticket ID**: {ticket.get('id', 'N/A')}
- **Subject**: {ticket.get('subject', 'N/A')}
- **Status**: {ticket.get('status', 'N/A')}
"""
            if ticket.get('category'):
                output += f"- **Category**: {ticket.get('category')}\n"
            if ticket.get('priority'):
                output += f"- **Priority**: {ticket.get('priority')}\n"
            responses = ticket.get('responses', [])
            output += f"- **Responses**: {len(responses)} sent\n"
            output += "\n"
        
        if done:
            output += "\n### Episode Complete!\n"
            output += f"**Final Score**: {info.get('current_score', 0.0):.3f}\n"
        
        return output
    
    except json.JSONDecodeError:
        return "Error: Invalid JSON. Please check your action format."
    except Exception as e:
        return f"Error: {str(e)}"


def get_environment_info() -> str:
    """Get information about the environment"""
    return """
### Support Ticket Triage Environment

This environment simulates a customer support workflow where AI agents must:
1. **Categorize** tickets into correct departments
2. **Prioritize** based on urgency
3. **Respond** to customers professionally
4. **Escalate** when necessary
5. **Close** resolved tickets

#### Available Actions:

1. **categorize** - Set category and priority for a ticket
   ```json
   {"action_type": "categorize", "ticket_id": "abc123", "category": "technical", "priority": "high"}
   ```

2. **prioritize** - Set priority for a ticket
   ```json
   {"action_type": "prioritize", "ticket_id": "abc123", "priority": "critical"}
   ```

3. **respond** - Send a response to the customer
   ```json
   {"action_type": "respond", "ticket_id": "abc123", "response_text": "Thank you for contacting support..."}
   ```

4. **escalate** - Escalate to a specialized team
   ```json
   {"action_type": "escalate", "ticket_id": "abc123", "escalation_reason": "Complex technical issue", "target_team": "engineering"}
   ```

5. **request_info** - Ask customer for more information
   ```json
   {"action_type": "request_info", "ticket_id": "abc123", "response_text": "Could you please provide more details..."}
   ```

6. **close** - Close a resolved ticket
   ```json
   {"action_type": "close", "ticket_id": "abc123"}
   ```

#### Categories:
- technical, billing, account, general, sales, urgent

#### Priority Levels:
- low, medium, high, critical

#### Ticket Statuses:
- new, in_progress, waiting_customer, resolved, escalated, closed
"""


# ============================================================================
# Gradio Interface
# ============================================================================

with gr.Blocks(title="Support Ticket Triage Environment", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🎫 Support Ticket Triage Environment")
    gr.Markdown("An AI agent environment for learning customer support workflows")
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Environment Control")
            
            task_dropdown = gr.Dropdown(
                choices=[
                    ("Easy - Ticket Categorization", "categorize_ticket"),
                    ("Medium - Prioritize and Route", "prioritize_and_route"),
                    ("Hard - Full Workflow", "full_workflow")
                ],
                value="categorize_ticket",
                label="Select Task"
            )
            
            reset_btn = gr.Button("🔄 Reset Environment", variant="primary")
            
            gr.Markdown("### Take Action")
            
            action_input = gr.Textbox(
                label="Action (JSON)",
                placeholder='{"action_type": "categorize", "ticket_id": "...", "category": "technical", "priority": "high"}',
                lines=3
            )
            
            action_btn = gr.Button("▶️ Execute Action", variant="secondary")
        
        with gr.Column(scale=2):
            gr.Markdown("### Environment Status")
            output_display = gr.Markdown("Click 'Reset Environment' to start.")
            
            gr.Markdown("### Environment Information")
            with gr.Accordion("How to use this environment", open=False):
                info_display = gr.Markdown(get_environment_info())
    
    # Connect buttons
    reset_btn.click(
        fn=reset_environment,
        inputs=[task_dropdown],
        outputs=[output_display]
    )
    
    action_btn.click(
        fn=take_action,
        inputs=[action_input],
        outputs=[output_display]
    )
    
    # Footer
    gr.Markdown("""
    ---
    **Support Ticket Triage Environment** | Built with OpenEnv Framework | Meta Env Hackathon 2024
    """)


# ============================================================================
# Launch
# ============================================================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    demo.launch(server_name="0.0.0.0", server_port=port, share=False)