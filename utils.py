import re
import logging
from datetime import datetime
from urllib.parse import urlparse
from typing import Tuple, List

logger = logging.getLogger(__name__)

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

def enhance_mermaid_blocks(content: str) -> str:
    """Simplify Mermaid code block handling to avoid rendering conflicts"""
    # Find all Mermaid code blocks and return directly without extra wrappers
    # Because wrappers may cause rendering issues
    mermaid_pattern = r'```mermaid\n(.*?)\n```'
    
    def clean_mermaid_block(match):
        mermaid_content = match.group(1)
        # Directly return cleaned Mermaid block
        return f'```mermaid\n{mermaid_content}\n```'
    
    content = re.sub(mermaid_pattern, clean_mermaid_block, content, flags=re.DOTALL)
    
    return content

def fix_mermaid_syntax(content: str) -> str:
    """Fix syntax errors in Mermaid charts and optimize rendering"""
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

def enhance_real_links(content: str) -> str:
    """Verify and enhance the usability of real links"""
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

def validate_and_clean_links(content: str) -> str:
    """Validate and clean fake links to enhance link quality"""
    # Detect and remove fake link patterns
    fake_link_patterns = [
        # Markdown link formats
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

def fix_date_consistency(content: str) -> str:
    """Fix date consistency issues"""
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

def generate_enhanced_reference_info(url: str, source_type: str, error_msg: str = None) -> str:
    """Generate enhanced reference information to provide useful context when MCP service is unavailable"""
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
        content_hints.append("👨‍💻 Developer Community")
    elif "hackernoon.com" in domain:
        content_hints.append("📝 Tech Article")
    elif "medium.com" in domain:
        content_hints.append("📝 Tech Blog")
    elif "stackoverflow.com" in domain:
        content_hints.append("❓ Tech Q&A")
    elif "blog" in domain:
        content_hints.append("📖 Technical Blog")
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
    
    reference_info = f\"\"\"
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
\"\"\"
    
    if error_msg and not error_msg.startswith("❌"):
        reference_info += f"\\n**⚠️ Service status：** {error_msg}\\n"
    
    return reference_info

def fix_links_for_new_window(content: str) -> str:
    """Fix all links to open in new window"""
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
            return full_tag.replace('>', ' target="_blank" rel="noopener noreferrer">')
        return full_tag
    
    content = re.sub(r'<a [^>]*href=[^>]*>', add_target_blank, content)
    return content

def enhance_markdown_structure(content: str) -> str:
    """Enhance Markdown structure, add visual highlights and hierarchy"""
    lines = content.split('\\n')
    enhanced_lines = []
    
    for line in lines:
        stripped = line.strip()
        
        # Enhance level 1 headings
        if stripped and not stripped.startswith('#') and len(stripped) < 50 and '：' not in stripped and '.' not in stripped[:5]:
            if any(keyword in stripped for keyword in ['Product Overview', 'Technical Solution', 'Development Plan', 'Deployment Plan', 'Growth Strategy', 'AI', '编程助手', '提示词']):
                enhanced_lines.append(f"\\n## 🎯 {stripped}\\n")
                continue
        
        # Enhance level 2 headings
        if stripped and '.' in stripped[:5] and len(stripped) < 100:
            if stripped[0].isdigit():
                enhanced_lines.append(f"\\n### 📋 {stripped}\\n")
                continue
                
        # Enhance feature lists
        if stripped.startswith('主要功能') or stripped.startswith('目标用户'):
            enhanced_lines.append(f"\\n#### 🔹 {stripped}\\n")
            continue
            
        # Enhance tech stack sections
        if stripped in ['Frontend', 'Backend', 'AI 模型', '工具和库']:
            enhanced_lines.append(f"\\n#### 🛠️ {stripped}\\n")
            continue
            
        # Enhance phase titles
        if '阶段' in stripped and '：' in stripped:
             enhanced_lines.append(f"\\n#### 🚀 {stripped}\\n")
             continue
            
        # Enhance task list
        if stripped.startswith('任务：'):
            enhanced_lines.append(f"\\n**📝 {stripped}**\\n")
            continue
            
        enhanced_lines.append(line)
    
    return '\\n'.join(enhanced_lines)

def clean_prompts_for_copy(prompts_content: str) -> str:
    """Clean prompts content, remove HTML tags, optimize copy experience"""
    import re
    clean_content = re.sub(r'<[^>]+>', '', prompts_content)
    lines = clean_content.split('\\n')
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped:
            cleaned_lines.append(line)
        elif cleaned_lines and cleaned_lines[-1].strip():
            cleaned_lines.append('')
    return '\\n'.join(cleaned_lines)

def extract_prompts_section(content: str) -> str:
    """Extract the AI programming prompts section from the full content"""
    parts = content.split('# AI编程助手提示词')
    if len(parts) >= 2:
        return clean_prompts_for_copy('# AI编程助手提示词' + parts[1])
    
    lines = content.split('\\n')
    prompts_section = []
    in_prompts_section = False
    for line in lines:
        if any(keyword in line for keyword in ['编程提示词', '编程助手', 'Prompt', 'AI助手']):
            in_prompts_section = True
        if in_prompts_section:
            prompts_section.append(line)
            
    return '\\n'.join(prompts_section) if prompts_section else "Programming prompts section not found"

def enhance_prompts_display(prompts_content: str) -> str:
    """Simplify AI programming prompts display"""
    lines = prompts_content.split('\\n')
    enhanced_lines = []
    in_code_block = False
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('# AI编程助手提示词'):
            enhanced_lines.extend(['', '<div class="prompts-highlight">', '', '# 🤖 AI Programming Assistant Prompts', '', '> 💡 **Instructions**: The following prompts are custom generated based on your project requirements.', ''])
            continue
        if stripped.startswith('## ') and not in_code_block:
            title = stripped[3:].strip()
            enhanced_lines.extend(['', f'### 🎯 {title}', ''])
            continue
        if stripped.startswith('```'):
            in_code_block = not in_code_block
            enhanced_lines.append(line)
            if not in_code_block: enhanced_lines.append('')
            continue
        enhanced_lines.append(line)
    
    enhanced_lines.extend(['', '</div>'])
    return '\\n'.join(enhanced_lines)

def format_response(content: str) -> str:
    """Format AI response"""
    content = fix_links_for_new_window(content)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    parts = content.split('# AI编程助手提示词')
    
    if len(parts) >= 2:
        plan_content = parts[0].strip()
        prompts_content = '# AI编程助手提示词' + parts[1]
        enhanced_prompts = enhance_prompts_display(prompts_content)
        formatted_content = f\"\"\"
<div class="plan-header">
# 🚀 AI-generated Development Plan
<div class="meta-info">
**⏰ Generated Time:** {timestamp}  
**🤖 AI Model:** Qwen2.5-72B-Instruct  
**💡 Intelligently generated based on user creativity**  
</div>
</div>
---
{enhance_markdown_structure(plan_content)}
---
{enhanced_prompts}
\"\"\"
    else:
        formatted_content = f\"\"\"
<div class="plan-header">
# 🚀 AI-generated Development Plan
<div class="meta-info">
**⏰ Generated Time:** {timestamp}  
**🤖 AI Model:** Qwen2.5-72B-Instruct  
**💡 Intelligently generated based on user creativity**  
</div>
</div>
---
{enhance_markdown_structure(content)}
\"\"\"
    return formatted_content

