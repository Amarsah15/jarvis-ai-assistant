import speech_recognition as sr
import os
import webbrowser
from openai import OpenAI
import datetime
import random
import pyttsx3
import time
import sys

# Import API key from config file
try:
    from config import apikey
except ImportError:
    print("Error: Please create a 'config.py' file with your Gemini API key.")
    print("Example: apikey = 'YOUR_GEMINI_API_KEY_HERE'")
    sys.exit(1)

# Initialize OpenAI client with Gemini API
client = OpenAI(
    api_key=apikey,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# Global variable to store chat history
chatStr = ""

# Function to convert text to speech
def say(text):
    # This function takes text as input and speaks it using pyttsx3 library

    print(f"Jarvis: {text}")
    
    try:
        # Initialize text-to-speech engine
        engine = pyttsx3.init('sapi5')
        voices = engine.getProperty('voices')
        
        # Set voice properties
        if len(voices) > 0:
            engine.setProperty('voice', voices[0].id)
        
        engine.setProperty('rate', 180)  # Speed of speech
        engine.setProperty('volume', 1.0)  # Volume level
        
        # Speak the text
        engine.say(text)
        engine.runAndWait()
        engine.stop()

    except Exception as e:
        print(f"Error in text-to-speech: {e}")
    

# Function to save chat history to a file
def save_chat_history(chat_content):
    # Saves the conversation history to a text file with timestamp

    try:
        # Create directory if it doesn't exist
        if not os.path.exists("ChatHistory"):
            os.mkdir("ChatHistory")
        
        # Generate filename with timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"ChatHistory/chat_{timestamp}.txt"
        
        # Write chat content to file
        with open(filename, "w", encoding="utf-8") as f:
            f.write(chat_content)
        
    except Exception as e:
        print(f"Error saving chat history: {e}")

# Function to chat with Gemini AI
def chat(query):
    """
    This function sends user query to Gemini AI and returns the response
    It maintains conversation context using chat history
    """
    global chatStr
    
    # Add user query to chat history
    chatStr += f"User: {query}\nJarvis: "
    
    try:
        # Call Gemini API using OpenAI client
        response = client.chat.completions.create(
            model="gemini-2.0-flash-exp",
            messages=[
                {"role": "system", "content": "You are Jarvis, a helpful AI assistant. Provide concise and clear responses."},
                {"role": "user", "content": chatStr}
            ],
            temperature=0.7,
            max_tokens=300,
        )
        
        # Extract answer from API response
        answer = response.choices[0].message.content.strip()
        say(answer)
        
        # Update chat history with AI response
        chatStr += answer + "\n"
        save_chat_history(chatStr)
        
        return answer
        
    except Exception as e:
        say("Sorry sir, I'm having trouble connecting to Gemini right now.")
        print(f"Error in chat function: {e}")
        return ""

# Function to generate AI content and save to file
def ai(prompt):
    """
    Generates content using Gemini AI based on user prompt
    Saves long content to files and speaks short answers
    """
    try:
        # Extract actual prompt from command
        if "artificial intelligence" in prompt.lower():
            actual_prompt = prompt.lower().split("artificial intelligence", 1)[1].strip()
        else:
            actual_prompt = prompt
        
        if not actual_prompt:
            say("Please specify what you'd like me to generate.")
            return
        
        # Determine if it's a short question or long content request
        short_triggers = ["who is", "what is", "when is", "where is", "why is", "how is",
                         "who are", "what are", "define", "meaning of", "explain"]
        
        is_short_answer = any(trigger in actual_prompt.lower() for trigger in short_triggers)
        
        long_triggers = ["write", "create", "compose", "draft", "generate", "make", 
                        "email", "letter", "essay", "article", "story", "poem", "code",
                        "script", "list of", "paragraph"]
        
        is_long_content = any(trigger in actual_prompt.lower() for trigger in long_triggers)
        
        # Generate content using Gemini API
        response = client.chat.completions.create(
            model="gemini-2.0-flash-exp",
            messages=[
                {"role": "system", "content": "You are an intelligent content generator. Create detailed content based on user requests."},
                {"role": "user", "content": actual_prompt}
            ],
            temperature=0.8,
            max_tokens=1000 if is_long_content else 200
        )
        
        content = response.choices[0].message.content
        
        # Prepare output with metadata
        output_text = f"Gemini AI Response\n"
        output_text += f"Prompt: {actual_prompt}\n"
        output_text += f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        output_text += "=" * 70 + "\n\n"
        output_text += content
        
        # Create output directory if not exists
        if not os.path.exists("GeminiOutput"):
            os.mkdir("GeminiOutput")
        
        # Create safe filename from prompt
        safe_name = "".join(c for c in actual_prompt[:30] if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"GeminiOutput/{safe_name}_{random.randint(1000,9999)}.txt"
        
        # Save to file
        with open(filename, "w", encoding="utf-8") as f:
            f.write(output_text)
        
        # Speak answer for short questions, confirm save for long content
        if is_short_answer:
            say(content)
        else:
            say(f"Content generated and saved successfully sir.")
        
    except Exception as e:
        say("Sorry sir, I couldn't generate that content right now.")
        print(f"Error in AI function: {e}")

# Function to listen and recognize speech
def takeCommand():
    """
    Listens to microphone input and converts speech to text using Google Speech Recognition
    Returns the recognized text as string
    """
    r = sr.Recognizer()
    
    # Configure recognition parameters
    # threshold = 4000 as it works well in most environments
    # as we want to capture longer phrases, we set pause_threshold higher
    r.energy_threshold = 4000
    r.dynamic_energy_threshold = True
    r.pause_threshold = 0.8
    
    try:
        with sr.Microphone() as source:
            print("Listening...")
            # Adjust for ambient noise
            r.adjust_for_ambient_noise(source, duration=1)
            # Listen for audio input
            audio = r.listen(source, timeout=10, phrase_time_limit=10)
            
        print("Recognizing...")
        # Use Google Speech Recognition to convert audio to text
        query = r.recognize_google(audio, language="en-in")
        print(f"You said: {query}")
        
        return query
    
    except sr.RequestError:
        say("Sorry, the speech service is not available right now.")
        return ""
    
    except Exception as e:
        return ""

# Function to open websites
def open_website(site_name, url):
    # Opens the specified website in the default web browser
    say(f"Opening {site_name}, sir...")
    # Open the website using webbrowser module
    # webbrowser is an inbuilt module to open URLs in browser
    webbrowser.open(url)

# Function to tell current time
def tell_time():
    # Function to get and speak current time
    now = datetime.datetime.now()
    hour = now.strftime("%I")
    minute = now.strftime("%M")
    # period means AM/PM
    period = now.strftime("%p")
    
    say(f"Sir, the time is {hour} {minute} {period}")

# Function to open applications
def open_application(app_name, command):
    # Opens system applications using os.system command

    try:
        say(f"Opening {app_name}, sir...")
        os.system(command)
    except Exception as e:
        say(f"Sorry, I couldn't open {app_name}")
        print(f"Error opening {app_name}: {e}")

# Main function - Entry point of the program
def main():
    print("\n" + "="*60)
    print("JARVIS - Voice Controlled AI Assistant")
    print("="*60)
    print("\nAvailable Commands:")
    print("  • 'Open YouTube/Google/Wikipedia' - Open websites")
    print("  • 'What is the time?' - Get current time")
    print("  • 'Open Notepad/Calculator' - Open applications")
    print("  • 'Using artificial intelligence write...' - Generate AI content")
    print("  • 'Reset chat' - Clear conversation history")
    print("  • 'Jarvis quit/exit/goodbye' - Exit program")
    print("="*60 + "\n")
    
    say("Hello sir, Jarvis is online and ready to assist you!")
    
    # Main program loop
    while True:
        query = takeCommand().lower()
        
        # Skip if no input received
        if not query or query.strip() == "":
            continue
        
        # Dictionary of websites with their URLs
        websites = [
            ("youtube", "https://www.youtube.com"),
            ("google", "https://www.google.com"),
            ("wikipedia", "https://www.wikipedia.org"),
            ("github", "https://www.github.com"),
            ("stack overflow", "https://stackoverflow.com")
        ]
        
        # Check if command is to open a website
        website_opened = False
        for site_name, url in websites:
            if f"open {site_name}" in query:
                open_website(site_name, url)
                website_opened = True
                break
        
        if website_opened:
            continue
        
        # Handle time query
        if "time" in query and ("what" in query or "tell" in query or "the" in query):
            tell_time()
        
        # Handle application opening commands
        elif "open notepad" in query:
            open_application("Notepad", "notepad.exe")
        
        elif "open calculator" in query:
            open_application("Calculator", "calc.exe")
        
        elif "open paint" in query:
            open_application("Paint", "mspaint.exe")
        
        elif "open file explorer" in query or "open explorer" in query:
            open_application("File Explorer", "explorer.exe")
        
        # Handle AI content generation
        elif "using artificial intelligence" in query or "generate using ai" in query:
            ai(prompt=query)
        
        # Reset chat history
        elif "reset chat" in query or "clear chat" in query:
            global chatStr
            chatStr = ""
            say("Chat history has been cleared, sir.")
        
        # Exit commands
        elif any(phrase in query for phrase in ["jarvis quit", "exit", "goodbye", "bye jarvis"]):
            say("Goodbye sir, have a wonderful day!")
            break
        
        # Help command
        elif "help" in query or "what can you do" in query:
            say("I can open websites, tell you the time, open applications, generate content with AI, and chat with you. Just ask!")
        
        # Default: Chat with Gemini AI
        else:
            chat(query)
        
        # Small delay to prevent overwhelming the system
        time.sleep(0.3)

# Program entry point
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
        say("Shutting down, goodbye sir!")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        say("An unexpected error occurred. Shutting down.")
    finally:
        print("\nJarvis AI Assistant terminated.\n")