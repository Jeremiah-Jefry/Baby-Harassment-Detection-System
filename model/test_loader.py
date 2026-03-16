from torch.utils.data import DataLoader
from video_dataset import GuardianEyesDataset

csv_path = r"C:\Users\KiTE\Desktop\model\label\all_labels.csv"
root_dir = r"C:\Users\KiTE\Desktop\model"

dataset = GuardianEyesDataset(csv_path, root_dir, frames_per_clip=8)
loader = DataLoader(dataset, batch_size=2, shuffle=True)

for videos, labels in loader:
    print("Video batch shape:", videos.shape)  # [B, C, T, H, W]
    print("Labels:", labels)
    break
