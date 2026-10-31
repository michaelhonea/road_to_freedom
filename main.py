"""Entry point. Run locally with:  python main.py
In production the host runs:     uvicorn main:app --host 0.0.0.0 --port $PORT
"""
import uvicorn

from src.app import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
