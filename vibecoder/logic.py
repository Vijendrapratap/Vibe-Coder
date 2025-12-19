"""
Core Logic Module for Vibe-Coder.

This module orchestrates the main business logic of the application, including:
- User idea optimization via AI.
- Fetching external knowledge (via MCP or direct requests).
- Generating the final development plan.
"""

import logging
import json
import requests
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any, List

from .config import config
from .prompt_optimizer import prompt_optimizer
from .explanation_manager import explanation_manager
from .utils import (
    validate_input, 
    validate_url, 
    validate_and_fix_content, 
    generate_enhanced_reference_info,
    format_response
)

logger = logging.getLogger(__name__)

def optimize_user_idea(user_idea: str) -> Tuple[str, str]:
    """
    Optimize the user's creative description
    """
    if not user_idea or not user_idea.strip():
        return "", "❌ Please enter your product idea first!"
    
    # Call prompt optimizer
    success, optimized_idea, suggestions = prompt_optimizer.optimize_user_input(user_idea)
    
    if success:
        optimization_info = f"""
## ✨ Idea Optimization Successful!

**🎯 Optimization Suggestions:**
{suggestions}

**💡 Tip:** The optimized description is more detailed and professional, which will help generate a higher quality development plan. You can:
- Use the optimized description directly to generate the plan
- Manually adjust the optimization result as needed
- Click "Re-optimize" to get different optimization suggestions
"""
        return optimized_idea, optimization_info
    else:
        return user_idea, f"⚠️ Optimization failed: {suggestions}"

def fetch_knowledge_from_url_via_mcp(url: str) -> tuple[bool, str]:
    """Fetch knowledge from URL via enhanced asynchronous MCP service"""
    from .enhanced_mcp_client import call_fetch_mcp_async, call_deepwiki_mcp_async
    
    # Intelligent selection of MCP service
    if "deepwiki.org" in url.lower():
        try:
            logger.info(f"🔍 Detected deepwiki.org link, using asynchronous DeepWiki MCP: {url}")
            result = call_deepwiki_mcp_async(url)
            
            if result.success and result.data and len(result.data.strip()) > 10:
                logger.info(f"✅ DeepWiki MCP async call succeeded, content length: {len(result.data)}")
                return True, result.data
            else:
                logger.warning(f"⚠️ DeepWiki MCP failed, switching to Fetch MCP: {result.error_message}")
        except Exception as e:
            logger.error(f"❌ DeepWiki MCP call exception, switching to Fetch MCP: {str(e)}")
    
    # Use general asynchronous Fetch MCP service
    try:
        logger.info(f"🌐 Using asynchronous Fetch MCP to get content: {url}")
        result = call_fetch_mcp_async(url, max_length=8000)
        
        if result.success and result.data and len(result.data.strip()) > 10:
            logger.info(f"✅ Fetch MCP async call succeeded, content length: {len(result.data)}")
            return True, result.data
        else:
            logger.warning(f"⚠️ Fetch MCP call failed: {result.error_message}")
            return False, f"MCP service call failed: {result.error_message or 'Unknown error'}"
    except Exception as e:
        logger.error(f"❌ Fetch MCP call exception: {str(e)}")
        return False, f"MCP service call exception: {str(e)}"

def get_mcp_status_display() -> str:
    """Get MCP service status display"""
    try:
        from enhanced_mcp_client import async_mcp_client

        # Quick test connectivity of two services
        fetch_test_result = async_mcp_client.call_mcp_service_async(
            "fetch", "fetch", {"url": "https://httpbin.org/get", "max_length": 100}
        )
        fetch_ok = fetch_test_result.success
        fetch_time = fetch_test_result.execution_time

        deepwiki_test_result = async_mcp_client.call_mcp_service_async(
            "deepwiki", "deepwiki_fetch", {"url": "https://deepwiki.org/openai/openai-python", "mode": "aggregate"}
        )
        deepwiki_ok = deepwiki_test_result.success
        deepwiki_time = deepwiki_test_result.execution_time

        fetch_icon = "✅" if fetch_ok else "❌"
        deepwiki_icon = "✅" if deepwiki_ok else "❌"

        status_lines = [
            "## 🚀 Asynchronous MCP Service Status",
            f"- {fetch_icon} **Fetch MCP**: {'Online' if fetch_ok else 'Offline'} (General web scraping)"
        ]
        
        if fetch_ok:
            status_lines.append(f"  ⏱️ Response time: {fetch_time:.2f} seconds")
        
        status_lines.append(f"- {deepwiki_icon} **DeepWiki MCP**: {'Online' if deepwiki_ok else 'Offline'} (Only for deepwiki.org)")
        
        if deepwiki_ok:
            status_lines.append(f"  ⏱️ Response time: {deepwiki_time:.2f} seconds")
        
        status_lines.extend([
            "",
            "🧠 **Intelligent asynchronous routing:**",
            "- `deepwiki.org` → DeepWiki MCP",
            "- Other websites → Fetch MCP",
            "- Automatic fallback + error recovery"
        ])
        
        return "\\n".join(status_lines)
        
    except Exception as e:
        return f"## MCP Service Status\\n- ❌ **Check failed**: {str(e)}"

def fetch_external_knowledge(reference_url: str) -> str:
    """Fetch external knowledge base content"""
    if not reference_url or not reference_url.strip():
        return ""
    
    url = reference_url.strip()
    logger.info(f"🔍 Starting to process external reference link: {url}")
    
    try:
        # Simple HEAD request to check if URL exists
        response = requests.head(url, timeout=10, allow_redirects=True)
        
        if response.status_code >= 400:
            return f"""
## ⚠️ Reference Link Status Notice
**🔗 Provided link**: {url}
**❌ Link status**: Not accessible (HTTP {response.status_code})
**💡 Suggestions**: 
- Please check if the link is correct
- Or remove the reference link and use pure AI generation mode
---
"""
            
    except Exception as e:
        return f"""
## 🔗 Reference Link Handling Instructions
**📍 Provided Link**: {url}
**🔍 Processing Status**: Unable to verify link availability temporarily ({str(e)[:100]})
**🤖 AI Processing**: Will perform intelligent analysis based on creative content
---
"""
    
    # Attempt to call MCP service
    logger.info(f"🔄 Attempting to call MCP service to fetch knowledge...")
    mcp_start_time = datetime.now()
    success, knowledge = fetch_knowledge_from_url_via_mcp(url)
    mcp_duration = (datetime.now() - mcp_start_time).total_seconds()
    
    if success and knowledge and len(knowledge.strip()) > 50:
        if not any(keyword in knowledge.lower() for keyword in ['error', 'failed', 'unavailable']):
            return f"""
## 📚 External Knowledge Base Reference
**🔗 Source Link**: {url}
**✅ Fetch Status**: MCP service successfully fetched
**📊 Content Overview**: Reference material of {len(knowledge)} characters obtained
---
{knowledge}
---
"""
    
    # MCP service failed or returned invalid content
    mcp_status = get_mcp_status_display()
    
    return f"""
## 🔗 External Knowledge Handling Instructions
**📍 Reference Link**: {url}
**🎯 Processing Method**: Intelligent analysis mode
** MCP Service Status**: 
{mcp_status}
---
"""

def generate_development_plan(user_idea: str, reference_url: str = "") -> Tuple[str, str, str]:
    """
    Generate a complete product development plan
    """
    # Start processing chain tracking
    explanation_manager.start_processing()
    
    # 1. Validate input
    is_valid, error_msg = validate_input(user_idea)
    if not is_valid:
        explanation_manager.record_step("Input Validation", "Failed", error_msg)
        return error_msg, "", None
    
    explanation_manager.record_step("Input Validation", "Success", "Input valid")
    
    # 2. Fetch external knowledge
    knowledge_context = ""
    if reference_url and reference_url.strip():
        knowledge_context = fetch_external_knowledge(reference_url)
        explanation_manager.record_step("Knowledge Retrieval", "Complete", f"Processed URL: {reference_url}")
    
    # 3. Build prompts
    # Note: Need to verify if we need to call prompt_optimizer.optimize_user_input again or if we trust the input
    # In app.py strict flow, user might have already optimized it.
    
    system_prompt = config.ai_model.system_prompt
    user_prompt = f"""
Please generate a comprehensive product development plan based on the following information:

User Idea:
{user_idea}

External Knowledge Context:
{knowledge_context or "None provided"}

Requirements:
1. detailed architecture design
2. Clear feature list
3. Tech stack recommendations
4. Step-by-step implementation plan
5. Mermaid diagrams for visualization
"""

    explanation_manager.record_step("Prompt Engineering", "Complete", "Built system and user prompts")
    
    # 4. Call AI Model
    try:
        from .config import config
        headers = {
            "Authorization": f"Bearer {config.ai_model.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": config.ai_model.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": config.ai_model.temperature,
            "max_tokens": config.ai_model.max_tokens,
            "stream": False # Use non-stream for simplicity in refactor
        }
        
        response = requests.post(config.ai_model.api_url, headers=headers, json=payload, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            explanation_manager.record_step("AI Generation", "Success", f"Generated {len(content)} chars")
        else:
            error_msg = f"API Error: {response.text}"
            explanation_manager.record_step("AI Generation", "Failed", error_msg)
            return f"❌ Generation failed: {error_msg}", "", None
            
    except Exception as e:
        error_msg = f"Exception: {str(e)}"
        explanation_manager.record_step("AI Generation", "Failed", error_msg)
        return f"❌ Generation failed: {error_msg}", "", None

    # 5. Post-processing
    final_content = validate_and_fix_content(content)
    
    # 6. Format response
    formatted_response = format_response(final_content)
    
    # 7. Extract prompts
    prompts = "" # TODO: extract prompts logic
    from utils import extract_prompts_section
    prompts = extract_prompts_section(final_content)
    
    # 8. Create download file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md', encoding='utf-8') as f:
        f.write(final_content)
        download_path = f.name
    
    return formatted_response, prompts, download_path
