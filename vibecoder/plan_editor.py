"""
User Plan Editor
Allows users to edit and modify AI-generated development plans in segments
"""

import re
import json
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class EditableSection:
    """Editable plan section"""
    section_id: str
    title: str
    content: str
    section_type: str  # 'heading', 'paragraph', 'list', 'code', 'table'
    level: int  # 1-6 for headings, 0 for others
    start_line: int
    end_line: int
    is_editable: bool = True

class PlanEditor:
    """Development Plan Editor"""
    
    def __init__(self):
        self.sections: List[EditableSection] = []
        self.original_content = ""
        self.modified_content = ""
        self.edit_history: List[Dict] = []
    
    def parse_plan_content(self, content: str) -> List[EditableSection]:
        """Parse development plan content into editable sections"""
        self.original_content = content
        self.sections = []
        
        lines = content.split('\n')
        current_section = None
        section_counter = 0
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Detect headings (# ## ### etc.)
            if line.startswith('#') and not line.startswith('```'):
                level = len(line) - len(line.lstrip('#'))
                if level <= 6:  # Valid heading level
                    title = line.lstrip('#').strip()
                    
                    # Save previous section
                    if current_section and current_section.content.strip():
                        self.sections.append(current_section)
                    
                    # Create new heading section
                    section_counter += 1
                    current_section = EditableSection(
                        section_id=f"section_{section_counter}",
                        title=title,
                        content=line,
                        section_type='heading',
                        level=level,
                        start_line=i,
                        end_line=i,
                        is_editable=self._is_section_editable(title)
                    )
                    i += 1
                    continue
            
            # Detect code blocks
            if line.startswith('```'):
                if current_section and current_section.content.strip():
                    self.sections.append(current_section)
                
                # Collect entire code block
                code_content = [line]
                i += 1
                start_line = i - 1
                
                while i < len(lines) and not lines[i].strip().startswith('```'):
                    code_content.append(lines[i])
                    i += 1
                
                if i < len(lines):  # Add closing ```
                    code_content.append(lines[i])
                    i += 1
                
                section_counter += 1
                code_section = EditableSection(
                    section_id=f"code_{section_counter}",
                    title="Code Block",
                    content='\n'.join(code_content),
                    section_type='code',
                    level=0,
                    start_line=start_line,
                    end_line=i - 1,
                    is_editable=True
                )
                self.sections.append(code_section)
                current_section = None
                continue
            
            # Detect tables
            if '|' in line and line.count('|') >= 2:
                if current_section and current_section.content.strip():
                    self.sections.append(current_section)
                
                # Collect entire table
                table_content = [line]
                start_line = i
                i += 1
                
                while i < len(lines) and '|' in lines[i] and lines[i].count('|') >= 2:
                    table_content.append(lines[i])
                    i += 1
                
                section_counter += 1
                table_section = EditableSection(
                    section_id=f"table_{section_counter}",
                    title="Table",
                    content='\n'.join(table_content),
                    section_type='table',
                    level=0,
                    start_line=start_line,
                    end_line=i - 1,
                    is_editable=True
                )
                self.sections.append(table_section)
                current_section = None
                continue
            
            # Detect lists
            if line.startswith(('-', '*', '+')) or re.match(r'^\d+\.', line):
                if current_section and current_section.section_type != 'list':
                    if current_section.content.strip():
                        self.sections.append(current_section)
                    
                    section_counter += 1
                    current_section = EditableSection(
                        section_id=f"list_{section_counter}",
                        title="List",
                        content=line,
                        section_type='list',
                        level=0,
                        start_line=i,
                        end_line=i,
                        is_editable=True
                    )
                elif current_section and current_section.section_type == 'list':
                    current_section.content += '\n' + line
                    current_section.end_line = i
                else:
                    section_counter += 1
                    current_section = EditableSection(
                        section_id=f"list_{section_counter}",
                        title="List",
                        content=line,
                        section_type='list',
                        level=0,
                        start_line=i,
                        end_line=i,
                        is_editable=True
                    )
                i += 1
                continue
            
            # Normal paragraph
            if line:
                if current_section and current_section.section_type == 'paragraph':
                    current_section.content += '\n' + line
                    current_section.end_line = i
                elif current_section and current_section.section_type == 'heading':
                    # The first paragraph after the heading
                    section_counter += 1
                    new_section = EditableSection(
                        section_id=f"paragraph_{section_counter}",
                        title="Paragraph",
                        content=line,
                        section_type='paragraph',
                        level=0,
                        start_line=i,
                        end_line=i,
                        is_editable=True
                    )
                    self.sections.append(current_section)
                    current_section = new_section
                else:
                    if current_section and current_section.content.strip():
                        self.sections.append(current_section)
                    
                    section_counter += 1
                    current_section = EditableSection(
                        section_id=f"paragraph_{section_counter}",
                        title="Paragraph",
                        content=line,
                        section_type='paragraph',
                        level=0,
                        start_line=i,
                        end_line=i,
                        is_editable=True
                    )
            
            i += 1
        
        # Save the last paragraph
        if current_section and current_section.content.strip():
            self.sections.append(current_section)
        
        logger.info(f"Parsing completed, found {len(self.sections)} editable paragraphs in total")
        return self.sections
    
    def _is_section_editable(self, title: str) -> bool:
        """Determine if a paragraph is editable"""
        non_editable_patterns = [
            r'Generation time',
            r'AI model',
            r'Based on user creativity',
            r'Agent application',
            r'meta-info'
        ]
        
        title_lower = title.lower()
        return not any(re.search(pattern, title_lower) for pattern in non_editable_patterns)
    
    def get_editable_sections(self) -> List[Dict]:
        """Get the list of editable paragraphs (for frontend display)"""
        editable_sections = []
        
        for section in self.sections:
            if section.is_editable:
                editable_sections.append({
                    'id': section.section_id,
                    'title': section.title,
                    'content': section.content,
                    'type': section.section_type,
                    'level': section.level,
                    'preview': self._get_section_preview(section.content)
                })
        
        return editable_sections
    
    def _get_section_preview(self, content: str, max_length: int = 100) -> str:
        """Get paragraph preview"""
        # Remove Markdown formatting symbols
        preview = re.sub(r'[#*`|]', '', content)
        preview = re.sub(r'\n+', ' ', preview).strip()
        
        if len(preview) > max_length:
            preview = preview[:max_length] + '...'
        
        return preview
    
    def update_section(self, section_id: str, new_content: str, user_comment: str = "") -> bool:
        """Update the content of the specified paragraph"""
        try:
            # Find the target paragraph
            target_section = None
            for section in self.sections:
                if section.section_id == section_id:
                    target_section = section
                    break
            
            if not target_section:
                logger.error(f"Paragraph {section_id} not found")
                return False
            
            if not target_section.is_editable:
                logger.error(f"Paragraph {section_id} is not editable")
                return False
            
            # Record edit history
            self.edit_history.append({
                'timestamp': datetime.now().isoformat(),
                'section_id': section_id,
                'old_content': target_section.content,
                'new_content': new_content,
                'user_comment': user_comment
            })
            
            # Update content
            target_section.content = new_content
            
            # Rebuild the full content
            self._rebuild_content()
            
            logger.info(f"Successfully updated paragraph {section_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update paragraph: {str(e)}")
            return False
    
    def _rebuild_content(self):
        """Rebuild the full content"""
        try:
            lines = self.original_content.split('\n')
            
            # Sort sections by line number
            sorted_sections = sorted(self.sections, key=lambda x: x.start_line)
            
            # Rebuild content
            new_lines = []
            current_line = 0
            
            for section in sorted_sections:
                # Add blank lines before the section
                while current_line < section.start_line:
                    new_lines.append(lines[current_line])
                    current_line += 1
                
                # Add updated section content
                new_lines.extend(section.content.split('\n'))
                
                # Skip original section lines
                current_line = section.end_line + 1
            
            # Add remaining lines
            while current_line < len(lines):
                new_lines.append(lines[current_line])
                current_line += 1
            
            self.modified_content = '\n'.join(new_lines)
            
        except Exception as e:
            logger.error(f"Failed to rebuild content: {str(e)}")
            self.modified_content = self.original_content
    
    def get_modified_content(self) -> str:
        """Get the modified full content"""
        return self.modified_content if self.modified_content else self.original_content
    
    def get_edit_history(self) -> List[Dict]:
        """Get edit history"""
        return self.edit_history
    
    def get_edit_summary(self) -> Dict:
        """Get edit summary"""
        return {
            'total_sections': len(self.sections),
            'editable_sections': len([s for s in self.sections if s.is_editable]),
            'edited_sections': len(self.edit_history),
            'last_edit_time': self.edit_history[-1]['timestamp'] if self.edit_history else None
        }
    
    def reset_to_original(self):
        """Reset to original content"""
        self.modified_content = self.original_content
        self.edit_history = []
        # Re-parse sections
        self.parse_plan_content(self.original_content)
        logger.info("Reset to original content")
    
    def export_edited_content(self, format_type: str = 'markdown') -> str:
        """Export edited content"""
        content = self.get_modified_content()
        
        if format_type == 'markdown':
            return content
        elif format_type == 'html':
            # Simple Markdown to HTML conversion
            import markdown
            return markdown.markdown(content)
        else:
            return content

# Global editor instance
plan_editor = PlanEditor()