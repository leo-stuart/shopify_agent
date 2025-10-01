"""
Main application entry point for Behold WhatsApp Shopify Agent.
"""

import os
import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Import agent conditionally - use when available, fallback when not
try:
    from agent.agent import root_agent
    agent_available = True
    logger.info("✅ Behold agent loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ Failed to import root_agent: {e}")
    root_agent = None
    agent_available = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Behold WhatsApp Shopify Agent")
    yield
    logger.info("Shutting down Behold WhatsApp Shopify Agent")


def create_application() -> FastAPI:
    """Create FastAPI application with all components."""
    app = FastAPI(
        title="Behold WhatsApp Shopify Agent",
        description="WhatsApp integration for Shopify store assistance using Google ADK",
        version="1.0.0"
    )
    
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {"message": "Behold WhatsApp Shopify Agent is running"}
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "Behold WhatsApp Shopify Agent"}
    
    @app.get("/debug/app")
    async def debug_app():
        """Debug application status."""
        return {
            "app_status": "running",
            "agent_available": agent_available,
            "agent_loaded": root_agent is not None,
            "environment_vars": {
                "SHOPIFY_STORE": bool(os.getenv("SHOPIFY_STORE")),
                "SHOPIFY_ADMIN_TOKEN": bool(os.getenv("SHOPIFY_ADMIN_TOKEN")),
                "SHOPIFY_STOREFRONT_TOKEN": bool(os.getenv("SHOPIFY_STOREFRONT_TOKEN")),
                "WHATSAPP_BRIDGE_URL": bool(os.getenv("WHATSAPP_BRIDGE_URL")),
                "GOOGLE_API_KEY": bool(os.getenv("GOOGLE_API_KEY"))
            },
            "adk_agent_mode": "enabled" if agent_available else "fallback_mode"
        }
    
    @app.get("/debug/bridge")
    async def debug_bridge():
        """Debug WhatsApp bridge connection."""
        import requests
        
        bridge_url = os.getenv("WHATSAPP_BRIDGE_URL", "http://localhost:3001")
        
        try:
            # Direct HTTP request to bridge
            response = requests.get(f"{bridge_url}/health", timeout=10)
            
            if response.status_code == 200:
                bridge_data = response.json()
                return {
                    "bridge_status": "connected",
                    "bridge_url": bridge_url,
                    "bridge_response": bridge_data,
                    "agent_import": "not_used"
                }
            else:
                return {
                    "bridge_status": "error",
                    "bridge_url": bridge_url,
                    "error": f"Bridge returned status {response.status_code}",
                    "response_text": response.text,
                    "agent_import": "not_used"
                }
                
        except requests.exceptions.ConnectionError:
            return {
                "bridge_status": "disconnected",
                "bridge_url": bridge_url,
                "error": f"Cannot connect to WhatsApp bridge at {bridge_url}. Is the bridge server running?",
                "agent_import": "not_used"
            }
        except Exception as e:
            return {
                "bridge_status": "error",
                "bridge_url": bridge_url,
                "error": f"Failed to check bridge: {str(e)}",
                "agent_import": "not_used"
            }
    
    @app.post("/process-whatsapp-message")
    async def process_whatsapp_message(request: Request):
        """Process WhatsApp message through the Behold agent."""
        try:
            data = await request.json()
            user_id = data.get("user_id")
            message = data.get("message")
            message_id = data.get("message_id")
            
            if not user_id or not message:
                raise HTTPException(status_code=400, detail="Missing user_id or message")
            
            logger.info(f"Processing message from {user_id}: {message}")
            
            # Use the ADK agent properly
            if agent_available and root_agent:
                try:
                    # ADK agents use run method which returns the response directly
                    response_text = root_agent.run(message)

                    logger.info(f"Agent response: {response_text}")

                except Exception as agent_error:
                    logger.error(f"Agent processing failed: {agent_error}")
                    raise HTTPException(status_code=500, detail=f"Agent execution failed: {agent_error}")
            else:
                logger.error("Agent not available")
                raise HTTPException(status_code=500, detail="Agent not available")

            return {"reply": str(response_text)}
            
        except Exception as e:
            logger.error(f"Error processing WhatsApp message: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    
    @app.post("/test-message")
    async def test_message():
        """Simple test endpoint for WhatsApp bridge to call."""
        return {"reply": "Test message received successfully!"}
    
    @app.post("/test-agent")
    async def test_agent():
        """Test the ADK agent with a simple message."""
        if not agent_available or not root_agent:
            return {"error": "Agent not available", "agent_available": agent_available}
        
        try:
            # Test with a simple product search request
            test_input = "User message: What products do you have?"
            
            # Use direct agent invocation
            response = root_agent.run(test_input)
            response_text = str(response) if response else "Test response"
            
            return {
                "success": True,
                "agent_response": response_text,
                "agent_available": agent_available,
                "test_input": test_input
            }
            
        except Exception as e:
            return {
                "error": f"Agent test failed: {str(e)}",
                "agent_available": agent_available
            }
    
    return app


# Create the app
app = create_application()
app.router.lifespan_context = lifespan


def main():
    """Main entry point."""
    # Log environment variable status but don't fail startup
    env_vars = [
        "SHOPIFY_STORE",
        "SHOPIFY_ADMIN_TOKEN", 
        "SHOPIFY_STOREFRONT_TOKEN",
        "WHATSAPP_BRIDGE_URL",
        "GOOGLE_API_KEY"
    ]
    
    missing_vars = [var for var in env_vars if not os.getenv(var)]
    if missing_vars:
        logger.warning(f"Missing environment variables: {', '.join(missing_vars)}")
        logger.warning("Some features may not work without these variables")

    # Get configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))  # Railway uses 8080 by default
    debug = os.getenv("DEBUG", "false").lower() == "true"

    logger.info(f"Starting server on {host}:{port}")

    # Run the application
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )


if __name__ == "__main__":
    main()