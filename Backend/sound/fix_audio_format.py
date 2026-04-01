import os
import glob
import subprocess

sound_folder = os.path.join(os.path.dirname(__file__), 'raw_sound')
wav_files = glob.glob(os.path.join(sound_folder, '*.wav'))

print(f"Found {len(wav_files)} files. We will convert any 24-bit/32-bit files to 16-bit 48000Hz.")

for wav in wav_files:
    # Only convert if not already processed by us or if we just want to run it on everything safely
    # If the file exists but we want to do it in-place:
    temp_wav = wav + ".tmp.wav"
    try:
        # ffmpeg -i input.wav -c:a pcm_s16le -ar 48000 output.wav -y
        # -loglevel error to reduce spam
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', wav, '-c:a', 'pcm_s16le', '-ar', '48000', temp_wav], check=True)
        # overwrite original
        os.replace(temp_wav, wav)
    except subprocess.CalledProcessError as e:
        print(f"Failed to convert {wav}")
    except Exception as e:
        print(e)
        
print("Done! All files are now 16-bit 48000Hz.")
