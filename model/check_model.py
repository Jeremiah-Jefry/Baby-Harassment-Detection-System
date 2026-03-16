import torch
from model_3dcnn import Simple3DCNN   # keep this name same as in your code

ckpt_path = "checkpoints/best_model.pt"   # or "checkpoints/final_model.pt"
ckpt = torch.load(ckpt_path, map_location="cpu")

print("Checkpoint keys:", ckpt.keys())

label2idx = ckpt["label2idx"]
num_classes = len(label2idx)

model = Simple3DCNN(num_classes)
model.load_state_dict(ckpt["model_state_dict"])
model.eval()

print("Model loaded OK with", num_classes, "classes")
