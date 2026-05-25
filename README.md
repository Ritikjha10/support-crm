# SupportDesk — Customer Support CRM

A full-stack support ticket management system built with **FastAPI**, **SQLite**, and a clean HTML/Tailwind frontend.

## Tech Stack
- **Backend:** Python 3.11 + FastAPI + Uvicorn
- **Database:** SQLite (zero-config, file-based)
- **Frontend:** Vanilla HTML + Tailwind CSS (CDN) + Vanilla JS
- **Deploy:** Railway.app

## Features
1. **Create Tickets** — customer name, email, subject, description, priority
2. **List All Tickets** — clean table with ID, name, email, subject, priority, status, date
3. **Search** — real-time search across names, IDs, emails, and descriptions
4. **Filter by Status** — Open / In Progress / Closed
5. **View & Update Tickets** — full detail page, status updates, notes/comments with author
6. **Dashboard** — stats overview (total, open, in progress, closed)

## Local Setup

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/support-crm.git
cd support-crm

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy env file
cp .env.example .env

# 5. Run the app
uvicorn backend.main:app --reload --port 8000
```

Open http://localhost:8000 in your browser.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/tickets` | Create a new ticket |
| GET | `/api/tickets` | List tickets (supports `?status=Open&search=query`) |
| GET | `/api/tickets/{ticket_id}` | Get a single ticket with notes |
| PUT | `/api/tickets/{ticket_id}` | Update status or add a note |
| GET | `/api/stats` | Get ticket counts by status |

## Database Schema

**tickets**
```
id, ticket_id (TKT-0001), customer_name, customer_email,
subject, description, status, priority, created_at, updated_at
```

**notes**
```
id, ticket_id (fk), note_text, author, created_at
```

## Deploy to Railway

1. Push this repo to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Select your repo — Railway auto-detects Python via `Procfile`
4. Your app will be live at `https://your-app.railway.app`

No environment variables needed for basic deployment (SQLite is file-based).

## Project Structure

```
support-crm/
├── backend/
│   └── main.py          # FastAPI app, routes, DB logic
├── frontend/
│   └── templates/
│       └── index.html   # Single-page frontend (SPA)
├── requirements.txt
├── Procfile
├── railway.toml
├── .env.example
├── .gitignore
└── README.md
```
