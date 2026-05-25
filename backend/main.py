from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import sqlite3
import uuid
import os
from datetime import datetime, timezone

app = FastAPI(title="Support CRM API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.environ.get("DB_PATH", "crm.db")

# ── Database ──────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS tickets (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id   TEXT    UNIQUE NOT NULL,
            customer_name  TEXT NOT NULL,
            customer_email TEXT NOT NULL,
            subject     TEXT NOT NULL,
            description TEXT NOT NULL,
            status      TEXT NOT NULL DEFAULT 'Open',
            priority    TEXT NOT NULL DEFAULT 'Medium',
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS notes (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT NOT NULL REFERENCES tickets(ticket_id),
            note_text TEXT NOT NULL,
            author    TEXT NOT NULL DEFAULT 'Agent',
            created_at TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()


init_db()

# ── Helpers ───────────────────────────────────────────────────────────────────

def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def next_ticket_id(conn):
    row = conn.execute("SELECT COUNT(*) as c FROM tickets").fetchone()
    return f"TKT-{(row['c'] + 1):04d}"


# ── Schemas ───────────────────────────────────────────────────────────────────

class CreateTicketBody(BaseModel):
    customer_name: str
    customer_email: str
    subject: str
    description: str
    priority: Optional[str] = "Medium"


class UpdateTicketBody(BaseModel):
    status: Optional[str] = None
    note: Optional[str] = None
    author: Optional[str] = "Agent"


# ── Routes ────────────────────────────────────────────────────────────────────

@app.post("/api/tickets", status_code=201)
def create_ticket(body: CreateTicketBody):
    conn = get_db()
    ticket_id = next_ticket_id(conn)
    ts = now_iso()
    conn.execute(
        """INSERT INTO tickets
           (ticket_id, customer_name, customer_email, subject, description, priority, status, created_at, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (ticket_id, body.customer_name, body.customer_email,
         body.subject, body.description, body.priority, "Open", ts, ts)
    )
    conn.commit()
    conn.close()
    return {"ticket_id": ticket_id, "created_at": ts}


@app.get("/api/tickets")
def list_tickets(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    conn = get_db()
    query = "SELECT ticket_id, customer_name, customer_email, subject, status, priority, created_at, updated_at FROM tickets WHERE 1=1"
    params = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if priority:
        query += " AND priority = ?"
        params.append(priority)
    if search:
        like = f"%{search}%"
        query += " AND (customer_name LIKE ? OR customer_email LIKE ? OR ticket_id LIKE ? OR subject LIKE ? OR description LIKE ?)"
        params.extend([like, like, like, like, like])
    query += " ORDER BY created_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/tickets/{ticket_id}")
def get_ticket(ticket_id: str):
    conn = get_db()
    row = conn.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket = dict(row)
    notes = conn.execute(
        "SELECT id, note_text, author, created_at FROM notes WHERE ticket_id = ? ORDER BY created_at ASC",
        (ticket_id,)
    ).fetchall()
    ticket["notes"] = [dict(n) for n in notes]
    conn.close()
    return ticket


@app.put("/api/tickets/{ticket_id}")
def update_ticket(ticket_id: str, body: UpdateTicketBody):
    conn = get_db()
    row = conn.execute("SELECT id FROM tickets WHERE ticket_id = ?", (ticket_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ts = now_iso()
    if body.status:
        conn.execute("UPDATE tickets SET status = ?, updated_at = ? WHERE ticket_id = ?",
                     (body.status, ts, ticket_id))
    if body.note:
        conn.execute("INSERT INTO notes (ticket_id, note_text, author, created_at) VALUES (?,?,?,?)",
                     (ticket_id, body.note, body.author or "Agent", ts))
        conn.execute("UPDATE tickets SET updated_at = ? WHERE ticket_id = ?", (ts, ticket_id))
    conn.commit()
    conn.close()
    return {"success": True, "updated_at": ts}


@app.get("/api/stats")
def stats():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) as c FROM tickets").fetchone()["c"]
    open_ = conn.execute("SELECT COUNT(*) as c FROM tickets WHERE status='Open'").fetchone()["c"]
    inprog = conn.execute("SELECT COUNT(*) as c FROM tickets WHERE status='In Progress'").fetchone()["c"]
    closed = conn.execute("SELECT COUNT(*) as c FROM tickets WHERE status='Closed'").fetchone()["c"]
    conn.close()
    return {"total": total, "open": open_, "in_progress": inprog, "closed": closed}


# ── Serve Frontend ────────────────────────────────────────────────────────────

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_DIR, "static")), name="static")


@app.get("/{full_path:path}", include_in_schema=False)
def serve_spa(full_path: str):
    return FileResponse(os.path.join(FRONTEND_DIR, "templates", "index.html"))
