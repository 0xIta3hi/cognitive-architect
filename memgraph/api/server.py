"""
Entry point for running the MemGraph FastAPI server.

Usage:
    python -m memgraph.api.server
    # or
    uvicorn memgraph.api.server:app --reload
"""

import uvicorn
from memgraph.api.main import app


if __name__ == "__main__":
    """
    Run the FastAPI server.
    
    Visit http://localhost:8000/docs for interactive API documentation
    """
    uvicorn.run(
        "memgraph.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
