# 🤖 Cozmo Rebirthed

> **Bringing life back to Cozmo — one line of code at a time.**

Cozmo Rebirthed is an open-source project dedicated to fully reviving the **Anki Cozmo robot** after Anki's shutdown in 2019 left the little guy stranded without an official app or backend support. The goal is to restore — and eventually *surpass* — everything the original Cozmo app was capable of, giving Cozmo a full second life as a playful, expressive, and interactive companion robot.

---

## 🎯 Vision & Goal

The original Anki Cozmo app was remarkable: it gave Cozmo a personality, animations, a rich set of behaviours, games, and the ability to recognise faces and interact with the world around him. When Anki shut down, all of that was effectively orphaned.

**Cozmo Rebirthed aims to:**

- ✅ Restore full manual control of Cozmo (movement, lift, head)
- ✅ Restore the live camera feed from Cozmo's front-facing camera
- 🔄 Restore Cozmo's animations and emotional expressions
- 🔄 Restore face recognition and object/cube interaction
- 🔄 Restore Cozmo's AI behaviours and idle personality
- 🔜 Build a polished desktop GUI as a drop-in replacement for the original app
- 🔜 Add features *beyond* the original app (scripting, custom behaviours, community extensions)
- 🔜 Optionally expose a web interface for browser-based control

This is a long-term, ambitious project — but every commit brings Cozmo closer to being fully alive again.

---

## 🏗️ Current State of Progress

> **Status: Early Development — Core Infrastructure In Place**

The project currently has a working multi-process architecture with a basic desktop GUI and a Flask-based command runtime. Here is what is done and what is still in progress:

### ✅ Done
| Feature | Details |
|---|---|
| **Project architecture** | Multi-process design — runtime runs in a separate OS process from the GUI, connected via a local Flask HTTP server |
| **Robot connection** | Connects to Cozmo over USB/Wi-Fi using [pycozmo](https://github.com/zayfod/pycozmo) |
| **Drive base control** | Forward, backward, turn left, turn right, stop |
| **Lift control** | Raise and lower Cozmo's forklift arm |
| **Desktop GUI (basic)** | A `customtkinter`-based window with Connect/Disconnect and directional control buttons |
| **Camera integration** | `CozmoCamera` class streams Cozmo's camera as an MJPEG feed via Flask Blueprint |
| **Keyboard remote control** | `remotecontrol.py` allows WASD + arrow key control directly from the terminal |
| **Process management** | `runner.py` handles spawning, monitoring, and killing backend processes cleanly |
| **Graceful shutdown** | GUI window close triggers a full clean shutdown of all backend processes |

### 🔄 In Progress / Planned
| Feature | Status |
|---|---|
| Live camera feed displayed inside the GUI | 🔄 In Progress |
| Head angle control | 🔜 Planned |
| Cozmo animations & emotional expressions | 🔜 Planned |
| Face recognition | 🔜 Planned |
| Light cube detection & interaction | 🔜 Planned |
| Cozmo's idle/personality AI behaviours | 🔜 Planned |
| Audio / sound effects | 🔜 Planned |
| Polished GUI (full app replacement) | 🔜 Planned |
| Web interface (browser control) | 🔜 Planned |
| Custom scripting / behaviour editor | 🔜 Future |
| Community plugin/extension support | 🔜 Future |

---

## 🗂️ Project Structure

```
Cozmo-Rebirthed/
├── main.py                  # Entry point — starts runtime process + GUI
└── Backend/
    ├── __init__.py
    ├── abstract.py          # GUI-side command API (sends HTTP requests to runtime)
    ├── CozmoUI.py           # Desktop GUI built with customtkinter
    ├── runtime.py           # Flask server + pycozmo robot control loop
    ├── camera.py            # MJPEG camera stream via Flask Blueprint
    ├── remotecontrol.py     # Terminal keyboard control (WASD) for testing
    └── runner.py            # Process/thread manager for backend modules
```

### How it works

```
┌─────────────────────���        HTTP (localhost:5000)       ┌──────────────────────────┐
│   GUI Process       │  ─────────────────────────────►   │   Runtime Process        │
│  (CozmoUI.py)       │  /trigger/<cmd>                    │  (runtime.py + Flask)    │
│                     │                                    │                          │
│  customtkinter app  │                                    │  pycozmo client          │
│  Buttons / bindings │                                    │  Command dispatch loop   │
└─────────────────────┘                                    └──────────────┬───────────┘
                                                                          │ pycozmo
                                                                          ▼
                                                                   🤖 Cozmo Robot
```

`main.py` uses `runner.py` to spin up the Flask runtime in its own OS process, then runs the GUI in the main thread. The GUI calls `abstract.py` functions, which fire HTTP requests to the runtime. The runtime translates those commands into `pycozmo` calls on the physical robot.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- A physical **Anki Cozmo** robot + USB charging cable (used for the data connection)
- The Cozmo app on a mobile device is **not** required

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/moob453/Cozmo-Rebirthed.git
cd Cozmo-Rebirthed

# 2. Install dependencies
pip install pycozmo customtkinter flask requests opencv-python pillow numpy keyboard
```

### Running

```bash
python main.py
```

This will:
1. Start the Flask runtime server in a background process
2. Open the Cozmo Rebirthed desktop GUI
3. Connect to your Cozmo robot (press **Connect** in the GUI)

#### Terminal / Keyboard Control (for testing)
```bash
python -m Backend.remotecontrol
```
Use `W A S D` to drive and `↑ ↓` arrow keys to control the lift.

---

## 🤝 Contributing

This project is in active early development and contributions are very welcome! Whether you want to help restore a specific feature, improve the GUI, fix a bug, or just experiment — jump in.

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes and open a Pull Request

If you're not sure where to start, check the **In Progress / Planned** table above — any of those items are fair game.

---

## 📄 License

This project is licensed under the terms of the [LICENSE](LICENSE) file included in the repository.

---

## 🙏 Acknowledgements

- [**pycozmo**](https://github.com/zayfod/pycozmo) — the open-source Python library that makes direct communication with Cozmo possible. This project would not exist without it.
- The Anki team for creating such a wonderful little robot in the first place.
- Everyone in the Cozmo community keeping the dream alive.

---

*Cozmo deserves to live again. Let's make it happen.* 🤖❤️