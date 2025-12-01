"""
AI Explainability Manager
Provides transparency for processing chains and explainability features combined with SOP
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class ProcessingStage(Enum):
    """Processing Stage Enum"""
    INPUT_VALIDATION = "input_validation"
    PROMPT_OPTIMIZATION = "prompt_optimization"
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"
    AI_GENERATION = "ai_generation"
    QUALITY_ASSESSMENT = "quality_assessment"
    CONTENT_FORMATTING = "content_formatting"
    RESULT_VALIDATION = "result_validation"

@dataclass
class ProcessingStep:
    """Processing Step Data Structure"""
    stage: ProcessingStage
    title: str
    description: str
    timestamp: str
    duration: float
    success: bool
    details: Dict[str, Any]
    quality_score: Optional[float] = None
    evidence: Optional[str] = None

class ExplanationManager:
    """AI Explainability Manager"""
    
    def __init__(self):
        self.processing_steps: List[ProcessingStep] = []
        self.sop_guidelines = self._load_sop_guidelines()
        self.quality_metrics = {}
        
    def start_processing(self):
        """Start processing"""
        self.processing_steps.clear()
        self.quality_metrics.clear()
        logger.info("🔄 Starting processing chain tracking")
    
    def add_processing_step(self, 
                          stage: ProcessingStage,
                          title: str,
                          description: str,
                          success: bool,
                          details: Dict[str, Any],
                          duration: float = 0.0,
                          quality_score: Optional[float] = None,
                          evidence: Optional[str] = None):
        """Add a processing step"""
        step = ProcessingStep(
            stage=stage,
            title=title,
            description=description,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            duration=duration,
            success=success,
            details=details,
            quality_score=quality_score,
            evidence=evidence
        )
        
        self.processing_steps.append(step)
        logger.info(f"📝 Recorded processing step: {title} - {'✅' if success else '❌'}")
    
    def get_processing_explanation(self) -> str:
        """Get detailed explanation of the processing"""
        if not self.processing_steps:
            return "No processing records yet"
        
        explanation = self._generate_explanation_header()
        explanation += self._generate_sop_compliance_report()
        explanation += self._generate_processing_steps_report()
        explanation += self._generate_quality_metrics_report()
        explanation += self._generate_evidence_summary()
        
        return explanation
    
    def _generate_explanation_header(self) -> str:
        """Generate explanation header"""
        total_steps = len(self.processing_steps)
        successful_steps = sum(1 for step in self.processing_steps if step.success)
        success_rate = (successful_steps / total_steps * 100) if total_steps > 0 else 0
        
        return f"""
# 🔍 Detailed Explanation of AI Generation Process

## 📊 Processing Overview
- **Total Processing Steps**: {total_steps}
- **Successful Steps**: {successful_steps}
- **Success Rate**: {success_rate:.1f}%
- **Processing Time**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

"""
    
    def _generate_sop_compliance_report(self) -> str:
        """Generate SOP compliance report"""
        return f"""
## 📋 SOP (Standard Operating Procedure) Compliance Report

### 🎯 Quality Assurance Standards
{self._format_sop_guidelines()}

### ✅ Compliance Check
- **Input Validation**: {'✅ Passed' if self._check_sop_compliance('input_validation') else '❌ Failed'}
- **Knowledge Retrieval**: {'✅ Passed' if self._check_sop_compliance('knowledge_retrieval') else '❌ Failed'}
- **AI Generation**: {'✅ Passed' if self._check_sop_compliance('ai_generation') else '❌ Failed'}
- **Quality Assessment**: {'✅ Passed' if self._check_sop_compliance('quality_assessment') else '❌ Failed'}
- **Content Formatting**: {'✅ Passed' if self._check_sop_compliance('content_formatting') else '❌ Failed'}

---

"""
    
    def _generate_processing_steps_report(self) -> str:
        """Generate processing steps report"""
        report = "## 🔄 Detailed Processing Steps\n\n"
        
        for i, step in enumerate(self.processing_steps, 1):
            status_icon = "✅" if step.success else "❌"
            quality_info = f" (Quality Score: {step.quality_score:.1f})" if step.quality_score else ""
            
            report += f"""
### Step {i}: {step.title} {status_icon}

- **Stage**: {self._get_stage_name(step.stage)}
- **Time**: {step.timestamp}
- **Duration**: {step.duration:.2f} seconds{quality_info}
- **Description**: {step.description}

**Details**:
{self._format_step_details(step.details)}

"""
            
            if step.evidence:
                report += f"**Evidence**: {step.evidence}\n\n"
        

        return report + "---\n\n"
    
    def _generate_quality_metrics_report(self) -> str:
        """Generate quality metrics report"""
        if not self.quality_metrics:
            return ""
        
        report = "## 📈 Quality Metrics Details\n\n"
        
        for metric_name, metric_value in self.quality_metrics.items():
            report += f"- **{metric_name}**: {metric_value}\n"
        
        return report + "\n---\n\n"
    
    def _generate_evidence_summary(self) -> str:
        """Generate evidence summary"""
        evidence_steps = [step for step in self.processing_steps if step.evidence]
        
        if not evidence_steps:
            return ""
        
        report = "## 🧾 Evidence Summary\n\n"
        
        for i, step in enumerate(evidence_steps, 1):
            report += f"**{i}. {step.title}**\n{step.evidence}\n\n"
        
        return report
    
    def _load_sop_guidelines(self) -> Dict[str, Any]:
        """Load SOP guidelines"""
        return {
            "input_validation": {
                "title": "Input Validation Standards",
                "requirements": [
                    "User input length >= 10 characters",
                    "Input content includes product description",
                    "No malicious content or sensitive information"
                ]
            },
            "knowledge_retrieval": {
                "title": "External Knowledge Acquisition",
                "requirements": [
                    "MCP service connection status check",
                    "Reference link validity verification",
                    "Knowledge content relevance assessment"
                ]
            },
            "ai_generation": {
                "title": "AI Content Generation",
                "requirements": [
                    "Use professional system prompts",
                    "Generated content structure is complete",
                    "Includes necessary technical details"
                ]
            },
            "quality_assessment": {
                "title": "Quality Assessment Standards",
                "requirements": [
                    "Content completeness check",
                    "Mermaid chart syntax validation",
                    "Link validity check",
                    "Date accuracy verification"
                ]
            },
            "content_formatting": {
                "title": "Content Formatting",
                "requirements": [
                    "Markdown format specification",
                    "Add timestamps and metadata",
                    "Enhance prompt display effects"
                ]
            }
        }
    
    def _format_sop_guidelines(self) -> str:
        """Format SOP guidelines"""
        formatted = ""
        for key, guideline in self.sop_guidelines.items():
            formatted += f"**{guideline['title']}**:\n"
            for requirement in guideline['requirements']:
                formatted += f"- {requirement}\n"
            formatted += "\n"
        return formatted
    
    def _check_sop_compliance(self, stage_name: str) -> bool:
        """Check SOP compliance"""
        relevant_steps = [step for step in self.processing_steps 
                         if step.stage.value == stage_name]
        return len(relevant_steps) > 0 and all(step.success for step in relevant_steps)
    
    def _get_stage_name(self, stage: ProcessingStage) -> str:
        """Get stage name"""
        stage_names = {
            ProcessingStage.INPUT_VALIDATION: "Input Validation",
            ProcessingStage.PROMPT_OPTIMIZATION: "Prompt Optimization",
            ProcessingStage.KNOWLEDGE_RETRIEVAL: "Knowledge Retrieval",
            ProcessingStage.AI_GENERATION: "AI Generation",
            ProcessingStage.QUALITY_ASSESSMENT: "Quality Assessment",
            ProcessingStage.CONTENT_FORMATTING: "Content Formatting",
            ProcessingStage.RESULT_VALIDATION: "Result Validation"
        }
        return stage_names.get(stage, stage.value)
    
    def _format_step_details(self, details: Dict[str, Any]) -> str:
        """Format step details"""
        formatted = ""
        for key, value in details.items():
            if isinstance(value, dict):
                formatted += f"  - **{key}**: {self._format_nested_dict(value)}\n"
            elif isinstance(value, list):
                formatted += f"  - **{key}**: {', '.join(str(item) for item in value)}\n"
            else:
                formatted += f"  - **{key}**: {value}\n"
        return formatted
    
    def _format_nested_dict(self, nested_dict: Dict[str, Any]) -> str:
        """Format nested dictionary"""
        items = []
        for key, value in nested_dict.items():
            items.append(f"{key}={value}")
        return f"{{{', '.join(items)}}}"
    
    def update_quality_metrics(self, metrics: Dict[str, Any]):
        """Update quality metrics"""
        self.quality_metrics.update(metrics)
        
    def get_trust_score(self) -> float:
        """Calculate trust score"""
        if not self.processing_steps:
            return 0.0
        
        # Calculate trust score based on success rate and quality score
        success_rate = sum(1 for step in self.processing_steps if step.success) / len(self.processing_steps)
        
        quality_scores = [step.quality_score for step in self.processing_steps if step.quality_score]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.5
        
        # Trust score = success rate * 0.6 + average quality score * 0.4
        trust_score = success_rate * 0.6 + (avg_quality / 100) * 0.4
        
        return round(trust_score * 100, 1)

# Global explanation manager instance
explanation_manager = ExplanationManager()