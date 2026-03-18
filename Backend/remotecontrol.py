# Test code to check runtime functionality
import time, keyboard, os
import requests
state = 1

def send_command(cmd):
    try:
        response = requests.get("http://127.0.0.1:5000/trigger/" + cmd)
        print("Server responded:",response.status_code)
    except Exception as e:
        print("Failed to connect:",e)

def all_keys_released():
    return not bool(keyboard._pressed_events)

def test_runtime_loop():
    global statewwdaddddddddddddddsw
    while True:
        # DriveBase
        if keyboard.is_pressed('w'):
            state = 1
            print("FORWARD")
            send_command('fwd')
        if keyboard.is_pressed('a'):
            state = 1
            print("TURN LEFT")
            send_command('turnl')
        if keyboard.is_pressed('d'):
            state = 1
            print("TURN RIGHT")
            send_command('turnr')
        if keyboard.is_pressed('s'):
            state = 1
            print("BACKWARD")
            send_command('back')
        # Lift
        if keyboard.is_pressed('up'):
            state = 1
            print("LIFT UP")
            send_command('liftup')
        if keyboard.is_pressed('down'):
            state = 1
            print("LIFT DOWN")
            send_command('liftdown')
        # Head
        if keyboard.is_pressed('y'):
            state = 1
            print("HEAD UP")
            send_command('headup')
        if keyboard.is_pressed('h'):
            state = 1
            print("HEAD DOWN")
            send_command('headdown')
        #Stop all actions
        if all_keys_released() and state == 1:
            state = 0
            print("STOP")
            send_command('stop')

if __name__ == "__main__":
    test_runtime_loop()