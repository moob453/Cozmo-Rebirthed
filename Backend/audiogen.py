import pycozmo
import os
import subprocess
import win32com.client  # Direct Windows speech API to avoid pyttsx3 freezing bug

def clear():
    os.system("cls")

# Initialize the SAPI Windows Speech Engine directly
speaker = win32com.client.Dispatch("SAPI.SpVoice")
# Set a slightly slower base rate (-10 to 10 scale, default is 0)
speaker.Rate = -2 

text = "Null"

# Save the speech to a file with this name
temp_file = "temp_audio.wav"
output_file = "audio.wav"

def generate_tts_wav(text_to_speak, filepath):
    stream = win32com.client.Dispatch("SAPI.SpFileStream")
    audio_format = win32com.client.Dispatch("SAPI.SpAudioFormat")
    # Setting format type 22 strictly sets 22050Hz, 16Bit, Mono.
    audio_format.Type = 22 
    stream.Format = audio_format
    
    # 3 = SSFMCreateForWrite (Overwrites the file safely)
    stream.Open(filepath, 3, False)
    speaker.AudioOutputStream = stream
    speaker.Speak(text_to_speak)
    stream.Close()

with pycozmo.connect() as cli:
    # Set volume to ~75%.
    cli.set_volume(25000)

     # Set head to look up
    angle = (pycozmo.robot.MAX_HEAD_ANGLE.radians - pycozmo.robot.MIN_HEAD_ANGLE.radians) / 2.0
    cli.set_head_angle(angle)
    
    while True:
        clear()
        text = input("Type what you want it to say (or 'q' to quit): ")
        if text.lower() in ['q', 'quit', 'exit']:
            break
            
        # Generate base TTS using SAPI to bypass pyttsx3 freezing COM errors
        generate_tts_wav(text, temp_file)
        
        # Apply Cozmo-like audio effects via ffmpeg
        pitch_multiplier = 1.55
        
        # NOTE: FFMPEG's atempo filter fails completely if tempo < 0.5. 
        # Chain two atempos to bypass this limit (e.g., 0.63 * 0.63 approx 0.4)
        print("Synthesizing internal Cozmo voice...")

        subprocess.run([
            "ffmpeg", "-y", "-i", temp_file,
            "-af", f"asetrate={int(22050 * pitch_multiplier)},aresample=22050,atempo=0.63,atempo=0.63",
            "-ac", "1", "-ar", "22050", "-sample_fmt", "s16",
            output_file
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # A 22 kHz, 16-bit, mono file is required.
        cli.play_audio(output_file)
        cli.wait_for(pycozmo.event.EvtAudioCompleted)