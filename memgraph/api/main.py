"""
FastAPI application for MemGraph REST API.

Provides HTTP endpoints for all MemGraph operations.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from typing import Optional
import os
from dotenv import load_dotenv

from memgraph.core.memory import MemoryGraph

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global MemoryGraph instance
_memory_graph: Optional[MemoryGraph] = None


def get_memory_graph() -> MemoryGraph:
    """
    Dependency injection for MemoryGraph instance.
    
    Returns:
        MemoryGraph instance
        
    Raises:
        HTTPException: If MemoryGraph is not initialized
    """
    if _memory_graph is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MemoryGraph service not initialized"
        )
    return _memory_graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown.
    
    Initializes MemoryGraph on startup and closes connection on shutdown.
    """
    global _memory_graph
    
    # Startup
    try:
        logger.info("🚀 Initializing MemoryGraph connection...")
        
        neo4j_uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "12345678")
        
        _memory_graph = MemoryGraph(
            neo4j_uri=neo4j_uri,
            neo4j_user=neo4j_user,
            neo4j_password=neo4j_password
        )
        
        # Verify connection
        if _memory_graph.health_check():
            logger.info("✅ MemoryGraph connected successfully")
        else:
            logger.error("❌ MemoryGraph health check failed")
            _memory_graph = None
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize MemoryGraph: {e}")
        _memory_graph = None
    
    yield
    
    # Shutdown
    if _memory_graph:
        try:
            logger.info("🔌 Closing MemoryGraph connection...")
            _memory_graph.close()
            logger.info("✅ MemoryGraph connection closed")
        except Exception as e:
            logger.error(f"❌ Error closing MemoryGraph: {e}")


# Create FastAPI app
app = FastAPI(
    title="MemGraph API",
    description="Memory layer for AI agents with persistent context graphs",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ══════════════════════════════════════════════════════════════
# IMPORT AND REGISTER ROUTERS
# ══════════════════════════════════════════════════════════════

# Import routers from routes module
from memgraph.api.routes import (
    router_agents,
    router_memories,
    router_contexts,
    router_relationships,
    router_sharing
)

# Include all routers in the app
app.include_router(router_agents)
app.include_router(router_memories)
app.include_router(router_contexts)
app.include_router(router_relationships)
app.include_router(router_sharing)


# ══════════════════════════════════════════════════════════════
# HEALTH CHECK ENDPOINTS
# ══════════════════════════════════════════════════════════════

@app.get("/health", tags=["Health"])
async def health_check(memory_graph: MemoryGraph = Depends(get_memory_graph)):
    """
    Check if MemGraph API is operational.
    
    Returns:
        Health status and service info
    """
    is_healthy = memory_graph.health_check()
    
    status_code = status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if is_healthy else "unhealthy",
            "service": "MemGraph API",
            "version": "0.1.0"
        }
    )


@app.get("/", tags=["Info"])
async def root():
    """
    Root endpoint with API information.
    
    Returns:
        API metadata and available endpoints
    """
    return {
        "name": "MemGraph API",
        "description": "Memory layer for AI agents with persistent context graphs",
        "version": "0.1.0",
        "docs": "/docs",
        "endpoints": {
            "agents": "/agents",
            "memories": "/memories",
            "contexts": "/contexts",
            "relationships": "/relationships",
            "sharing": "/sharing",
            "health": "/health"
        }
    }
