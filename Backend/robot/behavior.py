import time
import random
import pycozmo
import sys


# The "Personality" Palette
# Cozmo has hundreds of anims. These are the ones that make him look "Idle/Thinking"
# You can dump all names via cli.anim_names if you want to find more.
IDLE_ANIMS = [
    "anim_bored_01",
    "anim_bored_02",
    "anim_bored_event_02",
    "anim_bored_event_03",
    "anim_gazing_lookat_01",
    "anim_reacttoface_happy_01",
    "anim_reacttoface_curious_01",
    "anim_sparking_suggestion_01",
    "anim_user_listen_loop_01",
    "anim_keepalive_test_01",
]

def on_robot_state(cli, pkt: pycozmo.protocol_encoder.RobotState):
    """(Optional) Watchdog to print battery or cliff status"""
    # If you want to check cliff sensors, they are in pkt.cliff_data_raw
    pass

def run_idle_behavior(cli):
    print("[Ghost] Loading Animation Definitions (this takes a second)...")
    cli.load_anims()
    print(f"[Ghost] Loaded {len(cli.anim_names)} animations.")
    
    # Enable camera so his head tracking/auto-exposure internal logic works
    cli.enable_camera(True)
    
    # Set volume (0-65535) - Set to medium so he isn't annoying
    cli.set_headlight(True)
    
    print("[Ghost] Cozmo is now alive. Press Ctrl+C to kill him.")

    while True:
        # 1. Roll the dice
        # Weights: [Animation, Turn, Head/Lift Twitch, Wait]
        decision = random.choices(
            ["anim", "turn", "twitch", "wait"], 
            weights=[30, 20, 20, 30], # 30% chance to animate, 20% to turn, etc.
            k=1
        )[0]

        if decision == "anim":
            anim = random.choice(IDLE_ANIMS)
            print(f"[Action] Playing: {anim}")
            try:
                # Play and wait for it to finish so actions don't overlap
                cli.play_anim(anim)
                cli.wait_for(pycozmo.event.EvtAnimationCompleted)
            except ValueError:
                print(f"[Error] Animation {anim} not found.")

        elif decision == "turn":
            # Random turn between -90 and 90 degrees
            speed = random.choice([30, 50, -30, -50])
            duration = random.uniform(0.5, 2.0)
            print(f"[Action] Turning (Speed: {speed})")
            
            cli.drive_wheels(speed, -speed)
            time.sleep(duration)
            cli.stop_all_motors()

        elif decision == "twitch":
            # Move head or lift slightly
            sub_decision = random.choice(["head", "lift"])
            if sub_decision == "head":
                angle = random.uniform(pycozmo.MIN_HEAD_ANGLE.radians, pycozmo.MAX_HEAD_ANGLE.radians)
                print(f"[Action] Moving Head to {int(angle)} rad")
                cli.set_head_angle(angle) 
                # No sleep here, let him do it while moving to next state
            else:
                # Lift is mechanical, so we just move it a bit
                height = random.uniform(pycozmo.MIN_LIFT_HEIGHT.mm, pycozmo.MAX_LIFT_HEIGHT.mm * 0.5)
                print(f"[Action] Moving Lift to {int(height)} mm")
                cli.set_lift_height(height)

        elif decision == "wait":
            wait_time = random.uniform(1.0, 5.0)
            print(f"[Action] Staring into the void for {wait_time:.1f}s...")
            time.sleep(wait_time)

        # Small delay between thoughts
        time.sleep(0.5)

def main():
    cli = pycozmo.Client()
    
    # Hook into state updates if we need cliff detection later
    cli.add_handler(pycozmo.event.EvtRobotStateUpdated, on_robot_state)

    cli.start()
    print("[System] Connecting...")
    cli.connect()
    cli.wait_for_robot()
    print("[System] Connected.")

    try:
        run_idle_behavior(cli)
    except KeyboardInterrupt:
        print("\n[System] Shutting down...")
        cli.stop_all_motors()
        cli.disconnect()
        print("[System] Offline.")

if __name__ == "__main__":
    main()