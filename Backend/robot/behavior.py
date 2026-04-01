import pycozmo
import os
import time
import threading
import random
import xml.etree.ElementTree as ET

# Monkey-patch PyCozmo's u_law_encoding to avoid "byte must be in range(0, 256)" error when max is 256.
_orig_u_law = pycozmo.audio.u_law_encoding
def _safe_u_law(sample: int) -> int:
    val = _orig_u_law(sample)
    return val if val < 256 else 255
pycozmo.audio.u_law_encoding = _safe_u_law

# Build paths to the raw_sound folder
current_dir = os.path.dirname(os.path.abspath(__file__))
sound_folder = os.path.abspath(os.path.join(current_dir, '..', 'sound', 'raw_sound'))
listname_file = os.path.join(sound_folder, 'listname.txt')

# Path to the specific .bin file on your computer
bin_file = r"C:\Users\Lachy\pycozmo\assets\cozmo_resources\assets\animations\launch.bin"

# Parse the Wwise SoundbanksInfo XML to map Event IDs to string Names
xml_path = os.path.abspath(os.path.join(bin_file, "..", "..", "..", "sound", "SoundbanksInfo.xml"))
events_map = {}
if os.path.exists(xml_path):
    try:
        tree = ET.parse(xml_path)
        for event in tree.findall('.//Event'):
            events_map[int(event.attrib['Id'])] = event.attrib['Name']
    except Exception as e:
        print(f"Failed to parse SoundbanksInfo.xml: {e}")

# Pre-load available wav files for fuzzy matching
available_wavs = []
if os.path.exists(sound_folder):
    available_wavs = [f for f in os.listdir(sound_folder) if f.endswith('.wav')]

def get_audio_file(event_id, sound_folder, available_wavs, events_map):
    str_id = str(event_id)
    
    # 1. Try direct ID
    if f"{str_id}.wav" in available_wavs:
        return os.path.join(sound_folder, f"{str_id}.wav")
        
    # 2. Try fuzzy string matching with the Wwise Event name
    if event_id in events_map:
        name = events_map[event_id].lower()
        # Clean up the name for better token matching
        name = name.replace('play__', '').replace('robot_vo__', '').replace('robot_sfx__', '')
        tokens = [t for t in name.split('_') if t and t not in ('p1', 'p2', 'p3')]
        
        matches = []
        for w in available_wavs:
            lw = w.lower()
            if all(t in lw for t in tokens):
                matches.append(w)
                
        # Fallback: drop the last token if no matches (e.g. specific variation)
        if not matches and len(tokens) > 1:
            for w in available_wavs:
                if all(t in w.lower() for t in tokens[:-1]):
                    matches.append(w)
                    
        if matches:
            chosen = random.choice(matches) # Pick a random variation
            return os.path.join(sound_folder, chosen)
            
    return None

with pycozmo.connect() as cli:
    cli.set_volume(65535)

    # 1. Parse the .bin file using the anim_encoder
    anim_clips = pycozmo.anim_encoder.AnimClips.from_fb_file(bin_file)

    # A .bin file can contain multiple clips. Iterate through them:
    for clip in anim_clips.clips:
        print(f"Playing clip: {clip.name}")
        
# 2. Preprocessed clip
        ppclip = pycozmo.anim.PreprocessedClip.from_anim_clip(clip)

        # 3. Flawless Synchronized Playback Loop
        # Calculate max durations
        last_anim_ms = max(ppclip.keyframes.keys()) if ppclip.keyframes else 0
        last_audio_ms = 0
        
        audio_frames = {}
        for kf in clip.keyframes:
            if isinstance(kf, pycozmo.anim_encoder.AnimRobotAudio):
                for audio_id in kf.audio_event_ids:
                    wav_path = get_audio_file(audio_id, sound_folder, available_wavs, events_map)
                    if wav_path:
                        print(f"Found perfectly synced match for {audio_id}: {os.path.basename(wav_path)}")
                        try:
                            pkts = pycozmo.audio.load_wav(wav_path)
                            start_frame = int(kf.trigger_time_ms / 33.3333)
                            for i, pkt in enumerate(pkts):
                                audio_frames[start_frame + i] = pkt
                            
                            end_time = kf.trigger_time_ms + len(pkts) * 33.3333
                            if end_time > last_audio_ms:
                                last_audio_ms = end_time
                        except Exception as e:
                            print(f"Error loading {wav_path}: {e}")
                    else:
                        print(f"Audio for event {audio_id} not found.")

        total_ms = max(last_anim_ms, last_audio_ms)
        total_frames = int(total_ms / 33.3333) + 1

        cli.cancel_anim()
        start_pkt = pycozmo.protocol_encoder.StartAnimation(anim_id=cli._next_anim_id)
        cli.anim_controller.play_anim_frame(None, None, (start_pkt, ))
        cli._next_anim_id += 1

        anim_keys = sorted(ppclip.keyframes.keys())
        key_idx = 0
        
        for frame_idx in range(total_frames):
            window_end = (frame_idx + 1) * 33.3333
            
            image_pkt = None
            pkts = []
            
            while key_idx < len(anim_keys) and anim_keys[key_idx] < window_end:
                for action in ppclip.keyframes[anim_keys[key_idx]]:
                    if isinstance(action, pycozmo.protocol_encoder.DisplayImage):
                        image_pkt = action
                    elif isinstance(action, pycozmo.protocol_encoder.Packet):
                        pkts.append(action)
                key_idx += 1
                
            audio_pkt = audio_frames.get(frame_idx, None)
            cli.anim_controller.play_anim_frame(audio_pkt, image_pkt, pkts)

        end_pkt = pycozmo.protocol_encoder.EndAnimation()
        cli.anim_controller.play_anim_frame(None, None, (end_pkt, ))
        
        # Wait for the animation to finish before proceeding
        cli.wait_for(pycozmo.event.EvtAnimationCompleted)