# Contributing to VibeDoc

Thank you for your interest in contributing to VibeDoc! This document provides guidelines and instructions for contributing.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Community](#community)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive experience for everyone. We pledge to:

- Use welcoming and inclusive language
- Respect differing viewpoints and experiences
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment, trolling, or discriminatory comments
- Personal attacks or insults
- Publishing others' private information
- Other conduct considered inappropriate in a professional setting

---

## Getting Started

### Prerequisites

- Python 3.11+
- Git
- GitHub account
- Basic understanding of Gradio and Python

### Find an Issue

1. Browse [open issues](https://github.com/YourUsername/VibeDoc-English/issues)
2. Look for issues labeled `good first issue` or `help wanted`
3. Comment on the issue to express interest
4. Wait for maintainer approval before starting work

### Report a Bug

Before creating a bug report:

1. Check if the bug has already been reported
2. Verify you're using the latest version
3. Collect relevant information (error messages, logs, screenshots)

Create a bug report with:

- **Title**: Clear, concise description
- **Description**: Detailed explanation of the issue
- **Steps to Reproduce**: Numbered list of steps
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Environment**: OS, Python version, dependencies
- **Logs**: Relevant error messages or logs
- **Screenshots**: If applicable

### Suggest a Feature

Feature requests should include:

- **Problem**: What problem does this solve?
- **Solution**: Proposed implementation
- **Alternatives**: Other solutions considered
- **Additional Context**: Examples, mockups, or references

---

## Development Setup

### 1. Fork the Repository

Click the "Fork" button on GitHub to create your own copy.

### 2. Clone Your Fork

```bash
git clone https://github.com/YourUsername/VibeDoc-English.git
cd VibeDoc-English
```

### 3. Add Upstream Remote

```bash
git remote add upstream https://github.com/OriginalOwner/VibeDoc-English.git
```

### 4. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If available
```

### 6. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 7. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

---

## How to Contribute

### Types of Contributions

#### Code Contributions

- Bug fixes
- New features
- Performance improvements
- Code refactoring

#### Documentation

- README improvements
- API documentation
- Tutorials and guides
- Code comments

#### Testing

- Unit tests
- Integration tests
- Bug reports with test cases

#### Design

- UI/UX improvements
- Visual assets
- User experience enhancements

#### Translation

- Interface translations
- Documentation translations
- Error message translations

---

## Coding Standards

### Python Style Guide

Follow [PEP 8](https://pep8.org/) with these specifics:

#### Formatting

```python
# Use 4 spaces for indentation
def example_function(param1, param2):
    """Docstring describing the function."""
    result = param1 + param2
    return result

# Maximum line length: 100 characters
# Use meaningful variable names
user_input = get_user_input()

# Use type hints
def process_data(data: str) -> dict:
    return {"processed": data}
```

#### Naming Conventions

```python
# Functions and variables: snake_case
def calculate_total():
    total_amount = 0

# Classes: PascalCase
class DataProcessor:
    pass

# Constants: UPPER_CASE
MAX_RETRIES = 3
API_TIMEOUT = 300

# Private methods: _leading_underscore
def _internal_helper():
    pass
```

#### Imports

```python
# Standard library imports
import os
import sys
from typing import List, Dict

# Third-party imports
import gradio as gr
import requests

# Local imports
from config import config
from utils import helper_function
```

#### Documentation

```python
def generate_plan(idea: str, reference_url: str = None) -> dict:
    """
    Generate a development plan based on user idea.
    
    Args:
        idea: User's product idea description
        reference_url: Optional reference URL for additional context
        
    Returns:
        Dictionary containing:
            - plan: Generated development plan
            - prompts: AI coding prompts
            - metadata: Generation metadata
            
    Raises:
        ValueError: If idea is empty or too short
        APIError: If API call fails
        
    Example:
        >>> plan = generate_plan("Build a todo app")
        >>> print(plan['plan'])
    """
    pass
```

### JavaScript/CSS

```javascript
// Use camelCase for variables and functions
function handleCopyClick(elementId) {
    const element = document.getElementById(elementId);
    // ...
}

// Use meaningful names
const userInputField = document.querySelector('.user-input');

// Add comments for complex logic
// Calculate the optimal rendering time based on content size
const renderDelay = contentSize > 1000 ? 500 : 200;
```

### Git Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**

```bash
feat(ui): add dark mode toggle button

Implements a toggle button in the header that switches between
light and dark themes. Theme preference is saved to localStorage.

Closes #123

---

fix(api): handle timeout errors gracefully

Previously, timeout errors would crash the application. Now they
are caught and a user-friendly error message is displayed.

Fixes #456

---

docs(readme): update installation instructions

Add instructions for Python 3.11+ and clarify API key setup.
```

---

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_api.py

# Run with coverage
pytest --cov=. --cov-report=html
```

### Writing Tests

```python
import pytest
from app import generate_plan

def test_generate_plan_with_valid_input():
    """Test plan generation with valid input."""
    result = generate_plan("Build a todo app")
    assert result is not None
    assert 'plan' in result
    assert len(result['plan']) > 0

def test_generate_plan_with_empty_input():
    """Test plan generation with empty input."""
    with pytest.raises(ValueError):
        generate_plan("")

@pytest.mark.parametrize("idea,expected_length", [
    ("Short idea", 100),
    ("A much longer and more detailed product idea description", 500),
])
def test_plan_length_varies_with_input(idea, expected_length):
    """Test that plan length varies based on input."""
    result = generate_plan(idea)
    assert len(result['plan']) >= expected_length
```

---

## Submitting Changes

### Before Submitting

1. **Test your changes**
   ```bash
   pytest
   ```

2. **Check code style**
   ```bash
   flake8 .
   black --check .
   ```

3. **Update documentation**
   - Update README if needed
   - Add docstrings to new functions
   - Update CHANGELOG.md

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

5. **Sync with upstream**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

### Creating a Pull Request

1. Go to your fork on GitHub
2. Click "New Pull Request"
3. Select your branch
4. Fill out the PR template:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe how you tested your changes

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests added/updated
- [ ] All tests passing
```

5. Link related issues (e.g., "Closes #123")
6. Request review from maintainers

### Pull Request Review Process

1. **Automated Checks**: CI/CD runs tests and linters
2. **Code Review**: Maintainers review your code
3. **Feedback**: Address any requested changes
4. **Approval**: Once approved, PR will be merged
5. **Cleanup**: Delete your branch after merge

---

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Discord** (if available): Real-time chat
- **Email**: For private matters

### Getting Help

- Check existing documentation
- Search closed issues
- Ask in GitHub Discussions
- Join community chat

### Recognition

Contributors are recognized in:
- README.md contributors section
- CHANGELOG.md for each release
- GitHub contributors page

---

## Development Tips

### Debugging

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Use breakpoints
import pdb; pdb.set_trace()

# Or use ipdb for better experience
import ipdb; ipdb.set_trace()
```

### Performance Profiling

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

### Gradio Development

```python
# Enable auto-reload during development
demo.launch(debug=True, show_error=True)

# Test specific components
with gr.Blocks() as demo:
    # Your component
    pass

demo.launch()
```

---

## License

By contributing to VibeDoc, you agree that your contributions will be licensed under the MIT License.

---

## Questions?

Don't hesitate to ask! Open an issue or discussion if you need help.

**Thank you for contributing to VibeDoc!** 🚀
