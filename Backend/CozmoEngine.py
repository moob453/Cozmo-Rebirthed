from time import sleep
import cv2
import mediapipe as mp
import time
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class Engine:
    def __init__(self, energy, boardem, sleeping):
        self.energy = energy
        self.boardem = boardem
        self.sleeping = sleeping

    def tick(self):
        if self.boardem > 100:
            self.sleeping = True
        if self.sleeping:
            print("cozmo is sleeping")
            self.boardem = 0
            sleep(0.1)
        self.boardem += 1
        sleep(0.1)


Cozmo = Engine(100, 0, False)

print("Starting Cozmo Engine...")
sleep(1)
print("begin wake animation")
#future - add wake animation here


#while True:
#    
#   Cozmo.tick()
#    print(Cozmo.boardem)
#    if Cozmo.boardem > 50:
#        print("cozmo is getting bored")


#Opencv experimentation
# 1. Configuration
model_path = 'Backend/face_detector.tflite' # Ensure this file is in your folder

BaseOptions = mp.tasks.BaseOptions
FaceDetector = mp.tasks.vision.FaceDetector
FaceDetectorOptions = mp.tasks.vision.FaceDetectorOptions
VisionRunningMode = mp.tasks.vision.RunningMode

# 2. Setup the Detector
options = FaceDetectorOptions(
    base_options=BaseOptions(model_asset_path=model_path),
    running_mode=VisionRunningMode.VIDEO # Optimized for camera feeds
)

with FaceDetector.create_from_options(options) as detector:
    cap = cv2.VideoCapture(0)
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success: break

        # 3. Convert frame to MediaPipe Image object
        # MediaPipe requires RGB and a timestamp for VIDEO/LIVE_STREAM mode
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        timestamp_ms = int(time.time() * 1000)
        
        # 4. Detect Faces
        detection_result = detector.detect_for_video(mp_image, timestamp_ms)

        # 5. Draw Results
        if detection_result.detections:
            for detection in detection_result.detections:
                bbox = detection.bounding_box
                cv2.rectangle(frame, (int(bbox.origin_x), int(bbox.origin_y)),
                              (int(bbox.origin_x + bbox.width), int(bbox.origin_y + bbox.height)),
                              (0, 255, 0), 2)

        cv2.imshow('MediaPipe Tasks Face Detection', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()