import os
import cv2
import numpy as np
import torch
from torch.utils.data import Dataset
import pandas as pd

class GuardianEyesDataset(Dataset):
    def __init__(self, csv_path, root_dir, frames_per_clip=16, transform=None):
        self.df = pd.read_csv(csv_path)
        self.root_dir = root_dir
        self.frames_per_clip = frames_per_clip
        self.transform = transform

        labels = sorted(self.df["label"].unique())
        self.label2idx = {lbl: i for i, lbl in enumerate(labels)}
        self.idx2label = {i: lbl for lbl, i in self.label2idx.items()}

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        rel_path = row["filepath"]
        label_str = row["label"]
        label = self.label2idx[label_str]

        video_path = os.path.join(self.root_dir, rel_path)
        print("Loading:", video_path)

        frames = self._load_video(video_path)   # [T, H, W, C]

        if self.transform is not None:
            frames = self.transform(frames)

        frames = torch.from_numpy(frames).permute(3, 0, 1, 2).float() / 255.0
        label = torch.tensor(label, dtype=torch.long)
        return frames, label

    def _load_video(self, path):
        cap = cv2.VideoCapture(path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if total == 0:
            raise RuntimeError(f"Empty video: {path}")

        if total >= self.frames_per_clip:
            step = total / self.frames_per_clip
            idxs = [int(i * step) for i in range(self.frames_per_clip)]
        else:
            idxs = list(range(total))
            while len(idxs) < self.frames_per_clip:
                idxs.append(idxs[-1])

        frames = []
        target_size = (224, 224)   # width, height

        for fi in idxs:
            cap.set(cv2.CAP_PROP_POS_FRAMES, fi)
            ok, frame = cap.read()
            if not ok:
                frame = frames[-1]
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, target_size)  # <- make all frames same size
            frames.append(frame)

        cap.release()
        import numpy as np
        return np.stack(frames, axis=0)


      