# Support Ticket Triage Submission

This repository is intentionally structured as a single deployable environment inside `support-ticket-env/`.

## Deployable Environment

```text
support-ticket-env/
├── openenv.yaml
├── env.py
├── inference.py
├── pyproject.toml
├── uv.lock
├── Dockerfile
└── server/
    └── app.py
```

## Usage

```bash
cd support-ticket-env
openenv validate
python -m server.app
python inference.py
```

See `support-ticket-env/README.md` for full documentation.
