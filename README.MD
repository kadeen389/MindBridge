# MindBridge - Mental Health Early Detection Web App

MindBridge is a web-based mental health support chatbot designed to provide early-stage support for young users. The system analyses user text, classifies emotional risk levels, and responds with supportive guidance and relevant signposting to trusted services such as NHS, Samaritans, and YoungMinds.

The final system uses a hybrid classification approach, combining:

a rule-based baseline classifier
an AI-based NLP classifier using the OpenAI API
a FastAPI backend
a frontend built with HTML, CSS, and JavaScript

## Features
- Web-based chatbot interface
- Anonymous session-based interaction
- Consent modal and ethical notice
- Hybrid risk classification (low / medium / high)
- Crisis escalation behaviour for high-risk inputs
- Dynamic support resources panel
- Evaluation scripts for classifier testing

## Project Structure

```text
MindBridge/
│
├── backend-ml/
│   ├── server.py
│   ├── model.py
│   ├── .env
│
├── frontend/
│   ├── index.html
│   ├── chat.html
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── chat.js
│
├── mindbridge-evaluation/
│   ├── evaluate_rule_model.py
│   └── evaluate_hybrid_model.py
│
└── README.md

## Requirements
Before running the project, make sure you have the following installed:

- Python 3.10+
- pip
- A modern web browser


Optional but useful:

- VS Code
- Live Server extension (for serving - frontend files)
- virtualenv or venv

## Run locally

### 1) Backend Setup Windows
```bash
cd backend-ml
python -m venv venv
venv\Scripts\activate
pip install -r ../requirements.txt
pip install scikit-learn matplotlib
python -m uvicorn server:app --reload --port 8000
```
### 1) Backend Setup Mac/Linux
```bash
cd backend-ml
python3 -m venv venv
source venv/bin/activate
pip install -r ../requirements.txt
pip install scikit-learn matplotlib
python -m uvicorn server:app --reload --port 8000
```

This should start the API locally at:
http://127.0.0.1:8000

You can test that it is running by visiting:
http://127.0.0.1:8000/health

If working correctly, the API should return a health/status response.

### 2) Frontend Setup
You can open index.html in your browser.

However, it is usually better to serve it locally.

For example:
Windows 
```bash
python -m http.server 5500 
```
Mac/Linux
```bash
python3 -m http.server 5500 
```

Then open `http://127.0.0.1:5500`

## Environment Variables

Create a `.env` file in the `backend-ml` folder and add:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4.1-mini

For security reasons, the OpenAI API key is not included in this repository. 
To run the system with full functionality, users should generate their own API key 
via the OpenAI platform and add it to the `.env` file.

A temporary API key can be provided for demonstration purposes upon request.

## How the System Works
- The user opens the website and accepts the consent modal.
- The user enters a message in the chatbot.
- The frontend sends the message to the FastAPI backend.

 The backend:
- runs the rule-based classifier
-runs the AI NLP classifier
combines both using the hybrid risk logic

The backend returns:
- a chatbot reply
- next-step guidance
- support resources if needed
- The frontend displays the response and support cards.

## Common Issues
Consent modal does not reappear

The consent state is stored in browser localStorage.

To reset it, open browser console and run:
``` bash
localStorage.removeItem("mindbridge_consent")
```
To reset everything:
```bash
localStorage.clear()
sessionStorage.clear()
```

## Technologies Used
- Python
- FastAPI
- OpenAI API
- Pydantic
- python-dotenv
- HTML
- CSS
- JavaScript
- scikit-learn
- matplotlib

## Author

Callum Walters
Final Year Project – University of Westminster
