from google.cloud import speech
import google.auth

def format_timedelta(td):
    if td is None:
        return "00:00:00,000"  # Handle None case, though it shouldn't happen

    total_seconds = td.seconds + td.nanos / 1e9  # Convert to total seconds
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    milliseconds = int((total_seconds % 1) * 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

def transcribe_with_word_time_offsets(speech_file, words_per_group=5):
    """Transcribe the given audio file synchronously and output the word time
    offsets, grouping words into phrases.  No sequence numbers in the SRT."""
    credentials, project = google.auth.load_credentials_from_file("./TTS_key.json")
    client = speech.SpeechClient(credentials=credentials)

    with open(speech_file, "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.MP3,  # Adjust if needed
        sample_rate_hertz=16000,  # Adjust if needed
        language_code="en-US",
        enable_word_time_offsets=True,
    )

    response = client.recognize(config=config, audio=audio)

    srt_entries = []

    for result in response.results:
        alternative = result.alternatives[0]
        words = alternative.words
        num_words = len(words)

        for i in range(0, num_words, words_per_group):
            group = words[i:i + words_per_group]
            phrase = " ".join(word_info.word for word_info in group)

            start_time = group[0].start_time
            end_time = group[-1].end_time

            start_str = format_timedelta(start_time)
            end_str = format_timedelta(end_time)

            srt_entry = f"{start_str} --> {end_str}\n{phrase}\n\n"  # No sequence number
            srt_entries.append(srt_entry)

    # Write all SRT entries to the file at once
    with open("timing.srt", "w") as file:
        file.writelines(srt_entries)

    print("Transcript:", alternative.transcript)  # Print the entire transcript
    print("SRT file created: timing.srt")

if __name__ == "__main__":
    transcribe_with_word_time_offsets("speech.mp3", words_per_group=2)