# VibeDoc Quick Reference Card

## 🚀 Quick Start (30 seconds)

```bash
# 1. Extract
tar -xzf VibeDoc-English-v2.0.0.tar.gz
cd VibeDoc-English

# 2. Setup
./quickstart.sh

# 3. Configure API Key
nano .env  # Add: SILICONFLOW_API_KEY=your_key

# 4. Launch
python app.py
```

**Access**: http://localhost:7860

---

## 📋 Essential Commands

### Local Development
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run application
python app.py

# Run on different port
PORT=8080 python app.py
```

### Docker
```bash
# Build
docker build -t vibedoc .

# Run
docker run -p 7860:7860 -e SILICONFLOW_API_KEY=key vibedoc

# Docker Compose
docker-compose up -d
docker-compose logs -f
docker-compose down
```

### Testing
```bash
# Check if app starts
timeout 10 python app.py

# Verify modules
python -c "import app; print('OK')"

# Check dependencies
pip list | grep gradio
```

---

## 🔧 Configuration

### Required
```bash
SILICONFLOW_API_KEY=your_api_key_here
```

### Optional
```bash
API_TIMEOUT=300
MCP_TIMEOUT=60
ENVIRONMENT=production
DEBUG=false
PORT=7860
LOG_LEVEL=INFO
```

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `app.py` | Main application |
| `config.py` | Configuration |
| `.env` | Environment variables |
| `requirements.txt` | Dependencies |
| `README.md` | Full documentation |
| `DEPLOYMENT.md` | Deployment guide |

---

## 🐛 Troubleshooting

### Port in use
```bash
# Find and kill process
lsof -i :7860
kill -9 <PID>

# Or use different port
PORT=7861 python app.py
```

### Module not found
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### API key error
```bash
# Verify .env file
cat .env | grep SILICONFLOW

# Check environment
python -c "import os; print(os.getenv('SILICONFLOW_API_KEY'))"
```

---

## 🌐 Deployment

### Hugging Face Spaces
```bash
git clone https://huggingface.co/spaces/user/vibedoc
cp -r VibeDoc-English/* vibedoc/
cd vibedoc
git add . && git commit -m "Deploy" && git push
```

### Railway
```bash
railway login
railway init
railway up
railway variables set SILICONFLOW_API_KEY=key
```

### AWS EC2
```bash
# After SSH into instance
git clone <repo>
cd VibeDoc-English
./quickstart.sh
# Configure .env
python app.py
```

---

## 📊 Features at a Glance

✅ AI-powered development plan generation  
✅ Technical architecture diagrams (Mermaid)  
✅ AI coding prompts for each module  
✅ Multi-format export (MD, DOCX, PDF, HTML)  
✅ External knowledge integration (MCP)  
✅ Visual Gantt charts and flowcharts  
✅ Dark mode support  
✅ One-click copy and download  

---

## 🔗 Important Links

- **Get API Key**: https://siliconflow.cn
- **Original Repo**: https://github.com/JasonRobertDestiny/VibeDoc
- **Gradio Docs**: https://gradio.app/docs
- **Mermaid Docs**: https://mermaid.js.org

---

## 💡 Usage Tips

1. **Optimize Ideas**: Use "Optimize Idea Description" for better results
2. **Add References**: Include URLs for context-aware generation
3. **Copy Prompts**: Use generated prompts directly in Claude, GPT, or Cursor
4. **Export Plans**: Download in your preferred format
5. **Edit Plans**: Use built-in editor to refine generated content

---

## 🆘 Getting Help

- **Documentation**: See README.md and DEPLOYMENT.md
- **Issues**: GitHub Issues for bugs
- **Discussions**: GitHub Discussions for questions
- **Email**: support@vibedoc.example.com

---

## 📦 Package Contents

- ✅ Fully translated Python application
- ✅ Comprehensive English documentation
- ✅ Docker configuration files
- ✅ Quick start automation script
- ✅ Example environment configuration
- ✅ Contributing guidelines
- ✅ Deployment guides for multiple platforms

---

**Version**: 2.0.0-en | **License**: MIT | **Updated**: 2025-11-29

**Ready to build amazing products!** 🎉
