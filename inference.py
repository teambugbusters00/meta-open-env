"""
Baseline Inference Script for Support Ticket Triage Environment
This script demonstrates how to interact with the environment using an LLM agent.
"""

import asyncio
import os
import textwrap
import json
from typing import List, Optional, Dict, Any

from openai import OpenAI
import httpx

# ============================================================================
# Environment Configuration
# ============================================================================

# Required environment variables
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "")

# Environment configuration
ENV_URL = os.getenv("ENV_URL", "http://localhost:8000")
TASK_NAME = os.getenv("SUPPORT_TICKET_TASK", "categorize_ticket")
BENCHMARK = os.getenv("SUPPORT_TICKET_BENCHMARK", "support-ticket-triage")

# Inference parameters
MAX_STEPS = 10
TEMPERATURE = 0.7
MAX_TOKENS = 200
SUCCESS_SCORE_THRESHOLD = 0.5


# ============================================================================
# Logging Functions (Mandatory Format)
# ============================================================================

def log_start(task: str, env: str, model: str) -> None:
    """Log episode start"""
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    """Log each step"""
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    """Log episode end"""
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)


# ============================================================================
# Environment Client
# ============================================================================

class EnvironmentClient:
    """Client for interacting with the Support Ticket Environment"""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def reset(self, task_id: str = "categorize_ticket") -> Dict[str, Any]:
        """Reset the environment"""
        try:
            response = await self.client.post(
                f"{self.base_url}/reset",
                json={"task_id": task_id}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[DEBUG] Reset failed: {e}", flush=True)
            raise

    async def step(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a step in the environment"""
        try:
            response = await self.client.post(
                f"{self.base_url}/step",
                json=action
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[DEBUG] Step failed: {e}", flush=True)
            raise

    async def get_state(self) -> Dict[str, Any]:
        """Get current environment state"""
        try:
            response = await self.client.get(f"{self.base_url}/state")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[DEBUG] Get state failed: {e}", flush=True)
            raise

    async def health_check(self) -> bool:
        """Check if environment is healthy"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception:
            return False

    async def close(self):
        """Close the client"""
        await self.client.aclose()


# ============================================================================
# LLM Agent
# ============================================================================

SYSTEM_PROMPT = textwrap.dedent(
    """
    You are an AI assistant helping to triage customer support tickets.

    Your task is to:
    1. Read each ticket carefully
    2. Categorize it into one of: technical, billing, account, general, sales, urgent
    3. Assign priority: low, medium, high, critical
    4. For medium/hard tasks, you may also need to respond or escalate

    Available actions:
    - categorize: Set category and priority for a ticket
    - prioritize: Set priority for a ticket
    - respond: Send a response to the customer
    - escalate: Escalate to a specialized team
    - request_info: Ask customer for more information
    - close: Close a resolved ticket

    Always respond with a JSON object containing:
    {
        "action_type": "your_action",
        "ticket_id": "ticket_id",
        "category": "category_if_applicable",
        "priority": "priority_if_applicable",
        "response_text": "text_if_responding",
        "escalation_reason": "reason_if_escalating",
        "target_team": "team_if_escalating"
    }

    Be professional, thorough, and prioritize urgent issues appropriately.
    """
).strip()


def build_user_prompt(observation: Dict[str, Any]) -> str:
    """Build user prompt from observation"""
    tickets = observation.get("tickets", [])
    instructions = observation.get("instructions", "")
    current_step = observation.get("current_step", 0)
    max_steps = observation.get("max_steps", 10)
    last_result = observation.get("last_action_result", "")

    prompt = f"Instructions: {instructions}\n\n"
    prompt += f"Step {current_step}/{max_steps}\n\n"

    if last_result:
        prompt += f"Last action result: {last_result}\n\n"

    prompt += "Current Tickets:\n"
    for ticket in tickets:
        prompt += f"- ID: {ticket['id']}\n"
        prompt += f"  From: {ticket['customer_name']} ({ticket['customer_email']})\n"
        prompt += f"  Subject: {ticket['subject']}\n"
        prompt += f"  Content: {ticket['content']}\n"
        prompt += f"  Status: {ticket['status']}\n"
        if ticket.get('category'):
            prompt += f"  Category: {ticket['category']}\n"
        if ticket.get('priority'):
            prompt += f"  Priority: {ticket['priority']}\n"
        prompt += "\n"

    queue_status = observation.get("queue_status", {})
    if queue_status:
        prompt += f"Queue Status: {queue_status}\n\n"

    prompt += "What action should be taken next? Respond with a JSON object."

    return prompt


def get_llm_action(client: OpenAI, observation: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get action from LLM"""
    user_prompt = build_user_prompt(observation)

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )

        content = (completion.choices[0].message.content or "").strip()

        try:
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            action = json.loads(content)
            return action
        except json.JSONDecodeError:
            print(f"[DEBUG] Failed to parse LLM response as JSON: {content}", flush=True)
            return None

    except Exception as e:
        print(f"[DEBUG] LLM request failed: {e}", flush=True)
        return None


# ============================================================================
# Main Inference Loop
# ============================================================================

async def main() -> None:
    """Main inference loop"""

    llm_client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    env_client = EnvironmentClient(ENV_URL)

    if not await env_client.health_check():
        print(f"[ERROR] Environment not reachable at {ENV_URL}", flush=True)
        log_end(success=False, steps=0, score=0.0, rewards=[])
        return

    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=TASK_NAME, env=BENCHMARK, model=MODEL_NAME)

    try:
        result = await env_client.reset(TASK_NAME)
        observation = result.get("observation", {})

        for step in range(1, MAX_STEPS + 1):
            if result.get("done", False):
                break

            action = get_llm_action(llm_client, observation)

            if action is None:
                action = {
                    "action_type": "categorize",
                    "ticket_id": observation.get("tickets", [{}])[0].get("id", ""),
                    "category": "general",
                    "priority": "medium"
                }

            result = await env_client.step(action)
            observation = result.get("observation", {})
            reward = result.get("reward", 0.0)
            done = result.get("done", False)
            error = None

            rewards.append(reward)
            steps_taken = step

            action_str = f"{action.get('action_type', 'unknown')}({action.get('ticket_id', '')})"
            log_step(step=step, action=action_str, reward=reward, done=done, error=error)

            if done:
                break

        state = await env_client.get_state()
        score = state.get("score", 0.0)
        score = min(max(score, 0.0), 1.0)
        success = score >= SUCCESS_SCORE_THRESHOLD

    except Exception as e:
        print(f"[ERROR] Inference failed: {e}", flush=True)
        success = False

    finally:
        try:
            await env_client.close()
        except Exception:
            pass

        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)


if __name__ == "__main__":
    asyncio.run(main())