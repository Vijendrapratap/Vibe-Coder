import logging
import json
from config import config
from web_ui import create_ui

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level),
    format=config.log_format
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("🚀 Vibe-Coder: Your AI Product Team")
    logger.info(f"🌍 Environment: {config.environment}")
    logger.info(f" Version: 2.0.0 Refactored")
    
    # Create the UI
    demo = create_ui()
    
    # Launch logic
    ports_to_try = [7860, 7861, 7862]
    launched = False
    
    for port in ports_to_try:
        try:
            logger.info(f"🌐 Attempting to launch on port: {port}")
            demo.launch(
                server_name="0.0.0.0",
                server_port=port,
                share=False,
                show_error=True
            )
            launched = True
            logger.info(f"✅ Application launched on http://localhost:{port}")
            break
        except Exception as e:
            logger.warning(f"⚠️ Port {port} failed: {str(e)}")
            continue
            
    if not launched:
        logger.error("❌ Failed to launch application.")