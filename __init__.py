"""
VibeDoc: Your AI Product Manager & Architect
Transform ideas into complete development plans with AI coding prompts in 60-180 seconds
"""

__version__ = "2.0.0"
__author__ = "VibeDoc Team"
__license__ = "MIT"
__description__ = "Your AI Product Manager & Architect - Generate complete development plans in 60 seconds"
__url__ = "https://github.com/JasonRobertDestiny/VibeDoc"

# Export key components
from .config import config
from .export_manager import export_manager
from .prompt_optimizer import prompt_optimizer

__all__ = [
    "config",
    "export_manager",
    "prompt_optimizer",
]
