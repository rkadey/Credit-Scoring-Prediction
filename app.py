# chat_component.py
import streamlit as st
import streamlit.components.v1 as components
import json
import base64
from dataclasses import dataclass
from typing import Optional

@dataclass
class ChatMessage:
    text: Optional[str] = None
    audio: Optional[bytes] = None

class ChatComponent:
    def __init__(self):
        # Initialize session state for messages
        if 'messages' not in st.session_state:
            st.session_state['messages'] = []
            
        self.html_content = '''
<!DOCTYPE html>
<html>
<head>
    <style>
        .chat-container {
            width: 100%;
            max-width: 800px;
            margin: 20px auto;
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        }

        .input-box {
            display: flex;
            align-items: center;
            padding: 10px;
            border: 1px solid #e1e1e1;
            border-radius: 12px;
            background: white;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }

        .message-input {
            flex-grow: 1;
            padding: 12px;
            border: none;
            outline: none;
            font-size: 16px;
            resize: none;
            min-height: 24px;
            max-height: 150px;
        }

        .button-group {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-left: 8px;
        }

        .icon-button {
            background: none;
            border: none;
            cursor: pointer;
            padding: 8px;
            border-radius: 50%;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .icon-button:hover {
            background-color: #f0f0f0;
        }

        .mic-button.recording {
            background-color: #ff45454d;
            animation: pulse 1.5s infinite;
        }

        .send-button {
            color: #2196F3;
        }

        .send-button:hover {
            background-color: #2196F31a;
        }

        .send-button:disabled {
            color: #ccc;
            cursor: not-allowed;
        }

        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="input-box">
            <textarea 
                class="message-input" 
                placeholder="Type your message..."
                rows="1"
            ></textarea>
            <div class="button-group">
                <button class="icon-button mic-button" title="Record audio">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                        <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                        <line x1="12" y1="19" x2="12" y2="23"/>
                        <line x1="8" y1="23" x2="16" y2="23"/>
                    </svg>
                </button>
                <button class="icon-button send-button" title="Send message">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="22" y1="2" x2="11" y2="13"/>
                        <polygon points="22 2 15 22 11 13 2 9 22 2"/>
                    </svg>
                </button>
            </div>
        </div>
    </div>

    <script>
        const messageInput = document.querySelector('.message-input');
        const micButton = document.querySelector('.mic-button');
        const sendButton = document.querySelector('.send-button');
        let mediaRecorder;
        let audioChunks = [];
        let isRecording = false;

        // Function to send data to Streamlit
        function sendToStreamlit(data) {
            window.parent.postMessage({
                type: 'streamlit:message',
                data: data
            }, '*');
        }

        // Auto-resize textarea
        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });

        // Mic button functionality
        micButton.addEventListener('click', async () => {
            if (!isRecording) {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    mediaRecorder = new MediaRecorder(stream);
                    
                    mediaRecorder.ondataavailable = (event) => {
                        audioChunks.push(event.data);
                    };

                    mediaRecorder.onstop = async () => {
                        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                        audioChunks = [];
                        
                        // Convert blob to base64
                        const reader = new FileReader();
                        reader.readAsDataURL(audioBlob);
                        reader.onloadend = () => {
                            const base64Audio = reader.result.split(',')[1];
                            sendToStreamlit({
                                type: 'audio',
                                audio: base64Audio
                            });
                        };
                    };

                    mediaRecorder.start();
                    isRecording = true;
                    micButton.classList.add('recording');
                } catch (err) {
                    console.error('Error accessing microphone:', err);
                    sendToStreamlit({
                        type: 'error',
                        error: 'Microphone access denied'
                    });
                }
            } else {
                mediaRecorder.stop();
                isRecording = false;
                micButton.classList.remove('recording');
            }
        });

        // Send button functionality
        sendButton.addEventListener('click', () => {
            const message = messageInput.value.trim();
            if (message) {
                sendToStreamlit({
                    type: 'text',
                    message: message
                });
                messageInput.value = '';
                messageInput.style.height = 'auto';
            }
        });

        // Handle Enter key
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendButton.click();
            }
        });
    </script>
</body>
</html>
'''

    def __call__(self):
        # Render the component
        components.html(
            self.html_content,
            height=100,
        )

        # Handle component messages using session state
        if 'new_message' in st.session_state:
            message_data = st.session_state.new_message
            del st.session_state.new_message  # Clear the message after processing
            
            if message_data['type'] == 'text':
                return ChatMessage(text=message_data['message'])
            elif message_data['type'] == 'audio':
                audio_bytes = base64.b64decode(message_data['audio'])
                return ChatMessage(audio=audio_bytes)
            elif message_data['type'] == 'error':
                st.error(f"Error: {message_data['error']}")
        
        return None

def main():
    st.title("Chat Application")

    # Initialize the chat component
    chat_component = ChatComponent()

    # Display existing messages
    for msg in st.session_state.messages:
        if msg.text:
            st.write(f"Message: {msg.text}")
        if msg.audio:
            st.audio(msg.audio)

    # Get new messages
    new_message = chat_component()
    if new_message:
        st.session_state.messages.append(new_message)
        st.experimental_rerun()

if __name__ == "__main__":
    main()