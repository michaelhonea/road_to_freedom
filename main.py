"""Entry point for Road to Freedom.

Render start command:  uvicorn main:app --host 0.0.0.0 --port $PORT
Local run:             python main.py
"""
import os

import uvicorn

from src.app import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
