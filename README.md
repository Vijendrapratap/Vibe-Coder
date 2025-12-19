# 🚀 Vibe-Coder: Your Autonomous AI Product Team

<div align="center">

![Vibe-Coder Banner](https://img.shields.io/badge/Vibe--Coder-AI%20Product%20Manager%20%26%20Architect-blue?style=for-the-badge&logo=openai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg?style=for-the-badge)](https://www.python.org/downloads/)
[![Gradio](https://img.shields.io/badge/Gradio-5.34.1-orange?style=for-the-badge)](https://gradio.app/)

**Transform a single sentence into a production-ready development plan in seconds.**

[Start Now](#-quick-start) | [Features](#-features) | [How it Works](#-how-it-works)

</div>

---

## 🌟 What is Vibe-Coder?

**Vibe-Coder** is an open-source AI agent that acts as your comprehensive software development team. It takes your raw idea—no matter how simple—and orchestrates a team of virtual experts to turn it into a concrete, executable plan.

It replaces the first 2 weeks of manual project planning with a 2-minute AI workflow.

### Why Vibe-Coder?
*   **For Founders:** Stop writing docs. Start building. Get a PRD, Tech Stack, and Roadmap instantly.
*   **For Developers:** Skip the "blank page" paralysis. Get architecture diagrams, database schemas, and boilerplate prompts.
*   **For PMs:** Automate the boring parts of spec writing. Focus on user value.

---

## ⚡ Quick Start

### Prerequisites
*   Python 3.11+
*   A **SiliconFlow** API Key (or compatible OpenAI-format key)

### Installation

1.  **Clone the Repo**
    ```bash
    git clone https://github.com/Vijendrapratap/Vibe-Coder.git
    cd Vibe-Coder
    ```

2.  **Run Setup Script**
    ```bash
    ./quickstart.sh
    # This will check Python, create venv, and install requirements.
    # It will also create your .env file.
    ```

3.  **Configure API Key**
    Edit the `.env` file and add your API key:
    ```bash
    SILICONFLOW_API_KEY=sk-your-api-key-here
    ```

4.  **Launch**
    ```bash
    python app.py
    ```
    Open your browser to `http://localhost:7860`.

---

## 🧠 How It Works: The AI Workflow

Vibe-Coder doesn't just "complete text". It follows a strict **Standard Operating Procedure (SOP)** that mirrors top-tier tech companies.

1.  **💡 Idea Optimization**:
    *   *Input*: "I want a shopping app."
    *   *Agent Action*: Uses Chain-of-Thought reasoning to expand this into "An AI-powered social commerce platform for Gen Z with real-time video feeds." (See `prompt_optimizer.py`)

2.  **🏗️ Architecture Design**:
    *   *Agent Action*: Selects the best tech stack (React Native vs Flutter? Node vs Go?) based on your specific requirements.
    *   *Output*: Generates visual Mermaid.js system architecture diagrams automatically.

3.  **📅 Roadmapping**:
    *   *Agent Action*: Breaks down the project into Phases (MVP -> Beta -> V1).
    *   *Output*: A proper Gantt chart and step-by-step implementation guide.

4.  **💻 Developer Hand-off**:
    *   *Output*: Generates exact Prompts you can paste into ChatGPT, Claude, or Cursor to actually write the code.

---

## ✨ Key Features

| Feature | Description |
| :--- | :--- |
| **SOP Enforcement** | Ensures every plan follows strict quality standards (Security, Scalability, Feasibility). |
| **Auto-Diagram** | Automatically generates Architecture, Flowchart, and ER diagrams. |
| **Context Awareness** | Understands recent tech trends (e.g., knows when to suggest Next.js App Router vs Pages Router). |
| **Multi-Format Export** | Download your plan as Markdown, PDF, or Word Doc. |
| **Tech Radar** | Built-in logic to avoid "hallucinated" libraries by verifying against common tech stacks. |

---

## 🛠️ Configuration

You can customize the AI behavior in `config.py` or `.env`:

*   `model_name`: Switch between models (e.g., deepseek-v3, qwen-2.5-coder).
*   `log_level`: Enable DEBUG for tracing the agent's "thought process".

---

## 🤝 Contributing

We love contributions!
1.  Fork the repo.
2.  Create a feature branch (`git checkout -b feature/NewAI`).
3.  Commit changes.
4.  Push and create a PR.

---

<div align="center">
Built with ❤️ for the AI era.
</div>
