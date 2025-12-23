import multiprocessing as mp, time, pycozmo
from flask import Flask, request

def runtime_loop(shared_data):
    """Handles connection to cozmo and
    processes commands from shared memory."""
    print("[Runtime] Connecting to Cozmo...")
    try:
        cli = pycozmo.Client()
        cli.start()
        cli.connect()
        cli.wait_for_robot(5)
        print("[Runtime] Connected to Cozmo.")
    except Exception as e:
        print("[Runtime] ERROR:",e)
    print("[Runtime] Runtime loop active.")
    while True:
        try:
            # Check shared dictionary
            if shared_data.get("command") == "turnl":
                print("[Runtime] TURNING LEFT!")
                shared_data["command"] = "idle"
                cli.drive_wheels(-50,50,0.1)

            elif shared_data.get("command") == "fwd":
                print("[Runtime] FORWARD!")
                shared_data["command"] = "idle"
                cli.drive_wheels(50,50,0.1)
            
            elif shared_data.get("command") == "turnr":
                print("[Runtime] TURNING RIGHT!")
                shared_data["command"] = "idle"
                cli.drive_wheels(50,-50,0.1)

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

            time.sleep(0.01)
        except Exception as e:
            print("[Runtime] Error in runtime loop:",e)
            print("continuing...")
            

app = Flask(__name__)
shared_data = None 

@app.route("/trigger/<cmd>")
def trigger(cmd):
    # write to shared memory
    shared_data["command"] = cmd
    return f"Set command to {cmd}", 200

def runtime():
    global shared_data
    # Manager
    manager = mp.Manager()
    
    # Create a shared dictionary
    shared_data = manager.dict()
    shared_data["command"] = "idle"

    p = mp.Process(target=runtime_loop, args=(shared_data,))
    p.daemon = True
    p.start()
    app.run(port=5000, debug=False)

if __name__ == "__main__":
    runtime()