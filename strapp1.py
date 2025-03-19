import streamlit as st
import json
import os
from dotenv import load_dotenv
import openai
from datetime import datetime
import re

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai.api_key = OPENAI_API_KEY

# Chat with ChatGPT as your sensei
def chat_with_sensei(topic, message):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # Use gpt-3.5-turbo for free tier
        messages=[
            {"role": "system", "content": f"You are my Japanese sensei. We're discussing {topic}. Use Japanese and English, and introduce new vocabulary in the format 'Japanese (romaji) - English' (e.g., きゅうり (kyuuri) - cucumber)."},
            {"role": "user", "content": message}
        ],
        max_tokens=150
    )
    return response.choices[0].message.content

# Save vocabulary
def save_vocab(word, meaning):
    vocab_file = "vocab.json"
    vocab_data = {}
    if os.path.exists(vocab_file):
        with open(vocab_file, "r") as f:
            vocab_data = json.load(f)
    vocab_data[word] = meaning
    with open(vocab_file, "w") as f:
        json.dump(vocab_data, f, ensure_ascii=False, indent=4)

# Save chat history
def save_chat_history(topic, user_message, sensei_response):
    history_file = "chat_history.json"
    history_data = []
    if os.path.exists(history_file):
        try:
            with open(history_file, "r") as f:
                content = f.read().strip()
                if content:
                    f.seek(0)
                    history_data = json.load(f)
        except json.JSONDecodeError:
            history_data = []
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "topic": topic,
        "user_message": user_message,
        "sensei_response": sensei_response
    }
    history_data.append(entry)
    with open(history_file, "w") as f:
        json.dump(history_data, f, ensure_ascii=False, indent=4)

# Save to flashcards
def save_to_flashcards(word, meaning):
    flashcards_file = "flashcards.json"
    flashcards_data = {}
    if os.path.exists(flashcards_file):
        with open(flashcards_file, "r") as f:
            flashcards_data = json.load(f)
    flashcards_data[word] = meaning
    with open(flashcards_file, "w") as f:
        json.dump(flashcards_data, f, ensure_ascii=False, indent=4)

# Improved vocab detection
def detect_vocab(text):
    pattern = r'([ぁ-んァ-ン一-龯]+)\s*\(([\w-]+)\)\s*-\s*([\w\s]+)'
    matches = re.findall(pattern, text, re.UNICODE)
    return [(match[0], match[2]) for match in matches]

# Chat Interface
def chat_interface():
    st.header("Chat with Sensei")
    
    # Topic input (persists across reruns)
    if "topic" not in st.session_state:
        st.session_state.topic = ""
    topic = st.text_input("Enter the topic:", value=st.session_state.topic, key="chat_topic")
    st.session_state.topic = topic  # Save topic to session state
    
    # Initialize chat history in session state
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    
    # Chat display area
    chat_container = st.container()
    with chat_container:
        for sender, msg in st.session_state.chat_messages:
            if sender == "You":
                st.markdown(f"<div style='text-align: right; background-color: #e1f5fe; padding: 10px; margin: 5px; border-radius: 10px;'>{sender}: {msg}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='text-align: left; background-color: #f0f0f0; padding: 10px; margin: 5px; border-radius: 10px;'>{sender}: {msg}</div>", unsafe_allow_html=True)
    
    # Create a callback to handle form submission
    def handle_form_submit():
        if st.session_state.user_message and topic:
            user_message = st.session_state.user_message
            
            # Add user message to chat
            st.session_state.chat_messages.append(("You", user_message))
            
            # Get Sensei response
            response = chat_with_sensei(topic, user_message)
            st.session_state.chat_messages.append(("Sensei", response))
            
            # Save chat history
            save_chat_history(topic, user_message, response)
            
            # Auto-detect vocab from user message and Sensei response
            for text in [user_message, response]:
                vocab_list = detect_vocab(text)
                for word, meaning in vocab_list:
                    save_vocab(word, meaning)
                    st.session_state.vocab_saved = True
                    st.session_state.last_saved_words.append((word, meaning))
            
            # Clear input after sending
            st.session_state.user_message = ""
    
    # Initialize session state for vocab saving feedback
    if "vocab_saved" not in st.session_state:
        st.session_state.vocab_saved = False
    if "last_saved_words" not in st.session_state:
        st.session_state.last_saved_words = []
    
    # Create a form for the message input
    with st.form(key="message_form", clear_on_submit=True):
        # Multi-line message input
        st.text_area(
            "You:", 
            key="user_message", 
            height=100,
            help="Press Enter for new line, Ctrl+Enter to send"
        )
        
        # Submit button
        submit_button = st.form_submit_button(label="Send", on_click=handle_form_submit)
    
    # JavaScript for Ctrl+Enter to submit form
    st.components.v1.html("""
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(function() {
                const textareas = window.parent.document.querySelectorAll('textarea');
                textareas.forEach(function(textarea) {
                    textarea.addEventListener('keydown', function(e) {
                        if (e.ctrlKey && e.key === 'Enter') {
                            e.preventDefault();
                            const form = textarea.closest('form');
                            if (form) {
                                const submitButton = form.querySelector('button[type="submit"]');
                                if (submitButton) {
                                    submitButton.click();
                                }
                            }
                        }
                    });
                });
            }, 1000); // Wait for components to load
        });
    </script>
    """, height=0)
    
    # Display vocab saving feedback
    if st.session_state.vocab_saved and st.session_state.last_saved_words:
        with st.container():
            for word, meaning in st.session_state.last_saved_words:
                st.success(f"Auto-saved vocab: {word} - {meaning}")
            # Reset after displaying
            st.session_state.vocab_saved = False
            st.session_state.last_saved_words = []

# Studying Interface (unchanged)
def studying_interface():
    st.header("Study Zone")
    
    # Review Chat History
    st.subheader("Chat History")
    history_file = "chat_history.json"
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            history_data = json.load(f)
        for entry in history_data:
            st.write(f"[{entry['timestamp']}] **Topic:** {entry['topic']}")
            st.write(f"You: {entry['user_message']}")
            st.write(f"Sensei: {entry['sensei_response']}")
            st.write("---")
    else:
        st.write("No chat history yet.")
    
    # Review Vocabulary
    st.subheader("Vocabulary")
    vocab_file = "vocab.json"
    if os.path.exists(vocab_file):
        with open(vocab_file, "r") as f:
            vocab_data = json.load(f)
        for word, meaning in vocab_data.items():
            st.write(f"{word}: {meaning}")
            if st.button(f"Add '{word}' to Flashcards", key=f"flash_{word}"):
                save_to_flashcards(word, meaning)
                st.success(f"Added {word} to flashcards!")
    else:
        st.write("No vocabulary saved yet.")
    
    # Flashcards
    st.subheader("Flashcards")
    flashcards_file = "flashcards.json"
    if os.path.exists(flashcards_file):
        with open(flashcards_file, "r") as f:
            flashcards_data = json.load(f)
        for word, meaning in flashcards_data.items():
            with st.expander(f"{word}"):
                st.write(f"Meaning: {meaning}")
    else:
        st.write("No flashcards yet.")

# Main App
def main():
    st.title("Nihongo ChatSensei")
    if not OPENAI_API_KEY:
        st.error("OPENAI_API_KEY not set. Please configure it.")
        return
    
    # Sidebar for navigation
    page = st.sidebar.selectbox("Choose Interface", ["Chat", "Study"])
    
    if page == "Chat":
        chat_interface()
    elif page == "Study":
        studying_interface()

if __name__ == "__main__":
    main()