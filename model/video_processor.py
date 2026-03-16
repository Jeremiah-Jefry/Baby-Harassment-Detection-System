import os
import cv2
import numpy as np
import torch
from typing import Tuple, Optional

class VideoProcessor:
    def __init__(self, frames_per_clip: int = 16, target_size: Tuple[int, int] = (224, 224)):
        """
        Initialize video processor for inference.
        
        Args:
            frames_per_clip: Number of frames to extract from video
            target_size: Target size for frames (width, height)
        """
        self.frames_per_clip = frames_per_clip
        self.target_size = target_size
    
    def process_video(self, video_path: str) -> Optional[np.ndarray]:
        """
        Process a video file and return frames as tensor.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Processed frames as numpy array [T, H, W, C] or None if failed
        """
        if not os.path.exists(video_path):
            print(f"Video file not found: {video_path}")
            return None
        
        try:
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if total_frames == 0:
                print(f"Empty video: {video_path}")
                cap.release()
                return None
            
            # Calculate frame indices to sample
            if total_frames >= self.frames_per_clip:
                step = total_frames / self.frames_per_clip
                frame_indices = [int(i * step) for i in range(self.frames_per_clip)]
            else:
                frame_indices = list(range(total_frames))
                # Repeat last frame if video is too short
                while len(frame_indices) < self.frames_per_clip:
                    frame_indices.append(frame_indices[-1])
            
            frames = []
            for frame_idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                
                if not ret:
                    # Use last valid frame if reading fails
                    if frames:
                        frame = frames[-1]
                    else:
                        print(f"Failed to read frame {frame_idx} from {video_path}")
                        cap.release()
                        return None
                
                # Convert BGR to RGB and resize
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, self.target_size)
                frames.append(frame)
            
            cap.release()
            
            # Stack frames: [T, H, W, C]
            video_array = np.stack(frames, axis=0)
            return video_array
            
        except Exception as e:
            print(f"Error processing video {video_path}: {str(e)}")
            return None
    
    def preprocess_for_model(self, video_array: np.ndarray) -> torch.Tensor:
        """
        Convert video array to tensor format expected by model.
        
        Args:
            video_array: Video frames as numpy array [T, H, W, C]
            
        Returns:
            Tensor ready for model input [1, 3, T, H, W]
        """
        # Convert to tensor and rearrange dimensions
        # [T, H, W, C] -> [C, T, H, W]
        tensor = torch.from_numpy(video_array).permute(3, 0, 1, 2).float()
        
        # Normalize to [0, 1]
        tensor = tensor / 255.0
        
        # Add batch dimension: [1, C, T, H, W]
        tensor = tensor.unsqueeze(0)
        
        return tensor
    
    def process_and_preprocess(self, video_path: str) -> Optional[torch.Tensor]:
        """
        Complete pipeline: process video and return model-ready tensor.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Model-ready tensor or None if processing failed
        """
        video_array = self.process_video(video_path)
        if video_array is None:
            return None
        
        return self.preprocess_for_model(video_array)

def save_uploaded_video(upload_folder: str, file) -> str:
    """
    Save uploaded video file to specified folder.
    
    Args:
        upload_folder: Directory to save the file
        file: Uploaded file object
        
    Returns:
        Path to saved file
    """
    os.makedirs(upload_folder, exist_ok=True)
    
    # Generate unique filename
    import uuid
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(upload_folder, unique_filename)
    
    # Save file
    file.save(file_path)
    
    return file_path

def cleanup_temp_file(file_path: str):
    """
    Clean up temporary file.
    
    Args:
        file_path: Path to file to delete
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Error cleaning up file {file_path}: {str(e)}")
