import re
import os
from moviepy.editor import (
    VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip, CompositeAudioClip
)
from moviepy.video.fx.all import crop

def parse_time(time_str):
    hours, minutes, seconds_ms = time_str.split(":")
    seconds, milliseconds = seconds_ms.split(",")
    return int(hours)*3600 + int(minutes)*60 + int(seconds) + int(milliseconds)/1000

def parse_timing_file(filename):
    cues = []
    with open(filename, 'r', encoding='utf-8') as f:  # Explicitly specify encoding
        content = f.read().strip()
    cue_blocks = re.split(r'\n\s*\n', content)
    for block in cue_blocks:
        lines = block.strip().splitlines()
        if len(lines) >= 2:
            time_line = lines[0].strip()
            text = "\n".join(line.strip() for line in lines[1:])
            try:
                start_str, end_str = time_line.split(" --> ")
                start = parse_time(start_str.strip())
                end = parse_time(end_str.strip())
                cues.append((start, end, text))
            except Exception as e:
                print(f"Error parsing cue: {block}. Error: {e}")
    return cues

def crop_to_16_9(video):
    # Crops the video to center 16:9 if needed
    w, h = video.size
    target_ratio = 9 / 16
    current_ratio = w / h

    if abs(current_ratio - target_ratio) < 0.01:
        return video  # already 16:9, no crop needed

    if current_ratio > target_ratio:
        # too wide, crop width
        new_w = int(h * target_ratio)
        x1 = (w - new_w) // 2
        return crop(video, x1=x1, width=new_w)
    else:
        # too tall, crop height
        new_h = int(w / target_ratio)
        y1 = (h - new_h) // 2
        return crop(video, y1=y1, height=new_h)

def main():
    video_file = "MC Parkour.mp4"
    timing_file = "timing.srt"
    audio_file = "speech.mp3"
    second_audio_file = "music.mp3" # Add second audio file
    output_file = "test_output.mp4"
    font_file = "Roboto-Bold.ttf"  # Store font file name in a variable

    video = VideoFileClip(video_file).without_audio()
    video = crop_to_16_9(video)  # ensure 16:9

    cues = parse_timing_file(timing_file)

    text_clips = []
    for start, end, text in cues:
        duration = end - start
        txt_clip = TextClip(
            text, fontsize=60, 
            color='black',
            font=font_file,  # Use the font file variable
            size=video.size,
            stroke_width=2,
            stroke_color='white',
            method='label'
        ).set_position(('center', 'bottom')).set_start(start).set_duration(duration)

        text_clips.append(txt_clip)

    all_clips = [video] + text_clips
    final_video = CompositeVideoClip(all_clips)

    # Load audio files
    first_audio = AudioFileClip(audio_file)
    second_audio = AudioFileClip(second_audio_file).volumex(0.5) # Adjust volume as needed

    # Determine the duration of the first audio file
    audio_duration = first_audio.duration

    # Crop the second audio file to the duration of the first audio file
    second_audio_cropped = second_audio.subclip(0, audio_duration)

    # Create a CompositeAudioClip with both audio files
    final_audio = CompositeAudioClip([first_audio.subclip(0, audio_duration), second_audio_cropped])

    # Set the audio of the final video
    final_video = final_video.set_audio(final_audio)

    final_video.subclip(0, audio_duration).write_videofile(
        output_file, codec="libx264", audio_codec="aac"
    )

if __name__ == "__main__":
    main()