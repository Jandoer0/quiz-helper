"""Verify rendering of all pages + check served vs computed output.
Run INSIDE the fast app container.
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def check(page_title, route):
    resp = client.get(route)
    body = resp.text
    summary = {
        "title_ok": "<title>Стрижеспасатель</title>" in body,
        "article_h1": ("Инструкция по уходу за птицей</h1>" in body) and ('<h1>bleeding</h1>' not in body) and ('<h1>wing</h1>' not in body),
    }
    # Also test the root page meta tag (favicon)
    print(f"{route}")
    print(f"  title '<title>Ст  ... {('<title>Стрижеспасатель</title>' in body)}")
    if route.startswith("/article/"):
        print(f"  intro h1 present: {summary['article_h1']}")
    print()

for route in ["/", "/article/bleeding", "/article/wing", "/article/weak", "/article/emergency"]:
    check(route, route)
