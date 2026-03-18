import pyttsx3
import pycozmo
import os

def clear():
    os.system("cls")

# Initialize the speech engine
engine = pyttsx3.init()

# Optional: Adjust properties like speed (rate) or volume
engine.setProperty('rate', 150)    # Default is usually 200
engine.setProperty('volume', 1.0)  # Range 0.0 to 1.0

text = "Null"

# Save the speech to a file with this name
output_file = "audio.wav"

# Process the commands
engine.runAndWait()

with pycozmo.connect() as cli:
    # Set volume to ~75%.
    cli.set_volume(65535)

     # Set head to look up
    angle = (pycozmo.robot.MAX_HEAD_ANGLE.radians - pycozmo.robot.MIN_HEAD_ANGLE.radians) / 2.0
    cli.set_head_angle(angle)
    while True:
        clear()
        text = input("Type what you want it to say: ")
        engine.save_to_file(text, output_file)
        # A 22 kHz, 16-bit, mono file is required.
        cli.play_audio("audio.wav")
        cli.wait_for(pycozmo.event.EvtAudioCompleted)