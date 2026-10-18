# Pose estimation

Owner: Person 3. Defines `PoseEstimator`, canonical `PoseSequence`, and the MVP MediaPipe adapter. YOLO Pose and MMPose remain future alternatives.

The adapter loads a local Pose Landmarker model and never downloads one. Tests that call the real model skip unless `MEDIAPIPE_POSE_MODEL_PATH` points to a file, with the reason `MEDIAPIPE_POSE_MODEL_PATH is not set or does not point to a file`. Unit tests inject a fake backend.
