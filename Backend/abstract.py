import pycozmo, requests

def send_command(cmd):
    try:
        response = requests.get("http://127.0.0.1:5000/trigger/" + cmd)
        print("Server responded:",response.status_code)
    except Exception as e:
        print("Failed to connect:",e)

def connect():
    """Connect to Cozmo robot."""
    send_command("connect")

def forward():
    """Move Cozmo forward."""
    send_command("fwd")

def backward():
    """Move Cozmo backward."""
    send_command("back")

def turn_left():
    """Turn Cozmo left."""
    send_command("turnl")
    
def turn_right():
    """Turn Cozmo right."""
    send_command("turnr")

def disconnect():
    """Disconnect from Cozmo robot."""
    send_command("disconnect")


def shutdown_all():
    """Request that the runtime shuts down all worker processes and exits.

    This calls the runtime's `/kill` endpoint; it's safe to call from the GUI
    when the user closes the window (or from any other process).
    """
    # Prefer calling the local runner if available (clean stop of processes/threads)
    try:
        from Backend import runner as _runner
        _runner.kill_all()
        print("Called local runner.kill_all()")
        return
    except Exception:
        pass

    # Fall back to the runtime's HTTP /kill endpoint
    try:
        response = requests.get("http://127.0.0.1:5000/kill")
        print("Shutdown request sent, server responded:", response.status_code)
    except Exception as e:
        print("Failed to send shutdown request:", e)
    