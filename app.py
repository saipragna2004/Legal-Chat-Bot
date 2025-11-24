
import streamlit as st
import speech_recognition as sr
import pyttsx3
import threading
import pandas as pd
import json
import os

# Try to import Google Generative AI
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Initialize text-to-speech engine safely
engine = None
try:
    engine = pyttsx3.init()
except Exception as e:
    print(f"Warning: TTS engine could not be initialized (expected on Cloud): {e}")

# Initialize session state attributes if not already set
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_context" not in st.session_state:
    st.session_state.conversation_context = []
if "interaction_log" not in st.session_state:
    st.session_state.interaction_log = pd.DataFrame(columns=["user_query", "assistant_response"])

# Ensure language_preference and user_logged_in are initialized
if "language_preference" not in st.session_state:
    st.session_state.language_preference = "English"
if "user_logged_in" not in st.session_state:
    st.session_state.user_logged_in = False

# Function to convert text to speech using threading
def speak(text):
    if engine is None:
        return
    try:
        def speak_thread():
            try:
                engine.say(text)
                engine.runAndWait()
            except:
                pass
        # Run the speech in a separate thread
        thread = threading.Thread(target=speak_thread)
        thread.start()
    except Exception:
        pass

# Function for voice input (speech to text)
def listen():
    try:
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            st.info("Listening... Speak now.")
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source, timeout=5)
            try:
                query = recognizer.recognize_google(audio)
                st.success(f"Voice Input: {query}")
                return query
            except sr.UnknownValueError:
                st.warning("Sorry, I couldn't understand that.")
            except sr.RequestError:
                st.error("Speech service is down.")
    except Exception as e:
        st.warning("Voice input is not available on this device/server.")
        return None

# Load patterns from JSON file
def load_patterns():
    try:
        with open('legal_patterns.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        # Return empty list if file not found
        return []
    except json.JSONDecodeError:
        # Return empty list if JSON is invalid
        return []

patterns = load_patterns()

# Define response function using Gemini API (Cloud Compatible)
def get_response(query):
    query = query.lower().strip()
    if len(query) < 3:
        return translations[st.session_state.language_preference]["no_response"]

    # Add the latest user query to the conversation context
    st.session_state.conversation_context.append(f"User: {query}")

    # Try to use Gemini API
    if GEMINI_AVAILABLE:
        try:
            # Robust API Key Loading
            api_key = None
            # 1. Try Streamlit Secrets
            if hasattr(st, 'secrets'):
                api_key = st.secrets.get("GEMINI_API_KEY")
            
            # 2. Try Environment Variable
            if not api_key:
                api_key = os.getenv("GEMINI_API_KEY")

            # 3. Try Direct File Read (Local Fallback)
            if not api_key:
                try:
                    import toml
                    secrets = toml.load(".streamlit/secrets.toml")
                    api_key = secrets.get("GEMINI_API_KEY")
                except:
                    pass
            
            if api_key:
                genai.configure(api_key=api_key)
                # Use the Flash model for better rate limits
                model = genai.GenerativeModel('gemini-2.0-flash')
                
                # Create prompt for Medium Length (Balanced) with Strict Legal Guardrails
                prompt = f"""You are a specialized legal assistant for Indian law. 
                Your task is to answer ONLY legal-related queries.
                
                Query: {query}
                
                Instructions:
                1. If the query is NOT related to law, crime, rights, or legal procedures, reply EXACTLY: "I am a legal assistant. I can only help you with legal matters, laws, and rights in India."
                2. If the query IS legal, provide a clear, balanced answer (4-5 sentences).
                3. Mention key sections/acts but avoid overwhelming detail.
                4. Always remind users to consult a lawyer."""
                
                response_obj = model.generate_content(prompt)
                response = response_obj.text.strip()
                if response:
                    st.session_state.conversation_context.append(f"Assistant: {response}")
                    return response, True  # Return True to indicate AI response (for Read More button)
        except Exception as e:
            print(f"Gemini Error: {e}")
            # Don't show error to user, fall back to keywords
            pass

    # Check for matching patterns only if patterns exist
    if patterns and isinstance(patterns, list):
        for item in patterns:
            if isinstance(item, dict) and 'pattern' in item and 'response' in item:
                pattern = item['pattern'].lower().strip()
                if pattern in query:
                    response = item['response']
                    st.session_state.conversation_context.append(f"Assistant: {response}")
                    return response, False

    # Fallback response with basic keyword matching
    if 'ipc' in query or 'section' in query:
        response = "The Indian Penal Code (IPC) is the main criminal code of India. Please specify which section you'd like to know about."
    elif 'lawyer' in query or 'attorney' in query:
        response = "For specific legal advice, please consult a qualified lawyer or attorney in your area."
    elif 'court' in query:
        response = "Indian courts include District Courts, High Courts, and the Supreme Court. Each handles different types of cases."
    elif 'rights' in query:
        response = "Indian citizens have fundamental rights under the Constitution including right to equality, freedom, and justice."
    elif 'robbery' in query or 'theft' in query or 'dacoity' in query or 'roberry' in query:
        response = "Theft, Robbery, and Dacoity are offenses under the Indian Penal Code (Sections 378-402). Punishment varies based on severity. Report such incidents to the police immediately."
    else:
        response = translations[st.session_state.language_preference]["no_response"]
    
    st.session_state.conversation_context.append(f"Assistant: {response}")
    return response, False

# Language Translation Dictionary
translations = {
    "English": {
        "ask_query": "Ask your query for legal assistance",
        "thinking": "Thinking ✨...",
        "no_response": "Sorry, I couldn't find a matching response for your query.",
        "positive_feedback": "👍 Positive feedback",
        "negative_feedback": "👎 Negative feedback",
        "login_button": "Login",
        "welcome": "Welcome",
        "faq_button": "Show FAQs",
        "download_button": "Download Chat History as CSV",
        "interaction_history": "Show Interaction History",
        "voice_query": "Voice Query 🎙️",
        "view_history": "View History 📜",
        "download_law": "Download Law 📁",
        "info_section": "**Legal Laws Advisor Bot:📄**\n- **Objective:** Developed a conversational chatbot to provide legal law info and assistance.\n- **Features:**📜\n  - Allows users to ask their query of law.\n  - Provides a response to user query. ✔\n  - Offers a user-friendly interface for asking legal questions."
    },
    "Hindi - हिन्दी": {
        "ask_query": "कानूनी सहायता के लिए अपना प्रश्न पूछें",
        "thinking": "सोच रहे हैं ✨...",
        "no_response": "मुझे आपके प्रश्न का मिलान करने वाला उत्तर नहीं मिला।",
        "positive_feedback": "👍 सकारात्मक प्रतिक्रिया",
        "negative_feedback": "👎 नकारात्मक प्रतिक्रिया",
        "login_button": "लॉगिन करें",
        "welcome": "स्वागत है",
        "faq_button": "सामान्य प्रश्न दिखाएँ",
        "download_button": "चैट इतिहास डाउनलोड करें",
        "interaction_history": "इंटरएक्शन इतिहास दिखाएँ",
        "voice_query": "आवाज़ से पूछें 🎙️",
        "view_history": "इतिहास देखें 📜",
        "download_law": "कानून डाउनलोड करें 📁",
         "info_section": """
        **कानूनी क़ानून सलाहकार बॉट📄**
        - **लक्ष्य:** कानूनी क़ानून जानकारी और सहायता प्रदान करने के लिए एक संवादात्मक चैटबॉट विकसित किया गया।
        - **विशेषताएँ:**📜
          -  उपयोगकर्ताओं को कानून से संबंधित प्रश्न पूछने की अनुमति देता है। 𓍝
          -  उपयोगकर्ता के प्रश्न का उत्तर प्रदान करता है। ✔
          -  उपयोगकर्ता के प्रश्न का विस्तृत विवरण, दंड, लाभ, और हानियाँ प्रदर्शित करता है। ✉︎
          -  कानूनी प्रश्न पूछने के लिए एक उपयोगकर्ता-मित्र इंटरफेस प्रदान करता है। 🔗
        """
    },
    "Telugu - తెలుగు": {
        "ask_query": "న్యాయ సహాయం కోసం మీ ప్రశ్నను అడగండి",
        "thinking": "ఆలోచిస్తున్నాను ✨...",
        "no_response": "మీ ప్రశ్నకు సరిపడే సమాధానం కనుగొనలేకపోయాను.",
        "positive_feedback": "👍 సానుకూల అభిప్రాయం",
        "negative_feedback": "👎 ప్రతికూల అభిప్రాయం",
        "login_button": "లాగిన్ చేయండి",
        "welcome": "స్వాగతం",
        "faq_button": "ఎఫ్ ఏ క్యూ లను చూపించండి",
        "download_button": "చాట్ చరిత్రను డౌన్‌లోడ్ చేయండి",
        "interaction_history": "మాట్లాడిన చరిత్ర చూపించు",
        "voice_query": "వాయిస్ క్వెరీ 🎙️",
        "view_history": "చరిత్ర చూడండి 📜",
        "download_law": "డౌన్‌లోడ్ చేయండి 📁",
        "info_section": """
        **చట్టాల సలహా బాట్📄**
        - **ఉద్దేశం:** చట్టాల సమాచారం మరియు సహాయం అందించడానికి ఒక సంభాషణ చాట్‌బాట్‌ను అభివృద్ధి చేయడం।
        - **ప్రతి పౌరుడు చట్టాల గురించి అవగాహన కలిగి ఉండాలి.
        - **సదుపాయాలు:**📜
          -  వినియోగదారులు చట్టం గురించి తమ ప్రశ్నను అడగగలుగుతారు। 𓍝
          -  వినియోగదారుల ప్రశ్నకు సమాధానం అందిస్తుంది। ✔
          -  వినియోగదారు ప్రశ్నకు సంబంధించిన వివరణ, శిక్షలు, లాభాలు మరియు నష్టాలను ప్రదర్శిస్తుంది। ✉︎
          -  చట్టంపై ప్రశ్నలను అడగడానికి వినియోగదారు-అనుకూల ఇంటర్‌ఫేస్ అందిస్తుంది। 🔗
        - **ప్రాముఖ్యత:** సంభాషణ కృత్రిమ నుణ్ణి గుణం ద్వారా చట్ట సమాచారాన్ని అందించే లోనిపడి సరళత, సామర్థ్యం మరియు యాక్సెస్‌పై దృష్టి సారిస్తుంది। 📝
        """
    },
    "Tamil - தமிழ்": {
        "ask_query":"சட்ட உதவிக்கு உங்கள் கேள்வியைக் கேளுங்கள்",
        "thinking": "சிந்தித்து கொண்டிருக்கிறேன் ✨...",
        "no_response": "உங்கள் கேள்விக்கான பதிலை காணவில்லை.",
        "positive_feedback": "👍 நல்ல கருத்து",
        "negative_feedback": "👎 எதிர்மறை கருத்து",
        "login_button": "உள்நுழைய",
        "welcome": "வரவேற்கிறேன்",
        "faq_button": "கேள்விகளை காண்பிக்கவும்",
        "download_button": "அரட்டை வரலாற்றைப் பதிவிறக்கவும்",
        "interaction_history": "உரையாடல் வரலாற்றைக் காண்பிக்கவும்",
        "voice_query": "குரல் கேள்வி 🎙️",
        "view_history": "வரலாற்றைக் காண்க 📜",
        "download_law": "சட்டத்தை பதிவிறக்கவும் 📁",
        "info_section": """
        **சட்ட ஆலோசகர்போட்📄**
        - **நோக்கம்:** சட்ட தகவல்கள் மற்றும் உதவியை வழங்குவதற்காக உருவாக்கப்பட்ட ஒரு உரையாடல் சாட் பாட்டை உருவாக்கியது.
        - **ஒவ்வொரு குடிமகனும் சட்டங்களைப் பற்றி அறிந்திருக்க வேண்டும்.**
        - **சாதனைகள்:**📜
          -  பயனாளர்களுக்கு சட்டம் பற்றிய கேள்விகளை கேட்க அனுமதிக்கின்றது। 𓍝
          -  பயனாளரின் கேள்விக்கு பதில் அளிக்கின்றது। ✔
          -  பயனாளரின் கேள்விக்கு தொடர்புடைய விளக்கம், தண்டனைகள், நன்மைகள் மற்றும் தீமைகளை காட்டுகின்றது। ✉︎
          -  சட்டங்களைப் பற்றி கேட்க பயனாளர் நட்பான இடைமுகத்தை வழங்குகிறது। 🔗
        - **முக்கியத்துவம்:** உரையாடல் செயற்கை நுண்ணறிவு வழியாக சட்ட தகவல்களை வழங்குவதில் எளிமை, திறன் மற்றும் அணுகுமுறை என்பதிலுள்ள கவனம். 📝
        """
    },
    "Kannada - ಕನ್ನಡ": {
    "ask_query": "ನಿಮ್ಮ ಕಾನೂನು ಸಹಾಯಕ್ಕಾಗಿ ಪ್ರಶ್ನೆಯನ್ನು ಕೇಳಿ",
    "thinking": "ಆಲೋಚನೆ ✨...",
    "no_response": "ಕ್ಷಮಿಸಿ, ನಿಮ್ಮ ಪ್ರಶ್ನೆಗೆ ಹೊಂದುವ ಉತ್ತರವನ್ನು ನಾನು ಕಂಡುಹಿಡಿಯಲಿಲ್ಲ.",
    "positive_feedback": "👍 ಉತ್ತಮ ಪ್ರತಿಕ್ರಿಯೆ",
    "negative_feedback": "👎 ಹೀನಾಯ ಪ್ರತಿಕ್ರಿಯೆ",
    "login_button": "ಲಾಗಿನ್",
    "welcome": "ಸ್ವಾಗತ",
    "faq_button": "FAQಗಳನ್ನು ತೋರಿಸಿ",
    "download_button": "ಚಾಟ್ ಇತಿಹಾಸವನ್ನು CSVಗೆ ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ",
    "interaction_history": "ಇಂಟರಾಕ್ಷನ್ ಇತಿಹಾಸವನ್ನು ತೋರಿಸಿ",
    "voice_query": "ಧ್ವನಿ ಪ್ರಶ್ನೆ 🎙️",
    "view_history": "ಇತಿಹಾಸ ವೀಕ್ಷಿಸಿ 📜",
    "download_law": "ಕಾನೂನು ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ 📁",
    "info_section": "**ಕಾನೂನು ಸಲಹೆಗಾರ ಬಾಟ್:📄**\n- **ಉದ್ದೇಶ:** ಕಾನೂನು ಮಾಹಿತಿ ಮತ್ತು ಸಹಾಯ ನೀಡಲು ಸಂವಾದಾತ್ಮಕ ಚಾಟ್‌ಬಾಟ್ ಅನ್ನು ಅಭಿವೃದ್ಧಿಪಡಿಸಲಾಗಿದೆ.\n- **ವೈಶಿಷ್ಟ್ಯಗಳು:**📜\n  - ಬಳಕೆದಾರರಿಗೆ ಕಾನೂನು ಪ್ರಶ್ನೆಯನ್ನು ಕೇಳಲು ಅವಕಾಶ ನೀಡುತ್ತದೆ.\n  - ಬಳಕೆದಾರರ ಪ್ರಶ್ನೆಗೆ ಉತ್ತರವನ್ನು ನೀಡುತ್ತದೆ. ✔\n  - ಕಾನೂನು ಪ್ರಶ್ನೆಗಳನ್ನು ಕೇಳಲು ಬಳಕೆದಾರ-ಹಿತಕರ ಇಂಟರ್‌ಫೇಸ್ ಅನ್ನು ಒದಗಿಸುತ್ತದೆ."
},
    "Malayalam - മലയാളം": {
    "ask_query": "നിങ്ങളുടെ നിയമ സഹായത്തിനായുള്ള ചോദ്യം ചോദിക്കുക",
    "thinking": "ചിന്തിക്കുന്നു ✨...",
    "no_response": "ക്ഷമിക്കണം, നിങ്ങളുടെ ചോദ്യത്തിന് അനുയോജമായ പ്രതികരണം കണ്ടെത്താനായില്ല.",
    "positive_feedback": "👍 സാന്ദര്യപരമായ പ്രതികരണം",
    "negative_feedback": "👎 പ്രതികൂല പ്രതികരണം",
    "login_button": "ലോഗിൻ",
    "welcome": "സ്വാഗതം",
    "faq_button": "FAQ കാണിക്കുക",
    "download_button": "ചാറ്റ് ചരിത്രം CSV ആയി ഡൗൺലോഡ് ചെയ്യുക",
    "interaction_history": "ഇന്ററാക്ഷൻ ചരിത്രം കാണിക്കുക",
    "voice_query": "ശബ്ദ ചോദ്യം 🎙️",
    "view_history": "ചരിത്രം കാണുക 📜",
    "download_law": "നിയമം ഡൗൺലോഡ് ചെയ്യുക 📁",
    "info_section": "**നിയമ ഉപദേഷ്ടാവ് ബോട്ട്:📄**\n- **ലക്ഷ്യം:** നിയമ വിവരങ്ങളും സഹായവും നൽകാൻ സംഭാഷണ ചാറ്റ്‌ബോട്ട് വികസിപ്പിച്ചിരിക്കുന്നു.\n- **സവിശേഷതകൾ:**📜\n  - ഉപയോക്താക്കളെ നിയമ ചോദ്യങ്ങൾ ചോദിക്കാൻ അനുവദിക്കുന്നു.\n  - ഉപയോക്തൃ ചോദ്യത്തിന് പ്രതികരണം നൽകുന്നു. ✔\n  - നിയമ ചോദ്യങ്ങൾ ചോദിക്കാൻ ഉപയോക്തൃ സൗഹൃദ ഇന്റർഫേസ് നൽകുന്നു."
}
}



# Streamlit Title
st.title("AI-LEGAL LAWS ASSISTANT 🎗️")

# Custom CSS for better UI/UX
st.markdown("""
<style>
    /* Main container */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-attachment: fixed;
    }
    
    /* Title styling */
    h1 {
        color: #4a5568;
        font-weight: 700;
        text-align: center;
        padding: 1rem 0;
    }
    
    /* Info box styling */
    .stAlert {
        border-radius: 10px;
        border-left: 5px solid #667eea;
    }
    
    /* Input box styling */
    .stTextInput input {
        border-radius: 10px;
        border: 2px solid #667eea;
        padding: 10px;
        font-size: 16px;
    }
    
    /* Chat input styling */
    .stChatInputContainer {
        border-radius: 15px;
    }
    
    /* Better spacing */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Load and display the info section
st.info(translations[st.session_state.language_preference]["info_section"])

# Small disclaimer
st.caption("⚠️ Disclaimer: This is an AI assistant providing general legal information only, not legal advice. Consult a qualified lawyer for specific legal matters.")

# Sidebar - Features at top
st.sidebar.title("✨ Features")
st.sidebar.markdown("---")

# Language selection from the sidebar
language_preference = st.sidebar.selectbox(
    "Welcome Select your preferred language :",
    ["English", "Hindi - हिन्दी", "Telugu - తెలుగు", "Tamil - தமிழ்","Malayalam - മലയാളം","Kannada - ಕನ್ನಡ"],
    index=["English", "Hindi - हिन्दी", "Telugu - తెలుగు", "Tamil - தமிழ்","Malayalam - മലയാളം","Kannada - ಕನ್ನಡ"].index(st.session_state.language_preference)
)

# Save selected language preference in session state
if language_preference != st.session_state.language_preference:
    st.session_state.language_preference = language_preference

# User login logic
if not st.session_state.user_logged_in:
    st.session_state.username = st.text_input("Enter your name to start chatting with legal laws assistant 🎗️")
    if st.session_state.username:
        st.session_state.user_logged_in = True
        st.rerun()
else:
    st.write(f"👋 Hello {st.session_state.username}! {translations[st.session_state.language_preference]['ask_query']}")
    prompt = st.chat_input(translations[st.session_state.language_preference]["ask_query"])

    if prompt:
        st.write(f"👤 Your Query: {prompt}")
        response, is_ai_generated = get_response(prompt)
        st.write(f"🤖 Response: {response}")

        # Read More / Detailed View
        if is_ai_generated:
            with st.expander("📖 Read Detailed Explanation"):
                with st.spinner("Generating detailed legal analysis..."):
                    try:
                        # Re-use the configured model to generate a detailed response
                        model = genai.GenerativeModel('gemini-2.0-flash')
                        detailed_prompt = f"""You are an expert legal advisor.
                        Provide a comprehensive, detailed legal analysis of: {prompt}
                        Include:
                        1. Relevant Sections/Acts (IPC, CrPC, etc.)
                        2. Punishments/Fines
                        3. Legal Procedure/Steps
                        4. Rights of the involved parties
                        5. Important Case Laws (if any)
                        Format with clear headings and bullet points."""
                        
                        detailed_response = model.generate_content(detailed_prompt)
                        st.markdown(detailed_response.text)
                    except Exception as e:
                        st.error("Could not generate detailed explanation.")

        new_log = {"user_query": prompt, "assistant_response": response}
        st.session_state.interaction_log = pd.concat(
            [st.session_state.interaction_log, pd.DataFrame([new_log])], ignore_index=True
        )
       
        # Speak the response if voice is enabled (optional, currently manual button)
        # speak(response)

 # Adding custom styling for buttons
st.markdown("""
    <style>
        .stButton>button {
            border: 2px solid #4CAF50;
            border-radius: 8px;
            background-color: #4CAF50;
            color: #FFFFFF;
            padding: 10px 15px;
            font-size: 14px;
            font-weight: 600;
            margin: 5px;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .stButton>button:hover {
            background-color: #45a049;
            color: #FFFFFF;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
    </style>
""", unsafe_allow_html=True)        

# Create 3 columns for the buttons
col1, col2, col3 = st.columns(3)

# Speech to Text Button (disabled on cloud)
with col1:
    # Check if running on Streamlit Cloud (no microphone access)
    is_cloud = os.getenv('STREAMLIT_SHARING_MODE') or not engine
    
    if is_cloud:
        st.button(translations[st.session_state.language_preference]["voice_query"], disabled=True, help="Voice features are not available on cloud deployment")
    else:
        if st.button(translations[st.session_state.language_preference]["voice_query"]):
            query = listen()
            if query:
                st.session_state.messages.append(query)
                st.write(f"Your Query: {query}")
                response, _ = get_response(query)  # Unpack tuple, ignore is_ai flag for voice
                st.write(f"Assistant Response: {response}")
                speak(response)  # Speak the response

# Interaction History Button
with col2:
    if st.button(translations[st.session_state.language_preference]["view_history"]):
        st.dataframe(st.session_state.interaction_log)

# Download Button
with col3:
    if st.button(translations[st.session_state.language_preference]["download_law"]):
        st.download_button(
            translations[st.session_state.language_preference]["download_button"],
            st.session_state.interaction_log.to_csv(index=False),
            file_name="interaction_history.csv"
        )
# Folder where templates are stored
TEMPLATES_FOLDER = "templates"

# Legal templates with file names
legal_templates = {
    "Rental Agreement": "rental_agreement_template.pdf",
    "Loan Agreement":"loan-agreement-template.pdf",
    "Employment Agreement": "employment_agreement_template.pdf",
    "Business Agreement": "partnership_agreement_template.pdf",
    "Freelancer Agreement": "freelancer_contract_template.pdf",
    "Invoice Agreement": "invoice_template.pdf",
    "Lease Agreement": "lease_agreement_template.pdf",
    "Service Agreement": "service_agreement_template.pdf",
    "Non-Disclosure Agreement": "nda_template.pdf"  
}

# Sidebar for Language Selection (now for templates)
with st.sidebar:
    # Language selection dropdown for templates with placeholder
    template_selection = st.selectbox(
        "Select a legal template to download :",  # Title for the dropdown
        ["Select a template"] + list(legal_templates.keys())  # Add a placeholder option
    )
    
    st.markdown("---")
    
    # External Resources as expandable section
    with st.expander("🔗 External Resources"):
        st.markdown("[Indian Judiciary](https://www.india.gov.in/topics/law-justice/)")
        st.markdown("[Ministry of Law & Justice](https://legislative.gov.in/)")
        st.markdown("[Supreme Court of India](https://main.sci.gov.in/)")


# Get the selected template's file name
if template_selection != "Select a template":  # Ensure a valid selection is made
    selected_template_file = legal_templates.get(template_selection)

    # Check if the selected template file exists and provide the download button
    if selected_template_file:
        file_path = os.path.join(TEMPLATES_FOLDER, selected_template_file)
        
        if os.path.exists(file_path):  # Check if the file exists
            with open(file_path, "rb") as file:
                st.sidebar.download_button(
                    label=f"📄 Download {template_selection}",
                    data=file,
                    file_name=selected_template_file,
                    mime="application/pdf"
                )
        else:
            st.sidebar.warning(f"Template '{template_selection}' is not available.")
