from google.cloud import texttospeech
import google.auth
import os
def synthesize_text_from_file(input_file, output_filename="output.mp3", voice_name="en-US-Chirp3-HD-Charon"):
    """Synthesizes speech from the text in the input file."""

    try:
        credentials, project = google.auth.load_credentials_from_file("./TTS_key.json")
        client = texttospeech.TextToSpeechClient(credentials=credentials)
    except Exception as e:
        print(f"Error loading credentials: {e}")
        return

    try:
        with open(input_file, "r") as f:
            text = f.read()
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        return
    except Exception as e:
        print(f"Error reading input file: {e}")
        return

    input_text = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name=voice_name,
        ssml_gender=texttospeech.SsmlVoiceGender.MALE,  # Adjust as needed
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    try:
        response = client.synthesize_speech(
            request={"input": input_text, "voice": voice, "audio_config": audio_config}
        )
    except Exception as e:
        print(f"Error synthesizing speech: {e}")
        return

    try:
        with open(output_filename, "wb") as out:
            out.write(response.audio_content)
            print(f'Audio content written to file "{output_filename}"')
    except Exception as e:
        print(f"Error writing audio to file: {e}")
        return


if __name__ == "__main__":
    input_file = "input_text.txt"  # Replace with your text file
    output_file = "speech.mp3"

    # Create a sample text file if it doesn't exist
    if not os.path.exists(input_file):
        with open(input_file, "w") as f:
            f.write("Hello, this is a demonstration of text to speech from a file.")

    synthesize_text_from_file(input_file, output_file)