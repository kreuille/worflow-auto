# workflow-auto

> AI-powered n8n workflow generator — describe a workflow in plain language, Claude generates, audits, deploys and auto-debugs it.

---

## What it does

**workflow-auto** is a full-stack automation platform built on top of n8n and Claude. Describe a workflow in natural language — Claude generates the complete n8n JSON, audits it, fixes structural errors, injects test triggers, assigns auto-debugging and deploys it in ~20 seconds.

### Core features

- **Generate** — Natural language → production-ready n8n workflow, created and activated automatically
- **Audit** — Claude statically reviews the workflow JSON before deployment: empty credentials, missing connections, broken URLs, incorrect node types
- **Debug by ID** — Enter any workflow ID → Claude fetches, diagnoses and applies corrections via the n8n API
- **Auto-debug in production** — When a workflow crashes, the chain triggers automatically, attempts up to 3 corrections and notifies via Telegram
- **Run Trigger** — A webhook is injected into every generated workflow (`/webhook/run-{id}`) to allow programmatic test execution

---

## Architecture

```
Frontend (HTML/CSS/JS)
        │
        └── POST /webhook/generer-workflow
                │
        META Generator (n8n)
                │
                ├── phase: clarify ──→ Claude asks clarifying questions
                │
                ├── phase: generate
                │       └── Claude generates + audits JSON (single API call)
                │               └── Create → Inject triggers → Assign autodebug → Activate
                │
                └── phase: debug
                        └── Fetch workflow JSON → Claude fixes → PUT → Activate

Production crash:
  Workflow error → Autodebug → Auto-Corrector (x3 retries) → Telegram
```

---

## Stack

| Layer | Technology |
|-------|-----------|
| Orchestration | n8n self-hosted |
| AI | Claude Sonnet 4.6 (Anthropic API) |
| Infrastructure | Docker + Nginx Proxy Manager on VPS |
| Frontend | Pure HTML/CSS/JS |

---

## Workflows

| File | Role |
|------|------|
| `meta-generator.json` | Main orchestrator — handles all 3 phases |
| `autodebug.json` | Error trigger → Claude auto-fix |
| `auto-corrector.json` | Retry loop (max 3 attempts) |
| `execute-debug.json` | Trigger workflow + read last execution error |

---

## Setup

### 1. Clone

```bash
git clone https://github.com/YOUR_USERNAME/workflow-auto.git
cd workflow-auto
```

### 2. Replace placeholders

```python
import glob

SECRETS = {
    "YOUR_ANTHROPIC_API_KEY": "sk-ant-...",
    "YOUR_N8N_API_KEY": "eyJhbG...",
    "YOUR_N8N_URL": "https://n8n.yourdomain.com",
    "YOUR_AUTODEBUG_WORKFLOW_ID": "",  # Fill after importing autodebug.json
}

for f in glob.glob("workflows/*.json") + ["frontend/workflow-auto.html"]:
    with open(f) as fp: content = fp.read()
    for placeholder, value in SECRETS.items():
        if value: content = content.replace(placeholder, value)
    with open(f, 'w') as fp: fp.write(content)
    print(f"✓ {f}")
```

### 3. Import workflows into n8n

Import in this order:

1. `autodebug.json` → note the workflow ID
2. Set `YOUR_AUTODEBUG_WORKFLOW_ID` in `meta-generator.json`
3. Import `auto-corrector.json`, `execute-debug.json`, `meta-generator.json`
4. Activate all 4

n8n → **New workflow** → `...` → **Import from clipboard** → paste → **Save** → **Activate**

### 4. Configure CORS in Nginx Proxy Manager

NPM → your n8n proxy host → **Advanced**:

```nginx
location / {
    if ($request_method = 'OPTIONS') {
        add_header 'Access-Control-Allow-Origin' '*';
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS';
        add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization, X-N8N-API-KEY';
        add_header 'Access-Control-Max-Age' 1728000;
        add_header 'Content-Length' 0;
        return 204;
    }
    proxy_hide_header 'Access-Control-Allow-Origin';
    add_header 'Access-Control-Allow-Origin' '*' always;
    proxy_pass http://n8n:5678;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_cache_bypass $http_upgrade;
    proxy_read_timeout 120s;
    proxy_connect_timeout 120s;
    proxy_send_timeout 120s;
}
```

### 5. Configure n8n (docker-compose.yml)

```yaml
environment:
  - N8N_WEBHOOK_TIMEOUT=120
  - EXECUTIONS_TIMEOUT=120
  - N8N_CORS_ENABLED=true
  - N8N_CORS_ORIGINS=*
```

### 6. Launch frontend

```bash
cd frontend
python -m http.server 8080
# Open http://localhost:8080/workflow-auto.html
```

Set the webhook URL in the sidebar to `https://YOUR_N8N_URL/webhook/generer-workflow`

---

## Usage

### Generate a workflow

1. **Clarifier** tab — describe your workflow in plain language
2. **ANALYSER** — Claude asks clarifying questions (optional)
3. **GÉNÉRER** — generates, audits, deploys (~20s)

### Debug an existing workflow

1. **DÉBUGGER** tab → enter workflow ID
2. **ANALYSER ET CORRIGER** — Claude fetches JSON and applies static audit fixes
3. **DEBUG AVEC ERREUR** — paste a specific error message for targeted fix

---

## Auto-debug in production

Every generated workflow has `errorWorkflow` pointing to the Autodebug workflow. On crash:

```
Workflow crashes
  → Autodebug (Error Trigger)
      → Fetch workflow JSON
      → Claude analyzes + fixes
      → PUT corrected workflow
      → Auto-Corrector (up to 3 retries)
          → Wait 15s → verify execution
          → Telegram: success or failure
```

---

## License

MIT
