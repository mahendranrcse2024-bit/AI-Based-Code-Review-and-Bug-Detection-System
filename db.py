import json, sqlite3
from datetime import datetime, timezone
from pathlib import Path
from app.config import DB_PATH

def now(): return datetime.now(timezone.utc).isoformat()

def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c=sqlite3.connect(DB_PATH); c.row_factory=sqlite3.Row; return c

def init_db():
    with connect() as c:
        c.executescript('''CREATE TABLE IF NOT EXISTS reviews (id INTEGER PRIMARY KEY, project TEXT NOT NULL, version TEXT NOT NULL, review_date TEXT NOT NULL, metadata TEXT NOT NULL, source TEXT NOT NULL); CREATE TABLE IF NOT EXISTS findings (id INTEGER PRIMARY KEY AUTOINCREMENT, review_id INTEGER NOT NULL, data TEXT NOT NULL, FOREIGN KEY(review_id) REFERENCES reviews(id) ON DELETE CASCADE); CREATE TABLE IF NOT EXISTS ai_results (id INTEGER PRIMARY KEY AUTOINCREMENT, finding_id INTEGER, data TEXT NOT NULL, created_at TEXT NOT NULL);''')

def create_review(project, version, source, metadata, findings):
    init_db()
    with connect() as c:
        cur=c.execute("INSERT INTO reviews(project,version,review_date,metadata,source) VALUES(?,?,?,?,?)",(project,version,now(),json.dumps(metadata),source)); rid=cur.lastrowid
        for item in findings: c.execute("INSERT INTO findings(review_id,data) VALUES(?,?)",(rid,json.dumps(item)))
    return rid

def get_review(rid):
    init_db()
    with connect() as c:
        r=c.execute("SELECT * FROM reviews WHERE id=?",(rid,)).fetchone();
        if not r: return None
        fs=c.execute("SELECT data FROM findings WHERE review_id=? ORDER BY json_extract(data,'$.line')",(rid,)).fetchall()
        return {"id":r["id"],"project":r["project"],"version":r["version"],"review_date":r["review_date"],"metadata":json.loads(r["metadata"]),"source":r["source"],"findings":[json.loads(x[0]) for x in fs]}

def list_reviews():
    init_db()
    with connect() as c:
        rows=c.execute("SELECT id,project,version,review_date,metadata FROM reviews ORDER BY id DESC").fetchall()
        out=[]
        for r in rows:
            count=c.execute("SELECT COUNT(*) FROM findings WHERE review_id=?",(r["id"],)).fetchone()[0]
            out.append({"id":r["id"],"project":r["project"],"version":r["version"],"review_date":r["review_date"],"finding_count":count})
        return out

def update_status(rid, finding_id, status):
    with connect() as c:
        rows=c.execute("SELECT id,data FROM findings WHERE review_id=?",(rid,)).fetchall()
        for row in rows:
            data=json.loads(row["data"])
            if data.get("id")==finding_id: data["status"]=status; c.execute("UPDATE findings SET data=? WHERE id=?",(json.dumps(data),row["id"])); return True
    return False

def delete_review(rid):
    with connect() as c: c.execute("DELETE FROM reviews WHERE id=?",(rid,))
