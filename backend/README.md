# Blood Donor Matching System — Backend

FastAPI backend with Claude Agents SDK for AI-powered emergency blood donor matching in Karachi.

## Setup

### 1. Install dependencies

```bash
cd backend/
pip install fastapi uvicorn[standard] "sqlalchemy[asyncio]" aiosqlite anthropic pydantic pydantic-settings python-dotenv faker pandas numpy httpx
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and set your ANTHROPIC_API_KEY
```

### 3. Generate donor data and seed the database

```bash
python data/generate_donors.py   # Creates data/donors.csv (200 donors)
python seeds/seed_donors.py       # Loads CSV into blood_donor.db
```

### 4. Run the server

```bash
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/chat` | Submit blood request message (English/Urdu) |
| GET | `/api/requests` | List all blood requests |
| GET | `/api/requests/{id}` | Request detail with waves and donor responses |
| GET | `/api/donors` | List donors (filter: blood_group, area, health_status) |
| GET | `/api/dashboard/stats` | Aggregate dashboard statistics |
| WS | `/ws/dashboard` | Real-time WebSocket event stream |
| GET | `/health` | Health check |

---

## Architecture

```
POST /api/chat
  |
  +--> Request Extraction Agent (Claude Opus 4.8)
  |     Structured NLP: English + Urdu/Roman Urdu -> BloodRequestExtraction
  |
  +--> Save BloodRequest to SQLite
  |
  +--> Background Task: Orchestrator Agent (Claude Opus 4.8 + Tool Use)
        |
        +--> Tool: get_eligible_donors
        |     Filter by blood_group + 56-day eligibility
        |     Rank by distance / response_rate / availability
        |
        +--> Tool: launch_outreach_wave
        |     Contacts top-N donors in parallel
        |     Simulates responses (70% accept, 20% reject, 10% unavailable)
        |     Saves DonorResponse to DB
        |     Broadcasts events via WebSocket
        |
        +--> Tool: check_fulfillment_status
              If confirmed < needed -> next wave (max 5 waves)
              Broadcasts request_fulfilled or request_failed
```

### WebSocket Events

Connect to `ws://localhost:8000/ws/dashboard` to receive live events:

```json
{ "event": "wave_started",     "request_id": "...", "wave_number": 1, "data": {"donor_count": 10} }
{ "event": "donor_response",   "request_id": "...", "wave_number": 1, "data": {"donor": {...}, "intent": "accepted"} }
{ "event": "wave_completed",   "request_id": "...", "wave_number": 1, "data": {"accepted": 5, "rejected": 3, "unavailable": 2} }
{ "event": "request_fulfilled","request_id": "...", "data": {"confirmed_donors": 3, "total_waves": 1} }
{ "event": "request_failed",   "request_id": "...", "data": {"confirmed_donors": 1, "total_waves": 5} }
```

### Example Chat Request

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "abc123",
    "message": "Emergency! Need 2 units of O+ blood at Aga Khan Hospital in Saddar. Critical patient."
  }'
```

---

## Claude Agents SDK Usage

| Agent | Model | SDK Feature | Purpose |
|---|---|---|---|
| `request_extractor.py` | claude-opus-4-8 | `messages.create` + `output_config.format` (JSON schema) | NLP extraction from English/Urdu |
| `response_classifier.py` | claude-haiku-4-5 | `messages.create` + `output_config.format` | Classify donor reply intent |
| `orchestrator.py` | claude-opus-4-8 | Manual agentic loop + tool_use | Drive wave-based matching flow |

All agents use `thinking: {"type": "adaptive"}` (Opus 4.8).

---

## Donor Ranking Weights

| Factor | Weight | Formula |
|---|---|---|
| Distance | 40% | `1 - (dist_km / 30)` (Haversine) |
| Eligibility | 25% | `1.0` if last donation > 56 days ago |
| Response rate | 20% | Historical acceptance rate |
| Availability | 10% | `1.0` if health_status == available |
| Fatigue | 5% | `1 - (total_donations / 30)` |
