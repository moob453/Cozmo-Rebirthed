import logging
import multiprocessing as mp
import time
import pycozmo
import threading
from PIL import Image
import io
from flask import Flask, request, Response
import sys
import cv2
import numpy as np

app = Flask(__name__)
shared_data = None 
worker_proc = None
worker_thread = None
last_im = None

def on_camera_image(cli, new_im):
    """ Handle new images, coming from the robot. """
    global last_im
    last_im = new_im

def runtime_loop(shared_data):
    print("[Runtime] Connecting to Cozmo...")
    try:
        cli = pycozmo.Client()
        cli.start()
        cli.connect()
        cli.wait_for_robot(5)

        # Set head to look up
        angle = (pycozmo.robot.MAX_HEAD_ANGLE.radians - pycozmo.robot.MIN_HEAD_ANGLE.radians) / 2.0
        cli.set_head_angle(angle)

        # Register to receive new camera images and enable camera.
        cli.add_handler(pycozmo.event.EvtNewRawCameraImage, on_camera_image)
        cli.enable_camera()

        # Run with 14 FPS. This is the frame rate of the robot camera.
        timer = pycozmo.util.FPSTimer(14)

        print("[Runtime] Connected to Cozmo.")
    except Exception as e:
        print("[Runtime] ERROR:", e)
        return

    print("[Runtime] Runtime loop active.")

    try:
        while True:
            try:
                # Handle Drive Base
                if shared_data.get("command") == "turnl":
                    print("[Runtime] TURNING LEFT!")
                    shared_data["command"] = "idle"
                    cli.drive_wheels(-100,100)

                elif shared_data.get("command") == "fwd":
                    print("[Runtime] FORWARD!")
                    shared_data["command"] = "idle"
                    cli.drive_wheels(100,100)
                
                elif shared_data.get("command") == "turnr":
                    print("[Runtime] TURNING RIGHT!")
                    shared_data["command"] = "idle"
                    cli.drive_wheels(100,-100)
                
                elif shared_data.get("command") == "back":
                    print("[Runtime] BACKWARD!")
                    shared_data["command"] = "idle"
                    cli.drive_wheels(-100,-100)
                
                # Handle Lift
                elif shared_data.get("command") == "liftup":
                    print("[Runtime] LIFTING UP!")
                    shared_data["command"] = "idle"
                    cli.set_lift_height(pycozmo.MAX_LIFT_HEIGHT.mm)
                elif shared_data.get("command") == "liftdown":
                    print("[Runtime] LIFTING DOWN!")
                    shared_data["command"] = "idle"
                    cli.set_lift_height(pycozmo.MIN_LIFT_HEIGHT.mm)

                # Controll Head
                elif shared_data.get("command") == "headup":
                    print("[Runtime] LIFTING HEAD!")
                    shared_data["command"] = "idle"
                    cli.set_head_angle(pycozmo.MAX_HEAD_ANGLE.radians)
                elif shared_data.get("command") == "headdown":
                    print("[Runtime] LOWERING HEAD!")
                    shared_data["command"] = "idle"
                    cli.set_head_angle(pycozmo.MIN_HEAD_ANGLE.radians)
                
                # Stop all actions
                elif shared_data.get("command") == "stop":
                    print("[Runtime] STOP!")
                    shared_data["command"] = "idle"
                    cli.stop_all_motors()

                # Handle Connect/Disconnect
                elif shared_data.get("command") == "connect":
                    print("[Runtime] CONNECTING TO COZMO!")
                    shared_data["command"] = "idle"
                    cli = pycozmo.Client()
                    cli.start()
                    cli.connect()
                    cli.wait_for_robot(5)
                    print("[Runtime] Connected to Cozmo.")

                elif shared_data.get("command") == "disconnect":
                    print("[Runtime] DISCONNECTING FROM COZMO!")
                    shared_data["command"] = "idle"
                    cli.disconnect()
                    print("[Runtime] Disconnected from Cozmo.")

                # Allow an external 'kill_all' command to stop this worker loop
                if shared_data.get("command") == "kill_all":
                    print('[Runtime] kill_all received in worker loop, exiting...')
                    break

                # Show camera on laptop instead of robot face
                if last_im is not None:
                    frame_rgb = np.array(last_im.convert("RGB"))
                    frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
                    cv2.imshow("Cozmo Camera", frame_bgr)

                    # Press Q in the window to quit
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        shared_data["command"] = "kill_all"
                        break

                timer.sleep()
                time.sleep(0.01)

            except Exception as e:
                print("[Runtime] Error in runtime loop:", e)
                print("continuing...")
    finally:
        cv2.destroyAllWindows()

@app.route("/trigger/<cmd>")
def trigger(cmd):
    # write to shared memory
    shared_data["command"] = cmd
    return f"Set command to {cmd}", 200

def _shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        print('[Runtime] Server shutdown function not available; exiting process.')
        try:
            sys.exit(0)
        except SystemExit:
            pass
    else:
        func()


@app.route('/kill', methods=['GET', 'POST'])
def kill():
    global worker_proc, shared_data
    print('[Runtime] Kill request received; shutting down workers and server...')
    try:
        shared_data['command'] = 'kill_all'
    except Exception:
        pass

    global worker_thread
    if worker_thread is not None:
        try:
            if worker_thread.is_alive():
                worker_thread.join(timeout=3)
                print('[Runtime] Worker thread joined (or timed out).')
        except Exception as e:
            print('[Runtime] Error joining worker thread:', e)

    try:
        _shutdown_server()
    except Exception as e:
        print('[Runtime] Error shutting down server:', e)

    return 'Shutting down', 200

def runtime():
    global shared_data, worker_thread
    try:
        logging.getLogger('pycozmo.robot').setLevel(logging.WARNING)
        logging.getLogger('pycozmo.protocol').setLevel(logging.WARNING)
    except Exception:
        pass
    
    manager = mp.Manager()
    shared_data = manager.dict()
    shared_data["command"] = "idle"

    t = threading.Thread(target=runtime_loop, args=(shared_data,), daemon=True)
    worker_thread = t
    t.start()
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

if __name__ == "__main__":
    runtime()