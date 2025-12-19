"""
Prompt Optimization Module.

This module provides functionality to optimize user ideas using Chain-of-Thought (CoT)
reasoning. It transforms simple one-liners into detailed, professional product descriptions
ready for development planning.
"""

import requests
import json
import logging
from typing import Tuple, Dict, Any, Optional
from .config import config

logger = logging.getLogger(__name__)

class PromptOptimizer:
    """User Input Prompt Optimizer"""
    
    def __init__(self):
        self.api_key = config.ai_model.api_key
        self.api_url = config.ai_model.api_url
        self.model_name = config.ai_model.model_name
        
    def optimize_user_input(self, user_idea: str) -> Tuple[bool, str, str]:
        """
        Optimize user input creative description
        
        Args:
            user_idea: Original user input
            
        Returns:
            Tuple[bool, str, str]: (success status, optimized description, optimization suggestions)
        """
        if not self.api_key:
            return False, user_idea, "API key not configured, unable to optimize description"
        
        if not user_idea or len(user_idea.strip()) < 5:
            return False, user_idea, "Input content too short, unable to optimize"
        
        try:
            # Build optimization prompt
            optimization_prompt = self._build_optimization_prompt(user_idea)
            
            # Call AI for optimization
            response = self._call_ai_service(optimization_prompt)
            
            if response['success']:
                result = self._parse_optimization_result(response['data'])
                return True, result['optimized_idea'], result['suggestions']
            else:
                logger.error(f"AI optimization failed: {response['error']}")
                return False, user_idea, f"Optimization failed: {response['error']}"
                
        except Exception as e:
            logger.error(f"Prompt optimization exception: {e}")
            return False, user_idea, f"Error during optimization: {str(e)}"
    
    def _build_optimization_prompt(self, user_idea: str) -> str:
        """Build optimization prompt"""
        return f"""You are an expert Product Manager and System Architect, modeled after world-class tech leaders. Your goal is to take a simple user idea and expand it into a comprehensive, professional, and actionable product specification.

Original User Idea:
{user_idea}

Please think step-by-step to optimize this idea:
1.  **Analyze the Intent**: What is the core problem the user is trying to solve? Who is it for?
2.  **Expand the Scope**: What minimal features are needed for an MVP? What "wow" features could be added?
3.  **Technical Feasibility**: What is the high-level tech stack? (e.g., Mobile App vs Web App, AI integration).
4.  **Refine the Pitch**: Rephrase the idea to be more professional and compelling.

Output the result in the following JSON format:
{{
    "optimized_idea": "A detailed, professional description of the product (approx. 200-400 words). Include Core Features, Target Audience, and Key Differentiators.",
    "key_improvements": [
        "Added <Feature X> to solve <Problem Y>",
        "Clarified target audience as <Audience Z>",
        "suggested <Tech A> for better scalability"
    ],
    "suggestions": "Brief strategic advice for the user (e.g., 'Focus on mobile-first', 'Consider using existing APIs for X')."
}}

Requirements:
- **Language**: English ONLY.
- **Tone**: Professional, encouraging, and technically sound.
- **Goal**: Make the idea ready for a development plan.
"""

    def _call_ai_service(self, prompt: str) -> Dict[str, Any]:
        """Call AI service"""
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=300  # Optimization: creative description optimization timeout set to 300 seconds (5 minutes)
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                return {"success": True, "data": content}
            else:
                return {"success": False, "error": f"API call failed: {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _parse_optimization_result(self, ai_response: str) -> Dict[str, Any]:
        """Parse AI optimization result"""
        try:
            # Attempt to parse JSON
            start_idx = ai_response.find('{')
            end_idx = ai_response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = ai_response[start_idx:end_idx]
                result = json.loads(json_str)
                
                return {
                    "optimized_idea": result.get("optimized_idea", ""),
                    "suggestions": result.get("suggestions", ""),
                    "key_improvements": result.get("key_improvements", [])
                }
            else:
                # If unable to parse JSON, return original response directly
                return {
                    "optimized_idea": ai_response,
                    "suggestions": "AI returned optimization suggestions, but the format needs adjustment",
                    "key_improvements": []
                }
                
        except json.JSONDecodeError:
            # JSON parsing failed, return original response
            return {
                "optimized_idea": ai_response,
                "suggestions": "AI returned optimization suggestions, but the format needs adjustment",
                "key_improvements": []
            }
    
    def get_optimization_examples(self) -> list:
        """Get optimization examples"""
        return [
            {
                "original": "I want to make a shopping website",
                "optimized": "Develop an intelligent e-commerce platform targeting Gen Z consumers, integrating an AI-powered recommendation engine, social shopping features, and a seamless mobile-first experience. The platform will feature dynamic product feeds, real-time social proof, gamified loyalty rewards, and one-click checkout, aiming to redefine online shopping with hyper-personalization.",
                "improvements": ["Defined target audience (Gen Z)", "Added specific features (AI, Social)", "Clarified Value Proposition"]
            },
            {
                "original": "Build a learning system",
                "optimized": "Create a comprehensive Learning Management System (LMS) designed for corporate training and upskilling. Key features include interactive video modules, automated progress tracking with analytics dashboards, gamified assessments, and peer-to-peer discussion forums. The system will support multi-tenant architecture for scalability and offline mobile access for learning on the go.",
                "improvements": ["Specified use case (Corporate Training)", "Added technical details (Multi-tenant, Offline)", "detailed core features"]
            }
        ]

# Global optimizer instance
prompt_optimizer = PromptOptimizer()