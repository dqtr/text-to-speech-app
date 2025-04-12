import pyttsx3
import os
import uuid  # To generate unique filenames
from flask import Flask, render_template, request, send_from_directory, url_for, redirect

# --- Configuration ---
AUDIO_FOLDER = 'audio'  # Folder to save generated audio files
ALLOWED_EXTENSIONS = {'mp3', 'wav'} # pyttsx3 typically saves as mp3 or others depending on driver

# --- Initialize pyttsx3 Engine ---
try:
    engine = pyttsx3.init()
    # Attempt to get voices immediately to catch potential init errors
    voices_data = engine.getProperty('voices')
    if not voices_data:
        print("Warning: No pyttsx3 voices found. TTS might not work.")
        print("Ensure you have a TTS engine installed (e.g., eSpeak on Linux, SAPI5 on Windows).")
    engine.stop() # Stop engine for now, will re-init per request if needed
except Exception as e:
    print(f"Error initializing pyttsx3 engine: {e}")
    print("Text-to-Speech functionality will likely fail.")
    print("Ensure a compatible TTS engine (SAPI5, NSSpeech, eSpeak) is installed and functional.")
    engine = None # Set engine to None if init fails
    voices_data = []

# --- Helper Function to Guess Gender (Very Basic) ---
def guess_gender(voice_name):
    name_lower = voice_name.lower()
    if 'female' in name_lower or 'zira' in name_lower or 'hazel' in name_lower or 'eva' in name_lower:
        return "Female"
    if 'male' in name_lower or 'david' in name_lower or 'mark' in name_lower:
        return "Male"
    return "Unknown" # Default if no common keyword is found

# --- Prepare Voice List for Template ---
available_voices = []
for voice in voices_data:
    # Sometimes voice.languages is a list, sometimes not. Handle potential errors.
    try:
        lang = voice.languages[0] if voice.languages else 'N/A'
    except (AttributeError, IndexError):
        lang = 'N/A' # Fallback if languages attribute is missing or empty

    available_voices.append({
        'id': voice.id,
        'name': voice.name,
        'lang': lang,
        'gender_guess': guess_gender(voice.name) # Add our basic gender guess
    })

# --- Initialize Flask App ---
app = Flask(__name__)
app.config['AUDIO_FOLDER'] = os.path.abspath(AUDIO_FOLDER)

# --- Ensure Audio Directory Exists ---
if not os.path.exists(app.config['AUDIO_FOLDER']):
    os.makedirs(app.config['AUDIO_FOLDER'])
    print(f"Created audio directory: {app.config['AUDIO_FOLDER']}")

# --- Routes ---
@app.route('/')
def index():
    """Renders the main page with the form."""
    if engine is None:
         return render_template('index.html', voices=[], error="TTS Engine failed to initialize. Please check installation.")
    return render_template('index.html', voices=available_voices)

@app.route('/synthesize', methods=['POST'])
def synthesize():
    """Handles form submission, generates speech, and provides download."""
    if engine is None:
         # Redirect back with error if engine isn't working
         return render_template('index.html', voices=[], error="TTS Engine is not available.")

    text = request.form.get('text', '').strip()
    voice_id = request.form.get('voice')

    if not text:
        return render_template('index.html', voices=available_voices, error="Text cannot be empty.", selected_voice_id=voice_id)

    if not voice_id:
         return render_template('index.html', voices=available_voices, error="Please select a voice.", text_input=text)

    # Generate a unique filename
    # Note: pyttsx3 might force specific extensions depending on the driver
    # '.mp3' is common, but it could be '.wav' or others. Let's try mp3 first.
    filename = f"speech_{uuid.uuid4()}.mp3"
    filepath = os.path.join(app.config['AUDIO_FOLDER'], filename)

    try:
        # Re-initialize engine for the request (safer for potential concurrency issues)
        # Though pyttsx3 is generally NOT thread-safe, this simple app might be okay
        # For production, use a task queue (Celery)
        tts_engine = pyttsx3.init()
        tts_engine.setProperty('voice', voice_id)

        # Adjust rate and volume if desired
        # tts_engine.setProperty('rate', 150)  # Speed percent (can go over 100)
        # tts_engine.setProperty('volume', 0.9) # Volume 0-1

        print(f"Synthesizing speech with voice: {voice_id}")
        print(f"Saving to: {filepath}")

        tts_engine.save_to_file(text, filepath)
        tts_engine.runAndWait()
        tts_engine.stop() # Clean up the engine instance

        # Check if file was actually created (runAndWait might fail silently)
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
             print(f"Error: File not created or empty after runAndWait: {filepath}")
             raise RuntimeError("TTS synthesis failed to produce an audio file.")

        print(f"File saved successfully: {filepath}")

        # Render the template again, showing the download link
        return render_template('index.html',
                               voices=available_voices,
                               audio_filename=filename,
                               text_input=text,
                               selected_voice_id=voice_id)

    except Exception as e:
        print(f"Error during TTS synthesis or saving: {e}")
        # Clean up potentially failed file
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass # Ignore removal error if it happens
        return render_template('index.html',
                               voices=available_voices,
                               error=f"Failed to generate speech: {e}",
                               text_input=text,
                               selected_voice_id=voice_id)

@app.route('/audio/<filename>')
def download_file(filename):
    """Serves the generated audio file for download or playback."""
    print(f"Serving file: {filename} from {app.config['AUDIO_FOLDER']}")
    try:
        return send_from_directory(app.config['AUDIO_FOLDER'], filename, as_attachment=False) # False for playback in browser
        # Use as_attachment=True if you want to force download immediately
    except FileNotFoundError:
         from flask import abort
         abort(404, description="Resource not found")


# --- Run the App ---
if __name__ == '__main__':
    # Note: Flask's default development server is single-threaded.
    # pyttsx3 might block while speaking if not saved to file first.
    # For production, use a proper WSGI server (like Gunicorn or Waitress).
    # Example using Waitress (install with `pip install waitress`):
    # waitress-serve --host 0.0.0.0 --port 5000 app:app
    print("Starting Flask development server...")
    print(f"Audio files will be saved in: {app.config['AUDIO_FOLDER']}")
    print(f"Available Voices: {[v['name'] for v in available_voices]}")
    app.run(debug=True) # debug=True is helpful for development, disable for production