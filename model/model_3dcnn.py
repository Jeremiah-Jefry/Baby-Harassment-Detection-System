import torch
import torch.nn as nn
import torch.nn.functional as F

class Simple3DCNN(nn.Module):
    def __init__(self, num_classes):
        super().__init__()

        self.conv1 = nn.Conv3d(3, 16, kernel_size=3, padding=1)
        self.bn1   = nn.BatchNorm3d(16)
        self.pool1 = nn.MaxPool3d((1, 2, 2))   # keep time, downsample H,W

        self.conv2 = nn.Conv3d(16, 32, kernel_size=3, padding=1)
        self.bn2   = nn.BatchNorm3d(32)
        self.pool2 = nn.MaxPool3d((2, 2, 2))   # downsample T,H,W

        self.conv3 = nn.Conv3d(32, 64, kernel_size=3, padding=1)
        self.bn3   = nn.BatchNorm3d(64)
        self.pool3 = nn.AdaptiveMaxPool3d((1, 1, 1))  # global pool

        self.fc = nn.Linear(64, num_classes)

    def forward(self, x):
        # x: [B, 3, T, 224, 224]
        x = self.pool1(F.relu(self.bn1(self.conv1(x))))
        x = self.pool2(F.relu(self.bn2(self.conv2(x))))
        x = self.pool3(F.relu(self.bn3(self.conv3(x))))
        x = x.view(x.size(0), -1)  # [B, 64]
        x = self.fc(x)
        return x
