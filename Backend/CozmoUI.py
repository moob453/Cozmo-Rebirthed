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
        self.forward = customtkinter.CTkButton(self, text="Forward")
        self.forward.pack(padx=20, pady=20)
        self.backward = customtkinter.CTkButton(self, text="Backward")
        self.backward.pack(padx=20, pady=20)
        self.turnleft = customtkinter.CTkButton(self, text="Turn Left")
        self.turnleft.pack(padx=20, pady=20)
        self.turnright = customtkinter.CTkButton(self, text="Turn Right")
        self.turnright.pack(padx=20, pady=20)

        # Intercept window close (user presses the X button)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        def forward(self):
            backend.forward()
        def backward(self):
            backend.backward()
        def left(self):
            backend.turn_left()
        def right(self):
            backend.turn_right()
        def stop(self):
            backend.stop()

        self.forward.bind("<ButtonPress-1>", forward)
        self.forward.bind("<ButtonRelease-1>", stop)
        self.backward.bind("<ButtonPress-1>", backward)
        self.backward.bind("<ButtonRelease-1>", stop)
        self.turnleft.bind("<ButtonPress-1>", left)
        self.turnleft.bind("<ButtonRelease-1>", stop)
        self.turnright.bind("<ButtonPress-1>", right)
        self.turnright.bind("<ButtonRelease-1>", stop)
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