from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from pydantic import BaseModel, Field
from app.core.preprocessing import validate_source, ValidationError
from app.core.static_analyzer import analyze
from app.database.db import init_db, create_review, get_review, list_reviews, update_status, delete_review
from app.core.report_generator import json_report, csv_report, html_report
from app.core.ai_analyzer import explain, AIUnavailable

app=FastAPI(title="AI-Based Code Review and Bug Detection", version="1.0.0", description="Static analysis first; AI explanations are optional and advisory.")
init_db()
class ReviewRequest(BaseModel):
    filename: str = Field(default="main.py", max_length=255)
    code: str = Field(min_length=1)
    project: str = Field(default="Untitled", max_length=100)
    version: str = Field(default="1.0", max_length=50)
    language: str|None = None
class StatusRequest(BaseModel): status: str

@app.get("/health")
def health(): return {"status":"ok"}
@app.post("/api/reviews")
def create(req: ReviewRequest):
    try: unit=validate_source(req.filename, req.code)
    except ValidationError as e: raise HTTPException(400,str(e))
    unit.project,unit.version=req.project,req.version
    findings, metadata=analyze(unit)
    rid=create_review(req.project,req.version,unit.code,metadata,findings)
    return {"review_id":rid,"metadata":metadata,"findings":findings}
@app.post("/api/reviews/upload")
async def upload(file: UploadFile = File(...), project: str = Form("Untitled"), version: str = Form("1.0")):
    if not file.filename: raise HTTPException(400, "A filename is required.")
    raw = await file.read()
    try: code = raw.decode("utf-8")
    except UnicodeDecodeError: raise HTTPException(400, "Only UTF-8 text source files are supported.")
    try: unit=validate_source(file.filename, code)
    except ValidationError as e: raise HTTPException(400,str(e))
    findings, metadata=analyze(unit)
    rid=create_review(project,version,unit.code,metadata,findings)
    return {"review_id":rid,"metadata":metadata,"findings":findings}
@app.get("/api/reviews")
def history(): return list_reviews()
@app.get("/api/reviews/{rid}")
def review(rid:int):
    data=get_review(rid)
    if not data: raise HTTPException(404,"Review not found")
    return data
@app.patch("/api/reviews/{rid}/findings/{finding_id}")
def status(rid:int,finding_id:str,req:StatusRequest):
    if req.status not in {"Open","Accepted","Fixed","False Positive"}: raise HTTPException(400,"Invalid status")
    if not update_status(rid,finding_id,req.status): raise HTTPException(404,"Finding not found")
    return {"status":"updated"}
@app.delete("/api/reviews/{rid}")
def remove(rid:int): delete_review(rid); return {"deleted":True}
@app.get("/api/reviews/{rid}/report/{kind}")
def report(rid:int,kind:str):
    data=get_review(rid)
    if not data: raise HTTPException(404,"Review not found")
    formats={"json":(json_report(data),"application/json","review.json"),"csv":(csv_report(data),"text/csv","review.csv"),"html":(html_report(data),"text/html","review.html")}
    if kind not in formats: raise HTTPException(400,"Use json, csv, or html")
    body,media,name=formats[kind]; return Response(body,media_type=media,headers={"Content-Disposition":f"attachment; filename={name}"})
@app.post("/api/reviews/{rid}/findings/{finding_id}/ai")
def ai(rid:int,finding_id:str):
    data=get_review(rid)
    if not data: raise HTTPException(404,"Review not found")
    match=next((f for f in data["findings"] if f["id"]==finding_id),None)
    if not match: raise HTTPException(404,"Finding not found")
    try: return explain(data["source"],match)
    except AIUnavailable as e: raise HTTPException(503,str(e))
