import re
import random
from moviepy import *
from moviepy.audio import fx as afx
from moviepy.video import fx as vfx


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
         return video.cropped(x1=x1, width=new_w)
     else:
         # too tall, crop height
         new_h = int(w / target_ratio)
         y1 = (h - new_h) // 2
         return video.cropped(y1=y1, height=new_h)

def main():
    video_id = random.randint(1,2)
    video_file = f"./videos/{video_id}.mp4"
    timing_file = "timing.srt"
    narration_file = "speech.mp3"
    music_id = random.randint(1,2)
    music_file = f"./music/{music_id}.mp3" 
    output_file = "output.mp4"
    font_file = "Roboto-Bold.ttf"  # Store font file name in a variable

    video = VideoFileClip(video_file).without_audio()
    video = crop_to_16_9(video)  # ensure 16:9

    cues = parse_timing_file(timing_file)
    text_clips = []
    for start, end, text in cues:
        duration = end - start
        txt_clip = TextClip(
            font_file,
            text,
            font_size=int(video.w * 0.075),
            color='black',
            method='caption',                  # Use 'caption' to enable text wrapping
            size=(int(video.w * 0.95), None),     # Set width to 90% of video width; height auto-calculated
            stroke_width=int(video.w * 0.0065),
            stroke_color='white'
        ).with_position(('center')).with_start(start).with_duration(duration)

        text_clips.append(txt_clip)

    narration = AudioFileClip(narration_file)
    
    music = AudioFileClip(music_file).with_volume_scaled(0.43)
    
    music_looped = music.with_effects([afx.AudioLoop(duration=narration.duration+3)])
    
    video = video.with_effects([vfx.Loop(n=int((narration.duration+3)/video.duration))])
    video = video.with_duration(narration.duration+3)

    all_clips = [video] + text_clips
    final_video = CompositeVideoClip(all_clips)

    final_audio = CompositeAudioClip([narration, music_looped])

    final_video = final_video.with_audio(final_audio)

    final_video.write_videofile(output_file, codec="libx264", audio_codec="aac")

if __name__ == "__main__":
    main()
