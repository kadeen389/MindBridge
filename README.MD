# MindBridge - Mental Health Early Detection Web App

A final-year project web application for early mental health support in young people.

## Features
- Responsive landing page and full chat interface
- FastAPI backend with risk-aware routing
- Optional OpenAI integration for stronger conversational quality
- Fallback local response system when no API key is configured
- Trusted support resources surfaced in the UI

## Run locally

### 1) Backend
```bash
cd backend-ml
python -m venv venv
source venv/bin/activate
pip install -r ../requirements.txt
cp ../.env.example ../.env
# Add your OPENAI_API_KEY to ../.env if you want AI responses
python -m uvicorn server:app --reload --port 8000
```

### 2) Frontend
Open `index.html` directly in the browser, or serve the folder with a local server.
For example:
```bash
python -m http.server 5500
```
Then open `http://127.0.0.1:5500`

## API endpoints
- `GET /health`
- `POST /chat`

### Sample request
```json
{
  "text": "I feel anxious and overwhelmed lately.",
  "session_id": "demo-session",
  "history": []
}
```
