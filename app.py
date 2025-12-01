import gradio as gr
import requests
import os
import logging
import json
import tempfile
import re
import html
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any, List
from urllib.parse import urlparse

# Import modular components
from config import config
# Removed mcp_direct_client, using enhanced_mcp_client
from export_manager import export_manager
from prompt_optimizer import prompt_optimizer
from explanation_manager import explanation_manager, ProcessingStage
from plan_editor import plan_editor

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level),
    format=config.log_format
)
logger = logging.getLogger(__name__)

# API configuration
API_KEY = config.ai_model.api_key
API_URL = config.ai_model.api_url

# Initialization at app startup
logger.info("🚀 VibeDoc: Your AI Product Manager and Architect on the Go")
logger.info("📦 Version: 2.0.0 | Open Source Edition")
logger.info(f"📊 Configuration: {json.dumps(config.get_config_summary(), ensure_ascii=False, indent=2)}")

# Validate configuration
config_errors = config.validate_config()
if config_errors:
    for key, error in config_errors.items():
        logger.warning(f"⚠️ Configuration Warning {key}: {error}")

def get_processing_explanation() -> str:
    """Get detailed explanation of the processing"""
    return explanation_manager.get_processing_explanation()

def show_explanation() -> Tuple[str, str, str]:
    """Show processing explanation"""
    explanation = get_processing_explanation()
    return (
        gr.update(visible=False),  # Hide plan_output
        gr.update(value=explanation, visible=True),  # Show process_explanation
        gr.update(visible=True)   # Show hide_explanation_btn
    )

def hide_explanation() -> Tuple[str, str, str]:
    """Hide processing explanation"""
    return (
        gr.update(visible=True),   # Show plan_output
        gr.update(visible=False),  # Hide process_explanation
        gr.update(visible=False)   # Hide hide_explanation_btn
    )

def optimize_user_idea(user_idea: str) -> Tuple[str, str]:
    """
    Optimize the user's creative description
    
    Args:
        user_idea: Original user input
        
    Returns:
        Tuple[str, str]: (Optimized description, Optimization info)
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

def validate_input(user_idea: str) -> Tuple[bool, str]:
    """Validate user input"""
    if not user_idea or not user_idea.strip():
        return False, "❌ Please enter your product idea!"
    
    if len(user_idea.strip()) < 10:
        return False, "❌ Product idea description is too short, please provide more detailed information"
    
    return True, ""

def validate_url(url: str) -> bool:
    """Validate URL format"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def fetch_knowledge_from_url_via_mcp(url: str) -> tuple[bool, str]:
    """Fetch knowledge from URL via enhanced asynchronous MCP service"""
    from enhanced_mcp_client import call_fetch_mcp_async, call_deepwiki_mcp_async
    
    # Intelligent selection of MCP service
    if "deepwiki.org" in url.lower():
        # DeepWiki MCP specially handles deepwiki.org domain
        try:
            logger.info(f"🔍 Detected deepwiki.org link, using asynchronous DeepWiki MCP: {url}")
            result = call_deepwiki_mcp_async(url)
            
            if result.success and result.data and len(result.data.strip()) > 10:
                logger.info(f"✅ DeepWiki MCP async call succeeded, content length: {len(result.data)}, time taken: {result.execution_time:.2f}s")
                return True, result.data
            else:
                logger.warning(f"⚠️ DeepWiki MCP failed, switching to Fetch MCP: {result.error_message}")
        except Exception as e:
            logger.error(f"❌ DeepWiki MCP call exception, switching to Fetch MCP: {str(e)}")
    
    # Use general asynchronous Fetch MCP service
    try:
        logger.info(f"🌐 Using asynchronous Fetch MCP to get content: {url}")
        result = call_fetch_mcp_async(url, max_length=8000)  # Increased length limit
        
        if result.success and result.data and len(result.data.strip()) > 10:
            logger.info(f"✅ Fetch MCP async call succeeded, content length: {len(result.data)}, time taken: {result.execution_time:.2f}s")
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
        services_status = []

        # Test Fetch MCP
        fetch_test_result = async_mcp_client.call_mcp_service_async(
            "fetch", "fetch", {"url": "https://httpbin.org/get", "max_length": 100}
        )
        fetch_ok = fetch_test_result.success
        fetch_time = fetch_test_result.execution_time

        # Test DeepWiki MCP
        deepwiki_test_result = async_mcp_client.call_mcp_service_async(
            "deepwiki", "deepwiki_fetch", {"url": "https://deepwiki.org/openai/openai-python", "mode": "aggregate"}
        )
        deepwiki_ok = deepwiki_test_result.success
        deepwiki_time = deepwiki_test_result.execution_time

        # Build status display
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
            "- `deepwiki.org` → DeepWiki MCP (asynchronous processing)",
            "- Other websites → Fetch MCP (asynchronous processing)", 
            "- HTTP 202 → SSE listening → result retrieval",
            "- Automatic fallback + error recovery"
        ])
        
        return "\n".join(status_lines)
        
    except Exception as e:
        return f"## MCP Service Status\n- ❌ **Check failed**: {str(e)}\n- 💡 Please ensure enhanced_mcp_client.py file exists"

def call_mcp_service(url: str, payload: Dict[str, Any], service_name: str, timeout: int = 120) -> Tuple[bool, str]:
    """Unified MCP service call function
    
    Args:
        url: MCP service URL
        payload: Request payload
        service_name: Service name (for logging)
        timeout: Timeout duration
        
    Returns:
        (success, data): Success flag and returned data
    """
    try:
        logger.info(f"🔥 DEBUG: Calling {service_name} MCP service at {url}")
        logger.info(f"🔥 DEBUG: Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=timeout
        )
        
        logger.info(f"🔥 DEBUG: Response status: {response.status_code}")
        logger.info(f"🔥 DEBUG: Response headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            logger.info(f"🔥 DEBUG: Response JSON: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
        except:
            response_text = response.text[:1000]  # Only print the first 1000 characters
            logger.info(f"🔥 DEBUG: Response text: {response_text}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check multiple possible response formats
            content = None
            if "data" in data and data["data"]:
                content = data["data"]
            elif "result" in data and data["result"]:
                content = data["result"]
            elif "content" in data and data["content"]:
                content = data["content"]
            elif "message" in data and data["message"]:
                content = data["message"]
            else:
                # If none of the above, try using the entire response directly
                content = str(data)
            
            if content and len(str(content).strip()) > 10:
                logger.info(f"✅ {service_name} MCP service returned {len(str(content))} characters")
                return True, str(content)
            else:
                logger.warning(f"⚠️ {service_name} MCP service returned empty or invalid data: {data}")
                return False, f"❌ {service_name} MCP returned empty data or format error"
        else:
            logger.error(f"❌ {service_name} MCP service failed with status {response.status_code}")
            logger.error(f"❌ Response content: {response.text[:500]}")
            return False, f"❌ {service_name} MCP call failed: HTTP {response.status_code}"
            
    except requests.exceptions.Timeout:
        logger.error(f"⏰ {service_name} MCP service timeout after {timeout}s")
        return False, f"❌ {service_name} MCP call timed out"
    except requests.exceptions.ConnectionError as e:
        logger.error(f"🔌 {service_name} MCP service connection failed: {str(e)}")
        return False, f"❌ {service_name} MCP connection failed"
    except Exception as e:
        logger.error(f"💥 {service_name} MCP service error: {str(e)}")
        return False, f"❌ {service_name} MCP call error: {str(e)}"

def fetch_external_knowledge(reference_url: str) -> str:
    """Fetch external knowledge base content - use modular MCP manager to prevent fake link generation"""
    if not reference_url or not reference_url.strip():
        return ""
    
    # Verify if URL is accessible
    url = reference_url.strip()
    logger.info(f"🔍 Starting to process external reference link: {url}")
    
    try:
        # Simple HEAD request to check if URL exists
        logger.info(f"🌐 Verifying link accessibility: {url}")
        response = requests.head(url, timeout=10, allow_redirects=True)
        logger.info(f"📡 Link verification result: HTTP {response.status_code}")
        
        if response.status_code >= 400:
            logger.warning(f"⚠️ Provided URL is not accessible: {url} (HTTP {response.status_code})")
            return f"""
## ⚠️ Reference Link Status Notice

**🔗 Provided link**: {url}

**❌ Link status**: Not accessible (HTTP {response.status_code})

**💡 Suggestions**: 
- Please check if the link is correct
- Or remove the reference link and use pure AI generation mode
- AI will generate professional development plans based on creative descriptions

``` 
---
"""
        else:
            logger.info(f"✅ Link is accessible, status code: {response.status_code}")
            
    except requests.exceptions.Timeout:
        logger.warning(f"⏰ URL verification timed out: {url}")
        return f"""
## 🔗 Reference Link Handling Instructions

**📍 Provided Link**: {url}

**⏰ Processing Status**: Link verification timed out

**🤖 AI Processing**: Will perform intelligent analysis based on creative content, not relying on external links

**💡 Note**: To ensure generation quality, AI will generate a complete plan based on the creative description, avoiding referencing uncertain external content

---
"""
    except Exception as e:
        logger.warning(f"⚠️ URL verification failed: {url} - {str(e)}")
        return f"""
## 🔗 Reference Link Handling Instructions

**📍 Provided Link**: {url}

**🔍 Processing Status**: Unable to verify link availability temporarily ({str(e)[:100]})

**🤖 AI Processing**: Will perform intelligent analysis based on creative content, not relying on external links

**💡 Note**: To ensure generation quality, AI will generate a complete plan based on the creative description, avoiding referencing uncertain external content

---
"""
    
    # Attempt to call MCP service
    logger.info(f"🔄 Attempting to call MCP service to fetch knowledge...")
    mcp_start_time = datetime.now()
    success, knowledge = fetch_knowledge_from_url_via_mcp(url)
    mcp_duration = (datetime.now() - mcp_start_time).total_seconds()
    
    logger.info(f"📊 MCP service call result: Success={success}, Content length={len(knowledge) if knowledge else 0}, Duration={mcp_duration:.2f} seconds")
    
    if success and knowledge and len(knowledge.strip()) > 50:
        # MCP service successfully returned valid content
        logger.info(f"✅ MCP service successfully fetched knowledge, content length: {len(knowledge)} characters")
        
        # Verify if returned content contains actual knowledge rather than error messages
        if not any(keyword in knowledge.lower() for keyword in ['error', 'failed', 'error', 'failed', 'unavailable']):
            return f"""
## 📚 External Knowledge Base Reference

**🔗 Source Link**: {url}

**✅ Fetch Status**: MCP service successfully fetched

**📊 Content Overview**: Reference material of {len(knowledge)} characters obtained

---

{knowledge}

---
"""
        else:
            logger.warning(f"⚠️ MCP returned content contains error information: {knowledge[:200]}")
    else:
        # MCP service failed or returned invalid content, provide clear explanation
        logger.warning(f"⚠️ MCP service call failed or returned invalid content")
        
        # Detailed diagnosis of MCP service status
        mcp_status = get_mcp_status_display()
        logger.info(f"🔍 MCP service status details: {mcp_status}")
        
        return f"""
## 🔗 External Knowledge Handling Instructions

**📍 Reference Link**: {url}

**🎯 Processing Method**: Intelligent analysis mode

**� MCP Service Status**: 
{mcp_status}

**�💭 Processing Strategy**: The current external knowledge service is temporarily unavailable, AI will generate the plan based on the following methods:
- ✅ Deep analysis based on creative description
- ✅ Combined with industry best practices
- ✅ Providing complete technical solutions
- ✅ Generating practical programming prompts

**🎉 Advantages**: Ensures accuracy and reliability of generated content, avoiding referencing uncertain external information

**🔧 Technical Details**: 
- MCP call duration: {mcp_duration:.2f} seconds
- Returned content length: {len(knowledge) if knowledge else 0} characters
- Service status: {'Success' if success else 'Failure'}

---
"""

def generate_enhanced_reference_info(url: str, source_type: str, error_msg: str = None) -> str:
    """Generate enhanced reference information to provide useful context when MCP service is unavailable"""
    from urllib.parse import urlparse
    
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    path = parsed_url.path
    
    # Infer content type based on URL structure
    content_hints = []
    
    # Detect common tech sites
    if "github.com" in domain:
        content_hints.append("💻 Open source code repository")
    elif "stackoverflow.com" in domain:
        content_hints.append("❓ Technical Q&A")
    elif "medium.com" in domain:
        content_hints.append("📝 Technical blog")
    elif "dev.to" in domain:
        content_hints.append("👨‍💻 Developer community")
    elif "csdn.net" in domain:
        content_hints.append("🇨🇳 CSDN technical blog")
    elif "juejin.cn" in domain:
        content_hints.append("💎 Juejin technical article")
    elif "zhihu.com" in domain:
        content_hints.append("🧠 Zhihu technical discussion")
    elif "blog" in domain:
        content_hints.append("📖 Technical blog")
    elif "docs" in domain:
        content_hints.append("📚 Technical documentation")
    elif "wiki" in domain:
        content_hints.append("📖 Knowledge base")
    else:
        content_hints.append("🔗 Reference material")
    
    # Infer content based on path
    if "/article/" in path or "/post/" in path:
        content_hints.append("📄 Article content")
    elif "/tutorial/" in path:
        content_hints.append("📚 Tutorial guide")
    elif "/docs/" in path:
        content_hints.append("📖 Technical documentation")
    elif "/guide/" in path:
        content_hints.append("📋 User guide")
    
    hint_text = " | ".join(content_hints) if content_hints else "📄 Web content"
    
    reference_info = f"""
## 🔗 {source_type} Reference

**📍 Source link：** [{domain}]({url})

**🏷️ Content type：** {hint_text}

**🤖 AI enhanced analysis：** 
> Although the MCP service is temporarily unavailable, AI will perform intelligent analysis based on the link information and context,
> and incorporate relevance suggestions of this reference material into the generated development plan.

**📋 Reference value：**
- ✅ Provide technical selection reference
- ✅ Supplement implementation details
- ✅ Enhance solution feasibility
- ✅ Enrich best practices

---
"""
    
    if error_msg and not error_msg.startswith("❌"):
        reference_info += f"\n**⚠️ Service status：** {error_msg}\n"
    
    return reference_info

def validate_and_fix_content(content: str) -> str:
    """Validate and fix generated content, including Mermaid syntax, link verification, etc."""
    if not content:
        return content
    
    logger.info("🔍 Starting content validation and fixing...")
    
    # Record fixes applied
    fixes_applied = []
    
    # Calculate initial quality score
    initial_quality_score = calculate_quality_score(content)
    logger.info(f"📊 Initial content quality score: {initial_quality_score}/100")
    
    # 1. Fix Mermaid diagram syntax errors
    original_content = content
    content = fix_mermaid_syntax(content)
    if content != original_content:
        fixes_applied.append("Fixed Mermaid diagram syntax")
    
    # 2. Validate and clean fake links
    original_content = content
    content = validate_and_clean_links(content)
    if content != original_content:
        fixes_applied.append("Cleaned fake links")
    
    # 3. Fix date consistency
    original_content = content
    content = fix_date_consistency(content)
    if content != original_content:
        fixes_applied.append("Updated expired dates")
    
    # 4. Fix formatting issues
    original_content = content
    content = fix_formatting_issues(content)
    if content != original_content:
        fixes_applied.append("Fixed formatting issues")
    
    # Recalculate quality score
    final_quality_score = calculate_quality_score(content)
    
    # Remove quality report display, only log
    if final_quality_score > initial_quality_score + 5:
        improvement = final_quality_score - initial_quality_score
        logger.info(f"📈 Content quality improvement: {initial_quality_score}/100 → {final_quality_score}/100 (Improved by {improvement} points)")
        if fixes_applied:
            logger.info(f"🔧 Applied fixes: {', '.join(fixes_applied)}")
    
    logger.info(f"✅ Content validation and fixes completed, final quality score: {final_quality_score}/100")
    if fixes_applied:
        logger.info(f"🔧 The following fixes were applied: {', '.join(fixes_applied)}")
    
    return content

def calculate_quality_score(content: str) -> int:
    """Calculate content quality score (0-100)"""
    if not content:
        return 0
    
    score = 0
    max_score = 100
    
    # 1. Basic content completeness (30 points)
    if len(content) > 500:
        score += 15
    if len(content) > 2000:
        score += 15
    
    # 2. Structural completeness (25 points)
    structure_checks = [
        '# 🚀 AI-generated development plan',  # Title
        '## 🤖 AI programming assistant prompts',   # AI prompts section
        '```mermaid',              # Mermaid chart
        'Project development Gantt chart',           # Gantt chart
    ]
    
    for check in structure_checks:
        if check in content:
            score += 6
    
    # 3. Date accuracy (20 points)
    import re
    current_year = datetime.now().year
    
    # Check for current year or later dates
    recent_dates = re.findall(r'202[5-9]-\d{2}-\d{2}', content)
    if recent_dates:
        score += 10
    
    # Check if no expired dates
    old_dates = re.findall(r'202[0-3]-\d{2}-\d{2}', content)
    if not old_dates:
        score += 10
    
    # 4. Link quality (15 points)
    fake_link_patterns = [
        r'blog\.csdn\.net/username',
        r'github\.com/username', 
        r'example\.com',
        r'xxx\.com'
    ]
    
    has_fake_links = any(re.search(pattern, content, re.IGNORECASE) for pattern in fake_link_patterns)
    if not has_fake_links:
        score += 15
    
    # 5. Mermaid syntax quality (10 points)
    mermaid_issues = [
        r'## 🎯 [A-Z]',  # Incorrect title inside chart
        r'```mermaid\n## 🎯',  # Formatting error
    ]
    
    has_mermaid_issues = any(re.search(pattern, content, re.MULTILINE) for pattern in mermaid_issues)
    if not has_mermaid_issues:
        score += 10
    
    return min(score, max_score)

def fix_mermaid_syntax(content: str) -> str:
    """Fix syntax errors in Mermaid charts and optimize rendering"""
    import re
    
    # Fix common Mermaid syntax errors
    fixes = [
        # Remove extra symbols and markers in chart code
        (r'## 🎯 ([A-Z]\s*-->)', r'\1'),
        (r'## 🎯 (section [^)]+)', r'\1'),
        (r'(\n|\r\n)## 🎯 ([A-Z]\s*-->)', r'\n    \2'),
        (r'(\n|\r\n)## 🎯 (section [^\n]+)', r'\n    \2'),
        
        # Fix extra symbols in node definitions
        (r'## 🎯 ([A-Z]\[[^\]]+\])', r'\1'),
        
        # Ensure Mermaid code block format is correct
        (r'```mermaid\n## 🎯', r'```mermaid'),
        
        # Remove incorrect heading levels
        (r'\n##+ 🎯 ([A-Z])', r'\n    \1'),
        
        # Fix issues with Chinese node names - thoroughly clean quote formats
        (r'([A-Z]+)\["([^"]+)"\]', r'\1["\2"]'),  # Standard format: A["text"]
        (r'([A-Z]+)\[""([^"]+)""\]', r'\1["\2"]'),  # Double quote error: A[""text""]
        (r'([A-Z]+)\["⚡"([^"]+)""\]', r'\1["\2"]'),  # Emoji related error
        (r'([A-Z]+)\[([^\]]*[^\x00-\x7F][^\]]*)\]', r'\1["\2"]'),  # Chinese without quotes
        
        # Ensure flowchart syntax correctness
        (r'graph TB\n\s*graph', r'graph TB'),
        (r'flowchart TD\n\s*flowchart', r'flowchart TD'),
        
        # Fix arrow syntax
        (r'-->', r' --> '),
        (r'-->([A-Z])', r'--> \1'),
        (r'([A-Z])-->', r'\1 -->'),
    ]
    
    for pattern, replacement in fixes:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    # Add Mermaid rendering enhancement markers
    content = enhance_mermaid_blocks(content)
    
    return content

def enhance_mermaid_blocks(content: str) -> str:
    """Simplify Mermaid code block handling to avoid rendering conflicts"""
    import re
    
    # Find all Mermaid code blocks and return directly without extra wrappers
    # Because wrappers may cause rendering issues
    mermaid_pattern = r'```mermaid\n(.*?)\n```'
    
    def clean_mermaid_block(match):
        mermaid_content = match.group(1)
        # Directly return cleaned Mermaid block
        return f'```mermaid\n{mermaid_content}\n```'
    
    content = re.sub(mermaid_pattern, clean_mermaid_block, content, flags=re.DOTALL)
    
    return content

def validate_and_clean_links(content: str) -> str:
    """Validate and clean fake links to enhance link quality"""
    import re
    
    # Detect and remove fake link patterns
    fake_link_patterns = [
        # Markdown link formats
        r'\[([^\]]+)\]\(https?://blog\.csdn\.net/username/article/details/\d+\)',
        r'\[([^\]]+)\]\(https?://github\.com/username/[^\)]+\)',
        r'\[([^\]]+)\]\(https?://[^/]*example\.com[^\)]*\)',
        r'\[([^\]]+)\]\(https?://[^/]*xxx\.com[^\)]*\)',
        r'\[([^\]]+)\]\(https?://[^/]*test\.com[^\)]*\)',
        r'\[([^\]]+)\]\(https?://localhost[^\)]*\)',
        
        # Added: more fake link patterns
        r'\[([^\]]+)\]\(https?://medium\.com/@[^/]+/[^\)]*\d{9,}[^\)]*\)',  # Medium fake articles
        r'\[([^\]]+)\]\(https?://github\.com/[^/]+/[^/\)]*education[^\)]*\)',  # GitHub fake education projects
        r'\[([^\]]+)\]\(https?://www\.kdnuggets\.com/\d{4}/\d{2}/[^\)]*\)',  # KDNuggets fake articles
        r'\[([^\]]+)\]\(https0://[^\)]+\)',  # Incorrect protocol
        
        # Plain URL formats
        r'https?://blog\.csdn\.net/username/article/details/\d+',
        r'https?://github\.com/username/[^\s\)]+',
        r'https?://[^/]*example\.com[^\s\)]*',
        r'https?://[^/]*xxx\.com[^\s\)]*',
        r'https?://[^/]*test\.com[^\s\)]*',
        r'https?://localhost[^\s\)]*',
        r'https0://[^\s\)]+',  # Incorrect protocol
        r'https?://medium\.com/@[^/]+/[^\s]*\d{9,}[^\s]*',
        r'https?://github\.com/[^/]+/[^/\s]*education[^\s]*',
        r'https?://www\.kdnuggets\.com/\d{4}/\d{2}/[^\s]*',
    ]
    
    for pattern in fake_link_patterns:
        # Replace fake links with plain text descriptions
        def replace_fake_link(match):
            if match.groups():
                return f"**{match.group(1)}** (Based on industry standards)"
            else:
                return "(Based on industry best practices)"
        
        content = re.sub(pattern, replace_fake_link, content, flags=re.IGNORECASE)
    
    # Validate and enhance real links
    content = enhance_real_links(content)
    
    return content

def enhance_real_links(content: str) -> str:
    """Verify and enhance the usability of real links"""
    import re
    
    # Find all markdown links
    link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    
    def validate_link(match):
        link_text = match.group(1)
        link_url = match.group(2)
        
        # Check if it is a valid URL format
        if not validate_url(link_url):
            return f"**{link_text}** (Reference Resource)"
        
        # Check if it is a common technical documentation website
        trusted_domains = [
            'docs.python.org', 'nodejs.org', 'reactjs.org', 'vuejs.org',
            'angular.io', 'flask.palletsprojects.com', 'fastapi.tiangolo.com',
            'docker.com', 'kubernetes.io', 'github.com', 'gitlab.com',
            'stackoverflow.com', 'developer.mozilla.org', 'w3schools.com',
            'jwt.io', 'redis.io', 'mongodb.com', 'postgresql.org',
            'mysql.com', 'nginx.org', 'apache.org'
        ]
        
        # If it is a trusted domain, keep the link
        for domain in trusted_domains:
            if domain in link_url.lower():
                return f"[{link_text}]({link_url})"
        
        # For other links, convert to safe text reference
        return f"**{link_text}** (Technical Reference)"
    
    content = re.sub(link_pattern, validate_link, content)
    
    return content

def fix_date_consistency(content: str) -> str:
    """Fix date consistency issues"""
    import re
    from datetime import datetime
    
    current_year = datetime.now().year
    
    # Replace dates before 2024 with the current year
    old_year_patterns = [
        r'202[0-3]-\d{2}-\d{2}',  # Dates from 2020-2023
        r'202[0-3]year',            # Years 2020-2023
    ]
    
    for pattern in old_year_patterns:
        def replace_old_date(match):
            old_date = match.group(0)
            if '-' in old_date:
                # Date format: YYYY-MM-DD
                parts = old_date.split('-')
                return f"{current_year}-{parts[1]}-{parts[2]}"
            else:
                # Year format: YYYYyear
                return f"{current_year}year"
        
        content = re.sub(pattern, replace_old_date, content)
    
    return content

def fix_formatting_issues(content: str) -> str:
    """Fix formatting issues"""
    import re
    
    # Fix common formatting problems
    fixes = [
        # Fix empty or incorrectly formatted headings
        (r'#### 🚀 \*\*$', r'#### 🚀 **Development Stage**'),
        (r'#### 🚀 Phase：\*\*', r'#### 🚀 **Stage 1**:'),
        (r'### 📋 (\d+)\. \*\*第\d+阶段', r'### 📋 \1. **Stage \1'),
        
        # Fix table formatting issues
        (r'\n## 🎯 \| ([^|]+) \| ([^|]+) \| ([^|]+) \|', r'\n| \1 | \2 | \3 |'),
        (r'\n### 📋 (\d+)\. \*\*([^*]+)\*\*：', r'\n**\1. \2**:'),
        (r'\n### 📋 (\d+)\. \*\*([^*]+)\*\*$', r'\n**\1. \2**'),
        
        # Fix excessive blank lines
        (r'\n{4,}', r'\n\n\n'),
        
        # Fix incomplete paragraph endings
        (r'##\n\n---', r'## Summary\n\nAbove is the complete development plan and technical solution.\n\n---'),
    ]
    
    for pattern, replacement in fixes:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    return content

def generate_development_plan(user_idea: str, reference_url: str = "") -> Tuple[str, str, str]:
    """
    Generate a complete product development plan and corresponding AI programming assistant prompts based on user ideas.
    
    Args:
        user_idea (str): User's product idea description
        reference_url (str): Optional reference URL
        
    Returns:
        Tuple[str, str, str]: Development plan, AI programming prompt, temporary file path
    """
    # Start processing chain tracking
    explanation_manager.start_processing()
    start_time = datetime.now()
    
    # Step 1: Validate input
    validation_start = datetime.now()
    is_valid, error_msg = validate_input(user_idea)
    validation_duration = (datetime.now() - validation_start).total_seconds()
    
    explanation_manager.add_processing_step(
        stage=ProcessingStage.INPUT_VALIDATION,
        title="Input Validation",
        description="Validate whether the user's idea description meets the requirements",
        success=is_valid,
        details={
            "Input Length": len(user_idea.strip()) if user_idea else 0,
            "Includes Reference URL": bool(reference_url),
            "Validation Result": "Passed" if is_valid else error_msg
        },
        duration=validation_duration,
        quality_score=100 if is_valid else 0,
        evidence=f"User input: '{user_idea[:50]}...' (Length: {len(user_idea.strip()) if user_idea else 0} characters)"
    )
    
    if not is_valid:
        return error_msg, "", None
    
    # Step 2: API key check
    api_check_start = datetime.now()
    if not API_KEY:
        api_check_duration = (datetime.now() - api_check_start).total_seconds()
        explanation_manager.add_processing_step(
            stage=ProcessingStage.AI_GENERATION,
            title="API Key Check",
            description="Check AI model API key configuration",
            success=False,
            details={"Error": "API key not configured"},
            duration=api_check_duration,
            quality_score=0,
            evidence="SILICONFLOW_API_KEY not found in system environment variables"
        )
        
        logger.error("API key not configured")
        error_msg = """
## ❌ Configuration Error: API key not set

### 🔧 How to fix:

1. **Obtain API key**:
   - Visit [Silicon Flow](https://siliconflow.cn) 
   - Register an account and get the API key

2. **Set environment variable**:
   ```bash
   export SILICONFLOW_API_KEY=your_api_key_here
   ```

3. **Configure on Mota platform**:
   - Add environment variable in the creation space settings
   - Variable name: `SILICONFLOW_API_KEY`
   - Variable value: your actual API key

### 📋 Restart the application after configuration to use full features!

---

**💡 Tip**: The API key is required; without it, AI service cannot generate development plans.
"""
        return error_msg, "", None
    
    # Step 3: Fetch external knowledge base content
    knowledge_start = datetime.now()
    retrieved_knowledge = fetch_external_knowledge(reference_url)
    knowledge_duration = (datetime.now() - knowledge_start).total_seconds()
    
    explanation_manager.add_processing_step(
        stage=ProcessingStage.KNOWLEDGE_RETRIEVAL,
        title="External Knowledge Retrieval",
        description="Fetch external reference knowledge from MCP service",
        success=bool(retrieved_knowledge and "success获取" in retrieved_knowledge),
        details={
            "Reference URL": reference_url or "None",
            "MCP Service Status": get_mcp_status_display(),
            "Knowledge Content Length": len(retrieved_knowledge) if retrieved_knowledge else 0
        },
        duration=knowledge_duration,
        quality_score=80 if retrieved_knowledge else 50,
        evidence=f"Retrieved knowledge content: '{retrieved_knowledge[:100]}...' (Length: {len(retrieved_knowledge) if retrieved_knowledge else 0} characters)"
    )
    
    # Get current date and calculate project start date
    current_date = datetime.now()
    # Project start date: next Monday (to give user preparation time)
    days_until_monday = (7 - current_date.weekday()) % 7
    if days_until_monday == 0:  # If today is Monday, start next Monday
        days_until_monday = 7
    project_start_date = current_date + timedelta(days=days_until_monday)
    project_start_str = project_start_date.strftime("%Y-%m-%d")
    current_year = current_date.year
    
    # Construct system prompt - prevent fake link generation, strengthen programming prompt generation, enhance visualization content, and reinforce date context
    system_prompt = f"""You are a senior technical project manager, proficient in product planning and AI programming assistant (such as GitHub Copilot, ChatGPT Code) prompt writing.

📅 **Current time context**: Today is {current_date.strftime("%Yyear%m月%d日")}, the current year is {current_year}. All project timelines must be reasonably planned based on the current time.

🔴 Important requirements:
1. When receiving external knowledge base references, you must explicitly cite and integrate this information in the development plan
2. Must mention the reference sources (such as CSDN blogs, GitHub projects, etc.) at the beginning of the development plan
3. Must adjust technical selection and implementation suggestions based on external references
4. Must use expressions like "refer to XXX's suggestions" in relevant sections
5. Development phases must have clear numbering (Phase 1, Phase 2, etc.)

🚫 Prohibited behaviors (strictly enforced):
- **Never fabricate any fake links or references**
- **Do not generate any non-existent URLs, including but not limited to:**
  - ❌ https://medium.com/@username/... (username + numeric ID format)
  - ❌ https://github.com/username/... (placeholder username)
  - ❌ https://blog.csdn.net/username/... 
  - ❌ https://www.kdnuggets.com/year/month/... (fictional articles)
  - ❌ https://example.com, xxx.com, test.com and other test domains
  - ❌ Any links starting with https0:// with incorrect protocol
- **Do not add any links in the "References" section unless explicitly provided by the user**
- **Do not use titles like "References", "Further Reading" to add fake links**

✅ Correct practices:
- If no external references are provided, **completely omit the "References" section**
- Only cite reference links actually provided by the user (if any)
- When external knowledge is unavailable, clearly state it is generated based on best practices
- Use expressions like "based on industry standards", "refer to common architectures", "following best practices"
- **The development plan should start directly without fabricating any external resources**

📊 Visualization content requirements (new):
- Must include Mermaid code for architecture diagrams in the technical solution
- Must include Mermaid code for Gantt charts in the development plan
- Must include Mermaid code for flowcharts in the functional modules
- Must include a technology stack comparison table
- Must include a project milestone timeline

🎯 Mermaid chart format requirements (strictly followed):

⚠️ **Strictly prohibit incorrect formats**:
- ❌ Never use `A[""text""]` format (double quotes)
- ❌ Never use `## 🎯` or similar headings inside charts
- ❌ Never use emoji symbols in node names

✅ **Correct Mermaid syntax**:

**Architecture diagram example**:
```mermaid
flowchart TD
    A["User Interface"] --> B["Business Logic Layer"]
    B --> C["Data Access Layer"]
    C --> D["Database"]
    B --> E["External API"]
    F["Cache"] --> B
```

**Flowchart example**:
```mermaid
flowchart TD
    Start([start]) --> Input[用户输入]
    Input --> Validate{{validation输入}}
    Validate -->|有效| Process[processing数据]
    Validate -->|无效| Error[显示error]
    Process --> Save[Save结果]
    Save --> Success[success提示]
    Error --> Input
    Success --> End([end])
```

**Gantt chart example (must use real project start date)**:
```mermaid
gantt
    title Project Development Gantt Chart
    dateFormat YYYY-MM-DD
    axisFormat %m-%d
    
    section Requirements Analysis
    Requirement Research     :done, req1, {project_start_str}, 3d
    Requirement Organization :done, req2, after req1, 4d
    
    section System Design
    Architecture Design      :active, design1, after req2, 7d
    UI Design                :design2, after design1, 5d
    
    section Development & Implementation
    Backend Development      :dev1, after design2, 14d
    Frontend Development     :dev2, after design2, 14d
    Integration Testing      :test1, after dev1, 7d
    
    section Deployment & Launch
    Deployment Preparation   :deploy1, after test1, 3d
    Official Launch          :deploy2, after deploy1, 2d
```

⚠️ **Date Generation Rules**：
- Project start date: {project_start_str} (starting next Monday)
- All dates must be based on the year {current_year} and later
- Dates before 2024 are strictly prohibited
- Milestone dates must be consistent with the Gantt chart

🎯 Charts must be generated strictly according to Mermaid syntax specifications, with no formatting errors

🎯 AI Programming Prompt Format Requirements (Important):
- A dedicated "# AI Programming Assistant Prompts" section must be generated after the development plan
- Each functional module must have a dedicated AI programming prompt
- Each prompt must use ```code block format for easy copying
- Prompt content should be based on specific project functions, not generic templates
- Prompts should be detailed, specific, and directly usable in AI programming tools
- Must include complete context and specific requirements

🔧 Prompt Structure Requirements:
Each prompt uses the following format:

## [Function Name] Development Prompt

```
Please develop [specific feature description] for [specific project name].

Project Background:
[Project background based on the development plan]

Functional Requirements:
1. [Specific requirement 1]
2. [Specific requirement 2]
...

Technical Constraints:
- Use [specific technology stack]
- Follow [specific standards]
- Achieve [specific performance requirements]

Output Requirements:
- Complete runnable code
- Detailed comments and explanations
- Error handling mechanisms
- Test cases
```

Please strictly follow this format to generate personalized programming prompts, ensuring each prompt is based on specific project needs.

Format requirements: output the development plan first, then the programming prompt section."""

    # Construct user prompt
    user_prompt = f"""Product Idea: {user_idea}"""
    
    # If external knowledge is successfully retrieved, inject it into the prompt
    if retrieved_knowledge and not any(keyword in retrieved_knowledge for keyword in ["❌", "⚠️", "Handling Instructions", "Temporarily Unavailable"]):
        user_prompt += f"""

# External Knowledge Base Reference
{retrieved_knowledge}

Please generate based on the above external knowledge base reference and product idea:"""
    else:
        user_prompt += """

Please generate:"""
    
    user_prompt += """
1. Detailed development plan (including product overview, technical solution, development plan, deployment plan, promotion strategy, etc.)
2. AI programming assistant prompts corresponding to each functional module

Ensure the prompts are specific, actionable, and can be directly used in AI programming tools."""

    try:
        logger.info("🚀 Starting AI API call to generate development plan...")
        
        # Step 3: AI generation preparation
        ai_prep_start = datetime.now()
        
        # Construct request data
        request_data = {
            "model": "Qwen/Qwen2.5-72B-Instruct",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 4096,  # Fix: API limit max 4096 tokens
            "temperature": 0.7
        }
        
        ai_prep_duration = (datetime.now() - ai_prep_start).total_seconds()
        
        explanation_manager.add_processing_step(
            stage=ProcessingStage.AI_GENERATION,
            title="AI Request Preparation",
            description="Construct AI model request parameters and prompts",
            success=True,
            details={
                "AI Model": request_data['model'],
                "System Prompt Length": f"{len(system_prompt)} characters",
                "User Prompt Length": f"{len(user_prompt)} characters",
                "Max Tokens": request_data['max_tokens'],
                "Temperature Parameter": request_data['temperature']
            },
            duration=ai_prep_duration,
            quality_score=95,
            evidence=f"Preparing to call {request_data['model']} model, total prompt length: {len(system_prompt + user_prompt)} characters"
        )
        
        # Log request information (excluding full prompts to avoid overly long logs)
        logger.info(f"📊 API request model: {request_data['model']}")
        logger.info(f"📏 System prompt length: {len(system_prompt)} characters")
        logger.info(f"📏 User prompt length: {len(user_prompt)} characters")
        
        # Step 4: AI API call
        api_call_start = datetime.now()
        logger.info(f"🌐 Calling API: {API_URL}")
        
        response = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            json=request_data,
            timeout=300  # Optimization: generation timeout set to 300 seconds (5 minutes)
        )
        
        api_call_duration = (datetime.now() - api_call_start).total_seconds()
        
        logger.info(f"📈 API response status code: {response.status_code}")
        logger.info(f"⏱️ API call duration: {api_call_duration:.2f} seconds")
        
        if response.status_code == 200:
            content = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            
            content_length = len(content) if content else 0
            logger.info(f"📝 Generated content length: {content_length} characters")
            
            explanation_manager.add_processing_step(
                stage=ProcessingStage.AI_GENERATION,
                title="AI Content Generation",
                description="AI model successfully generated development plan content",
                success=bool(content),
                details={
                    "Response status": f"HTTP {response.status_code}",
                    "Generated content length": f"{content_length} characters",
                    "API call duration": f"{api_call_duration:.2f} seconds",
                    "Average generation speed": f"{content_length / api_call_duration:.1f} characters/second" if api_call_duration > 0 else "N/A"
                },
                duration=api_call_duration,
                quality_score=90 if content_length > 1000 else 70,
                evidence=f"Successfully generated {content_length} characters of development plan content, including technical solutions and programming prompts"
            )
            
            if content:
                # Step 5: Content post-processing
                postprocess_start = datetime.now()
                
                # Post-processing: ensure content is structured
                final_plan_text = format_response(content)
                
                # Apply content validation and fixes
                final_plan_text = validate_and_fix_content(final_plan_text)
                
                postprocess_duration = (datetime.now() - postprocess_start).total_seconds()
                
                explanation_manager.add_processing_step(
                    stage=ProcessingStage.CONTENT_FORMATTING,
                    title="Content Post-processing",
                    description="Formatting and validating generated content",
                    success=True,
                    details={
                        "Formatting": "Markdown structure optimization",
                        "Content validation": "Mermaid syntax fixes, link checks",
                        "Final content length": f"{len(final_plan_text)} characters",
                        "Processing time": f"{postprocess_duration:.2f} seconds"
                    },
                    duration=postprocess_duration,
                    quality_score=85,
                    evidence=f"Completed content post-processing, final output is {len(final_plan_text)} characters of complete development plan"
                )
                
                # Create temporary file
                temp_file = create_temp_markdown_file(final_plan_text)
                
                # If temporary file creation fails, use None to avoid Gradio permission errors
                if not temp_file:
                    temp_file = None
                
                # Total processing time
                total_duration = (datetime.now() - start_time).total_seconds()
                logger.info(f"🎉 Development plan generation completed, total time: {total_duration:.2f} seconds")
                
                return final_plan_text, extract_prompts_section(final_plan_text), temp_file
            else:
                explanation_manager.add_processing_step(
                    stage=ProcessingStage.AI_GENERATION,
                    title="AI Generation Failed",
                    description="AI model returned empty content",
                    success=False,
                    details={
                        "Response status": f"HTTP {response.status_code}",
                        "Error reason": "AI returned empty content"
                    },
                    duration=api_call_duration,
                    quality_score=0,
                    evidence="AI API call succeeded but returned empty content"
                )
                
                logger.error("API returned empty content")
                return "❌ AI returned empty content, please try again later", "", None
        else:
            # Log detailed error information
            logger.error(f"API request failed with status {response.status_code}")
            try:
                error_detail = response.json()
                logger.error(f"API error details: {error_detail}")
                error_message = error_detail.get('message', 'Unknown error')
                error_code = error_detail.get('code', '')
                
                explanation_manager.add_processing_step(
                    stage=ProcessingStage.AI_GENERATION,
                    title="AI API call failed",
                    description="AI model API request failed",
                    success=False,
                    details={
                        "HTTP Status Code": response.status_code,
                        "Error Code": error_code,
                        "Error Message": error_message
                    },
                    duration=api_call_duration,
                    quality_score=0,
                    evidence=f"API returned error: HTTP {response.status_code} - {error_message}"
                )
                
                return f"❌ API request failed: HTTP {response.status_code} (Error Code: {error_code}) - {error_message}", "", None
            except:
                logger.error(f"API response content: {response.text[:500]}")
                
                explanation_manager.add_processing_step(
                    stage=ProcessingStage.AI_GENERATION,
                    title="AI API call failed",
                    description="AI model API request failed, unable to parse error information",
                    success=False,
                    details={
                        "HTTP Status Code": response.status_code,
                        "Response Content": response.text[:200]
                    },
                    duration=api_call_duration,
                    quality_score=0,
                    evidence=f"API request failed, status code: {response.status_code}"
                )
                
                return f"❌ API request failed: HTTP {response.status_code} - {response.text[:200]}", "", None
            
    except requests.exceptions.Timeout:
        logger.error("API request timeout")
        return "❌ API request timed out, please try again later", "", None
    except requests.exceptions.ConnectionError:
        logger.error("API connection failed")
        return "❌ Network connection failed, please check your network settings", "", None
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return f"❌ Processing error: {str(e)}", "", None

def extract_prompts_section(content: str) -> str:
    """Extract the AI programming prompts section from the full content"""
    lines = content.split('\n')
    prompts_section = []
    in_prompts_section = False
    
    for line in lines:
        if any(keyword in line for keyword in ['Programming Prompts', 'Programming Assistant', 'Prompt', 'AI Assistant']):
            in_prompts_section = True
        if in_prompts_section:
            prompts_section.append(line)
    
    return '\n'.join(prompts_section) if prompts_section else "Programming prompts section not found"

def create_temp_markdown_file(content: str) -> str:
    """Create a temporary markdown file"""
    try:
        import tempfile
        import os
        
        # Create a temporary file using a safer method
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.md', 
            delete=False, 
            encoding='utf-8'
        ) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Verify if the file was created successfully
        if os.path.exists(temp_file_path):
            logger.info(f"✅ Successfully created temporary file: {temp_file_path}")
            return temp_file_path
        else:
            logger.warning("⚠️ Temporary file does not exist after creation")
            return ""
            
    except PermissionError as e:
        logger.error(f"❌ Permission error, unable to create temporary file: {e}")
        return ""
    except Exception as e:
        logger.error(f"❌ Failed to create temporary file: {e}")
        return ""

def enable_plan_editing(plan_content: str) -> Tuple[str, str]:
    """Enable plan editing feature"""
    try:
        # Parse plan content
        sections = plan_editor.parse_plan_content(plan_content)
        editable_sections = plan_editor.get_editable_sections()
        
        # Generate edit interface HTML
        edit_interface = generate_edit_interface(editable_sections)
        
        # Generate edit summary
        summary = plan_editor.get_edit_summary()
        edit_summary = f"""
## 📝 Plan Editing Mode Enabled

**📊 Edit Statistics**：
- Total sections: {summary['total_sections']}
- Editable sections: {summary['editable_sections']}
- Edited sections: {summary['edited_sections']}

**💡 Editing Instructions**：
- Click on any section below to edit
- The system will automatically save edit history
- You can restore to the original version at any time

---
"""
        
        return edit_interface, edit_summary
        
    except Exception as e:
        logger.error(f"Failed to enable editing: {str(e)}")
        return "", f"❌ Failed to enable editing: {str(e)}"

def generate_edit_interface(editable_sections: List[Dict]) -> str:
    """Generate edit interface HTML"""
    interface_html = """
<div class="plan-editor-container">
    <div class="editor-header">
        <h3>📝 Section Editor</h3>
        <p>Click any section to edit, the system will automatically save your changes</p>
    </div>
    
    <div class="sections-container">
"""
    
    for section in editable_sections:
        section_html = f"""
        <div class="editable-section" data-section-id="{section['id']}" data-section-type="{section['type']}">
            <div class="section-header">
                <span class="section-type">{get_section_type_emoji(section['type'])}</span>
                <span class="section-title">{section['title']}</span>
                <button class="edit-section-btn" onclick="editSection('{section['id']}')">
                    ✏️ Edit
                </button>
            </div>
            
            <div class="section-preview">
                <div class="preview-content">{section['preview']}</div>
                <div class="section-content" style="display: none;">{_html_escape(section['content'])}</div>
            </div>
        </div>
"""
        interface_html += section_html
    
    interface_html += """
    </div>
    
    <div class="editor-actions">
        <button class="apply-changes-btn" onclick="applyAllChanges()">
            ✅ Apply All Changes
        </button>
        <button class="reset-changes-btn" onclick="resetAllChanges()">
            🔄 Reset All Changes
        </button>
    </div>
</div>

<script>
function editSection(sectionId) {
    const section = document.querySelector(`[data-section-id="${sectionId}"]`);
    const content = section.querySelector('.section-content').textContent;
    const type = section.getAttribute('data-section-type');
    
    // Detect current theme
    const isDark = document.documentElement.classList.contains('dark');
    
    // Create edit dialog
    const editDialog = document.createElement('div');
    editDialog.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.6);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 10000;
    `;
    
    editDialog.innerHTML = `
        <div style="
            background: ${isDark ? '#2d3748' : 'white'};
            color: ${isDark ? '#f7fafc' : '#2d3748'};
            padding: 2rem;
            border-radius: 1rem;
            max-width: 90%;
            max-height: 90%;
            overflow-y: auto;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        ">
            <h3 style="margin-bottom: 1rem; color: ${isDark ? '#f7fafc' : '#2d3748'};">
                ✏️ Edit Paragraph - ${type}
            </h3>
            <textarea
                id="section-editor-${sectionId}"
                style="
                    width: 100%;
                    height: 400px;
                    padding: 1rem;
                    border: 2px solid ${isDark ? '#4a5568' : '#e2e8f0'};
                    border-radius: 0.5rem;
                    font-family: 'Fira Code', monospace;
                    font-size: 0.9rem;
                    resize: vertical;
                    line-height: 1.6;
                    background: ${isDark ? '#1a202c' : 'white'};
                    color: ${isDark ? '#f7fafc' : '#2d3748'};
                "
                placeholder="Edit paragraph content here..."
            >${content}</textarea>
            <div style="margin-top: 1rem;">
                <label style="display: block; margin-bottom: 0.5rem;">Edit comment (optional):</label>
                <input
                    type="text"
                    id="edit-comment-${sectionId}"
                    style="
                        width: 100%;
                        padding: 0.5rem;
                        border: 1px solid ${isDark ? '#4a5568' : '#e2e8f0'};
                        border-radius: 0.25rem;
                        background: ${isDark ? '#1a202c' : 'white'};
                        color: ${isDark ? '#f7fafc' : '#2d3748'};
                    "
                    placeholder="Briefly describe your changes..."
                />
            </div>
            <div style="margin-top: 1.5rem; display: flex; gap: 1rem; justify-content: flex-end;">
                <button
                    onclick="document.body.removeChild(this.closest('.edit-dialog-overlay'))"
                    style="
                        padding: 0.5rem 1rem;
                        border: 1px solid ${isDark ? '#4a5568' : '#cbd5e0'};
                        background: ${isDark ? '#2d3748' : 'white'};
                        color: ${isDark ? '#f7fafc' : '#4a5568'};
                        border-radius: 0.5rem;
                        cursor: pointer;
                    "
                >Cancel</button>
                <button
                    onclick="saveSectionEdit('${sectionId}')"
                    style="
                        padding: 0.5rem 1rem;
                        background: linear-gradient(45deg, #667eea, #764ba2);
                        color: white;
                        border: none;
                        border-radius: 0.5rem;
                        cursor: pointer;
                    "
                >Save</button>
            </div>
        </div>
    `;
    
    editDialog.className = 'edit-dialog-overlay';
    document.body.appendChild(editDialog);
    
    // ESC key to close
    const escapeHandler = (e) => {
        if (e.key === 'Escape') {
            document.body.removeChild(editDialog);
            document.removeEventListener('keydown', escapeHandler);
        }
    };
    document.addEventListener('keydown', escapeHandler);
    
    // Click outside to close
    editDialog.addEventListener('click', (e) => {
        if (e.target === editDialog) {
            document.body.removeChild(editDialog);
            document.removeEventListener('keydown', escapeHandler);
        }
    });
}

function saveSectionEdit(sectionId) {
    const newContent = document.getElementById(`section-editor-${sectionId}`).value;
    const comment = document.getElementById(`edit-comment-${sectionId}`).value;
    
    // Update hidden component values to trigger Gradio events
    const sectionIdInput = document.querySelector('#section_id_input textarea');
    const sectionContentInput = document.querySelector('#section_content_input textarea'); 
    const sectionCommentInput = document.querySelector('#section_comment_input textarea');
    const updateTrigger = document.querySelector('#section_update_trigger textarea');
    
    if (sectionIdInput && sectionContentInput && sectionCommentInput && updateTrigger) {
        sectionIdInput.value = sectionId;
        sectionContentInput.value = newContent;
        sectionCommentInput.value = comment;
        updateTrigger.value = Date.now().toString(); // Trigger update
        
        // Manually trigger change events
        sectionIdInput.dispatchEvent(new Event('input'));
        sectionContentInput.dispatchEvent(new Event('input'));
        sectionCommentInput.dispatchEvent(new Event('input'));
        updateTrigger.dispatchEvent(new Event('input'));
    }
    
    // Close dialog
    document.body.removeChild(document.querySelector('.edit-dialog-overlay'));
    
    // Update preview
    const section = document.querySelector(`[data-section-id="${sectionId}"]`);
    const preview = section.querySelector('.preview-content');
    preview.textContent = newContent.substring(0, 100) + '...';
    
    // Show save success notification
    showNotification('✅ Paragraph saved', 'success');
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'success' ? '#48bb78' : '#4299e1'};
        color: white;
        border-radius: 0.5rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        z-index: 10001;
        animation: slideIn 0.3s ease-out;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-in forwards';
        setTimeout(() => document.body.removeChild(notification), 300);
    }, 3000);
}

// Add necessary CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);
</script>
"""
    
    return interface_html

def _html_escape(text: str) -> str:
    """HTML escape function"""
    import html
    return html.escape(text)

def get_section_type_emoji(section_type: str) -> str:
    """Get the emoji corresponding to the section type"""
    type_emojis = {
        'heading': '📋',
        'paragraph': '📝',
        'list': '📄',
        'code': '💻',
        'table': '📊'
    }
    return type_emojis.get(section_type, '📝')

def update_section_content(section_id: str, new_content: str, comment: str) -> str:
    """Update section content"""
    try:
        success = plan_editor.update_section(section_id, new_content, comment)
        
        if success:
            # Get the updated full content
            updated_content = plan_editor.get_modified_content()
            
            # Format and return
            formatted_content = format_response(updated_content)
            
            logger.info(f"Paragraph {section_id} updated successfully")
            return formatted_content
        else:
            logger.error(f"Paragraph {section_id} update failed")
            return "❌ Update failed"
            
    except Exception as e:
        logger.error(f"Failed to update paragraph content: {str(e)}")
        return f"❌ Update failed: {str(e)}"

def get_edit_history() -> str:
    """Get edit history"""
    try:
        history = plan_editor.get_edit_history()
        
        if not history:
            return "No edit history available"
        
        history_html = """
<div class="edit-history">
    <h3>📜 Edit History</h3>
    <div class="history-list">
"""
        
        for i, edit in enumerate(reversed(history[-10:]), 1):  # Show last 10 edits
            timestamp = datetime.fromisoformat(edit['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            history_html += f"""
            <div class="history-item">
                <div class="history-header">
                    <span class="history-index">#{i}</span>
                    <span class="history-time">{timestamp}</span>
                    <span class="history-section">Paragraph: {edit['section_id']}</span>
                </div>
                <div class="history-comment">{edit['user_comment'] or 'No description'}</div>
            </div>
"""
        
        history_html += """
    </div>
</div>
"""
        
        return history_html
        
    except Exception as e:
        logger.error(f"Failed to get edit history: {str(e)}")
        return f"❌ Failed to get edit history: {str(e)}"

def reset_plan_edits() -> str:
    """Reset all edits"""
    try:
        plan_editor.reset_to_original()
        logger.info("All edits have been reset")
        return "✅ Reset to original version"
    except Exception as e:
        logger.error(f"Reset failed: {str(e)}")
        return f"❌ Reset failed: {str(e)}"

def fix_links_for_new_window(content: str) -> str:
    """Fix all links to open in new window, solving Motta platform link issues"""
    import re
    
    # Match all markdown link formats [text](url)
    def replace_markdown_link(match):
        text = match.group(1)
        url = match.group(2)
        return f'<a href="{url}" target="_blank" rel="noopener noreferrer">{text}</a>'
    
    # Replace markdown links
    content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replace_markdown_link, content)
    
    # Match all HTML links and add target="_blank"
    def add_target_blank(match):
        full_tag = match.group(0)
        if 'target=' not in full_tag:
            # Add target="_blank" before >
            return full_tag.replace('>', ' target="_blank" rel="noopener noreferrer">')
        return full_tag
    
    # Replace HTML links
    content = re.sub(r'<a [^>]*href=[^>]*>', add_target_blank, content)
    
    return content

def format_response(content: str) -> str:
    """Format AI response, beautify display and keep original AI-generated prompts"""
    
    # Fix all links to open in new window
    content = fix_links_for_new_window(content)
    
    # Add timestamp and format title
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Split development plan and AI programming prompts
    parts = content.split('# AI编程助手提示词')
    
    if len(parts) >= 2:
        # There is a clear AI programming prompts section
        plan_content = parts[0].strip()
        prompts_content = '# AI编程助手提示词' + parts[1]
        
        # Beautify the AI programming prompts section
        enhanced_prompts = enhance_prompts_display(prompts_content)
        
        formatted_content = f"""
<div class="plan-header">

# 🚀 AI-generated Development Plan

<div class="meta-info">

**⏰ Generated Time:** {timestamp}  
**🤖 AI Model:** Qwen2.5-72B-Instruct  
**💡 Intelligently generated based on user creativity**  
**🔗 Agent application enhanced by MCP service**

</div>

</div>

---

{enhance_markdown_structure(plan_content)}

---

{enhanced_prompts}
"""
    else:
        # No clear split, use original content
        formatted_content = f"""
<div class="plan-header">

# 🚀 AI-generated Development Plan

<div class="meta-info">

**⏰ Generated Time:** {timestamp}  
**🤖 AI Model:** Qwen2.5-72B-Instruct  
**💡 Intelligently generated based on user creativity**  
**🔗 Agent application enhanced by MCP service**

</div>

</div>

---

{enhance_markdown_structure(content)}
"""
    
    return formatted_content

def enhance_prompts_display(prompts_content: str) -> str:
    """Simplify AI programming prompts display"""
    lines = prompts_content.split('\n')
    enhanced_lines = []
    in_code_block = False
    
    for line in lines:
        stripped = line.strip()
        
        # Handle title
        if stripped.startswith('# AI编程助手提示词'):
            enhanced_lines.append('')
            enhanced_lines.append('<div class="prompts-highlight">')
            enhanced_lines.append('')
            enhanced_lines.append('# 🤖 AI Programming Assistant Prompts')
            enhanced_lines.append('')
            enhanced_lines.append('> 💡 **Instructions**: The following prompts are custom generated based on your project requirements and can be directly copied into AI programming tools like GitHub Copilot, ChatGPT, Claude, etc.')
            enhanced_lines.append('')
            continue
            
        # Handle secondary titles (functional modules)
        if stripped.startswith('## ') and not in_code_block:
            title = stripped[3:].strip()
            enhanced_lines.append('')
            enhanced_lines.append(f'### 🎯 {title}')
            enhanced_lines.append('')
            continue
            
        # Handle code block start
        if stripped.startswith('```') and not in_code_block:
            in_code_block = True
            enhanced_lines.append('')
            enhanced_lines.append('```')
            continue
            
        # Handle code block end
        if stripped.startswith('```') and in_code_block:
            in_code_block = False
            enhanced_lines.append('```')
            enhanced_lines.append('')
            continue
            
        # Add other content directly
        enhanced_lines.append(line)
    
    # End highlight area
    enhanced_lines.append('')
    enhanced_lines.append('</div>')
    
    return '\n'.join(enhanced_lines)

def extract_prompts_section(content: str) -> str:
    """Extract the AI programming prompts section from the full content"""
    # Split content, find the AI programming prompts section
    parts = content.split('# AI编程助手提示词')
    
    if len(parts) >= 2:
        prompts_content = '# AI编程助手提示词' + parts[1]
        # Clean and format prompts content, remove HTML tags for copying
        clean_prompts = clean_prompts_for_copy(prompts_content)
        return clean_prompts
    else:
        # If no clear prompts section found, try other keywords
        lines = content.split('\n')
        prompts_section = []
        in_prompts_section = False
        
        for line in lines:
            if any(keyword in line for keyword in ['编程提示词', '编程助手', 'Prompt', 'AI助手']):
                in_prompts_section = True
            if in_prompts_section:
                prompts_section.append(line)
        
        return '\n'.join(prompts_section) if prompts_section else "Programming prompts section not found"

def clean_prompts_for_copy(prompts_content: str) -> str:
    """Clean prompts content, remove HTML tags, optimize copy experience"""
    import re
    
    # Remove HTML tags
    clean_content = re.sub(r'<[^>]+>', '', prompts_content)
    
    # Clean extra blank lines
    lines = clean_content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        stripped = line.strip()
        if stripped:
            cleaned_lines.append(line)
        elif cleaned_lines and cleaned_lines[-1].strip():  # Avoid consecutive blank lines
            cleaned_lines.append('')
    
    return '\n'.join(cleaned_lines)

# Remove redundant old code, this should be the enhance_markdown_structure function
def enhance_markdown_structure(content: str) -> str:
    """Enhance Markdown structure, add visual highlights and hierarchy"""
    lines = content.split('\n')
    enhanced_lines = []
    
    for line in lines:
        stripped = line.strip()
        
        # Enhance level 1 headings
        if stripped and not stripped.startswith('#') and len(stripped) < 50 and '：' not in stripped and '.' not in stripped[:5]:
            if any(keyword in stripped for keyword in ['Product Overview', 'Technical Solution', 'Development Plan', 'Deployment Plan', 'Growth Strategy', 'AI', '编程助手', '提示词']):
                enhanced_lines.append(f"\n## 🎯 {stripped}\n")
                continue
        
        # Enhance level 2 headings
        if stripped and '.' in stripped[:5] and len(stripped) < 100:
            if stripped[0].isdigit():
                enhanced_lines.append(f"\n### 📋 {stripped}\n")
                continue
                
        # Enhance feature lists
        if stripped.startswith('主要功能') or stripped.startswith('目标用户'):
            enhanced_lines.append(f"\n#### 🔹 {stripped}\n")
            continue
            
        # Enhance tech stack sections
        if stripped in ['Frontend', 'Backend', 'AI 模型', '工具和库']:
            enhanced_lines.append(f"\n#### 🛠️ {stripped}\n")
            continue
            
        # Enhance phase titles
        if '阶段' in stripped and '：' in stripped:
            if '第' in stripped and '阶段' in stripped:
                try:
                    # More robust phase number extraction logic
                    parts = stripped.split('第')
                    if len(parts) > 1:
                        phase_part = parts[1].split('阶段')[0].strip()
                        phase_name = stripped.split('：')[1].strip() if '：' in stripped else ''
                        enhanced_lines.append(f"\n#### 🚀 第{phase_part}阶段：{phase_name}\n")
                    else:
                        enhanced_lines.append(f"\n#### 🚀 {stripped}\n")
                except:
                    enhanced_lines.append(f"\n#### 🚀 {stripped}\n")
            else:
                enhanced_lines.append(f"\n#### 🚀 {stripped}\n")
            continue
            
        # Enhance task list
        if stripped.startswith('任务：'):
            enhanced_lines.append(f"\n**📝 {stripped}**\n")
            continue
            
        # Keep other content with original indentation
        enhanced_lines.append(line)
    
    return '\n'.join(enhanced_lines)

# Custom CSS - Maintain UI beautification
custom_css = """
.main-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

.header-gradient {
    background: linear-gradient(135deg, #1e40af 0%, #3b82f6 50%, #60a5fa 100%);
    color: white;
    padding: 2.5rem;
    border-radius: 1.5rem;
    text-align: center;
    margin-bottom: 2rem;
    box-shadow: 0 10px 30px rgba(59, 130, 246, 0.3);
    position: relative;
    overflow: hidden;
}

.header-gradient::before {
    content: "";
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: linear-gradient(45deg, transparent 40%, rgba(255,255,255,0.1) 50%, transparent 60%);
    animation: shine 3s infinite;
}

@keyframes shine {
    0% { transform: translateX(-100%) translateY(-100%) rotate(45deg); }
    100% { transform: translateX(100%) translateY(100%) rotate(45deg); }
}

.content-card {
    background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
    padding: 2rem;
    border-radius: 1.5rem;
    box-shadow: 0 8px 25px rgba(59, 130, 246, 0.1);
    margin: 1rem 0;
    border: 1px solid #e2e8f0;
}

.dark .content-card {
    background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
    border-color: #374151;
}

.result-container {
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    border-radius: 1.5rem;
    padding: 2rem;
    margin: 2rem 0;
    border: 2px solid #3b82f6;
    box-shadow: 0 10px 30px rgba(59, 130, 246, 0.15);
}

.dark .result-container {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border-color: #60a5fa;
}

.generate-btn {
    background: linear-gradient(45deg, #3b82f6, #1d4ed8) !important;
    border: none !important;
    color: white !important;
    padding: 1rem 2.5rem !important;
    border-radius: 2rem !important;
    font-weight: 700 !important;
    font-size: 1.1rem !important;
    transition: all 0.4s ease !important;
    box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4) !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    position: relative;
    overflow: hidden;
}

.generate-btn:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 12px 35px rgba(59, 130, 246, 0.5) !important;
    background: linear-gradient(45deg, #1d4ed8, #1e40af) !important;
}

.generate-btn::before {
    content: "";
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
    transition: left 0.5s;
}

.generate-btn:hover::before {
    left: 100%;
}

.tips-box {
    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
    padding: 1.5rem;
    border-radius: 1.2rem;
    margin: 1.5rem 0;
    border: 2px solid #93c5fd;
    box-shadow: 0 6px 20px rgba(147, 197, 253, 0.2);
}

.dark .tips-box {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border-color: #60a5fa;
}

.tips-box h4 {
    color: #1d4ed8;
    margin-bottom: 1rem;
    font-weight: 700;
    font-size: 1.2rem;
}

.dark .tips-box h4 {
    color: #60a5fa;
}

.tips-box ul {
    margin: 10px 0;
    padding-left: 20px;
}

.tips-box li {
    margin: 8px 0;
    color: #333;
}

.prompts-section {
    background: #f0f8ff;
    border: 2px dashed #007bff;
    border-radius: 10px;
    padding: 20px;
    margin: 20px 0;
}

/* Enhanced Plan Header */
.plan-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 2rem;
    border-radius: 15px;
    margin-bottom: 2rem;
    text-align: center;
}

.meta-info {
    background: rgba(255,255,255,0.1);
    padding: 1rem;
    border-radius: 10px;
    margin-top: 1rem;
}

/* Enhanced Markdown Styling */
#plan_result {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
    line-height: 1.7;
    color: #2d3748;
}

#plan_result h1 {
    font-size: 2.5rem;
    font-weight: 700;
    color: #1a202c;
    margin-top: 2rem;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 3px solid #4299e1;
}

#plan_result h2 {
    font-size: 2rem;
    font-weight: 600;
    color: #2d3748;
    margin-top: 2rem;
    margin-bottom: 1rem;
    padding-bottom: 0.3rem;
    border-bottom: 2px solid #68d391;
    position: relative;
}

#plan_result h2::before {
    content: "";
    position: absolute;
    left: 0;
    bottom: -2px;
    width: 50px;
    height: 2px;
    background: linear-gradient(90deg, #4299e1, #68d391);
}

#plan_result h3 {
    font-size: 1.5rem;
    font-weight: 600;
    color: #4a5568;
    margin-top: 1.5rem;
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    padding: 0.5rem 1rem;
    background: linear-gradient(90deg, #f7fafc, #edf2f7);
    border-left: 4px solid #4299e1;
    border-radius: 0.5rem;
}

#plan_result h4 {
    font-size: 1.25rem;
    font-weight: 600;
    color: #5a67d8;
    margin-top: 1.25rem;
    margin-bottom: 0.5rem;
    padding-left: 1rem;
    border-left: 3px solid #5a67d8;
}

#plan_result h5, #plan_result h6 {
    font-size: 1.1rem;
    font-weight: 600;
    color: #667eea;
    margin-top: 1rem;
    margin-bottom: 0.5rem;
}

#plan_result p {
    margin-bottom: 1rem;
    font-size: 1rem;
    line-height: 1.8;
}

#plan_result ul, #plan_result ol {
    margin: 1rem 0;
    padding-left: 2rem;
}

#plan_result li {
    margin-bottom: 0.5rem;
    line-height: 1.7;
}

#plan_result ul li {
    list-style-type: none;
    position: relative;
}

#plan_result ul li:before {
    content: "▶";
    color: #4299e1;
    font-weight: bold;
    position: absolute;
    left: -1.5rem;
}

#plan_result blockquote {
    border-left: 4px solid #4299e1;
    background: #ebf8ff;
    padding: 1rem 1.5rem;
    margin: 1.5rem 0;
    border-radius: 0.5rem;
    font-style: italic;
    color: #2b6cb0;
}

#plan_result code {
    background: #f7fafc;
    border: 1px solid #e2e8f0;
    border-radius: 0.25rem;
    padding: 0.125rem 0.375rem;
    font-family: 'Fira Code', 'Monaco', 'Consolas', monospace;
    font-size: 0.875rem;
    color: #d53f8c;
}

#plan_result pre {
    background: #1a202c;
    color: #f7fafc;
    border-radius: 0.5rem;
    padding: 1.5rem;
    margin: 1.5rem 0;
    overflow-x: auto;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

#plan_result pre code {
    background: transparent;
    border: none;
    padding: 0;
    color: #f7fafc;
    font-size: 0.9rem;
}

#plan_result table {
    width: 100%;
    border-collapse: collapse;
    margin: 1.5rem 0;
    background: white;
    border-radius: 0.5rem;
    overflow: hidden;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

#plan_result th {
    background: #4299e1;
    color: white;
    padding: 0.75rem 1rem;
    text-align: left;
    font-weight: 600;
}

#plan_result td {
    padding: 0.75rem 1rem;
    border-bottom: 1px solid #e2e8f0;
}

#plan_result tr:nth-child(even) {
    background: #f7fafc;
}

#plan_result tr:hover {
    background: #ebf8ff;
}

#plan_result strong {
    color: #2d3748;
    font-weight: 600;
}

#plan_result em {
    color: #5a67d8;
    font-style: italic;
}

#plan_result hr {
    border: none;
    height: 2px;
    background: linear-gradient(90deg, #4299e1 0%, #68d391 100%);
    margin: 2rem 0;
    border-radius: 1px;
}

/* Special styling for reference info */
.reference-info {
    background: linear-gradient(135deg, #f0f8ff 0%, #e6f3ff 100%);
    border: 2px solid #4299e1;
    border-radius: 1rem;
    padding: 1.5rem;
    margin: 1.5rem 0;
    box-shadow: 0 4px 15px rgba(66, 153, 225, 0.1);
}

/* Special styling for prompts section */
#plan_result .prompts-highlight {
    background: linear-gradient(135deg, #f0f8ff 0%, #e6f3ff 100%);
    border: 2px solid #4299e1;
    border-radius: 1rem;
    padding: 1.5rem;
    margin: 1.5rem 0;
    position: relative;
}

#plan_result .prompts-highlight:before {
    content: "🤖";
    position: absolute;
    top: -0.5rem;
    left: 1rem;
    background: #4299e1;
    color: white;
    padding: 0.5rem;
    border-radius: 50%;
    font-size: 1.2rem;
}

/* Improved section dividers */
#plan_result .section-divider {
    background: linear-gradient(90deg, transparent 0%, #4299e1 20%, #68d391 80%, transparent 100%);
    height: 1px;
    margin: 2rem 0;
}

/* 编程提示词专用样式 */
.prompts-highlight {
    background: linear-gradient(135deg, #f0f8ff 0%, #e6f3ff 100%);
    border: 2px solid #4299e1;
    border-radius: 1rem;
    padding: 2rem;
    margin: 2rem 0;
    position: relative;
    box-shadow: 0 8px 25px rgba(66, 153, 225, 0.15);
}

.prompts-highlight:before {
    content: "🤖";
    position: absolute;
    top: -0.8rem;
    left: 1.5rem;
    background: linear-gradient(135deg, #4299e1, #667eea);
    color: white;
    padding: 0.8rem;
    border-radius: 50%;
    font-size: 1.5rem;
    box-shadow: 0 4px 12px rgba(66, 153, 225, 0.3);
}

.prompt-section {
    background: rgba(255, 255, 255, 0.8);
    border-radius: 0.8rem;
    padding: 1.5rem;
    margin: 1.5rem 0;
    border-left: 4px solid #667eea;
    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.05);
}

.prompt-code-block {
    position: relative;
    margin: 1rem 0;
}

.prompt-code-block pre {
    background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%) !important;
    border: 2px solid #4299e1;
    border-radius: 0.8rem;
    padding: 1.5rem;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    position: relative;
    overflow-x: auto;
}

.prompt-code-block pre:before {
    content: "📋 ClickCopy此提示词";
    position: absolute;
    top: -0.5rem;
    right: 1rem;
    background: linear-gradient(45deg, #667eea, #764ba2);
    color: white;
    padding: 0.3rem 0.8rem;
    border-radius: 1rem;
    font-size: 0.8rem;
    font-weight: 500;
    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.prompt-code-block code {
    color: #e2e8f0 !important;
    font-family: 'Fira Code', 'Monaco', 'Consolas', monospace !important;
    font-size: 0.95rem !important;
    line-height: 1.6 !important;
    background: transparent !important;
    border: none !important;
}

/* 提示词高亮关键词 */
.prompt-code-block code .keyword {
    color: #81e6d9 !important;
    font-weight: 600;
}

.prompt-code-block code .requirement {
    color: #fbb6ce !important;
}

.prompt-code-block code .output {
    color: #c6f6d5 !important;
}

/* 优化按钮样式 */
.optimize-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
    margin-right: 10px !important;
    transition: all 0.3s ease !important;
    padding: 0.6rem 1.2rem !important;
    border-radius: 1.5rem !important;
}

.optimize-btn:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4) !important;
}

.reset-btn {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    padding: 0.6rem 1.2rem !important;
    border-radius: 1.5rem !important;
}

.reset-btn:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(240, 147, 251, 0.4) !important;
}

.optimization-result {
    margin-top: 15px !important;
    padding: 15px !important;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    border-radius: 8px !important;
    color: white !important;
    border-left: 4px solid #4facfe !important;
}

.optimization-result h2 {
    color: #fff !important;
    margin-bottom: 10px !important;
}

.optimization-result strong {
    color: #e0e6ff !important;
}

/* processing过程说明区域样式 */
.process-explanation {
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%) !important;
    border: 2px solid #cbd5e0 !important;
    border-radius: 1rem !important;
    padding: 2rem !important;
    margin: 1rem 0 !important;
    font-family: 'Inter', -apple-system, system-ui, sans-serif !important;
}

.process-explanation h1 {
    color: #2b6cb0 !important;
    font-size: 1.8rem !important;
    margin-bottom: 1rem !important;
    border-bottom: 3px solid #3182ce !important;
    padding-bottom: 0.5rem !important;
}

.process-explanation h2 {
    color: #2c7a7b !important;
    font-size: 1.4rem !important;
    margin-top: 1.5rem !important;
    margin-bottom: 1rem !important;
    background: linear-gradient(135deg, #e6fffa 0%, #f0fff4 100%) !important;
    padding: 0.8rem !important;
    border-radius: 0.5rem !important;
    border-left: 4px solid #38b2ac !important;
}

.process-explanation h3 {
    color: #38a169 !important;
    font-size: 1.2rem !important;
    margin-top: 1rem !important;
    margin-bottom: 0.5rem !important;
}

.process-explanation strong {
    color: #e53e3e !important;
    font-weight: 600 !important;
}

.process-explanation ul {
    padding-left: 1.5rem !important;
}

.process-explanation li {
    margin-bottom: 0.5rem !important;
    color: #4a5568 !important;
}

.explanation-btn {
    background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    padding: 0.6rem 1.2rem !important;
    border-radius: 1.5rem !important;
    margin-right: 10px !important;
}

.explanation-btn:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(66, 153, 225, 0.4) !important;
}

/* Copy按钮增强 */
.copy-btn {
    background: linear-gradient(45deg, #667eea, #764ba2) !important;
    border: none !important;
    color: white !important;
    padding: 0.8rem 1.5rem !important;
    border-radius: 2rem !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
}

.copy-btn:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4) !important;
    background: linear-gradient(45deg, #5a67d8, #667eea) !important;
}

.copy-btn:active {
    transform: translateY(0) !important;
}

/* 响应式优化 */
@media (max-width: 768px) {
    .main-container {
        max-width: 100%;
        padding: 10px;
    }
    
    .prompts-highlight {
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .prompt-section {
        padding: 1rem;
    }
    
    .prompt-code-block pre {
        padding: 1rem;
        font-size: 0.85rem;
    }
    
    .prompt-copy-section {
        margin: 0.5rem 0;
        padding: 0.25rem;
        flex-direction: column;
        align-items: stretch;
    }
    
    .individual-copy-btn {
        width: 100% !important;
        justify-content: center !important;
        margin: 0.25rem 0 !important;
        padding: 0.5rem 1rem !important;
        font-size: 0.8rem !important;
    }
    
    #plan_result h1 {
        font-size: 2rem;
    }
    
    #plan_result h2 {
        font-size: 1.5rem;
    }
    
    #plan_result h3 {
        font-size: 1.25rem;
        padding: 0.375rem 0.75rem;
    }
}

@media (max-width: 1024px) and (min-width: 769px) {
    .main-container {
        max-width: 95%;
        padding: 15px;
    }
    
    .individual-copy-btn {
        padding: 0.45rem 0.9rem !important;
        font-size: 0.78rem !important;
    }
    
    .prompt-copy-section {
        margin: 0.6rem 0;
    }
}

/* Mermaid图表样式优化 */
.mermaid {
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%) !important;
    border: 2px solid #3b82f6 !important;
    border-radius: 1rem !important;
    padding: 2rem !important;
    margin: 2rem 0 !important;
    text-align: center !important;
    box-shadow: 0 8px 25px rgba(59, 130, 246, 0.15) !important;
}

.dark .mermaid {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
    border-color: #60a5fa !important;
    color: #f8fafc !important;
}

/* Mermaid包装器样式 */
.mermaid-wrapper {
    margin: 2rem 0;
    position: relative;
    overflow: hidden;
    border-radius: 1rem;
    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
    border: 2px solid #3b82f6;
    box-shadow: 0 10px 30px rgba(59, 130, 246, 0.2);
}

.mermaid-render {
    min-height: 200px;
    padding: 1.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
}

.dark .mermaid-wrapper {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border-color: #60a5fa;
}

/* 图表errorprocessing */
.mermaid-error {
    background: #fef2f2;
    border: 2px solid #f87171;
    color: #991b1b;
    padding: 1rem;
    border-radius: 0.5rem;
    text-align: center;
    font-family: monospace;
}

.dark .mermaid-error {
    background: #7f1d1d;
    border-color: #ef4444;
    color: #fecaca;
}

/* Mermaid图表容器增强 */
.chart-container {
    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
    border: 3px solid #3b82f6;
    border-radius: 1.5rem;
    padding: 2rem;
    margin: 2rem 0;
    text-align: center;
    position: relative;
    box-shadow: 0 10px 30px rgba(59, 130, 246, 0.2);
}

.chart-container::before {
    content: "📊";
    position: absolute;
    top: -1rem;
    left: 2rem;
    background: linear-gradient(135deg, #3b82f6, #1d4ed8);
    color: white;
    padding: 0.8rem;
    border-radius: 50%;
    font-size: 1.5rem;
    box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
}

.dark .chart-container {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border-color: #60a5fa;
}

.dark .chart-container::before {
    background: linear-gradient(135deg, #60a5fa, #3b82f6);
}

/* 表格样式全面增强 */
.enhanced-table {
    width: 100%;
    border-collapse: collapse;
    margin: 2rem 0;
    background: white;
    border-radius: 1rem;
    overflow: hidden;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
    border: 2px solid #e5e7eb;
}

.enhanced-table th {
    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
    color: white;
    padding: 1.2rem;
    text-align: left;
    font-weight: 700;
    font-size: 1rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.enhanced-table td {
    padding: 1rem 1.2rem;
    border-bottom: 1px solid #e5e7eb;
    vertical-align: top;
    font-size: 0.95rem;
    line-height: 1.6;
}

.enhanced-table tr:nth-child(even) {
    background: linear-gradient(90deg, #f8fafc 0%, #f1f5f9 100%);
}

.enhanced-table tr:hover {
    background: linear-gradient(90deg, #eff6ff 0%, #dbeafe 100%);
    transform: translateY(-1px);
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(59, 130, 246, 0.1);
}

.dark .enhanced-table {
    background: #1f2937;
    border-color: #374151;
}

.dark .enhanced-table th {
    background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
    color: #f9fafb;
}

.dark .enhanced-table td {
    border-bottom-color: #374151;
    color: #f9fafb;
}

.dark .enhanced-table tr:nth-child(even) {
    background: linear-gradient(90deg, #374151 0%, #1f2937 100%);
}

.dark .enhanced-table tr:hover {
    background: linear-gradient(90deg, #4b5563 0%, #374151 100%);
}

/* 单独Copy按钮样式 */
.prompt-copy-section {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    margin: 0.75rem 0;
    padding: 0.375rem;
    background: rgba(66, 153, 225, 0.05);
    border-radius: 0.375rem;
}

.individual-copy-btn {
    background: linear-gradient(45deg, #4299e1, #3182ce) !important;
    border: none !important;
    color: white !important;
    padding: 0.4rem 0.8rem !important;
    border-radius: 0.75rem !important;
    font-size: 0.75rem !important;
    font-weight: 500 !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 1px 4px rgba(66, 153, 225, 0.2) !important;
    display: inline-flex !important;
    align-items: center !important;
    gap: 0.25rem !important;
    min-width: auto !important;
    max-height: 32px !important;
}

.individual-copy-btn:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 2px 8px rgba(66, 153, 225, 0.3) !important;
    background: linear-gradient(45deg, #3182ce, #2c5aa0) !important;
}

.individual-copy-btn:active {
    transform: translateY(0) !important;
}

.edit-prompt-btn {
    background: linear-gradient(45deg, #667eea, #764ba2) !important;
    border: none !important;
    color: white !important;
    padding: 0.4rem 0.8rem !important;
    border-radius: 0.75rem !important;
    font-size: 0.75rem !important;
    font-weight: 500 !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 1px 4px rgba(102, 126, 234, 0.2) !important;
    display: inline-flex !important;
    align-items: center !important;
    gap: 0.25rem !important;
    min-width: auto !important;
    max-height: 32px !important;
    margin-left: 0.5rem !important;
}

.edit-prompt-btn:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3) !important;
    background: linear-gradient(45deg, #5a67d8, #667eea) !important;
}

.edit-prompt-btn:active {
    transform: translateY(0) !important;
}

.copy-success-msg {
    font-size: 0.85rem;
    font-weight: 600;
    animation: fadeInOut 2s ease-in-out;
}

@keyframes fadeInOut {
    0% { opacity: 0; transform: translateX(-10px); }
    20% { opacity: 1; transform: translateX(0); }
    80% { opacity: 1; transform: translateX(0); }
    100% { opacity: 0; transform: translateX(10px); }
}

.dark .prompt-copy-section {
    background: rgba(99, 179, 237, 0.1);
}

.dark .individual-copy-btn {
    background: linear-gradient(45deg, #63b3ed, #4299e1) !important;
    box-shadow: 0 1px 4px rgba(99, 179, 237, 0.2) !important;
}

.dark .individual-copy-btn:hover {
    background: linear-gradient(45deg, #4299e1, #3182ce) !important;
    box-shadow: 0 2px 8px rgba(99, 179, 237, 0.3) !important;
}

.dark .edit-prompt-btn {
    background: linear-gradient(45deg, #9f7aea, #805ad5) !important;
    box-shadow: 0 1px 4px rgba(159, 122, 234, 0.2) !important;
}

.dark .edit-prompt-btn:hover {
    background: linear-gradient(45deg, #805ad5, #6b46c1) !important;
    box-shadow: 0 2px 8px rgba(159, 122, 234, 0.3) !important;
}

/* Fix accordion height issue - AgentApply架构说明折叠问题 */
.gradio-accordion {
    transition: all 0.3s ease !important;
    overflow: hidden !important;
}

.gradio-accordion[data-testid$="accordion"] {
    min-height: auto !important;
    height: auto !important;
}

.gradio-accordion .gradio-accordion-content {
    transition: max-height 0.3s ease !important;
    overflow: hidden !important;
}

/* Gradio内部accordion组件修复 */
details.gr-accordion {
    transition: all 0.3s ease !important;
}

details.gr-accordion[open] {
    height: auto !important;
    min-height: auto !important;
}

details.gr-accordion:not([open]) {
    height: auto !important;
    min-height: 50px !important;
}

/* 确保折叠后页面恢复正常大小 */
.gr-block.gr-box {
    transition: height 0.3s ease !important;
    height: auto !important;
}

/* Fix for quick start text contrast */
#quick_start_container p {
    color: #4A5568;
}

.dark #quick_start_container p {
    color: #E2E8F0;
}

/* 重要：大幅改善dark模式下的文字对比度 */

/* 主要content区域 - AIgeneratecontent显示区 */
.dark #plan_result {
    color: #F7FAFC !important;
    background: #2D3748 !important;
}

.dark #plan_result p {
    color: #F7FAFC !important;
}

.dark #plan_result strong {
    color: #FFFFFF !important;
}

/* Dark模式下占位符样式优化 */
.dark #plan_result div[style*="background: linear-gradient"] {
    background: linear-gradient(135deg, #2D3748 0%, #4A5568 100%) !important;
    border-color: #63B3ED !important;
}

.dark #plan_result h3 {
    color: #63B3ED !important;
}

.dark #plan_result div[style*="background: linear-gradient(90deg"] {
    background: linear-gradient(90deg, #2D3748 0%, #1A202C 100%) !important;
    border-left-color: #4FD1C7 !important;
}

.dark #plan_result div[style*="background: linear-gradient(45deg"] {
    background: linear-gradient(45deg, #4A5568 0%, #2D3748 100%) !important;
}

/* Dark模式下的彩色文字优化 */
.dark #plan_result span[style*="color: #e53e3e"] {
    color: #FC8181 !important;
}

.dark #plan_result span[style*="color: #38a169"] {
    color: #68D391 !important;
}

.dark #plan_result span[style*="color: #3182ce"] {
    color: #63B3ED !important;
}

.dark #plan_result span[style*="color: #805ad5"] {
    color: #B794F6 !important;
}

.dark #plan_result strong[style*="color: #d69e2e"] {
    color: #F6E05E !important;
}

.dark #plan_result strong[style*="color: #e53e3e"] {
    color: #FC8181 !important;
}

.dark #plan_result p[style*="color: #2c7a7b"] {
    color: #4FD1C7 !important;
}

.dark #plan_result p[style*="color: #c53030"] {
    color: #FC8181 !important;
}

/* 重点优化：AI编程助手Usage Instructions区域 */
.dark #ai_helper_instructions {
    color: #F7FAFC !important;
    background: rgba(45, 55, 72, 0.8) !important;
}

.dark #ai_helper_instructions p {
    color: #F7FAFC !important;
}

.dark #ai_helper_instructions li {
    color: #F7FAFC !important;
}

.dark #ai_helper_instructions strong {
    color: #FFFFFF !important;
}

/* generatecontent的markdown渲染 - 主要问题区域 */
.dark #plan_result {
    color: #FFFFFF !important;
    background: #1A202C !important;
}

.dark #plan_result h1,
.dark #plan_result h2,
.dark #plan_result h3,
.dark #plan_result h4,
.dark #plan_result h5,
.dark #plan_result h6 {
    color: #FFFFFF !important;
}

.dark #plan_result p {
    color: #FFFFFF !important;
}

.dark #plan_result li {
    color: #FFFFFF !important;
}

.dark #plan_result strong {
    color: #FFFFFF !important;
}

.dark #plan_result em {
    color: #E2E8F0 !important;
}

.dark #plan_result td {
    color: #FFFFFF !important;
    background: #2D3748 !important;
}

.dark #plan_result th {
    color: #FFFFFF !important;
    background: #1A365D !important;
}

/* 确保所有文字content都是白色 */
.dark #plan_result * {
    color: #FFFFFF !important;
}

/* 特殊元素保持样式 */
.dark #plan_result code {
    color: #81E6D9 !important;
    background: #1A202C !important;
}

.dark #plan_result pre {
    background: #0D1117 !important;
    color: #F0F6FC !important;
}

.dark #plan_result blockquote {
    color: #FFFFFF !important;
    background: #2D3748 !important;
    border-left-color: #63B3ED !important;
}

/* 确保generate报告在dark模式下清晰可见 */
.dark .plan-header {
    background: linear-gradient(135deg, #4A5568 0%, #2D3748 100%) !important;
    color: #FFFFFF !important;
}

.dark .meta-info {
    background: rgba(255,255,255,0.2) !important;
    color: #FFFFFF !important;
}

/* 提示词容器在dark模式下的优化 */
.dark .prompts-highlight {
    background: linear-gradient(135deg, #2D3748 0%, #4A5568 100%) !important;
    border: 2px solid #63B3ED !important;
    color: #F7FAFC !important;
}

.dark .prompt-section {
    background: rgba(45, 55, 72, 0.9) !important;
    color: #F7FAFC !important;
    border-left: 4px solid #63B3ED !important;
}

/* 确保所有文字content在dark模式下都清晰可见 */
.dark textarea,
.dark input {
    color: #F7FAFC !important;
    background: #2D3748 !important;
}

.dark .gr-markdown {
    color: #F7FAFC !important;
}

/* 特别针对提示文字的优化 */
.dark .tips-box {
    background: #2D3748 !important;
    color: #F7FAFC !important;
}

.dark .tips-box h4 {
    color: #63B3ED !important;
}

.dark .tips-box li {
    color: #F7FAFC !important;
}

/* 按钮在dark模式下的优化 */
.dark .copy-btn {
    color: #FFFFFF !important;
}

/* 确保AgentApply说明在dark模式下清晰 */
.dark .gr-accordion {
    color: #F7FAFC !important;
    background: #2D3748 !important;
}

/* 修复具体的文字对比度问题 */
.dark #input_idea_title {
    color: #FFFFFF !important;
}

.dark #input_idea_title h2 {
    color: #FFFFFF !important;
}

.dark #download_success_info {
    background: #2D3748 !important;
    color: #F7FAFC !important;
    border: 1px solid #4FD1C7 !important;
}

.dark #download_success_info strong {
    color: #68D391 !important;
}

.dark #download_success_info span {
    color: #F7FAFC !important;
}

.dark #usage_tips {
    background: #2D3748 !important;
    color: #F7FAFC !important;
    border: 1px solid #63B3ED !important;
}

.dark #usage_tips strong {
    color: #63B3ED !important;
}

/* Loading spinner */
.loading-spinner {
    border: 3px solid #f3f3f3;
    border-top: 3px solid #007bff;
    border-radius: 50%;
    width: 20px;
    height: 20px;
    animation: spin 1s linear infinite;
    display: inline-block;
    margin-right: 10px;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Copy buttons styling */
.copy-buttons {
    display: flex;
    gap: 10px;
    margin: 1rem 0;
}

.copy-btn {
    background: linear-gradient(45deg, #28a745, #20c997) !important;
    border: none !important;
    color: white !important;
    padding: 8px 16px !important;
    border-radius: 20px !important;
    font-size: 14px !important;
    transition: all 0.3s ease !important;
}

.copy-btn:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3) !important;
}

/* 分段Edit器样式 */
.plan-editor-container {
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    border: 2px solid #cbd5e0;
    border-radius: 1rem;
    padding: 2rem;
    margin: 2rem 0;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.editor-header {
    text-align: center;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 2px solid #e2e8f0;
}

.editor-header h3 {
    color: #2b6cb0;
    margin-bottom: 0.5rem;
    font-size: 1.5rem;
    font-weight: 700;
}

.editor-header p {
    color: #4a5568;
    margin: 0;
    font-size: 1rem;
}

.sections-container {
    display: grid;
    gap: 1.5rem;
    margin-bottom: 2rem;
}

.editable-section {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 0.75rem;
    padding: 1.5rem;
    transition: all 0.3s ease;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.editable-section:hover {
    border-color: #3b82f6;
    box-shadow: 0 4px 15px rgba(59, 130, 246, 0.1);
    transform: translateY(-2px);
}

.section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #f1f5f9;
}

.section-type {
    font-size: 1.2rem;
    margin-right: 0.5rem;
}

.section-title {
    font-weight: 600;
    color: #2d3748;
    flex: 1;
}

.edit-section-btn {
    background: linear-gradient(45deg, #667eea, #764ba2) !important;
    border: none !important;
    color: white !important;
    padding: 0.5rem 1rem !important;
    border-radius: 0.5rem !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2) !important;
}

.edit-section-btn:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3) !important;
    background: linear-gradient(45deg, #5a67d8, #667eea) !important;
}

.section-preview {
    position: relative;
}

.preview-content {
    color: #4a5568;
    line-height: 1.6;
    font-size: 0.95rem;
    padding: 1rem;
    background: #f8fafc;
    border-radius: 0.5rem;
    border-left: 4px solid #3b82f6;
}

.editor-actions {
    display: flex;
    gap: 1rem;
    justify-content: center;
    align-items: center;
    padding-top: 1.5rem;
    border-top: 2px solid #e2e8f0;
}

.apply-changes-btn {
    background: linear-gradient(45deg, #48bb78, #38a169) !important;
    border: none !important;
    color: white !important;
    padding: 0.8rem 1.5rem !important;
    border-radius: 0.75rem !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(72, 187, 120, 0.3) !important;
}

.apply-changes-btn:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(72, 187, 120, 0.4) !important;
    background: linear-gradient(45deg, #38a169, #2f855a) !important;
}

.reset-changes-btn {
    background: linear-gradient(45deg, #f093fb, #f5576c) !important;
    border: none !important;
    color: white !important;
    padding: 0.8rem 1.5rem !important;
    border-radius: 0.75rem !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(240, 147, 251, 0.3) !important;
}

.reset-changes-btn:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(240, 147, 251, 0.4) !important;
    background: linear-gradient(45deg, #f5576c, #e53e3e) !important;
}

/* Edit历史样式 */
.edit-history {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 0.75rem;
    padding: 1.5rem;
    margin: 1rem 0;
}

.edit-history h3 {
    color: #2b6cb0;
    margin-bottom: 1rem;
    font-size: 1.25rem;
}

.history-list {
    max-height: 300px;
    overflow-y: auto;
}

.history-item {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 0.5rem;
    padding: 1rem;
    margin-bottom: 0.75rem;
    transition: all 0.2s ease;
}

.history-item:hover {
    border-color: #3b82f6;
    box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
}

.history-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
}

.history-index {
    background: #3b82f6;
    color: white;
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;
    font-weight: 600;
    font-size: 0.8rem;
}

.history-time {
    color: #6b7280;
    font-family: 'Monaco', monospace;
}

.history-section {
    color: #4a5568;
    font-weight: 500;
}

.history-comment {
    color: #374151;
    font-style: italic;
    padding-left: 1rem;
    border-left: 2px solid #e5e7eb;
}

/* Dark模式适配 */
.dark .plan-editor-container {
    background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
    border-color: #4a5568;
}

.dark .editor-header h3 {
    color: #63b3ed;
}

.dark .editor-header p {
    color: #e2e8f0;
}

.dark .editable-section {
    background: #374151;
    border-color: #4a5568;
}

.dark .editable-section:hover {
    border-color: #60a5fa;
}

.dark .section-title {
    color: #f7fafc;
}

.dark .preview-content {
    color: #e2e8f0;
    background: #2d3748;
    border-left-color: #60a5fa;
}

.dark .edit-history {
    background: #2d3748;
    border-color: #4a5568;
}

.dark .edit-history h3 {
    color: #63b3ed;
}

.dark .history-item {
    background: #374151;
    border-color: #4a5568;
}

.dark .history-item:hover {
    border-color: #60a5fa;
}

.dark .history-time {
    color: #9ca3af;
}

.dark .history-section {
    color: #e2e8f0;
}

.dark .history-comment {
    color: #d1d5db;
    border-left-color: #4a5568;
}

/* 响应式设计 */
@media (max-width: 768px) {
    .plan-editor-container {
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .section-header {
        flex-direction: column;
        gap: 0.5rem;
        align-items: flex-start;
    }
    
    .edit-section-btn {
        align-self: flex-end;
    }
    
    .editor-actions {
        flex-direction: column;
        gap: 0.75rem;
    }
    
    .apply-changes-btn,
    .reset-changes-btn {
        width: 100%;
    }
}
"""

# 保持美化的Gradio界面
with gr.Blocks(
    title="VibeDoc Agent：您的随身AI产品经理与架构师",
    theme=gr.themes.Soft(primary_hue="blue"),
    css=custom_css
) as demo:
    
    gr.HTML("""
    <div class="header-gradient">
        <h1>🚀 VibeDoc - AI-Powered Development Plan Generator</h1>
        <p style="font-size: 18px; margin: 15px 0; opacity: 0.95;">
            🤖 Transform your ideas into comprehensive development plans in 60-180 seconds
        </p>
        <p style="opacity: 0.85;">
            ✨ AI-Driven Planning | � Visual Diagrams | 🎯 Professional Output | � Multi-format Export
        </p>
        <div style="margin-top: 1rem; padding: 0.5rem; background: rgba(255,255,255,0.1); border-radius: 0.5rem;">
            <small style="opacity: 0.9;">
                🌟 Open Source Project | 💡 Built with Qwen2.5-72B-Instruct | ⚡ Fast & Reliable
            </small>
        </div>
    </div>
    
    <!-- 添加Mermaid.js支持 -->
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <script>
        // 增强的Mermaidconfiguration
        mermaid.initialize({ 
            startOnLoad: true,
            theme: 'default',
            flowchart: {
                useMaxWidth: true,
                htmlLabels: true,
                curve: 'basis'
            },
            gantt: {
                useMaxWidth: true,
                gridLineStartPadding: 350,
                fontSize: 13,
                fontFamily: '"Inter", "Source Sans Pro", sans-serif',
                sectionFontSize: 24,
                numberSectionStyles: 4
            },
            themeVariables: {
                primaryColor: '#3b82f6',
                primaryTextColor: '#1f2937',
                primaryBorderColor: '#1d4ed8',
                lineColor: '#6b7280',
                secondaryColor: '#dbeafe',
                tertiaryColor: '#f8fafc',
                background: '#ffffff',
                mainBkg: '#ffffff',
                secondBkg: '#f1f5f9',
                tertiaryBkg: '#eff6ff'
            }
        });
        
        // 监听主题变化，动态更新Mermaid主题
        function updateMermaidTheme() {
            const isDark = document.documentElement.classList.contains('dark');
            const theme = isDark ? 'dark' : 'default';
            mermaid.initialize({ 
                startOnLoad: true,
                theme: theme,
                flowchart: {
                    useMaxWidth: true,
                    htmlLabels: true,
                    curve: 'basis'
                },
                gantt: {
                    useMaxWidth: true,
                    gridLineStartPadding: 350,
                    fontSize: 13,
                    fontFamily: '"Inter", "Source Sans Pro", sans-serif',
                    sectionFontSize: 24,
                    numberSectionStyles: 4
                },
                themeVariables: isDark ? {
                    primaryColor: '#60a5fa',
                    primaryTextColor: '#f8fafc',
                    primaryBorderColor: '#3b82f6',
                    lineColor: '#94a3b8',
                    secondaryColor: '#1e293b',
                    tertiaryColor: '#0f172a',
                    background: '#1f2937',
                    mainBkg: '#1f2937',
                    secondBkg: '#374151',
                    tertiaryBkg: '#1e293b'
                } : {
                    primaryColor: '#3b82f6',
                    primaryTextColor: '#1f2937',
                    primaryBorderColor: '#1d4ed8',
                    lineColor: '#6b7280',
                    secondaryColor: '#dbeafe',
                    tertiaryColor: '#f8fafc',
                    background: '#ffffff',
                    mainBkg: '#ffffff',
                    secondBkg: '#f1f5f9',
                    tertiaryBkg: '#eff6ff'
                }
            });
            
            // 重新渲染所有Mermaid图表
            renderMermaidCharts();
        }
        
        // 强化的Mermaiddiagram rendering函数
        function renderMermaidCharts() {
            try {
                // 清除现有的渲染content
                document.querySelectorAll('.mermaid').forEach(element => {
                    if (element.getAttribute('data-processed') !== 'true') {
                        element.removeAttribute('data-processed');
                    }
                });
                
                // processing包装器中的Mermaidcontent
                document.querySelectorAll('.mermaid-render').forEach(element => {
                    const content = element.textContent.trim();
                    if (content && !element.classList.contains('rendered')) {
                        element.innerHTML = content;
                        element.classList.add('mermaid', 'rendered');
                    }
                });
                
                // 重新初始化Mermaid
                mermaid.init(undefined, document.querySelectorAll('.mermaid:not([data-processed="true"])'));
                
            } catch (error) {
                console.warn('Mermaid渲染警告:', error);
                // 如果渲染failed，显示error信息
                document.querySelectorAll('.mermaid-render').forEach(element => {
                    if (!element.classList.contains('rendered')) {
                        element.innerHTML = '<div class="mermaid-error">diagram rendering中，please wait...</div>';
                    }
                });
            }
        }
        
        // 页面加载完成后初始化
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(renderMermaidCharts, 1000);
        });
        
        // 监听content变化，自动重新渲染图表
        function observeContentChanges() {
            const observer = new MutationObserver(function(mutations) {
                let shouldRender = false;
                mutations.forEach(function(mutation) {
                    if (mutation.type === 'childList') {
                        mutation.addedNodes.forEach(function(node) {
                            if (node.nodeType === Node.ELEMENT_NODE) {
                                if (node.classList && (node.classList.contains('mermaid') || node.querySelector('.mermaid'))) {
                                    shouldRender = true;
                                }
                            }
                        });
                    }
                });
                
                if (shouldRender) {
                    setTimeout(renderMermaidCharts, 500);
                }
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        }
        
        // 启动content观察器
        observeContentChanges();
        
        // 单独Copy提示词功能
        function copyIndividualPrompt(promptId, promptContent) {
            // 解码HTML实体
            const decodedContent = promptContent.replace(/\\n/g, '\n').replace(/\\'/g, "'").replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
            
            if (navigator.clipboard && window.isSecureContext) {
                navigator.clipboard.writeText(decodedContent).then(() => {
                    showCopySuccess(promptId);
                }).catch(err => {
                    console.error('Copyfailed:', err);
                    fallbackCopy(decodedContent);
                });
            } else {
                fallbackCopy(decodedContent);
            }
        }
        
        // Edit提示词功能
        function editIndividualPrompt(promptId, promptContent) {
            // 解码HTML实体
            const decodedContent = promptContent.replace(/\\n/g, '\n').replace(/\\'/g, "'").replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
            
            // 检测当前主题
            const isDark = document.documentElement.classList.contains('dark');
            
            // 创建Edit对话框
            const editDialog = document.createElement('div');
            editDialog.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 10000;
            `;
            
            editDialog.innerHTML = `
                <div style="
                    background: ${isDark ? '#2d3748' : 'white'};
                    color: ${isDark ? '#f7fafc' : '#2d3748'};
                    padding: 2rem;
                    border-radius: 1rem;
                    max-width: 80%;
                    max-height: 80%;
                    overflow-y: auto;
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
                ">
                    <h3 style="margin-bottom: 1rem; color: ${isDark ? '#f7fafc' : '#2d3748'};">✏️ Edit提示词</h3>
                    <textarea
                        id="prompt-editor-${promptId}"
                        style="
                            width: 100%;
                            height: 300px;
                            padding: 1rem;
                            border: 2px solid ${isDark ? '#4a5568' : '#e2e8f0'};
                            border-radius: 0.5rem;
                            font-family: 'Fira Code', monospace;
                            font-size: 0.9rem;
                            resize: vertical;
                            line-height: 1.5;
                            background: ${isDark ? '#1a202c' : 'white'};
                            color: ${isDark ? '#f7fafc' : '#2d3748'};
                        "
                        placeholder="在此Edit您的提示词..."
                    >${decodedContent}</textarea>
                    <div style="margin-top: 1rem; display: flex; gap: 1rem; justify-content: flex-end;">
                        <button
                            id="cancel-edit-${promptId}"
                            style="
                                padding: 0.5rem 1rem;
                                border: 1px solid ${isDark ? '#4a5568' : '#cbd5e0'};
                                background: ${isDark ? '#2d3748' : 'white'};
                                color: ${isDark ? '#f7fafc' : '#4a5568'};
                                border-radius: 0.5rem;
                                cursor: pointer;
                                transition: all 0.2s ease;
                            "
                        >Cancel</button>
                        <button
                            id="save-edit-${promptId}"
                            style="
                                padding: 0.5rem 1rem;
                                background: linear-gradient(45deg, #667eea, #764ba2);
                                color: white;
                                border: none;
                                border-radius: 0.5rem;
                                cursor: pointer;
                                transition: all 0.2s ease;
                            "
                        >Save并Copy</button>
                    </div>
                </div>
            `;
            
            document.body.appendChild(editDialog);
            
            // 绑定按钮事件
            document.getElementById(`cancel-edit-${promptId}`).addEventListener('click', () => {
                document.body.removeChild(editDialog);
            });
            
            document.getElementById(`save-edit-${promptId}`).addEventListener('click', () => {
                const editedContent = document.getElementById(`prompt-editor-${promptId}`).value;
                
                // CopyEdit后的content
                if (navigator.clipboard && window.isSecureContext) {
                    navigator.clipboard.writeText(editedContent).then(() => {
                        showCopySuccess(promptId);
                        document.body.removeChild(editDialog);
                    }).catch(err => {
                        console.error('Copyfailed:', err);
                        fallbackCopy(editedContent);
                        document.body.removeChild(editDialog);
                    });
                } else {
                    fallbackCopy(editedContent);
                    document.body.removeChild(editDialog);
                }
            });
            
            // ESC键Close
            const escapeHandler = (e) => {
                if (e.key === 'Escape') {
                    document.body.removeChild(editDialog);
                    document.removeEventListener('keydown', escapeHandler);
                }
            };
            document.addEventListener('keydown', escapeHandler);
            
            // Click外部Close
            editDialog.addEventListener('click', (e) => {
                if (e.target === editDialog) {
                    document.body.removeChild(editDialog);
                    document.removeEventListener('keydown', escapeHandler);
                }
            });
        }
        
        // 降级Copy方案
        function fallbackCopy(text) {
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            try {
                document.execCommand('copy');
                alert('✅ 提示词已Copy到剪贴板！');
            } catch (err) {
                alert('❌ Copyfailed，请手动选择文本Copy');
            }
            document.body.removeChild(textArea);
        }
        
        // 显示Copysuccess提示
        function showCopySuccess(promptId) {
            const successMsg = document.getElementById('copy-success-' + promptId);
            if (successMsg) {
                successMsg.style.display = 'inline';
                setTimeout(() => {
                    successMsg.style.display = 'none';
                }, 2000);
            }
        }
        
        // 绑定Copy和Edit按钮事件
        function bindCopyButtons() {
            document.querySelectorAll('.individual-copy-btn').forEach(button => {
                button.addEventListener('click', function() {
                    const promptId = this.getAttribute('data-prompt-id');
                    const promptContent = this.getAttribute('data-prompt-content');
                    copyIndividualPrompt(promptId, promptContent);
                });
            });
            
            document.querySelectorAll('.edit-prompt-btn').forEach(button => {
                button.addEventListener('click', function() {
                    const promptId = this.getAttribute('data-prompt-id');
                    const promptContent = this.getAttribute('data-prompt-content');
                    editIndividualPrompt(promptId, promptContent);
                });
            });
        }
        
        // 页面加载完成后初始化
        document.addEventListener('DOMContentLoaded', function() {
            updateMermaidTheme();
            bindCopyButtons();
            
            // 监听主题切换
            const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                        updateMermaidTheme();
                        // 重新渲染所有Mermaid图表
                        setTimeout(() => {
                            document.querySelectorAll('.mermaid').forEach(element => {
                                mermaid.init(undefined, element);
                            });
                        }, 100);
                    }
                });
            });
            observer.observe(document.documentElement, { attributes: true });
            
            // 监听content变化，重新绑定Copy按钮
            const contentObserver = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.type === 'childList') {
                        bindCopyButtons();
                    }
                });
            });
            
            // 监听plan_result区域的变化
            const planResult = document.getElementById('plan_result');
            if (planResult) {
                contentObserver.observe(planResult, { childList: true, subtree: true });
            }
        });
    </script>
    """)
    
    with gr.Row():
        with gr.Column(scale=2, elem_classes="content-card"):
            gr.Markdown("## 💡 输入您的产品创意", elem_id="input_idea_title")
            
            idea_input = gr.Textbox(
                label="产品创意描述",
                placeholder="例如：我想做一个帮助程序员管理代码片段的工具，支持多语言语法高亮，可以按标签分类，还能分享给团队成员...",
                lines=5,
                max_lines=10,
                show_label=False
            )
            
            # 优化按钮和结果显示
            with gr.Row():
                optimize_btn = gr.Button(
                    "✨ 优化创意描述",
                    variant="secondary",
                    size="sm",
                    elem_classes="optimize-btn"
                )
                reset_btn = gr.Button(
                    "🔄 Reset",
                    variant="secondary", 
                    size="sm",
                    elem_classes="reset-btn"
                )
            
            optimization_result = gr.Markdown(
                visible=False,
                elem_classes="optimization-result"
            )
            
            reference_url_input = gr.Textbox(
                label="参考链接 (可选)",
                placeholder="输入任何网页链接（如博客、新闻、文档）作为参考...",
                lines=1,
                show_label=True
            )
            
            generate_btn = gr.Button(
                "🤖 AIgenerateDevelopment Plan + 编程提示词",
                variant="primary",
                size="lg",
                elem_classes="generate-btn"
            )
        
        with gr.Column(scale=1):
            gr.HTML("""
            <div class="tips-box">
                <h4 style="color: #e53e3e;">💡 简单三步</h4>
                <div style="font-size: 16px; font-weight: 600; text-align: center; margin: 20px 0;">
                    <span style="color: #e53e3e;">创意描述</span> → 
                    <span style="color: #38a169;">智能分析</span> → 
                    <span style="color: #3182ce;">完整方案</span>
                </div>
                <h4 style="color: #38a169;">🎯 核心功能</h4>
                <ul>
                    <li><span style="color: #e53e3e;">📋</span> 完整Development Plan</li>
                    <li><span style="color: #3182ce;">🤖</span> AI编程提示词</li>
                    <li><span style="color: #38a169;">�</span> 可视化图表</li>
                    <li><span style="color: #d69e2e;">🔗</span> MCPservice增强</li>
                </ul>
                <h4 style="color: #3182ce;">⏱️ generate时间</h4>
                <ul>
                    <li><span style="color: #e53e3e;">✨</span> 创意优化：20seconds</li>
                    <li><span style="color: #38a169;">📝</span> 方案generate：150-200seconds</li>
                    <li><span style="color: #d69e2e;">⚡</span> 一键CopyDownload</li>
                </ul>
            </div>
            """)
    
    # 结果显示区域
    with gr.Column(elem_classes="result-container"):
        plan_output = gr.Markdown(
            value="""
<div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); border-radius: 1rem; border: 2px dashed #cbd5e0;">
    <div style="font-size: 3rem; margin-bottom: 1rem;">🤖</div>
    <h3 style="color: #2b6cb0; margin-bottom: 1rem; font-weight: bold;">智能Development Plangenerate</h3>
    <p style="color: #4a5568; font-size: 1.1rem; margin-bottom: 1.5rem;">
        💭 <strong style="color: #e53e3e;">输入创意，获得完整开发方案</strong>
    </p>
    <div style="background: linear-gradient(90deg, #edf2f7 0%, #e6fffa 100%); padding: 1rem; border-radius: 0.5rem; margin: 1rem 0; border-left: 4px solid #38b2ac;">
        <p style="color: #2c7a7b; margin: 0; font-weight: 600;">
            🎯 <span style="color: #e53e3e;">Technical Solution</span> • <span style="color: #38a169;">Development Plan</span> • <span style="color: #3182ce;">编程提示词</span>
        </p>
    </div>
    <p style="color: #a0aec0; font-size: 0.9rem;">
        Click <span style="color: #e53e3e; font-weight: bold;">"🤖 AIgenerateDevelopment Plan"</span> 按钮start
    </p>
</div>
            """,
            elem_id="plan_result",
            label="AIgenerate的Development Plan"
        )
        
        # processing过程说明区域
        process_explanation = gr.Markdown(
            visible=False,
            elem_classes="process-explanation"
        )
        
        # 切换按钮
        with gr.Row():
            show_explanation_btn = gr.Button(
                "🔍 查看AIgenerate过程详情",
                variant="secondary",
                size="sm",
                elem_classes="explanation-btn",
                visible=False
            )
            hide_explanation_btn = gr.Button(
                "📝 返回Development Plan",
                variant="secondary",
                size="sm",
                elem_classes="explanation-btn",
                visible=False
            )
        
        # 隐藏的组件用于Copy和Download
        prompts_for_copy = gr.Textbox(visible=False)
        download_file = gr.File(
            label="📁 DownloadDevelopment Plan文档", 
            visible=False,
            interactive=False,
            show_label=True
        )
        
        # 添加Copy和Download按钮
        with gr.Row():
            copy_plan_btn = gr.Button(
                "📋 CopyDevelopment Plan",
                variant="secondary",
                size="sm",
                elem_classes="copy-btn"
            )
            copy_prompts_btn = gr.Button(
                "🤖 Copy编程提示词",
                variant="secondary", 
                size="sm",
                elem_classes="copy-btn"
            )
            
        # Download提示信息
        download_info = gr.HTML(
            value="",
            visible=False,
            elem_id="download_info"
        )
            
        # 使用提示
        gr.HTML("""
        <div style="padding: 10px; background: #e3f2fd; border-radius: 8px; text-align: center; color: #1565c0;" id="usage_tips">
            💡 Click上方按钮Copycontent，或DownloadSave为文件
        </div>
        """)
        
    # 示例区域 - 展示多样化的Apply场景
    gr.Markdown("## 🎯 Example Use Cases", elem_id="quick_start_container")
    gr.Examples(
        examples=[
            [
                "AI-powered customer service system: Multi-turn dialogue, sentiment analysis, knowledge base search, automatic ticket generation, and intelligent responses",
                "https://docs.python.org/3/library/asyncio.html"
            ],
            [
                "Modern web application with React and TypeScript: User authentication, real-time data sync, responsive design, PWA support, and offline capabilities",
                "https://react.dev/learn"
            ],
            [
                "Task management platform: Team collaboration, project tracking, deadline reminders, file sharing, and progress visualization",
                ""
            ],
            [
                "E-commerce marketplace: Product catalog, shopping cart, payment integration, order management, and customer reviews",
                "https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps"
            ],
            [
                "Social media analytics dashboard: Data visualization, sentiment analysis, trend tracking, engagement metrics, and automated reporting",
                ""
            ],
            [
                "Educational learning management system: Course creation, student enrollment, progress tracking, assessments, and certificates",
                "https://www.w3.org/WAI/WCAG21/quickref/"
            ]
        ],
        inputs=[idea_input, reference_url_input],
        label="🎯 Popular Examples - Try These Ideas",
        examples_per_page=6,
        elem_id="enhanced_examples"
    )
    
    # Usage Instructions - 功能介绍
    gr.HTML("""
    <div class="prompts-section" id="ai_helper_instructions">
        <h3>🚀 How It Works - Intelligent Development Planning</h3>
        
        <!-- 核心功能 -->
        <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #e8f5e8 0%, #f0fff4 100%); border-radius: 15px; border: 3px solid #28a745; margin: 15px 0;">
            <span style="font-size: 36px;">🧠</span><br>
            <strong style="font-size: 18px; color: #155724;">AI-Powered Analysis</strong><br>
            <small style="color: #155724; font-weight: 600; font-size: 13px;">
                � Intelligent planning • ⚡ Fast generation • ✅ Professional output
            </small>
        </div>
        
        <!-- 可视化支持 -->
        <div style="text-align: center; padding: 15px; background: linear-gradient(135deg, #e3f2fd 0%, #f0f8ff 100%); border-radius: 12px; border: 2px solid #2196f3; margin: 15px 0;">
            <span style="font-size: 30px;">�</span><br>
            <strong style="font-size: 16px; color: #1976d2;">Visual Diagrams</strong><br>
            <small style="color: #1976d2; font-weight: 600; font-size: 12px;">
                🎨 Architecture • � Flowcharts • 📅 Gantt charts
            </small>
        </div>
        
        <!-- processing流程说明 -->
        <div style="background: linear-gradient(135deg, #fff3e0 0%, #fffaf0 100%); padding: 15px; border-radius: 10px; margin: 15px 0; border-left: 4px solid #ff9800;">
            <strong style="color: #f57c00;">⚡ Processing Pipeline:</strong>
            <ol style="margin: 10px 0; padding-left: 20px; font-size: 14px;">
                <li><strong>Input Analysis</strong> → Understanding your requirements</li>
                <li><strong>Prompt Optimization</strong> → Enhancing description quality</li>
                <li><strong>Knowledge Retrieval</strong> → Fetching relevant information</li>
                <li><strong>AI Generation</strong> → Creating comprehensive plan</li>
                <li><strong>Quality Validation</strong> → Ensuring professional output</li>
            </ol>
        </div>
        
        <!-- 核心优势 -->
        <div style="background: #f8f9fa; padding: 15px; border-radius: 10px; margin: 15px 0; border-left: 4px solid #6c757d;">
            <strong style="color: #495057;">🎯 Key Advantages:</strong>
            <ul style="margin: 10px 0; padding-left: 20px; font-size: 14px;">
                <li><strong>Speed</strong> → 60-180 seconds generation time</li>
                <li><strong>Quality</strong> → Professional industry-standard output</li>
                <li><strong>Flexibility</strong> → Multiple export formats</li>
                <li><strong>Integration</strong> → Works with all AI coding assistants</li>
            </ul>
        </div>
        
        <h4>🤖 Perfect for AI Coding Assistants</h4>
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 6px; margin: 12px 0;">
            <div style="text-align: center; padding: 8px; background: #e3f2fd; border-radius: 6px; border: 1px solid #2196f3; box-shadow: 0 2px 4px rgba(33,150,243,0.2);">
                <span style="font-size: 16px;">🔵</span> <strong style="font-size: 12px;">Claude</strong>
            </div>
            <div style="text-align: center; padding: 8px; background: #e8f5e8; border-radius: 6px; border: 1px solid #4caf50; box-shadow: 0 2px 4px rgba(76,175,80,0.2);">
                <span style="font-size: 16px;">🟢</span> <strong style="font-size: 12px;">GitHub Copilot</strong>
            </div>
            <div style="text-align: center; padding: 8px; background: #fff3e0; border-radius: 6px; border: 1px solid #ff9800; box-shadow: 0 2px 4px rgba(255,152,0,0.2);">
                <span style="font-size: 16px;">🟡</span> <strong style="font-size: 12px;">ChatGPT</strong>
            </div>
            <div style="text-align: center; padding: 8px; background: #fce4ec; border-radius: 6px; border: 1px solid #e91e63; box-shadow: 0 2px 4px rgba(233,30,99,0.2);">
                <span style="font-size: 16px;">🔴</span> <strong style="font-size: 12px;">Cursor</strong>
            </div>
        </div>
        <p style="text-align: center; color: #28a745; font-weight: 700; font-size: 15px; background: #d4edda; padding: 8px; border-radius: 8px; border: 1px solid #c3e6cb;">
            <em>🎉 Professional Development Plans + Ready-to-Use AI Prompts</em>
        </p>
    </div>
    """)
    
    # 绑定事件
    def show_download_info():
        return gr.update(
            value="""
            <div style="padding: 10px; background: #e8f5e8; border-radius: 8px; text-align: center; margin: 10px 0; color: #2d5a2d;" id="download_success_info">
                ✅ <strong style="color: #1a5a1a;">文档已generate！</strong> 您现在可以：
                <br>• 📋 <span style="color: #2d5a2d;">CopyDevelopment Plan或编程提示词</span>
                <br>• 📁 <span style="color: #2d5a2d;">Click下方Download按钮Save文档</span>
                <br>• 🔄 <span style="color: #2d5a2d;">调整创意重新generate</span>
            </div>
            """,
            visible=True
        )
    
    # 优化按钮事件
    optimize_btn.click(
        fn=optimize_user_idea,
        inputs=[idea_input],
        outputs=[idea_input, optimization_result]
    ).then(
        fn=lambda: gr.update(visible=True),
        outputs=[optimization_result]
    )
    
    # Reset按钮事件
    reset_btn.click(
        fn=lambda: ("", gr.update(visible=False)),
        outputs=[idea_input, optimization_result]
    )
    
    # processing过程说明按钮事件
    show_explanation_btn.click(
        fn=show_explanation,
        outputs=[plan_output, process_explanation, hide_explanation_btn]
    )
    
    hide_explanation_btn.click(
        fn=hide_explanation,
        outputs=[plan_output, process_explanation, hide_explanation_btn]
    )
    
    generate_btn.click(
        fn=generate_development_plan,
        inputs=[idea_input, reference_url_input],
        outputs=[plan_output, prompts_for_copy, download_file],
        api_name="generate_plan"
    ).then(
        fn=lambda: gr.update(visible=True),
        outputs=[download_file]
    ).then(
        fn=lambda: gr.update(visible=True),
        outputs=[show_explanation_btn]
    ).then(
        fn=show_download_info,
        outputs=[download_info]
    )
    
    # Copy按钮事件（使用JavaScript实现）
    copy_plan_btn.click(
        fn=None,
        inputs=[plan_output],
        outputs=[],
        js="""(plan_content) => {
            if (navigator.clipboard && window.isSecureContext) {
                navigator.clipboard.writeText(plan_content).then(() => {
                    alert('✅ Development Plan已Copy到剪贴板！');
                }).catch(err => {
                    console.error('Copyfailed:', err);
                    alert('❌ Copyfailed，请手动选择文本Copy');
                });
            } else {
                // 降级方案
                const textArea = document.createElement('textarea');
                textArea.value = plan_content;
                document.body.appendChild(textArea);
                textArea.select();
                try {
                    document.execCommand('copy');
                    alert('✅ Development Plan已Copy到剪贴板！');
                } catch (err) {
                    alert('❌ Copyfailed，请手动选择文本Copy');
                }
                document.body.removeChild(textArea);
            }
        }"""
    )
    
    copy_prompts_btn.click(
        fn=None,
        inputs=[prompts_for_copy],
        outputs=[],
        js="""(prompts_content) => {
            if (navigator.clipboard && window.isSecureContext) {
                navigator.clipboard.writeText(prompts_content).then(() => {
                    alert('✅ 编程提示词已Copy到剪贴板！');
                }).catch(err => {
                    console.error('Copyfailed:', err);
                    alert('❌ Copyfailed，请手动选择文本Copy');
                });
            } else {
                // 降级方案
                const textArea = document.createElement('textarea');
                textArea.value = prompts_content;
                document.body.appendChild(textArea);
                textArea.select();
                try {
                    document.execCommand('copy');
                    alert('✅ 编程提示词已Copy到剪贴板！');
                } catch (err) {
                    alert('❌ Copyfailed，请手动选择文本Copy');
                }
                document.body.removeChild(textArea);
            }
        }"""
    )

# 启动Apply - 开源版本
if __name__ == "__main__":
    logger.info("🚀 Starting VibeDoc Application")
    logger.info(f"🌍 Environment: {config.environment}")
    logger.info(f"� Version: 2.0.0 - Open Source Edition")
    logger.info(f"�🔧 External Services: {[s.name for s in config.get_enabled_mcp_services()]}")
    
    # 尝试多个端口以避免冲突
    ports_to_try = [7860, 7861, 7862, 7863, 7864]
    launched = False
    
    for port in ports_to_try:
        try:
            logger.info(f"🌐 Attempting to launch on port: {port}")
            demo.launch(
                server_name="0.0.0.0",
                server_port=port,
                share=False,  # 开源版本默认不分享
                show_error=config.debug,
                prevent_thread_lock=False
            )
            launched = True
            logger.info(f"✅ Application successfully launched on port {port}")
            logger.info(f"🔗 Local URL: http://localhost:{port}")
            logger.info(f"🔗 Network URL: http://0.0.0.0:{port}")
            break
        except Exception as e:
            logger.warning(f"⚠️ Port {port} failed: {str(e)}")
            continue
    
    if not launched:
        logger.error("❌ Failed to launch on all ports. Please check network configuration.")
    