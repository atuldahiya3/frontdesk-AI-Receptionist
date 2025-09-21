# Salon X Frontdesk Test
->A text-based AI receptionist system for a hair salon, Salon X, built with Python, Flask, and LiveKit Agents. The project ->includes an AI agent that answers customer questions and escalates unknown queries to a supervisor, and a web-based supervisor dashboard -> to manage and resolve requests.
-> Features

# AI Receptionist (agent.py):

-> Answers customer questions from a SQLite knowledge base (KB).
-> Uses exact, near-exact (via difflib), and keyword-based matching.
-> Escalates unanswered questions to a supervisor and stores them in the database.
-> Retrieves answers for previously resolved questions to avoid re-escalation.
-> Runs in console mode with a manual text input loop.


# Supervisor Dashboard (app.py):

-> Displays pending requests, request history, and the KB.
-> Allows supervisors to resolve requests, updating the KB.
-> Built with Flask and styled with Tailwind CSS.
-> Features sortable tables, auto-refresh (every 30s), and flash messages.


# Database (db.py):

-> SQLite database (db.sqlite) stores the KB and help requests.
-> Supports question/answer pairs and request tracking.



# Prerequisites

-> Python 3.11+
-> uv (Python package manager)
-> Ollama (for llama3.1:8b model)
-> SQLite
-> Docker (optional, for LiveKit server)
-> Web browser (for dashboard)

# Installation

-> Clone the Repository:
-> git clone https://github.com/atuldahiya3/frontdesk-AI-Receptionist
-> cd frontdesk-ai-receptionist


# Set Up Virtual Environment:
-> uv venv
-> source .venv/bin/activate  # macOS/Linux
-> .venv\Scripts\activate     # Windows


# Install Dependencies:
-> uv pip install livekit-agents livekit-plugins-openai flask


# Configure Ollama:

-> Install Ollama and start the server:ollama serve


-> Pull the model:ollama pull llama3.1:8b




# Set Environment Variables:

-> Create .env.local in the project root:LIVEKIT_API_KEY=dummy-key
-> LIVEKIT_API_SECRET=dummy-secret
-> LIVEKIT_URL=wss://localhost:7880


# Dummy values work for mock room testing.


# Initialize Database:
-> python db.py

-> Creates db.sqlite with initial KB.


# Project Structure
frontdesk-ai-receptionist/
├── agent.py          # AI receptionist logic
├── app.py            # Flask supervisor dashboard
├── db.py             # Database utilities
├── db.sqlite         # SQLite database
├── templates/
│   ├── index.html    # Dashboard UI
│   ├── resolve.html  # Resolve request form
│   ├── 404.html      # Custom 404 page
├── .env.local        # Environment variables
├── README.md         # This file

# Usage
-> AI Receptionist

-> Run the agent:uv run agent.py console


# At the prompt, enter questions:
-> "What are the saloon timings?" → "We are open from 9 AM to 6 PM, Monday to Saturday."
-> "What is the price of a perm?" → Escalates to supervisor


-> Type quit or Ctrl+C to exit.

# Supervisor Dashboard

-> Start the Flask server:python app.py


-> Open http://localhost:5000 in a browser.
-> Actions:
-> View pending requests and resolve them with answers.
-> Check request history (sortable by ID, status, etc.).
-> Inspect the KB for learned answers.



# Testing Resolved Questions

-> Ask "What is the price of a perm?" in the agent console (escalates).
-> In the dashboard, resolve the request (e.g., "$80").
-> Ask the same question again in the console:Answer (exact match): $80



# Database Inspection

-> Help requests:sqlite3 db.sqlite "SELECT * FROM help_requests;"
-> 

-> Knowledge base:sqlite3 db.sqlite "SELECT * FROM knowledge;"



# Troubleshooting

-> Agent Not Responding:

-> Verify Ollama is running (ollama serve) and llama3.1:8b is pulled.
-> Check .env.local for correct variables.
-> Inspect KB:python -c "from db import load_kb; print(load_kb())"




# Dashboard Issues:

-> Ensure db.sqlite exists and is populated.
-> Check Flask console for errors.


# Question Re-escalation:

-> Verify KB contains resolved question:sqlite3 db.sqlite "SELECT * FROM knowledge WHERE question = 'What is the price of a perm?';"