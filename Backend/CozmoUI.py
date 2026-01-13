import customtkinter
from . import abstract as backend

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("800x500")

        self.connect = customtkinter.CTkButton(self, text="Connect", command=backend.connect)
        self.connect.pack(padx=20, pady=20)
        self.disconnect = customtkinter.CTkButton(self, text="Disconnect", command=backend.disconnect)
        self.disconnect.pack(padx=20, pady=20)
        self.forward = customtkinter.CTkButton(self, text="Forward", command=backend.forward)
        self.forward.pack(padx=20, pady=20)
        self.backward = customtkinter.CTkButton(self, text="Backward", command=backend.backward)
        self.backward.pack(padx=20, pady=20)
        self.turnleft = customtkinter.CTkButton(self, text="Turn Left", command=backend.turn_left)
        self.turnleft.pack(padx=20, pady=20)
        self.turnright = customtkinter.CTkButton(self, text="Turn Right", command=backend.turn_right)
        self.turnright.pack(padx=20, pady=20)

        # Intercept window close (user presses the X button)
        self.protocol("WM_DELETE_WINDOW", self._on_close)


def init():
    app = App()
    app.mainloop()


    # Add on-close handler implementation to the App class
def _app_on_close(self):
    try:
        backend.shutdown_all()
    except Exception:
        pass
    self.destroy()

# Attach method to class (keeps the file simple and avoids reordering imports)
App._on_close = _app_on_close


if __name__ == '__main__':
    try:
        import multiprocessing as _mp
        _mp.freeze_support()
    except Exception:
        pass

    init()