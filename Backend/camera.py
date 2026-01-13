"""Cozmo camera Flask integration.

This module exposes a `CozmoCamera` class which can be imported and used
by a Flask application. The parent process is expected to create and own
the pycozmo `cli` object and pass it to `CozmoCamera`.

Example usage (in your Flask server file):

    with pycozmo.connect(...) as cli:
        app = Flask(__name__)
        cam = CozmoCamera(cli)
        app.register_blueprint(cam.bp)
        cam.start()  # enable camera and register handler
        app.run(host='0.0.0.0', port=5000)

"""

from io import BytesIO
import threading
from typing import Optional

import cv2
import numpy as np
from PIL import Image
from flask import Blueprint, Flask, Response, render_template_string

import pycozmo


DEFAULT_INDEX_HTML = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Cozmo Camera</title>
    <style>body{background:#111;color:#eee;font-family:Arial,Helvetica,sans-serif;text-align:center} img{max-width:100%;height:auto;border:4px solid #222;margin-top:12px}</style>
  </head>
  <body>
    <h1>Cozmo Camera Feed</h1>
    <img src="{{ url_for('cozmo_camera.video_feed') }}" alt="Camera feed" />
    <p>MJPEG stream from Cozmo</p>
  </body>
</html>
"""


class CozmoCamera:
    """Provide a Flask Blueprint that serves Cozmo's camera as an MJPEG stream.

    Args:
        cli: An active pycozmo client instance (created in the parent file).
        blueprint_name: Optional blueprint name (default 'cozmo_camera').
        url_prefix: Optional URL prefix for the blueprint (default None).
    """

    def __init__(self, cli: pycozmo.client.Client, *, blueprint_name: str = 'cozmo_camera', url_prefix: Optional[str] = None):
        self.cli = cli
        self._last_im: Optional[Image.Image] = None
        self._lock = threading.Lock()
        self._running = False
        self._stop_event = threading.Event()

        # Flask blueprint
        self.bp = Blueprint(blueprint_name, __name__, template_folder='templates', url_prefix=url_prefix)
        self.bp.add_url_rule('/', 'index', self._index)
        self.bp.add_url_rule('/video_feed', 'video_feed', self.video_feed)

    # --- Image handler -------------------------------------------------
    def _on_camera_image(self, cli, new_im):
        """pycozmo event handler for new raw camera images."""
        with self._lock:
            self._last_im = new_im

    # --- Lifecycle -----------------------------------------------------
    def start(self):
        """Start listening to the camera feed and enable the camera on the robot."""
        if self._running:
            return
        # Register handler
        self.cli.add_handler(pycozmo.event.EvtNewRawCameraImage, self._on_camera_image)
        # Enable camera on the robot
        self.cli.enable_camera()
        self._running = True
        self._stop_event.clear()

    def stop(self):
        """Stop listening and (optionally) disable the camera handler."""
        if not self._running:
            return
        try:
            self.cli.remove_handler(pycozmo.event.EvtNewRawCameraImage, self._on_camera_image)
        except Exception:
            # Some pycozmo versions might not expose remove_handler; ignore
            pass
        # Do not disable camera on robot here; leave that to the parent process
        self._running = False
        self._stop_event.set()

    # --- Flask views / generator --------------------------------------
    def _index(self):
        return render_template_string(DEFAULT_INDEX_HTML)

    def video_feed(self):
        return Response(self.generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

    def _get_latest_frame(self) -> Optional[bytes]:
        """Return the latest camera image as JPEG bytes, or None if unavailable."""
        with self._lock:
            im = self._last_im
            # clear last image so we don't resend the same frame repeatedly
            self._last_im = None

        if im is None:
            return None

        # Ensure PIL Image -> RGB numpy array
        frame = np.array(im.convert('RGB'))
        # Convert RGB -> BGR for OpenCV
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        # Encode as JPEG
        ret, buf = cv2.imencode('.jpg', frame)
        if not ret:
            return None
        return buf.tobytes()

    def generate_frames(self):
        """Generator yielding multipart JPEG frames for the MJPEG stream."""
        # Main loop: yield frames until stopped
        while not self._stop_event.is_set():
            data = self._get_latest_frame()
            if data is None:
                # No new frame; sleep a short time to avoid busy-looping
                self._stop_event.wait(0.05)
                continue

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + data + b'\r\n')


if __name__ == '__main__':
    # Example standalone run for quick testing. The user still needs to
    # run this while a Cozmo is available and connected.
    from flask import Flask

    app = Flask(__name__)

    print('Starting Cozmo camera example. This will block. Make sure Cozmo is available.')

    with pycozmo.connect(enable_procedural_face=False) as cli:
        cam = CozmoCamera(cli)
        app.register_blueprint(cam.bp, url_prefix=None)
        cam.start()
        app.run(host='0.0.0.0', port=5000)

