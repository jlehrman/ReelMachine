from google.cloud import speech
import google.auth
import difflib
from datetime import timedelta

# === CONFIGURATION ===
SCRIPT_FILE = "story.txt"              # Your script text file
SRT_OUTPUT = "timing.srt"
LANGUAGE_CODE = "en-US"
SAMPLE_RATE = 16000                         # Adjust to match your audio file
WORDS_PER_GROUP = 3                         # Default group size, can be adjusted in function call

def format_srt_time(seconds):
    if seconds is None:
        return "00:00:00,000"
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    millis = int((td.total_seconds() - total_seconds) * 1000)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"

def load_script_words(script_path):
    with open(script_path, 'r', encoding="utf-8") as f:
        script = f.read()
    # Split into words (preserving original capitalization)
    original_words = [w.strip() for w in script.split()]
    # Create a lower-cased version for matching
    lower_words = [w.lower() for w in original_words]
    return original_words, lower_words

def interpolate_timestamps(prev_end, next_start, count):
    """
    Evenly distribute timestamps between prev_end and next_start.
    Handles cases where prev_end or next_start are None, or gap is not positive.
    """
    if prev_end is None:
        prev_end = 0.0  # Start from the beginning if no previous timestamp
    if next_start is None:
        next_start = prev_end + 1.0 * count  # Estimate end time if no next timestamp

    total_gap = next_start - prev_end
    if total_gap <= 0:
        interval = 0.1  # Small interval if gap is not positive to avoid zero division
        timestamps = [(prev_end + interval * i, prev_end + interval * (i + 1)) for i in range(count)]
        return timestamps

    interval = total_gap / (count + 1)
    timestamps = []
    for i in range(1, count + 1):
        start = prev_end + interval * i
        end = prev_end + interval * (i + 1)
        timestamps.append((start, end))
    return timestamps

def align_to_script(transcribed_words, original_script, lower_script):
    # Use lowercased transcribed words for matching
    transcribed_only = [word.lower() for word, _, _ in transcribed_words]
    matcher = difflib.SequenceMatcher(None, transcribed_only, lower_script)
    aligned = []
    last_known_end = 0.0  # Initialize to start at time 0

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                # Use original script word to preserve capitalization
                orig_word = original_script[j1 + k]
                _, start, end = transcribed_words[i1 + k]
                aligned.append((orig_word, start, end))
                last_known_end = end
        elif tag == "replace":
            # Pair up as many words as possible
            common = min(i2 - i1, j2 - j1)
            for k in range(common):
                orig_word = original_script[j1 + k]
                _, start, end = transcribed_words[i1 + k]
                aligned.append((orig_word, start, end))
                last_known_end = end
            # For extra words in the script, interpolate their timestamps
            if (j2 - j1) > common:
                insert_count = (j2 - j1) - common
                if (i1 + common) < len(transcribed_words):
                    next_start = transcribed_words[i1 + common][1]
                else:
                    next_start = None
                interpolated = interpolate_timestamps(last_known_end, next_start, insert_count)
                for idx in range(insert_count):
                    orig_word = original_script[j1 + common + idx]
                    start, end = interpolated[idx]
                    aligned.append((orig_word, start, end))
                    last_known_end = end
        elif tag == "insert":
            # Words in the script not found in the transcript.
            insert_count = j2 - j1
            if i2 < len(transcribed_words):
                next_start = transcribed_words[i2][1]
            else:
                next_start = None
            interpolated = interpolate_timestamps(last_known_end, next_start, insert_count)
            for idx in range(insert_count):
                orig_word = original_script[j1 + idx]
                start, end = interpolated[idx]
                aligned.append((orig_word, start, end))
                last_known_end = end
        elif tag == "delete":
            # Skip extra words in the transcript that aren't in the script.
            for k in range(i2 - i1):
                _, _, end = transcribed_words[i1 + k]
                last_known_end = max(last_known_end, end)
    return aligned

def group_aligned_words(aligned, group_size=WORDS_PER_GROUP):
    """Group aligned words into blocks."""
    blocks = []
    for i in range(0, len(aligned), group_size):
        group = aligned[i:i+group_size]
        if group:
            group_start = group[0][1]
            group_end = group[-1][2]
            # Join using the original capitalized words
            group_text = " ".join(word for word, _, _ in group)
            blocks.append((group_text, group_start, group_end))
    return blocks

def transcribe_with_alignment(speech_file, script_file, words_per_group=WORDS_PER_GROUP):
    credentials, project = google.auth.load_credentials_from_file("./TTS_key.json")
    client = speech.SpeechClient(credentials=credentials)

    with open(speech_file, "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.MP3,
        sample_rate_hertz=SAMPLE_RATE,
        language_code=LANGUAGE_CODE,
        enable_word_time_offsets=True,
    )

    response = client.recognize(config=config, audio=audio)
    transcribed_words_raw = []

    for result in response.results:
        alternative = result.alternatives[0]
        for word_info in alternative.words:
            word = word_info.word.strip()
            start = word_info.start_time.total_seconds()
            end = word_info.end_time.total_seconds()
            transcribed_words_raw.append((word, start, end))

    # Load both original and lowercased script words
    original_script, lower_script = load_script_words(script_file)
    aligned_words = align_to_script(transcribed_words_raw, original_script, lower_script)

    srt_entries = []
    blocks = group_aligned_words(aligned_words, words_per_group)  # Group aligned words

    for index, (text, start, end) in enumerate(blocks, start=1):
        start_str = format_srt_time(start)
        end_str = format_srt_time(end)
        srt_entry = f"{start_str} --> {end_str}\n{text}\n\n"
        srt_entries.append(srt_entry)

    with open(SRT_OUTPUT, "w", encoding="utf-8") as file:
        file.writelines(srt_entries)

    print("Transcript (raw):", alternative.transcript)
    print("SRT file with alignment created:", SRT_OUTPUT)

if __name__ == "__main__":
    transcribe_with_alignment("speech.mp3", SCRIPT_FILE, words_per_group=3)
    print("Done!")
