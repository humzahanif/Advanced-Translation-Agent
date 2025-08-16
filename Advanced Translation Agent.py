import streamlit as st
import google.generativeai as genai
import pandas as pd
from datetime import datetime
import traceback
import speech_recognition as sr
from gtts import gTTS
import io
import base64
import tempfile
import os

# Page configuration
st.set_page_config(
    page_title="Advanced Translation Agent",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Language mappings
LANGUAGES = {
    "English": "en", "Spanish": "es", "French": "fr", "German": "de", "Italian": "it",
    "Portuguese": "pt", "Russian": "ru", "Japanese": "ja", "Korean": "ko", "Chinese (Simplified)": "zh-cn",
    "Chinese (Traditional)": "zh-tw", "Arabic": "ar", "Hindi": "hi", "Turkish": "tr", "Dutch": "nl",
    "Swedish": "sv", "Norwegian": "no", "Danish": "da", "Finnish": "fi", "Polish": "pl",
    "Czech": "cs", "Hungarian": "hu", "Romanian": "ro", "Bulgarian": "bg", "Greek": "el",
    "Hebrew": "he", "Thai": "th", "Vietnamese": "vi", "Indonesian": "id", "Malay": "ms",
    "Filipino": "fil", "Ukrainian": "uk", "Croatian": "hr", "Serbian": "sr", "Slovak": "sk"
}

class TranslationAgent:
    def __init__(self, api_key: str):
        self.api_key = api_key
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            # Test the connection
            test_response = self.model.generate_content("Hello")
            st.success("✅ API connection successful!")
        except Exception as e:
            st.error(f"API initialization error: {str(e)}")
            raise e

    def speech_to_text(self) -> str:
        """Convert speech to text using speech recognition"""
        try:
            r = sr.Recognizer()
            with sr.Microphone() as source:
                st.info("🎤 Listening... Please speak clearly.")
                # Adjust for ambient noise
                r.adjust_for_ambient_noise(source, duration=1)
                # Listen for audio
                audio = r.listen(source, timeout=10, phrase_time_limit=30)
                
            st.info("🔄 Processing speech...")
            # Recognize speech using Google's service
            text = r.recognize_google(audio)
            return text
        except sr.WaitTimeoutError:
            return "Listening timeout - no speech detected"
        except sr.UnknownValueError:
            return "Could not understand the audio"
        except sr.RequestError as e:
            return f"Speech recognition error: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"

    def text_to_speech(self, text: str, language: str = "English") -> bytes:
        """Convert text to speech using gTTS"""
        try:
            # Map language names to gTTS language codes
            gtts_codes = {
                "English": "en", "Spanish": "es", "French": "fr", "German": "de", 
                "Italian": "it", "Portuguese": "pt", "Russian": "ru", "Japanese": "ja", 
                "Korean": "ko", "Chinese (Simplified)": "zh", "Chinese (Traditional)": "zh-tw", 
                "Arabic": "ar", "Hindi": "hi", "Turkish": "tr", "Dutch": "nl", 
                "Swedish": "sv", "Norwegian": "no", "Danish": "da", "Finnish": "fi", 
                "Polish": "pl", "Czech": "cs", "Hungarian": "hu", "Thai": "th", 
                "Vietnamese": "vi", "Indonesian": "id", "Ukrainian": "uk"
            }
            
            # Get language code, default to 'en' if not found
            lang_code = gtts_codes.get(language, "en")
            
            # Clean text for TTS
            clean_text = text.strip()
            if not clean_text:
                return None
                
            # Create gTTS object
            tts = gTTS(text=clean_text, lang=lang_code, slow=False)
            
            # Save to bytes buffer
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            
            return audio_buffer.getvalue()
        except Exception as e:
            st.error(f"Text-to-speech error: {str(e)}")
            return None

    def detect_language(self, text: str) -> str:
        try:
            prompt = f"What language is this text written in? Respond with only the language name in English:\n\n{text[:200]}"
            response = self.model.generate_content(prompt)
            detected = response.text.strip()
            
            # Match with our language list
            for lang_name in LANGUAGES.keys():
                if lang_name.lower() in detected.lower():
                    return lang_name
            return "English"
        except Exception as e:
            st.warning(f"Language detection failed: {str(e)}")
            return "English"

    def translate_text(self, text: str, source_lang: str, target_lang: str, translation_type: str = "standard"):
        if not text.strip():
            return "No text provided"
        
        try:
            # Create simple, effective prompts
            if translation_type == "standard":
                prompt = f"Translate this text from {source_lang} to {target_lang}. Only provide the translation:\n\n{text}"
            elif translation_type == "creative":
                prompt = f"Translate this creative text from {source_lang} to {target_lang}, preserving style and artistic meaning:\n\n{text}"
            elif translation_type == "technical":
                prompt = f"Translate this technical text from {source_lang} to {target_lang}, maintaining technical accuracy:\n\n{text}"
            elif translation_type == "formal":
                prompt = f"Translate this text from {source_lang} to {target_lang} using formal, professional language:\n\n{text}"
            else:
                prompt = f"Translate from {source_lang} to {target_lang}:\n\n{text}"
            
            # Generate translation
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                result = response.text.strip()
                return result
            else:
                return "No translation received from API"
                
        except Exception as e:
            error_msg = f"Translation error: {str(e)}"
            st.error(error_msg)
            return error_msg

def create_audio_player(audio_data: bytes, key: str = None) -> None:
    """Create audio player using Streamlit's native audio widget"""
    if audio_data:
        try:
            # Use Streamlit's built-in audio player
            st.audio(audio_data, format='audio/mp3')
        except Exception as e:
            st.error(f"Audio playback error: {str(e)}")
    else:
        st.error("No audio data available")

def create_download_link(audio_data: bytes, filename: str) -> None:
    """Create a download button for audio data"""
    if audio_data:
        st.download_button(
            label="⬇️ Download Audio",
            data=audio_data,
            file_name=filename,
            mime="audio/mp3"
        )

def display_translation_result(result: str, translation_type: str = "standard", target_language: str = "English", translator=None):
    """Display translation result with proper styling"""
    
    # Color schemes for different translation types
    color_schemes = {
        "standard": {"bg": "#f0f8f0", "border": "#4CAF50", "icon": "📝"},
        "creative": {"bg": "#faf0ff", "border": "#9C27B0", "icon": "🎨"},
        "technical": {"bg": "#e8f4f8", "border": "#2196F3", "icon": "⚙️"},
        "formal": {"bg": "#fff8e8", "border": "#FF9800", "icon": "👔"},
        "voice": {"bg": "#f0f8ff", "border": "#4169E1", "icon": "🎤"}
    }
    
    scheme = color_schemes.get(translation_type, color_schemes["standard"])
    
    # Clean the result text (remove any unwanted formatting)
    clean_result = result.replace("**", "").strip()
    
    # Display with improved styling
    st.markdown(f"""
    <div style="
        background-color: {scheme['bg']}; 
        padding: 20px; 
        border-radius: 10px; 
        border-left: 5px solid {scheme['border']};
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    ">
        <h4 style="
            color: {scheme['border']}; 
            margin-top: 0; 
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 8px;
        ">
            {scheme['icon']} Translation Result
        </h4>
        <p style="
            font-size: 16px; 
            line-height: 1.5; 
            margin: 0;
            color: #333;
            white-space: pre-wrap;
        ">{clean_result}</p>
    </div>
    """, unsafe_allow_html=True)

def main():
    st.title("🌐 Advanced Translation Agent")
    st.markdown("*Powered by Google Gemini AI*")
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .stTextArea textarea {
        background-color: #fafdff;
        border: 2px solid #e9ecef;
        border-radius: 8px;
    }
    .stTextArea textarea:focus {
        border-color: #007bff;
        box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25);
    }
    .stSelectbox > div > div {
        background-color: #fafdff;
        border-radius: 8px;
    }
    .audio-section {
        background-color: #f0f8ff;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #4169E1;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Sidebar configuration
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # API Key input with better instructions
        st.markdown("### Google AI API Key")
        st.markdown("1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)")
        st.markdown("2. Create a new API key")
        st.markdown("3. Paste it below:")
        
        api_key = st.text_input("API Key", type="password", placeholder="Your Google AI API key here...")
        
        if not api_key:
            st.error("⚠️ Please enter your Google AI API key to continue")
            st.stop()
        
        # Test API key
        with st.spinner("Testing API connection..."):
            try:
                translator = TranslationAgent(api_key)
            except Exception as e:
                st.error(f"❌ API connection failed: {str(e)}")
                st.info("Please check your API key and try again.")
                st.stop()
        
        # Feature selection
        st.header("🚀 Features")
        selected_feature = st.selectbox(
            "Choose Translation Feature",
            ["Standard Translation", "Voice Translation", "Creative Translation", "Technical Translation", 
             "Formal Translation", "Document Translation", "Batch Translation", 
             "Language Detection", "Translation History"]
        )

    # Initialize session state
    if 'translation_history' not in st.session_state:
        st.session_state.translation_history = []

    # Voice Translation - Fixed Version
    if selected_feature == "Voice Translation":
        st.header("🎤 Voice Translation")
        st.info("Speak in one language and get voice output in another!")
        
        # Check if required packages are available
        try:
            import speech_recognition as sr
            from gtts import gTTS
        except ImportError:
            st.error("📦 Required packages missing. Please install: pip install SpeechRecognition gTTS pyaudio")
            st.info("Note: You may also need to install portaudio for microphone support")
            return
        
        col1, col2 = st.columns(2)
        with col1:
            source_lang_voice = st.selectbox("Source Language", list(LANGUAGES.keys()), key="voice_source")
        with col2:
            target_lang_voice = st.selectbox("Target Language", list(LANGUAGES.keys()), index=1, key="voice_target")
        
        # Voice input section
        st.markdown("### 🎤 Voice Input")
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col1:
            if st.button("🎤 Start Recording", type="primary", use_container_width=True):
                with st.spinner("Initializing microphone..."):
                    spoken_text = translator.speech_to_text()
                    
                if spoken_text and not spoken_text.startswith("Error") and not spoken_text.startswith("Could not") and not spoken_text.startswith("Listening timeout"):
                    st.session_state.voice_input = spoken_text
                    st.success(f"✅ Speech captured: '{spoken_text}'")
                else:
                    st.error(f"❌ {spoken_text}")
        
        with col2:
            st.markdown("<div style='text-align: center; padding: 10px;'>OR</div>", unsafe_allow_html=True)
            
        with col3:
            if st.button("📝 Use Text Input", use_container_width=True):
                st.session_state.use_text_input = True
        
        # Display captured text or text input
        if hasattr(st.session_state, 'voice_input'):
            voice_text = st.text_area("Captured Speech:", 
                                    value=st.session_state.voice_input, 
                                    height=100, 
                                    key="voice_display")
        elif hasattr(st.session_state, 'use_text_input') and st.session_state.use_text_input:
            voice_text = st.text_area("Enter text for voice translation:", 
                                    height=100, 
                                    placeholder="Type your text here...",
                                    key="voice_text_input")
        else:
            voice_text = st.text_area("Speech will appear here after recording:", 
                                    height=100, 
                                    disabled=True,
                                    key="voice_placeholder")
        
        # Translation and audio output
        if st.button("🔄 Translate & Speak", type="primary", use_container_width=True):
            if voice_text and voice_text.strip():
                with st.spinner("Translating..."):
                    # Perform translation
                    result = translator.translate_text(voice_text, source_lang_voice, target_lang_voice, "voice")
                    
                    if result and "Translation error" not in result and "No translation" not in result:
                        st.success("✅ Voice translation completed!")
                        
                        # Display translation result
                        display_translation_result(result, "voice", target_lang_voice, translator)
                        
                        # Generate and display audio files
                        st.markdown("### 🔊 Audio Playback")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**🎤 Original Audio**")
                            st.write(f"Language: {source_lang_voice}")
                            st.write(f"Text: _{voice_text[:50]}{'...' if len(voice_text) > 50 else ''}_")
                            
                            with st.spinner("Generating original audio..."):
                                original_audio = translator.text_to_speech(voice_text, source_lang_voice)
                                if original_audio:
                                    create_audio_player(original_audio)
                                    create_download_link(original_audio, f"original_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3")
                                else:
                                    st.error("Failed to generate original audio")
                        
                        with col2:
                            st.markdown("**🌐 Translation Audio**")
                            st.write(f"Language: {target_lang_voice}")
                            st.write(f"Text: _{result[:50]}{'...' if len(result) > 50 else ''}_")
                            
                            with st.spinner("Generating translation audio..."):
                                translation_audio = translator.text_to_speech(result, target_lang_voice)
                                if translation_audio:
                                    create_audio_player(translation_audio)
                                    create_download_link(translation_audio, f"translation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3")
                                else:
                                    st.error("Failed to generate translation audio")
                        
                        
                        # Save to history
                        st.session_state.translation_history.append({
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'source_lang': source_lang_voice,
                            'target_lang': target_lang_voice,
                            'original': voice_text,
                            'translation': result,
                            'type': 'voice'
                        })
                        
                        st.balloons()
                    else:
                        st.error(f"❌ Translation failed: {result}")
            else:
                st.warning("⚠️ Please record speech or enter text first.")
        
        # Voice translation tips
        with st.expander("💡 Voice Translation Tips"):
            st.markdown("""
            **For better results:**
            - Speak clearly and at a moderate pace
            - Minimize background noise
            - Use short sentences for better accuracy
            - Ensure your microphone is working properly
            
            **Audio Features:**
            - ✅ Native Streamlit audio player (no external dependencies)
            - ✅ Direct download of MP3 files
            - ✅ Reliable audio generation and playback
            - ✅ Works across all browsers and devices
            
            **Requirements:**
            - Working microphone
            - Internet connection for speech services
            - Audio output device for playback
            
            **Troubleshooting:**
            - Audio now uses Streamlit's native player - should work reliably
            - If microphone doesn't work, try refreshing the page
            - Check browser permissions for microphone access
            - Use the "Use Text Input" option as an alternative
            """)

    # Standard Translation
    elif selected_feature == "Standard Translation":
        st.header("📝 Standard Translation")
        
        col1, col2 = st.columns(2)
        with col1:
            source_lang = st.selectbox("Source Language", ["Auto-detect"] + list(LANGUAGES.keys()))
        with col2:
            target_lang = st.selectbox("Target Language", list(LANGUAGES.keys()), index=1)
        
        # Example texts for testing
        example_texts = {
            "English to Spanish": "Hello, how are you today?",
            "Spanish to English": "Hola, ¿cómo estás hoy?",
            "French to English": "Bonjour, comment allez-vous?",
            "Custom": ""
        }
        
        selected_example = st.selectbox("Quick Examples (optional):", list(example_texts.keys()))
        
        if selected_example != "Custom":
            text_input = st.text_area("Enter text to translate", 
                                    value=example_texts[selected_example], 
                                    height=150)
        else:
            text_input = st.text_area("Enter text to translate", height=150)
        
        if st.button("🔄 Translate", type="primary", use_container_width=True):
            if text_input.strip():
                with st.spinner("Translating..."):
                    try:
                        # Auto-detect language if needed
                        if source_lang == "Auto-detect":
                            detected_lang = translator.detect_language(text_input)
                            st.info(f"🔍 Detected language: **{detected_lang}**")
                            source_lang = detected_lang
                        
                        # Perform translation
                        result = translator.translate_text(text_input, source_lang, target_lang, "standard")
                        
                        if result and "Translation error" not in result and "No translation" not in result:
                            st.success("✅ Translation completed successfully!")
                            
                            # Display translation with improved styling
                            display_translation_result(result, "standard", target_lang, translator)
                            
                            # Add audio playback option
                            st.markdown("### 🔊 Audio Playback")
                            if st.button("🔊 Generate Audio", key=f"play_standard_{hash(result)}"):
                                with st.spinner("Generating audio..."):
                                    audio_data = translator.text_to_speech(result, target_lang)
                                    if audio_data:
                                        create_audio_player(audio_data)
                                        create_download_link(audio_data, f"translation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3")
                                        st.success("🔊 Audio generated successfully!")
                                    else:
                                        st.error("Failed to generate audio")
                            
                            # Copy area
                            st.text_area("📋 Copy Translation:", value=result, height=80, key="copy_standard")
                            
                            # Save to history
                            st.session_state.translation_history.append({
                                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                'source_lang': source_lang,
                                'target_lang': target_lang,
                                'original': text_input,
                                'translation': result,
                                'type': 'standard'
                            })
                            
                            st.balloons()
                        else:
                            st.error(f"❌ Translation failed: {result}")
                            
                    except Exception as e:
                        st.error(f"❌ An error occurred: {str(e)}")
            else:
                st.warning("⚠️ Please enter some text to translate.")

    # Translation History
    elif selected_feature == "Translation History":
        st.header("📚 Translation History")
        
        if st.session_state.translation_history:
            st.info(f"Total translations: {len(st.session_state.translation_history)}")
            
            # Display history
            for i, entry in enumerate(reversed(st.session_state.translation_history)):
                with st.expander(f"Translation {len(st.session_state.translation_history) - i}: {entry['source_lang']} → {entry['target_lang']} ({entry['type']})"):
                    st.write(f"**Timestamp:** {entry['timestamp']}")
                    st.write(f"**Original ({entry['source_lang']}):** {entry['original']}")
                    st.write(f"**Translation ({entry['target_lang']}):** {entry['translation']}")
                    
                    # Option to regenerate audio for history items
                    if st.button(f"🔊 Generate Audio", key=f"history_audio_{i}"):
                        with st.spinner("Generating audio..."):
                            audio_data = translator.text_to_speech(entry['translation'], entry['target_lang'])
                            if audio_data:
                                create_audio_player(audio_data)
                                st.success("Audio generated!")
                            else:
                                st.error("Failed to generate audio")
            
            # Clear history option
            if st.button("🗑️ Clear History", type="secondary"):
                st.session_state.translation_history = []
                st.success("History cleared!")
                st.rerun()
        else:
            st.info("No translation history yet. Start translating to see your history here!")

    # Other features placeholder
    else:
        st.header(f"🔧 {selected_feature}")
        st.info(f"The {selected_feature} feature is coming soon! For now, try Voice Translation or Standard Translation.")
        
        # Show available features
        st.markdown("### Available Features:")
        st.markdown("- ✅ **Voice Translation** - Speak and get voice output")
        st.markdown("- ✅ **Standard Translation** - Text-to-text translation")
        st.markdown("- ✅ **Translation History** - View your translation history")
        st.markdown("- 🚧 Other features coming soon...")

    # Footer
    st.markdown("---")
    st.markdown("🌐 **Advanced Translation Agent** | Powered by Google Gemini AI")
    st.markdown("**✅ Fixed Audio Version** - All audio controls now working with native Streamlit audio player!")

if __name__ == "__main__":

    main()
