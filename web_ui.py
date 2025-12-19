import gradio as gr
import logging
from logic import optimize_user_idea, generate_development_plan
from explanation_manager import explanation_manager  # Needed for local handlers

logger = logging.getLogger(__name__)

def show_explanation():
    """Show processing explanation"""
    explanation = explanation_manager.get_processing_explanation()
    return (
        gr.update(visible=False),  # Hide plan_output
        gr.update(value=explanation, visible=True),  # Show process_explanation
        gr.update(visible=True)   # Show hide_explanation_btn
    )

def hide_explanation():
    """Hide processing explanation"""
    return (
        gr.update(visible=True),   # Show plan_output
        gr.update(visible=False),  # Hide process_explanation
        gr.update(visible=False)   # Hide hide_explanation_btn
    )

def create_ui():
    """Create and return the Gradio UI blocks"""
    
    custom_css = """
    .header-gradient {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .dark .header-gradient {
        background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
    }
    .content-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        padding: 2rem;
        border-radius: 1.5rem;
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.1);
        margin: 1rem 0;
        border: 1px solid #e2e8f0;
    }
    .result-container {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border-radius: 1.5rem;
        padding: 2rem;
        margin: 2rem 0;
        border: 2px solid #3b82f6;
    }
    .tips-box {
        background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
        padding: 1.5rem;
        border-radius: 1.2rem;
        margin: 1.5rem 0;
        border: 2px solid #93c5fd;
    }
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
    .prompts-highlight {
        background: linear-gradient(135deg, #f0f8ff 0%, #e6f3ff 100%);
        border: 2px solid #4299e1;
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 1.5rem 0;
    }
    """
    
    with gr.Blocks(
        title="Vibe-Coder: Your AI Product Team",
        theme=gr.themes.Soft(primary_hue="blue"),
        css=custom_css
    ) as demo:
        
        gr.HTML("""
        <div class="header-gradient">
            <h1>🚀 Vibe-Coder - AI-Powered Development Plan Generator</h1>
            <p style="font-size: 18px; margin: 15px 0; opacity: 0.95;">
                🤖 Transform your ideas into comprehensive development plans in 60-180 seconds
            </p>
            <p style="opacity: 0.85;">
                ✨ AI-Driven Planning |  Visual Diagrams | 🎯 Professional Output |  Multi-format Export
            </p>
            <div style="margin-top: 1rem; padding: 0.5rem; background: rgba(255,255,255,0.1); border-radius: 0.5rem;">
                <small style="opacity: 0.9;">
                    🌟 Open Source Project | 💡 Built for Developers | ⚡ Fast & Reliable
                </small>
            </div>
        </div>
        
        <!-- Add Mermaid.js support -->
        <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
        <script>
            // Initialize Mermaid
            mermaid.initialize({ 
                startOnLoad: true,
                theme: 'default',
                flowchart: { useMaxWidth: true, htmlLabels: true, curve: 'basis' },
                gantt: { useMaxWidth: true }
            });
        </script>
        """)
        
        with gr.Row():
            with gr.Column(scale=2, elem_classes="content-card"):
                gr.Markdown("## 💡 Enter Your Product Idea", elem_id="input_idea_title")
                
                idea_input = gr.Textbox(
                    label="Product Idea Description",
                    placeholder="e.g., I want to build a tool to help developers manage code snippets with multi-language highlighting, tagging, and team sharing...",
                    lines=5,
                    max_lines=10,
                    show_label=False
                )
                
                with gr.Row():
                    optimize_btn = gr.Button("✨ Optimize Idea", variant="secondary", size="sm")
                    reset_btn = gr.Button("🔄 Reset", variant="secondary", size="sm")
                
                optimization_result = gr.Markdown(visible=False)
                
                reference_url_input = gr.Textbox(
                    label="Reference URL (Optional)",
                    placeholder="Enter any reference link (blog, docs, etc.)...",
                    lines=1,
                    show_label=True
                )
                
                generate_btn = gr.Button(
                    "🤖 AI Generate Development Plan + Prompts",
                    variant="primary",
                    size="lg"
                )
            
            with gr.Column(scale=1):
                gr.HTML("""
                <div class="tips-box">
                    <h4 style="color: #3182ce;">🚀 How It Works</h4>
                    <ul>
                        <li><span style="color: #e53e3e;">1. Describe</span> your idea creatively</li>
                        <li><span style="color: #38a169;">2. Optimize</span> it with AI reasoning</li>
                        <li><span style="color: #3182ce;">3. Generate</span> a full plan & prompts</li>
                    </ul>
                    <h4 style="color: #38a169;">🎯 outputs</h4>
                    <ul>
                        <li>📋 Full Development Plan</li>
                        <li>🤖 AI Coding Prompts</li>
                        <li> Architecture Diagrams</li>
                    </ul>
                </div>
                """)

        # Results Area
        with gr.Column(elem_classes="result-container"):
            plan_output = gr.Markdown(
                value="""
<div style="text-align: center; padding: 2rem;">
    <h3 style="color: #2b6cb0;">Ready to Generate</h3>
    <p style="color: #4a5568;">Click the <b>AI Generate</b> button to start.</p>
</div>
                """,
                elem_id="plan_result",
                label="AI Generated Plan"
            )
            
            process_explanation = gr.Markdown(visible=False)
            
            with gr.Row():
                show_explanation_btn = gr.Button("🔍 Show Process Details", variant="secondary", size="sm", visible=False)
                hide_explanation_btn = gr.Button("📝 Back to Plan", variant="secondary", size="sm", visible=False)
            
            prompts_for_copy = gr.Textbox(visible=False)
            download_file = gr.File(label="📁 Download Plan", visible=False, interactive=False)
            
            download_info = gr.HTML(visible=False)

        # Event Bindings
        optimize_btn.click(
            fn=optimize_user_idea,
            inputs=[idea_input],
            outputs=[idea_input, optimization_result]
        ).then(
            fn=lambda: gr.update(visible=True),
            outputs=[optimization_result]
        )
        
        reset_btn.click(
            fn=lambda: ("", gr.update(visible=False)),
            outputs=[idea_input, optimization_result]
        )
        
        show_explanation_btn.click(
            fn=show_explanation,
            outputs=[plan_output, process_explanation, hide_explanation_btn]
        )
        
        hide_explanation_btn.click(
            fn=hide_explanation,
            outputs=[plan_output, process_explanation, hide_explanation_btn]
        )
        
        def show_download_info():
            return gr.update(value="<div style='text-align: center; color: green;'>✅ Document Generated! You can download it below.</div>", visible=True)

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

    return demo
