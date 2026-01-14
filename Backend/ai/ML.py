import cv2
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import threading
from collections import deque
import time
# import requests # For your WebAPI

# --- 1. The Brain (Lightweight CNN) ---
class CozmoNet(nn.Module):
    def __init__(self, output_dim):
        super().__init__()
        # Simple 3-layer CNN. MobileNet is better, but this is fast for live training demo
        self.features = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, stride=2), nn.ReLU(),
            nn.Conv2d(16, 32, kernel_size=3, stride=2), nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=3, stride=2), nn.ReLU(),
            nn.Flatten()
        )
        # Calculate flatten size based on input 120x160 (or whatever your cam res is)
        # For 120x160 input, output is roughly 64 * 14 * 19 = 17024 (approx, check shape)
        self.fc = nn.Sequential(
            nn.Linear(64 * 14 * 19, 128), 
            nn.ReLU(),
            nn.Linear(128, output_dim)
        )

    def forward(self, x):
        return self.fc(self.features(x))

# --- 2. The Shared State ---
# Actions: 0: Idle, 1: Fwd, 2: Back, 3: Left, 4: Right, 5: Lift/Etc
ACTION_MAP = {0: "IDLE", 1: "FWD", 2: "BACK", 3: "LEFT", 4: "RIGHT"}
model = CozmoNet(output_dim=len(ACTION_MAP))
optimizer = optim.Adam(model.parameters(), lr=0.001)
criterion = nn.CrossEntropyLoss()

# The Replay Buffer: Stores (Image, Action_Index)
# Critical: If we don't shuffle past data, the AI overfits to "what just happened"
replay_buffer = deque(maxlen=5000) 
lock = threading.Lock()

# --- 3. The Training Thread ---
def trainer_loop():
    while True:
        if len(replay_buffer) < 32:
            time.sleep(0.1)
            continue
            
        with lock:
            # Randomly sample a batch so it remembers past lessons
            batch = np.random.choice(len(replay_buffer), 32, replace=False)
            data = [replay_buffer[i] for i in batch]
        
        # Unpack batch
        imgs, labels = zip(*data)
        img_tensor = torch.stack(imgs)
        label_tensor = torch.tensor(labels)

        # Train step
        optimizer.zero_grad()
        outputs = model(img_tensor)
        loss = criterion(outputs, label_tensor)
        loss.backward()
        optimizer.step()
        
        time.sleep(0.05) # Prevent CPU melting

# --- 4. The Main Loop (UI + Control) ---
def main():
    # Fire up the trainer in background
    t = threading.Thread(target=trainer_loop, daemon=True)
    t.start()

    cap = cv2.VideoCapture("http://127.0.0.1:5000/video_feed") # Connect to your WebAPI stream
    
    current_human_action = 0 # Default Idle
    
    print("System Online. Press WASD to drive. Q to quit.")

    while True:
        ret, frame = cap.read()
        if not ret: break

        # Preprocess frame for Model (Resize to 160x120, Normalize)
        small_frame = cv2.resize(frame, (160, 120))
        img_tensor = torch.from_numpy(small_frame).permute(2, 0, 1).float() / 255.0
        img_tensor = img_tensor.unsqueeze(0) # Add batch dim

        # --- A. AI PREDICTION ---
        with torch.no_grad():
            logits = model(img_tensor)
            ai_probs = torch.softmax(logits, dim=1)
            ai_choice = torch.argmax(ai_probs).item()
            confidence = ai_probs[0][ai_choice].item()

        # --- B. HUMAN INPUT ---
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'): break
        elif key == ord('w'): current_human_action = 1
        elif key == ord('s'): current_human_action = 2
        elif key == ord('a'): current_human_action = 3
        elif key == ord('d'): current_human_action = 4
        else: current_human_action = 0 # Auto-reset to idle if no key (optional)

        # TODO: Send `current_human_action` to your WebAPI here to actually move Cozmo
        
        # --- C. SAVE TO MEMORY ---
        # Only learn if we are doing something interesting (or balancing Idle)
        with lock:
            # Store the tensor (C, H, W) and the integer label
            replay_buffer.append((img_tensor.squeeze(0), current_human_action))

        # --- D. VISUALIZATION (The "Game") ---
        # Green if match, Red if mismatch
        color = (0, 255, 0) if ai_choice == current_human_action else (0, 0, 255)
        
        text_ai = f"AI: {ACTION_MAP[ai_choice]} ({confidence:.2f})"
        text_human = f"HUMAN: {ACTION_MAP[current_human_action]}"
        
        cv2.putText(frame, text_ai, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        cv2.putText(frame, text_human, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

        # Show buffer size so you know if it's learning
        cv2.putText(frame, f"Mem: {len(replay_buffer)}", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        cv2.imshow("Cozmo Neural Link", frame)

    cap.release()
    cv2.destroyAllWindows()
    # Save model on exit
    torch.save(model.state_dict(), "cozmo_brain.pth")

if __name__ == "__main__":
    main()