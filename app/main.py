from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

app = FastAPI(title="Gourmant", description="Recipe management API", version="0.1.0")

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}
