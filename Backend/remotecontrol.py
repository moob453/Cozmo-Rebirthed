# Test code to check runtime functionality
import time, keyboard, os
import requests

def send_command(cmd):
    try:
        response = requests.get("http://127.0.0.1:5000/trigger/" + cmd)
        print("Server responded:",response.status_code)
    except Exception as e:
        print("Failed to connect:",e)

def all_keys_released():
    return not bool(keyboard._pressed_events)

def test_runtime_loop():
    while True:
        # DriveBase
        if keyboard.is_pressed('w'):
            print("FORWARD")
            send_command('fwd')
        if keyboard.is_pressed('a'):
            print("TURN LEFT")
            send_command('turnl')
        if keyboard.is_pressed('d'):
            print("TURN RIGHT")
            send_command('turnr')
        if keyboard.is_pressed('s'):
            print("BACKWARD")
            send_command('back')
        # Lift
        if keyboard.is_pressed('up'):
            print("LIFT UP")
            send_command('liftup')
        if keyboard.is_pressed('down'):
            print("LIFT DOWN")
            send_command('liftdown')
        #Stop all actions
        if all_keys_released():
            print("STOP")
            send_command('stop')

if __name__ == "__main__":
    test_runtime_loop()