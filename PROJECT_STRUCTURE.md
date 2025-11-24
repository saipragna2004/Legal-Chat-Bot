# AI-Powered Legal Chat Bot - Project Structure

## 📁 Frontend
- **app.py** - Main Streamlit application (UI + Chat Interface)

## 📁 Backend
- **database.py** - Database operations for storing chat history
- **voice.py** - Voice input/output functionality
- **translations.py** - Multi-language support (English, Hindi, Tamil, etc.)

## 📁 Data
- **legal_assistant.db** - SQLite database for storing user interactions
- **templates/** - Legal document templates (PDF files)

## 📁 Deployment
- **requirements.txt** - Python package dependencies
- **packages.txt** - System-level dependencies (for Streamlit Cloud)
- **.streamlit/secrets.toml** - API keys and secrets (DO NOT COMMIT TO GIT)
- **DEPLOYMENT_GUIDE.md** - Instructions for deploying to Streamlit Cloud

## 📁 Documentation
- **README.md** - Project overview and setup instructions

## 🚀 Quick Start
1. Install dependencies: `pip install -r requirements.txt`
2. Set up API key in `.streamlit/secrets.toml`
3. Run the app: `streamlit run app.py`

## ☁️ Deploy to Streamlit Cloud
Follow the instructions in `DEPLOYMENT_GUIDE.md`
