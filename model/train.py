import os
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from sklearn.model_selection import train_test_split

from video_dataset import GuardianEyesDataset
from model_3dcnn import Simple3DCNN

import pandas as pd

# ----- config -----
root_dir = r"C:\Users\KiTE\Desktop\model"
csv_all  = os.path.join(root_dir, "label", "all_labels.csv")

batch_size = 2
frames_per_clip = 8
num_epochs = 5
lr = 1e-3

# ----- split CSV into train/val -----
df = pd.read_csv(csv_all)
train_df, val_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df["label"])

train_csv = os.path.join(root_dir, "label", "train_tmp.csv")
val_csv   = os.path.join(root_dir, "label", "val_tmp.csv")
train_df.to_csv(train_csv, index=False)
val_df.to_csv(val_csv, index=False)

# ----- datasets & loaders -----
train_dataset = GuardianEyesDataset(train_csv, root_dir, frames_per_clip=frames_per_clip)
val_dataset   = GuardianEyesDataset(val_csv,   root_dir, frames_per_clip=frames_per_clip)

train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
val_loader   = DataLoader(val_dataset,   batch_size=batch_size, shuffle=False)

num_classes = len(train_dataset.label2idx)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = Simple3DCNN(num_classes=num_classes).to(device)
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=lr)

print("Device:", device)
print("Num classes:", num_classes)

# ----- training loop -----
for epoch in range(1, num_epochs + 1):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for videos, labels in train_loader:
        videos = videos.to(device)   # [B, 3, T, 224, 224]
        labels = labels.to(device)

        optimizer.zero_grad()
        outputs = model(videos)      # [B, num_classes]
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * videos.size(0)
        _, preds = outputs.max(1)
        correct += (preds == labels).sum().item()
        total += labels.size(0)

    train_loss = running_loss / total
    train_acc  = correct / total

    # ----- validation -----
    model.eval()
    val_loss = 0.0
    val_correct = 0
    val_total = 0
    with torch.no_grad():
        for videos, labels in val_loader:
            videos = videos.to(device)
            labels = labels.to(device)

            outputs = model(videos)
            loss = criterion(outputs, labels)

            val_loss += loss.item() * videos.size(0)
            _, preds = outputs.max(1)
            val_correct += (preds == labels).sum().item()
            val_total += labels.size(0)

    val_loss /= val_total
    val_acc  = val_correct / val_total

    print(f"Epoch {epoch}/{num_epochs} "
          f"- train loss: {train_loss:.4f}, acc: {train_acc:.3f} "
          f"- val loss: {val_loss:.4f}, acc: {val_acc:.3f}")

# ----- save model -----
os.makedirs(os.path.join(root_dir, "checkpoints"), exist_ok=True)
save_path = os.path.join(root_dir, "checkpoints", "guardianeyes_3dcnn.pt")
torch.save({
    "model_state_dict": model.state_dict(),
    "label2idx": train_dataset.label2idx
}, save_path)

print("Saved model to:", save_path)
