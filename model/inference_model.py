import torch
from model_3dcnn import Simple3DCNN   # this IS your model code

ckpt_path = "checkpoints/best_model.pt"
ckpt = torch.load(ckpt_path, map_location="cpu")

label2idx = ckpt["label2idx"]
idx2label = ckpt["idx2label"]
num_classes = len(label2idx)

model = Simple3DCNN(num_classes)
model.load_state_dict(ckpt["model_state_dict"])
model.eval()
