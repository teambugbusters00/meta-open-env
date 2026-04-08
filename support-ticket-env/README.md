---
title: Support Ticket Triage
emoji: 🎫
colorFrom: blue
colorTo: green
sdk: docker
sdk_version: "3.10"
app_file: app.py
app_port: 8000
pinned: false
---

# Support Ticket Triage Environment

A real-world customer support ticket management environment for AI agents built with the OpenEnv framework. This environment simulates a customer support workflow where AI agents must triage, categorize, prioritize, and respond to support tickets.

## 🎯 Overview

This environment tests an AI agent's ability to handle realistic customer support scenarios including:

- **Ticket Categorization**: Classifying tickets into correct departments (Technical, Billing, Account, etc.)
- **Priority Assignment**: Determining urgency levels based on ticket content
- **Response Generation**: Crafting appropriate customer responses
- **Escalation Decisions**: Knowing when to escalate to specialized teams
- **Workflow Management**: Handling multiple tickets efficiently

## 📋 Tasks

The environment includes three tasks with increasing difficulty:

### 1. Ticket Categorization (Easy)
- **Task ID**: `categorize_ticket`
- **Max Steps**: 5
- **Description**: Categorize incoming support tickets into the correct department and priority level
- **Skills Tested**: Content analysis, classification, priority assessment

### 2. Prioritize and Route (Medium)
- **Task ID**: `prioritize_and_route`
- **Max Steps**: 10
- **Description**: Handle multiple tickets by prioritizing them correctly and routing to appropriate teams
- **Skills Tested**: Multi-task management, prioritization, routing decisions

### 3. Full Support Workflow (Hard)
- **Task ID**: `full_workflow`
- **Max Steps**: 15
- **Description**: Complete end-to-end support workflow including categorization, prioritization, drafting responses, and escalation when necessary
- **Skills Tested**: Complete customer support workflow, professional communication, judgment

## 🏗️ Architecture

### Observation Space

The agent receives observations containing:

```python
{
    "tickets": [
        {
            "id": "ticket_id",
            "customer_name": "Customer Name",
            "customer_email": "customer@example.com",
            "subject": "Ticket subject",
            "content": "Full ticket content",
            "status": "new|in_progress|waiting_customer|resolved|escalated|closed",
            "category": "technical|billing|account|general|sales|urgent",  # if set
            "priority": "low|medium|high|critical",  # if set
            "responses": ["response1", "response2"],  # if any
            "assigned_team": "team_name"  # if escalated
        }
    ],
    "current_step": 0,
    "max_steps": 10,
    "queue_status": {
        "new": 2,
        "in_progress": 1,
        "resolved": 0,
        "escalated": 0
    },
    "available_actions": ["categorize", "prioritize", "respond", "escalate", "request_info", "close"],
    "instructions": "Task description",
    "last_action_result": "Result of previous action"
}
```

### Action Space

The agent can take the following actions:

```python
{
    "action_type": "categorize|prioritize|respond|escalate|request_info|close",
    "ticket_id": "ticket_id_to_act_on",
    "category": "technical|billing|account|general|sales|urgent",  # for categorize
    "priority": "low|medium|high|critical",  # for categorize/prioritize
    "response_text": "Response message to customer",  # for respond/request_info
    "escalation_reason": "Reason for escalation",  # for escalate
    "target_team": "senior_support|engineering|management|billing_team"  # for escalate
}
```

### Reward Function

The environment provides dense rewards (0.0 to 1.0) based on:

1. **Categorization Accuracy** (60% weight):
   - Correct category: 0.6 points
   - Related category: 0.3 points
   - Incorrect category: 0.1 points
   - Correct priority: 0.4 points
   - Close priority: 0.2 points

2. **Response Quality** (for respond actions):
   - Relevant keywords: 60% of response score
   - Professionalism: 20% of response score
   - Appropriate length: 20% of response score

3. **Escalation Judgment**:
   - Appropriate escalation: 0.5-0.7 points
   - Over-escalation penalty: 0.1 points
   - Under-escalation: 0.2-0.4 points

4. **Task Completion Bonus**:
   - Completing all tickets: Additional score
   - Unresolved tickets penalty: -0.1 per ticket

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Docker (for containerized deployment)
- Hugging Face account (for deployment)

### Local Development

1. **Clone the repository**:
```bash
git clone <your-repo-url>
cd support-ticket-env
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Run the server**:
```bash
python -m server.app
```

The server will start on `http://localhost:8000`

4. **Test the environment**:
```bash
# Health check
curl http://localhost:8000/health

# Reset environment
curl -X POST http://localhost:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "categorize_ticket"}'

# Run inference
python inference.py
```

### Docker Deployment

1. **Build the Docker image**:
```bash
docker build -t support-ticket-env .
```

2. **Run the container**:
```bash
docker run -p 8000:8000 support-ticket-env
```

### Hugging Face Spaces Deployment

1. **Install Hugging Face CLI**:
```bash
pip install huggingface_hub
huggingface-cli login
```

2. **Deploy using OpenEnv**:
```bash
openenv push --repo-id your-username/support-ticket-triage
```

3. **Or deploy manually**:
   - Create a new Space on Hugging Face
   - Select "Docker" as the SDK
   - Push your Dockerfile and code
   - The Space will automatically build and deploy

## 📊 Evaluation

### Scoring

The final score is calculated as:

```
score = (correctness_ratio × 0.6 + completion_ratio × 0.4) - unresolved_penalty
```

Where:
- `correctness_ratio`: Proportion of correct actions
- `completion_ratio`: Proportion of completed tickets
- `unresolved_penalty`: 0.1 per unresolved ticket

### Success Thresholds

- **Easy Task**: 0.7 (70% score required)
- **Medium Task**: 0.6 (60% score required)
- **Hard Task**: 0.5 (50% score required)

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Server port | `8000` |
| `HOST` | Server host | `0.0.0.0` |
| `API_BASE_URL` | LLM API endpoint | `https://router.huggingface.co/v1` |
| `MODEL_NAME` | LLM model to use | `Qwen/Qwen2.5-72B-Instruct` |
| `HF_TOKEN` | Hugging Face API key | - |
| `SUPPORT_TICKET_TASK` | Default task | `categorize_ticket` |
| `SUPPORT_TICKET_BENCHMARK` | Benchmark name | `support-ticket-triage` |

## 📁 Project Structure

```
support-ticket-env/
├── env.py                 # Main environment implementation
├── inference.py           # Baseline inference script
├── server.py              # FastAPI server implementation
├── server/app.py          # Multi-mode deployment entrypoint
├── openenv.yaml           # OpenEnv configuration
├── Dockerfile             # Docker configuration
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## 🧪 Testing

### Run Local Tests

```bash
# Test environment directly
python -c "
from env import SupportTicketEnv
import asyncio

async def test():
    env = SupportTicketEnv()
    result = await env.reset('categorize_ticket')
    print('Environment initialized successfully!')
    print(f'Tickets: {len(result.observation.tickets)}')

asyncio.run(test())
```

### Validate Submission

Before submitting, run the validation script:

```bash
# Download validation script
curl -fsSL https://raw.githubusercontent.com/<your-repo>/main/scripts/validate-submission.sh -o validate-submission.sh
chmod +x validate-submission.sh

# Run validation (replace with your HF Space URL)
./validate-submission.sh https://your-username-support-ticket-triage.hf.space
```

## 🎓 Example Usage

### Using the Inference Script

```bash
# Set environment variables
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
export HF_TOKEN="your-huggingface-token"
export ENV_URL="http://localhost:8000"

# Run inference
python inference.py
```

### Expected Output Format

```
[START] task=categorize_ticket env=support-ticket-triage model=Qwen/Qwen2.5-72B-Instruct
[STEP] step=1 action=categorize(abc123) reward=0.80 done=false error=null
[STEP] step=2 action=categorize(def456) reward=0.60 done=false error=null
[STEP] step=3 action=prioritize(abc123) reward=0.80 done=false error=null
[STEP] step=4 action=respond(abc123) reward=0.70 done=false error=null
[STEP] step=5 action=close(abc123) reward=0.30 done=true error=null
[END] success=true steps=5 score=0.640 rewards=0.80,0.60,0.80,0.70,0.30
```

## 🤝 Contributing

This is a hackathon submission. For questions or issues, please contact the author.

## 📄 License

MIT License - See LICENSE file for details.

## 🙏 Acknowledgments

- Built with [OpenEnv](https://github.com/huggingface/openenv) framework
- Ticket templates inspired by real-world customer support scenarios
- Grading logic designed to provide meaningful learning signals

---

**Note**: This environment is designed for the Meta Env Hackathon Round 1 submission. It implements a complete, production-ready customer support ticket triage system that AI agents can learn from through the standard OpenEnv API.