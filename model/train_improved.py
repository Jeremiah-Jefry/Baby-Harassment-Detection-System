import os
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from tqdm import tqdm
import json

from video_dataset import GuardianEyesDataset
from model_3dcnn import Simple3DCNN

class Config:
    def __init__(self):
        self.root_dir = r"C:\Users\KiTE\Desktop\model"
        self.csv_all = os.path.join(self.root_dir, "label", "all_labels.csv")
        
        # Training parameters
        self.batch_size = 4
        self.frames_per_clip = 16
        self.num_epochs = 20
        self.lr = 1e-4
        self.weight_decay = 1e-5
        
        # Model parameters
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.save_dir = os.path.join(self.root_dir, "checkpoints")
        self.log_dir = os.path.join(self.root_dir, "logs")
        
        # Create directories
        os.makedirs(self.save_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)

def train_model():
    config = Config()
    
    print("=== Guardian Eyes Video Classification Training ===")
    print(f"Device: {config.device}")
    print(f"Root directory: {config.root_dir}")
    
    # Load and split data
    df = pd.read_csv(config.csv_all)
    print(f"Total samples: {len(df)}")
    print(f"Classes: {df['label'].value_counts().to_dict()}")
    
    # Stratified split
    train_df, val_df = train_test_split(
        df, test_size=0.2, random_state=42, stratify=df["label"]
    )
    
    # Save split CSVs
    train_csv = os.path.join(config.root_dir, "label", "train.csv")
    val_csv = os.path.join(config.root_dir, "label", "val.csv")
    train_df.to_csv(train_csv, index=False)
    val_df.to_csv(val_csv, index=False)
    
    print(f"Training samples: {len(train_df)}")
    print(f"Validation samples: {len(val_df)}")
    
    # Create datasets and loaders
    train_dataset = GuardianEyesDataset(
        train_csv, config.root_dir, frames_per_clip=config.frames_per_clip
    )
    val_dataset = GuardianEyesDataset(
        val_csv, config.root_dir, frames_per_clip=config.frames_per_clip
    )
    
    train_loader = DataLoader(
        train_dataset, batch_size=config.batch_size, shuffle=True, num_workers=2
    )
    val_loader = DataLoader(
        val_dataset, batch_size=config.batch_size, shuffle=False, num_workers=2
    )
    
    # Initialize model
    num_classes = len(train_dataset.label2idx)
    model = Simple3DCNN(num_classes=num_classes).to(config.device)
    
    # Loss and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(
        model.parameters(), lr=config.lr, weight_decay=config.weight_decay
    )
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=3
    )
    
    # Training history
    history = {
        'train_loss': [], 'train_acc': [],
        'val_loss': [], 'val_acc': [],
        'lr': []
    }
    
    best_val_acc = 0.0
    
    print("\n=== Starting Training ===")
    
    for epoch in range(1, config.num_epochs + 1):
        # Training phase
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0
        
        train_pbar = tqdm(train_loader, desc=f"Epoch {epoch}/{config.num_epochs} [Train]")
        
        for videos, labels in train_pbar:
            videos = videos.to(config.device)
            labels = labels.to(config.device)
            
            optimizer.zero_grad()
            outputs = model(videos)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item() * videos.size(0)
            _, preds = outputs.max(1)
            train_correct += (preds == labels).sum().item()
            train_total += labels.size(0)
            
            # Update progress bar
            current_acc = train_correct / train_total
            train_pbar.set_postfix({
                'loss': f'{loss.item():.4f}',
                'acc': f'{current_acc:.3f}'
            })
        
        train_loss /= train_total
        train_acc = train_correct / train_total
        
        # Validation phase
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        all_preds = []
        all_labels = []
        
        with torch.no_grad():
            val_pbar = tqdm(val_loader, desc=f"Epoch {epoch}/{config.num_epochs} [Val]")
            
            for videos, labels in val_pbar:
                videos = videos.to(config.device)
                labels = labels.to(config.device)
                
                outputs = model(videos)
                loss = criterion(outputs, labels)
                
                val_loss += loss.item() * videos.size(0)
                _, preds = outputs.max(1)
                val_correct += (preds == labels).sum().item()
                val_total += labels.size(0)
                
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())
                
                # Update progress bar
                current_val_acc = val_correct / val_total
                val_pbar.set_postfix({
                    'loss': f'{loss.item():.4f}',
                    'acc': f'{current_val_acc:.3f}'
                })
        
        val_loss /= val_total
        val_acc = val_correct / val_total
        
        # Update learning rate
        scheduler.step(val_loss)
        current_lr = optimizer.param_groups[0]['lr']
        
        # Save history
        history['train_loss'].append(train_loss)
        history['train_acc'].append(train_acc)
        history['val_loss'].append(val_loss)
        history['val_acc'].append(val_acc)
        history['lr'].append(current_lr)
        
        # Print epoch results
        print(f"\nEpoch {epoch}/{config.num_epochs}:")
        print(f"  Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.3f}")
        print(f"  Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.3f}")
        print(f"  Learning Rate: {current_lr:.6f}")
        
        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_model_path = os.path.join(config.save_dir, "best_model.pt")
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'label2idx': train_dataset.label2idx,
                'idx2label': train_dataset.idx2label,
                'val_acc': val_acc,
                'config': {
                    'frames_per_clip': config.frames_per_clip,
                    'num_classes': num_classes
                }
            }, best_model_path)
            print(f"  ✓ New best model saved! Val Acc: {val_acc:.3f}")
    
    # Save final model
    final_model_path = os.path.join(config.save_dir, "final_model.pt")
    torch.save({
        'epoch': config.num_epochs,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'label2idx': train_dataset.label2idx,
        'idx2label': train_dataset.idx2label,
        'val_acc': val_acc,
        'config': {
            'frames_per_clip': config.frames_per_clip,
            'num_classes': num_classes
        }
    }, final_model_path)
    
    # Save training history
    history_path = os.path.join(config.log_dir, "training_history.json")
    with open(history_path, 'w') as f:
        json.dump(history, f, indent=2)
    
    # Plot training curves
    plt.figure(figsize=(15, 5))
    
    plt.subplot(1, 3, 1)
    plt.plot(history['train_loss'], label='Train Loss')
    plt.plot(history['val_loss'], label='Val Loss')
    plt.title('Training and Validation Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.grid(True)
    
    plt.subplot(1, 3, 2)
    plt.plot(history['train_acc'], label='Train Acc')
    plt.plot(history['val_acc'], label='Val Acc')
    plt.title('Training and Validation Accuracy')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.legend()
    plt.grid(True)
    
    plt.subplot(1, 3, 3)
    plt.plot(history['lr'])
    plt.title('Learning Rate Schedule')
    plt.xlabel('Epoch')
    plt.ylabel('Learning Rate')
    plt.grid(True)
    
    plt.tight_layout()
    plot_path = os.path.join(config.log_dir, "training_curves.png")
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\n=== Training Complete ===")
    print(f"Best Validation Accuracy: {best_val_acc:.3f}")
    print(f"Best model saved to: {best_model_path}")
    print(f"Final model saved to: {final_model_path}")
    print(f"Training history saved to: {history_path}")
    print(f"Training curves saved to: {plot_path}")
    
    return model, train_dataset.label2idx, train_dataset.idx2label

if __name__ == "__main__":
    model, label2idx, idx2label = train_model()
