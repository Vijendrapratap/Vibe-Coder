# 🚀 VibeDoc: Your AI Product Manager & Architect

<div align="center">

![VibeDoc Banner](https://img.shields.io/badge/VibeDoc-AI%20Product%20Manager-blue?style=for-the-badge)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg?style=for-the-badge)](https://www.python.org/downloads/)
[![Gradio](https://img.shields.io/badge/Gradio-5.34.1-orange?style=for-the-badge)](https://gradio.app/)

**Transform Ideas into Complete Development Plans in 60-180 Seconds**

AI-powered Product Manager & Software Architect that generates technical documentation, architecture diagrams, and AI coding prompts

[🌐 Online Demo](#) | [📖 Documentation](#quick-start) | [🤝 Contributing](#contributing) | [💬 Discussions](https://github.com/JasonRobertDestiny/VibeDoc/discussions)

</div>

---

## ✨ Why VibeDoc?

As a developer, product manager, or entrepreneur, you face these challenges:

- **💭 Great Ideas, No Plan?** You have ideas but don't know how to turn them into actionable development plans
- **⏰ Documentation Takes Forever?** Writing technical specs and architecture docs consumes massive time
- **🤖 AI Tools Confusing?** You want AI-assisted coding but struggle with effective prompt engineering
- **📊 Missing Professional Diagrams?** You need architecture, flow, and Gantt charts but lack design tools expertise

**VibeDoc Solves Everything!**

---

## 🎯 Core Features

### 📋 Intelligent Development Plan Generation

Enter your product idea - AI generates a complete plan in 60-180 seconds:

- **Product Overview** - Background, target users, core value proposition
- **Technical Solution** - Tech stack selection, architecture design, technology comparison
- **Development Plan** - Phased implementation, timeline, resource allocation
- **Deployment Strategy** - Environment setup, CI/CD pipeline, operations monitoring
- **Growth Strategy** - Market positioning, operations advice, growth tactics

### 🤖 AI Coding Prompt Generation

Generate ready-to-use prompts for each feature module, supporting:

- ✅ **Claude** - Code generation, architecture design
- ✅ **GitHub Copilot** - Intelligent code completion
- ✅ **ChatGPT** - Technical consultation, code optimization
- ✅ **Cursor** - AI-assisted programming

### 📊 Auto-Generated Visual Diagrams

Professional diagrams using Mermaid:

- 🏗️ **System Architecture** - Component relationships visualization
- 📈 **Business Flowcharts** - Business logic visualization
- 📅 **Gantt Charts** - Project timeline at a glance
- 📊 **Tech Comparison Tables** - Technology decision reference

### 📁 Multi-Format Export

One-click export for different scenarios:

- **Markdown (.md)** - Version control friendly, GitHub display
- **Word (.docx)** - Business documents, project reports
- **PDF (.pdf)** - Formal proposals, print archives
- **HTML (.html)** - Web display, online sharing

---

## 💡 Real-World Example

### Input Idea

```
Develop an AR sign language translation app that can translate sign language
into voice and text in real-time, and also translate voice and text into
sign language gestures displayed in AR
```

### Generated Output

The AI-generated plan includes:

#### 1. Product Overview
- Target users (deaf community, healthcare workers, educators)
- Core features (real-time translation, multi-language support, AR visualization)
- Market positioning and competitive analysis

#### 2. Technical Architecture

Complete system architecture with Mermaid diagrams showing:
- User interface components
- Backend services
- ML model integration
- Database design
- AR rendering pipeline

#### 3. Technology Stack

- **Frontend**: React Native (cross-platform)
- **Backend**: Node.js + Express
- **ML Models**: TensorFlow for sign language recognition
- **NLP**: spaCy for natural language processing
- **AR**: ARKit (iOS) / ARCore (Android)
- **Database**: MongoDB

#### 4. Development Timeline

6-month plan with 3 major milestones:
- **Month 1-2**: Core recognition & translation engine
- **Month 3-4**: AR integration & UI development
- **Month 5-6**: Testing, optimization & deployment

#### 5. 12+ AI Coding Prompts

Ready-to-use prompts for each module. Example:

```
Feature: Hand Gesture Recognition Model

Context:
Building a real-time hand gesture recognition system for sign language translation.
Need to detect and classify hand positions, movements, and facial expressions.

Requirements:
- Process video frames at 30+ FPS
- Recognize 500+ sign language gestures
- Support continuous gesture sequences
- Handle varying lighting conditions

Tech Stack:
- TensorFlow/Keras for model training
- MediaPipe for hand landmark detection
- OpenCV for image preprocessing

Constraints:
- Must run on mobile devices (iOS/Android)
- Model size < 50MB for mobile deployment
- Inference time < 100ms per frame

Expected Output:
- Model architecture code
- Training pipeline
- Data preprocessing functions
- Mobile optimization strategies
```

---

## 🚀 Quick Start

### 💻 Local Installation

#### Prerequisites

- Python 3.11+
- pip package manager
- SiliconFlow API Key ([free to obtain](https://siliconflow.cn))

#### Installation Steps

```bash
# 1. Clone the repository
git clone https://github.com/YourUsername/VibeDoc-English.git
cd VibeDoc-English

# 2. Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env file and add your API Key
```

#### Configuration

In `.env` file:

```bash
# Required: SiliconFlow API Key (free registration)
SILICONFLOW_API_KEY=your_api_key_here

# Optional: Advanced Configuration
API_TIMEOUT=300
LOG_LEVEL=INFO
ENVIRONMENT=production
```

#### Run Application

```bash
python app.py
```

Application starts at:
- **Local**: http://localhost:7860
- **Network**: http://0.0.0.0:7860

---

### 🐳 Docker Deployment (Optional)

```bash
# Build image
docker build -t vibedoc .

# Run container
docker run -p 7860:7860 \
  -e SILICONFLOW_API_KEY=your_key \
  vibedoc
```

Or using docker-compose:

```bash
docker-compose up -d
```

---

## 🏗️ Technical Architecture

Modular architecture design:

```
┌─────────────────────────────────────────┐
│         Gradio Web Interface            │
│   (User Interaction + UI + Export)      │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│       Core Processing Engine            │
├─────────────────────────────────────────┤
│  • Input Validation & Optimization      │
│  • AI Generation Coordination           │
│  • Content Quality Control              │
│  • Multi-format Export                  │
└──┬────────┬──────────┬───────────────┬──┘
   │        │          │               │
   ▼        ▼          ▼               ▼
Agent    Architect  Product      Vibe Coding
System   System     Manager      System
   │        │          │               │
   └────────┴──────────┴───────────────┘
                  │
        ┌─────────▼──────────┐
        │   MCP Services     │
        ├────────────────────┤
        │ • Fetch MCP        │
        │ • DeepWiki MCP     │
        └────────────────────┘
```

---

## 📦 Project Structure

```
VibeDoc-English/
├── app.py                      # Main application
├── config.py                   # Configuration management
├── enhanced_mcp_client.py      # MCP service client
├── explanation_manager.py      # Process explanations
├── export_manager.py           # Multi-format export
├── plan_editor.py              # Plan editing functionality
├── prompt_optimizer.py         # Prompt optimization
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template
├── README.md                   # This file
├── LICENSE                     # MIT License
├── Dockerfile                  # Docker configuration
├── docker-compose.yml          # Docker Compose config
└── image/                      # Assets directory
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SILICONFLOW_API_KEY` | ✅ Yes | - | API key for AI model |
| `API_TIMEOUT` | ❌ No | 300 | API timeout in seconds |
| `MCP_TIMEOUT` | ❌ No | 60 | MCP service timeout |
| `ENVIRONMENT` | ❌ No | development | Environment mode |
| `DEBUG` | ❌ No | false | Enable debug logging |
| `PORT` | ❌ No | 7860 | Application port |
| `LOG_LEVEL` | ❌ No | INFO | Logging level |

### Getting API Key

1. Visit [SiliconFlow](https://siliconflow.cn)
2. Register for a free account
3. Navigate to API Keys section
4. Generate a new API key
5. Copy and paste into `.env` file

---

## 🎨 Features in Detail

### Input Optimization

The system can automatically optimize your product idea description:

- Expands brief ideas into detailed descriptions
- Adds missing context and technical details
- Suggests improvements and enhancements
- Maintains original intent while adding clarity

### MCP Integration

**Model Context Protocol (MCP)** services enhance generation quality:

- **Fetch MCP**: Retrieves content from any web URL
- **DeepWiki MCP**: Specialized for technical documentation
- **Async Processing**: Non-blocking SSE-based communication
- **Smart Routing**: Automatic service selection based on URL
- **Fallback Mechanism**: Graceful degradation if services unavailable

### Content Validation

Automatic quality checks and fixes:

- Mermaid diagram syntax validation
- Link verification and cleanup
- Date consistency checks
- Format standardization
- Quality scoring system

---

## 📝 Usage Examples

### Example 1: E-commerce Platform

**Input:**
```
Build an e-commerce platform with AI-powered product recommendations
```

**Output Includes:**
- Complete technical architecture
- Database schema design
- API endpoint specifications
- Frontend component structure
- AI recommendation algorithm design
- Deployment pipeline
- 15+ coding prompts for different modules

### Example 2: Healthcare App

**Input:**
```
Create a telemedicine app for remote patient consultations
```

**Output Includes:**
- HIPAA compliance considerations
- Real-time video infrastructure
- Patient data security measures
- Appointment scheduling system
- Electronic health records integration
- 20+ feature-specific coding prompts

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit your changes** (`git commit -m 'Add some AmazingFeature'`)
4. **Push to the branch** (`git push origin feature/AmazingFeature`)
5. **Open a Pull Request**

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YourUsername/VibeDoc-English.git

# Install development dependencies
pip install -r requirements.txt

# Run tests (if available)
pytest

# Run linting
flake8 .
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Original VibeDoc project by [JasonRobertDestiny](https://github.com/JasonRobertDestiny)
- [Gradio](https://gradio.app/) for the amazing UI framework
- [SiliconFlow](https://siliconflow.cn) for AI model API
- [Mermaid](https://mermaid.js.org/) for diagram generation
- All contributors and users of VibeDoc

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/YourUsername/VibeDoc-English/issues)
- **Discussions**: [GitHub Discussions](https://github.com/YourUsername/VibeDoc-English/discussions)
- **Email**: support@vibedoc.example.com

---

## 🗺️ Roadmap

- [ ] Multi-language support (Spanish, French, German, Japanese)
- [ ] Integration with more AI coding assistants
- [ ] Custom template system
- [ ] Team collaboration features
- [ ] API access for programmatic use
- [ ] Plugin system for extensibility
- [ ] Cloud deployment options

---

## ⭐ Star History

If you find VibeDoc useful, please consider giving it a star! ⭐

---

<div align="center">

**Made with ❤️ by the VibeDoc Community**

[⬆ Back to Top](#-vibedoc-your-ai-product-manager--architect)

</div>
