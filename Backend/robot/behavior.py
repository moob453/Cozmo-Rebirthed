#!/usr/bin/env python

import time
import os
import pycozmo


with pycozmo.connect() as cli:
    
    # Set volume to 100%
    cli.set_volume(65535)

    # Load animations - one time.
    cli.load_anims()

    # Print the names of all available animations.
    names = cli.get_anim_names()
    for name in sorted(names):
        print(name)

    time.sleep(2)
    anim = "anim_launch_wakeup_01"
    while True:
        anim = input("Enter an animation name: ")
        try:
            # Play an animation.
            cli.play_anim(anim)
            cli.play_audio(anim)
            cli.wait_for(pycozmo.event.EvtAnimationCompleted)
        except Exception as e:
            print(f"Error occurred: {e}")