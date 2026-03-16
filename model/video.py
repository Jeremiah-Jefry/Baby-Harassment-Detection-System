import cv2
import os

video_path = r"C:\Users\KiTE\Downloads\dataset11.mp4"  # change per video

# folder name = video name without extension
video_name = os.path.splitext(os.path.basename(video_path))[0]
output_root = os.path.join("clips", video_name)
os.makedirs(output_root, exist_ok=True)

clip_duration_sec = 2
overlap = 0

cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    print("Error: could not open video")
    exit()

fps = cap.get(cv2.CAP_PROP_FPS)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

clip_frames = int(clip_duration_sec * fps)
step = int((clip_duration_sec - overlap) * fps) if overlap < clip_duration_sec else clip_frames

start = 0
clip_idx = 0

while start + clip_frames <= total_frames:
    cap.set(cv2.CAP_PROP_POS_FRAMES, start)
    ret, frame = cap.read()
    if not ret:
        break

    h, w = frame.shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out_path = os.path.join(output_root, f"clip_{clip_idx:04d}.mp4")
    writer = cv2.VideoWriter(out_path, fourcc, fps, (w, h))

    frames_written = 0
    writer.write(frame)
    frames_written += 1

    while frames_written < clip_frames:
        ret, frame = cap.read()
        if not ret:
            break
        writer.write(frame)
        frames_written += 1

    writer.release()
    clip_idx += 1
    start += step

cap.release()
print("Done, clips saved to:", output_root)
