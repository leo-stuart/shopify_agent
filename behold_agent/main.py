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

# Import agent conditionally to avoid startup failures
try:
    from agent.agent import root_agent
except ImportError as e:
    logger.warning(f"Failed to import root_agent: {e}")
    root_agent = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


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
            "agent_available": root_agent is not None,
            "environment_vars": {
                "SHOPIFY_STORE": bool(os.getenv("SHOPIFY_STORE")),
                "SHOPIFY_ADMIN_TOKEN": bool(os.getenv("SHOPIFY_ADMIN_TOKEN")),
                "SHOPIFY_STOREFRONT_TOKEN": bool(os.getenv("SHOPIFY_STOREFRONT_TOKEN")),
                "WHATSAPP_BRIDGE_URL": bool(os.getenv("WHATSAPP_BRIDGE_URL")),
                "GOOGLE_API_KEY": bool(os.getenv("GOOGLE_API_KEY"))
            }
        }
    
    @app.get("/debug/bridge")
    async def debug_bridge():
        """Debug WhatsApp bridge connection."""
        try:
            from agent.tools.whatsapp.whatsapp_tool import check_whatsapp_status
            bridge_status = check_whatsapp_status()
            return {
                "bridge_status": bridge_status,
                "bridge_url": os.getenv("WHATSAPP_BRIDGE_URL", "http://localhost:3001"),
                "agent_import": "success"
            }
        except ImportError as e:
            return {
                "bridge_status": {"error": "Failed to import WhatsApp tools"},
                "bridge_url": os.getenv("WHATSAPP_BRIDGE_URL", "http://localhost:3001"),
                "agent_import": "failed",
                "import_error": str(e)
            }
        except Exception as e:
            return {
                "bridge_status": {"error": f"Bridge check failed: {str(e)}"},
                "bridge_url": os.getenv("WHATSAPP_BRIDGE_URL", "http://localhost:3001"),
                "agent_import": "success"
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
            
            # Process message through the Behold agent
            # For now, return a simple response
            # TODO: Integrate with actual agent processing
            response_text = f"Thanks for your message! I'm your Shopify assistant. You said: '{message}'. How can I help you find products?"
            
            return {"reply": response_text}
            
        except Exception as e:
            logger.error(f"Error processing WhatsApp message: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
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
    port = int(os.getenv("PORT", "8000"))
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