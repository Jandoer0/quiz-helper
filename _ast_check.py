import asyncio, ast
from fastapi import Request
from app.main import app

client = app

def summarize(title, article_id):
    from fastapi.responses import HTMLResponse as _R
    resp = client
    # invoke the article_page callable directly
    def fake():
        pass
    try:
        resp = None
    except Exception as e:
        print("setup err", e)
        return {"ERR": str(e)}
    return resp

# Simpler: pull loader and questions to confirm structure, then inspect template rendering manually.
from app.loader import DataLoader
from app import main
import importlib
importlib.reload(main)
data, settings = main.data_loader.load_questions(), main.settings
print("start_node:", data.get("start_node"))
print("articles:", list(data.get("questions",{}).values())[:0])
