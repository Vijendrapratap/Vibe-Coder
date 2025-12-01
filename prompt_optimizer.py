"""
Prompt Optimizer Module
Uses AI to optimize user input creative descriptions to improve the quality of generated reports
"""

import requests
import json
import logging
from typing import Tuple, Dict, Any, Optional
from config import config

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
        return f"""You are a professional product manager and technical consultant, skilled at expanding users' simple ideas into detailed product descriptions.

Original user input:
{user_idea}

Please help optimize this creative description to make it more detailed, specific, and professional. The optimized description should include the following elements:

1. **Core Functionality**: Clearly define the main features and value of the product
2. **Target Users**: Define the target user group for the product
3. **Usage Scenarios**: Describe typical usage scenarios of the product
4. **Technical Features**: Mention key technical features that may be required
5. **Business Value**: Explain the market value and competitive advantages of the product

Please output in the following JSON format:
{{
    "optimized_idea": "Optimized detailed product description",
    "key_improvements": [
        "Improvement 1",
        "Improvement 2",
        "Improvement 3"
    ],
    "suggestions": "Further optimization suggestions"
}}

Requirements:
- Maintain the core idea of the original creative input
- Use professional but easy-to-understand language
- Length controlled between 200-400 words
- Highlight the product's innovation and practicality"""

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
                "original": "我想做一个购物网站",
                "optimized": "Develop an intelligent shopping platform targeting young consumers, integrating AI recommendation system, social sharing features, and personalized user experience. The platform will offer multi-category product display, intelligent search, user review system, and convenient mobile payment functions, aiming to provide users with a personalized shopping experience and high-quality product recommendation service.",
                "improvements": ["Define target users", "Specify core features", "Highlight technical features"]
            },
            {
                "original": "想搞个学习系统",
                "optimized": "Build an AI-based personalized online learning management system that supports multimedia content display, learning progress tracking, intelligent question bank management, and teacher-student interaction features. The system will provide a complete digital learning solution for educational institutions and individual learners, including course management, assignment grading, learning analytics, and performance evaluation.",
                "improvements": ["Expand feature description", "Clarify application scenarios", "Add technical highlights"]
            }
        ]

# Global optimizer instance
prompt_optimizer = PromptOptimizer()