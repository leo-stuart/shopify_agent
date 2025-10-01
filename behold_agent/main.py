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

# Import agent conditionally - use when available, fallback when not
try:
    from agent.agent import root_agent
    agent_available = True
    logger.info("✅ Behold agent loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ Failed to import root_agent: {e}")
    root_agent = None
    agent_available = False

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
            
            # Use the ADK agent properly - let it decide internally which tools to use
            if agent_available and root_agent:
                try:
                    import asyncio
                    from google.adk.core import InvocationContext
                    
                    # Simple, clean input - let the agent decide what to do
                    user_input = f"User message: {message}"
                    
                    async def get_agent_response():
                        ctx = InvocationContext()
                        ctx.set_input(user_input)
                        events = root_agent.run_async(ctx)
                        
                        # Collect the final response from the agent
                        agent_reply = ""
                        async for event in events:
                            if hasattr(event, 'text') and event.text:
                                agent_reply += event.text
                        return agent_reply

                    response_text = await get_agent_response()
                    logger.info(f"Agent response: {response_text}")
                    
                except Exception as agent_error:
                    logger.warning(f"Agent processing failed: {agent_error}")
                    # Fallback to direct Gemini
                    response_text = await fallback_gemini_response(message)
            else:
                logger.info("Using fallback Gemini response (agent not available)")
                response_text = await fallback_gemini_response(message)
            
            return {"reply": response_text}
            
        except Exception as e:
            logger.error(f"Error processing WhatsApp message: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def fallback_gemini_response(message: str) -> str:
        """Fallback response using direct Gemini API."""
        try:
            import google.generativeai as genai
            
            # Configure Gemini
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise Exception("GOOGLE_API_KEY not found")
                
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash')
            
            # Create prompt for Shopify assistant
            prompt = f"""You are Behold, an intelligent Shopify sales assistant. You help customers by:
- Providing product recommendations
- Answering questions about products
- Guiding purchasing decisions
- Managing carts and checkouts
- Calculating shipping fees

User message: "{message}"

Respond naturally and helpfully. Be concise but informative. If they're asking about products, offer to help them find what they need."""

            # Get response from Gemini
            response = model.generate_content(prompt)
            return response.text if response.text else "Hello! I'm Behold, your Shopify assistant. How can I help you today?"
            
        except Exception as ai_error:
            logger.warning(f"Fallback AI processing failed: {ai_error}")
            return f"Thanks for your message! I'm your Shopify assistant. You said: '{message}'. How can I help you find products?"
    
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
            import asyncio
            from google.adk.core import InvocationContext
            
            # Test with a simple product search request
            test_input = "User message: What products do you have?"
            
            async def get_agent_response():
                ctx = InvocationContext()
                ctx.set_input(test_input)
                events = root_agent.run_async(ctx)
                
                agent_reply = ""
                async for event in events:
                    if hasattr(event, 'text') and event.text:
                        agent_reply += event.text
                return agent_reply

            response_text = await get_agent_response()
            
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