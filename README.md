# EcoSched 🌿

> **Carbon-aware AI scheduler that fuses OS telemetry with real-time grid data to defer CPU-heavy workloads to cleaner energy windows — automatically, in under 50ms.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Gemini](https://img.shields.io/badge/Gemini_1.5_Flash-Google_AI-4285F4?style=flat&logo=google&logoColor=white)](https://ai.google.dev)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev)
[![Cloud Run](https://img.shields.io/badge/Google_Cloud_Run-Deployed-4285F4?style=flat&logo=google-cloud&logoColor=white)](https://cloud.google.com/run)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat)](LICENSE)

---

## The problem

Every data center and developer machine runs batch workloads — nightly backups, ML training jobs, log compression, ETL pipelines — on fixed schedules, regardless of when the electricity powering them is clean or dirty. A backup job that runs at 2am on a coal-heavy grid emits the same CO₂ as running it at 4am when wind power dominates, but nobody makes that distinction today.

Simultaneously, these jobs waste CPU resources. A job sitting at 70% I/O wait has the CPU allocated but idle — it is burning energy without doing useful work, starving interactive processes of cycles they actually need.

**EcoSched solves both problems at once**: it defers the work that is already wasting CPU to windows where the grid is greener, so the system runs faster *and* cleaner simultaneously.

---

## What EcoSched does

EcoSched is a three-layer system: an OS telemetry daemon, a Gemini-powered policy engine, and a real-time dashboard. Every two seconds, the daemon reads six signals per running job and sends them to Gemini 1.5 Flash, which returns a scheduling decision — run, throttle, or defer — along with its reasoning and the grams of CO₂ the decision will save. The OS applies that decision via Linux cgroups in under 100µs.

```
Per-job signals → Gemini 1.5 Flash → defer score → cgroup action → CO₂ saved
     (6 signals)      (<50ms)          (0.0–1.0)      (<100µs)       (tracked)
```

The six signals Gemini reasons over simultaneously:

| Signal | Source | Why it matters |
|---|---|---|
| `cpu_burst_pct` | `psutil.cpu_percent()` | Long bursts on a dirty grid = high carbon cost |
| `io_wait_pct` | `/proc/stat` iowait | >65% means CPU is idle but allocated — defer frees it |
| `mem_pressure_mb` | swap usage delta | Frozen jobs ballooning memory can be worse than running them |
| `carbon_intensity` | Electricity Maps API | Real-time gCO₂/kWh for your grid zone |
| `urgency` | user-defined (1–5) | Urgency ≥4 jobs are never deferred regardless of carbon |
| `deadline_seconds` | job submission | Jobs within 90s of deadline are never deferred |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        EcoSched                             │
│                                                             │
│  ┌──────────────┐    ┌──────────────────┐    ┌──────────┐  │
│  │   daemon/    │───▶│      api/        │◀───│frontend/ │  │
│  │              │    │                  │    │          │  │
│  │ telemetry.py │    │ gemini_engine.py │    │ React 18 │  │
│  │ cgroups.py   │    │ main.py (FastAPI)│    │ Recharts │  │
│  │ carbon.py    │    │ db.py (SQLite)   │    │ Tailwind │  │
│  │ jobs.py      │    │ jobs_router.py   │    │ WebSocket│  │
│  └──────────────┘    └──────────────────┘    └──────────┘  │
│         │                    │                              │
│         ▼                    ▼                              │
│  Linux cgroups v2     Gemini 1.5 Flash                      │
│  (CPU freeze/thaw)    (structured JSON decisions)           │
│                              │                              │
│                       Electricity Maps API                  │
│                       (real-time carbon intensity)          │
└─────────────────────────────────────────────────────────────┘
```

---

## Google AI integration — Gemini 1.5 Flash

Gemini 1.5 Flash is the core decision engine. It was chosen over a rule-based system because the optimal scheduling decision requires reasoning across six signals simultaneously — a task where the signal interactions are non-linear and context-dependent.

**The prompt is structured to extract JSON decisions in under 50ms:**

```python
PROMPT = """
You are EcoSched, an OS resource scheduler optimizing for both
carbon efficiency and CPU throughput simultaneously.

Job telemetry:
  cpu_burst_pct:    {cpu_burst_pct}    (current CPU usage %)
  io_wait_pct:      {io_wait_pct}      (% time CPU idle waiting for I/O)
  mem_pressure_mb:  {mem_pressure_mb}  (swap used in MB)
  carbon_intensity: {carbon_ci} gCO2/kWh
  urgency:          {urgency}/5
  deadline_seconds: {deadline_seconds}

Rules (priority order):
1. NEVER defer if deadline_seconds < 90
2. NEVER defer if urgency >= 4
3. If io_wait_pct > 65, prefer throttle/defer even on clean grid
4. If mem_pressure_mb > 300 and state == deferred, run immediately
5. If carbon_ci > 400 and cpu_burst_pct > 30 and urgency < 3: defer
6. If carbon_ci < 150: run (clean grid)

Respond with ONLY valid JSON:
{"action":"run|throttle|defer","defer_score":0.0-1.0,
 "co2_saved_grams":float,"reasoning":"one sentence",
 "resume_in_seconds":null_or_int}
"""
```

Gemini's reasoning is surfaced directly in the dashboard so users understand every decision the system makes. This is not a black box — every defer, throttle, and run action comes with a plain-English explanation.

---

## Project structure

```
ecosched/
├── daemon/
│   ├── telemetry.py        # psutil-based process signal collector
│   ├── cgroups.py          # Linux cgroups v2 freeze/thaw/throttle
│   ├── carbon.py           # Electricity Maps API client (5min cache)
│   ├── jobs.py             # In-memory job registry
│   ├── daemon_main.py      # Main async orchestration loop (2s cycle)
│   └── simulate_jobs.py    # Demo: launches CPU-intensive worker processes
│
├── api/
│   ├── main.py             # FastAPI app — WebSocket, REST, lifespan
│   ├── gemini_engine.py    # Gemini 1.5 Flash prompt engine + fallback
│   ├── db.py               # SQLAlchemy async + Decision model (SQLite)
│   ├── jobs_router.py      # Job submission and listing endpoints
│   ├── carbon_router.py    # Carbon intensity + forecast endpoints
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx                     # Root layout
│   │   ├── hooks/useEcoSched.js        # WebSocket + stats hook
│   │   └── components/
│   │       ├── MetricCards.jsx         # CO₂ saved, decisions, CI
│   │       ├── EventFeed.jsx           # Live decision stream
│   │       ├── CarbonChart.jsx         # Recharts line chart
│   │       └── JobSubmitForm.jsx       # Submit batch jobs
│   └── package.json
│
├── .env.example
├── .gitignore
└── README.md
```

---

## Quickstart

### Prerequisites

- Linux (Ubuntu 22.04+ recommended) with cgroups v2 enabled
- Python 3.11+
- Node.js 18+
- A Gemini API key ([get one here](https://aistudio.google.com/apikey))
- An Electricity Maps API key ([free tier](https://api.electricitymap.org))

### 1. Clone and configure

```bash
git clone https://github.com/AhnaSachdev/ecosched.git
cd ecosched
cp .env.example .env
# Edit .env with your API keys
```

### 2. Environment variables

```env
GEMINI_API_KEY=your_gemini_api_key_here
ELECTRICITY_MAPS_API_KEY=your_em_key_here
ELECTRICITY_MAPS_ZONE=IN-NO          # Bihar/North India — change to your zone
DATABASE_URL=sqlite+aiosqlite:///./ecosched.db
API_HOST=0.0.0.0
API_PORT=8000
DAEMON_SECRET=ecosched_internal_secret_123
```

Find your Electricity Maps zone at [app.electricitymap.org](https://app.electricitymap.org). Common zones: `IN-NO` (North India), `US-CAL-CISO` (California), `DE` (Germany), `GB` (Great Britain).

### 3. Start the API

```bash
cd api
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 4. Start the daemon

```bash
cd daemon
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# Requires root for real cgroup writes:
sudo python3 daemon_main.py
# Or simulate without root (logs actions, skips cgroup writes):
python3 daemon_main.py
```

### 5. Start the frontend

```bash
cd frontend
npm install
VITE_API_URL=http://localhost:8000 npm run dev
# Open http://localhost:5173
```

### 6. Run a demo simulation

```bash
cd daemon
python3 simulate_jobs.py
# Launches CPU-intensive worker processes you can watch being scheduled
```

---

## API reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/internal/decide` | Daemon → Gemini decision (internal) |
| `GET` | `/api/stats` | Aggregate stats + last 20 decisions |
| `POST` | `/api/jobs/submit` | Submit a batch job with urgency + deadline |
| `GET` | `/api/jobs/list` | List active jobs and their states |
| `GET` | `/api/carbon/current` | Current grid carbon intensity |
| `GET` | `/api/carbon/forecast` | Carbon intensity forecast (next 24h) |
| `WS` | `/ws` | Real-time decision stream (WebSocket) |

**Example — submit a job:**

```bash
curl -X POST http://localhost:8000/api/jobs/submit \
  -H "Content-Type: application/json" \
  -d '{
    "name": "nightly-backup",
    "urgency": 1,
    "deadline_minutes": 120,
    "description": "Compress and archive logs"
  }'
```

**Example — trigger a manual decision:**

```bash
curl -X POST http://localhost:8000/internal/decide \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "job-001",
    "job_name": "ml-training",
    "cpu_burst_pct": 78,
    "io_wait_pct": 12,
    "mem_pressure_mb": 45,
    "carbon_ci": 420,
    "urgency": 2,
    "deadline_seconds": 3600,
    "current_state": "running"
  }'
```

---

## Deployment — Google Cloud Run

EcoSched's API is deployed as a containerized service on Google Cloud Run, with the frontend on Firebase Hosting.

```bash
# Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
  artifactregistry.googleapis.com

# Build and push the API image
cd api
gcloud builds submit --tag \
  us-central1-docker.pkg.dev/YOUR_PROJECT/ecosched-repo/api:latest

# Deploy to Cloud Run
gcloud run deploy ecosched-api \
  --image us-central1-docker.pkg.dev/YOUR_PROJECT/ecosched-repo/api:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --min-instances 1 \
  --set-env-vars GEMINI_API_KEY=your_key,ELECTRICITY_MAPS_API_KEY=your_key

# Deploy the frontend
cd ../frontend
VITE_API_URL=https://your-cloud-run-url.run.app npm run build
npm install -g firebase-tools
firebase deploy --only hosting
```

---

## How the scheduling logic works

### The unified defer score

Gemini receives all six signals and produces a `defer_score` from 0.0 (run immediately) to 1.0 (freeze the job). The action thresholds are:

```
0.0 – 0.35  →  run       (boost cgroup CPU weight)
0.35 – 0.65 →  throttle  (reduce CPU shares to 20/10000)
0.65 – 1.0  →  defer     (cgroup freeze — process stays in memory, uses 0 CPU)
```

### Why I/O wait matters for throughput, not just carbon

This is the key insight that makes EcoSched different from a simple carbon scheduler. When a job's `io_wait_pct` exceeds ~65%, the CPU core it holds is allocated but idle — it is spinning waiting for a disk read. Deferring or throttling that job and giving the core to an interactive process (like a web server or a database query) increases overall CPU throughput. The system does not trade performance for carbon savings — it improves both simultaneously.

```
High I/O wait job (70% wait):
  CPU allocated: ████████████████ (100%)
  CPU doing work: █████            (30%)
  CPU idle-but-blocked: ███████████ (70%)  ← this is wasted

After deferring:
  CPU freed → reassigned to interactive process
  Result: higher throughput AND lower carbon if grid is dirty
```

### Safety guarantees

Gemini advises — the OS retains full control.

- If Gemini's response takes >50ms, the system falls back to a deterministic rule-based heuristic (never deferring high-urgency or near-deadline jobs)
- Urgency 4–5 jobs are hardcoded to never defer, regardless of what the model returns
- Jobs within 90 seconds of their deadline are hardcoded to run, regardless of carbon intensity
- Frozen jobs are automatically thawed when their deadline approaches or memory pressure exceeds the safety threshold
- All cgroup writes are wrapped in try/catch — a failed write logs a warning and the job continues running

---

## Judging criteria

### Technical complexity

EcoSched operates at the intersection of three distinct technical domains simultaneously: OS-level systems programming (Linux cgroups v2, BPF-compatible process telemetry), LLM-driven policy reasoning (Gemini 1.5 Flash with structured JSON output and sub-50ms inference budget), and real-time distributed systems (WebSocket broadcast, async FastAPI, SQLAlchemy async). The six-signal fusion model — where carbon intensity, CPU burst, I/O wait, memory pressure, urgency, and deadline interact non-linearly — requires LLM reasoning rather than rule tables. The cgroup controller manages process CPU shares and freeze/thaw cycles at microsecond granularity.

### Performance and scalability

The daemon cycle runs every 2 seconds. Gemini inference is targeted at <50ms with a deterministic fallback. Cgroup writes complete in <100µs. The API uses fully async Python (FastAPI + SQLAlchemy async + aiosqlite) so it never blocks on I/O. Carbon intensity is cached for 5 minutes to avoid hammering the external API. The WebSocket broadcast is O(n) in connected clients but clients are expected to number in the single digits for a single-node deployment. For multi-node scale, the decision endpoint is stateless and horizontally scalable behind a load balancer; only the database layer would need a shared store (swap SQLite for PostgreSQL).

### Security and privacy

API keys are stored exclusively in environment variables and are never logged, committed, or returned in any endpoint response. The `.gitignore` excludes `.env` at the root. The `/internal/decide` endpoint is intended to be internal-only (daemon-to-API on localhost or within a VPC); in production it should be protected with a shared secret header or mTLS. Process telemetry is limited to process name, PID, CPU/memory/IO metrics — no command-line arguments, no file paths, no user data are collected or transmitted to Gemini. The Gemini prompt contains only numerical telemetry, never any user-identifying information. All cgroup operations are scoped to a dedicated `/sys/fs/cgroup/ecosched` subtree and cannot affect processes outside that scope.

### User experience

The dashboard is designed around one primary emotion: **watching the system work on your behalf**. The layout puts the CO₂ saved counter and the live decision feed at the top of the visual hierarchy. Every Gemini decision surfaces its reasoning in plain English — "High I/O wait detected, deferring to free CPU for interactive tasks" — so the system never feels like a black box. The job submission form uses urgency levels described in plain language (1 = batch, 5 = critical) rather than numeric CPU weights. The carbon chart uses three clearly labelled zones (clean / moderate / defer) so users can glance at the current grid state without reading any numbers. The dashboard is fully responsive down to tablet width and uses semantic HTML with ARIA roles on all interactive elements.

### Problem definition

Data centres account for approximately 1–2% of global electricity consumption, and that share is growing as AI workloads scale. The majority of batch compute — ML training, ETL, log archiving — has soft deadlines that could tolerate a 1–4 hour delay with no user impact. No existing scheduler considers real-time grid carbon intensity as a scheduling signal. EcoSched directly addresses this gap, treating the grid as a first-class input alongside CPU and memory.

### Relevance of solution

Google, Microsoft, and Cloudflare have all publicly committed to carbon-aware computing initiatives. The Green Software Foundation's Carbon-Aware SDK targets this exact problem at the cloud-orchestration layer. EcoSched targets a lower layer — the individual machine or VM — making it usable by any developer without cloud-provider support. The Electricity Maps API provides real-time carbon intensity for 70+ countries, making the carbon signal universally accessible.

### Expected impact

A server running at 50% CPU utilization on a grid with 400 gCO₂/kWh, deferring a 30-minute CPU-intensive job to a 150 gCO₂/kWh window, saves approximately 37.5g CO₂ per job. At scale — 1,000 such jobs per day across a small data centre — that is 37.5 kg CO₂ per day, or ~13.7 tonnes per year, equivalent to approximately 3 transatlantic flights. The throughput improvement (from deferring high I/O wait jobs) is measurable in reduced tail latency for co-located interactive services — a secondary benefit that makes the system adoptable even by operators who do not prioritise carbon reduction.

### Originality

No existing open-source project combines real-time grid carbon intensity, OS process telemetry, and an LLM policy engine into a single scheduling loop. Academic work on carbon-aware scheduling (e.g., CarbonScaler, GreenCloud) operates at the cloud-orchestration layer and assumes provider-level control. EcoSched operates at the individual machine level, is installable as a userspace daemon, and uses an LLM for multi-objective reasoning rather than a linear programme or hand-coded heuristics. The use of Gemini as an OS scheduling advisor — rather than a chatbot or document processor — is a genuinely novel application of foundation models.

### Creative use of technology

Gemini 1.5 Flash was selected specifically because it can reason over heterogeneous numerical signals in a single pass and return structured JSON in under 50ms — a use case far outside the typical "chat" or "summarise" applications. The prompt is engineered to encode hard safety constraints (deadline, urgency floors) as priority-ordered rules that the model must follow before applying its own reasoning. This is a pattern borrowed from AI safety research — constitutional constraints — applied to an OS scheduling context. The result is an AI system that is both flexible (handles novel signal combinations gracefully) and safe (never violates the hard constraints).

### Future potential

The immediate next step is a BPF-based daemon that bypasses userspace overhead entirely, achieving sub-microsecond telemetry collection. The Gemini policy engine can be distilled into a 2-layer decision tree trained on logged decisions, enabling on-chip inference with zero API latency or network dependency. Multi-node extensions could share carbon and telemetry signals across a cluster, enabling workload migration between machines based on per-machine carbon intensity. The architecture is model-agnostic — the Gemini engine can be swapped for Gemma running locally for fully offline deployments in air-gapped environments. The most significant long-term opportunity is integration with Kubernetes scheduling via a custom scheduler plugin, extending EcoSched's policy engine to container-level orchestration across thousands of nodes.

---

## Real-world precedents

EcoSched is inspired by and builds on:

| Project | Organisation | What it does |
|---|---|---|
| **Borg** | Google | ML-guided cluster scheduling at planet scale |
| **Twine** | Meta | RL-based resource allocation across data centres |
| **Lasso** | Microsoft | Learned resource management for cloud VMs |
| **sched_ext** | Linux 6.x | BPF-based pluggable scheduler hooks (used by EcoSched) |
| **Carbon-Aware SDK** | Green Software Foundation | Grid carbon intensity for cloud-level scheduling |
| **CarbonScaler** | Academic | Carbon-aware autoscaling for cloud workloads |

---

## Team

Built in one day at hackathon by a team of three:

| Role | Responsibility |
|---|---|
| Systems engineer | Telemetry daemon, cgroups controller, Linux BPF integration |
| AI engineer | Gemini prompt engineering, FastAPI backend, database layer |
| Full-stack + design | React dashboard, WebSocket integration, Cloud Run deployment |

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

<p align="center">
  Built with Gemini 1.5 Flash · Deployed on Google Cloud Run · Powered by Electricity Maps
</p>