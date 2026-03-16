# Guardian Eyes - Video Classification System

An AI-powered video classification system using 3D CNN for activity recognition and video analysis.

## Features

- **Video Classification**: Classify videos into predefined categories using deep learning
- **Web Interface**: User-friendly web interface for video upload and analysis
- **REST API**: RESTful API for integration with other systems
- **Real-time Processing**: Fast inference with GPU acceleration support
- **Model Training**: Complete training pipeline with validation and metrics

## Project Structure

```
model/
├── app.py                 # Flask API server
├── train_improved.py      # Improved training script
├── video_dataset.py       # Dataset class for loading videos
├── model_3dcnn.py         # 3D CNN model architecture
├── video_processor.py     # Video preprocessing utilities
├── templates/
│   └── index.html        # Web interface
├── checkpoints/          # Saved model checkpoints
├── logs/                 # Training logs and plots
├── uploads/              # Temporary video uploads
├── label/                # CSV files with video labels
├── clips/                # Video files
├── requirements.txt      # Python dependencies
├── BACKEND_UPGRADE_GUIDE.md  # Scaling recommendations
└── README.md            # This file
```

## Quick Start

### 1. Installation

```bash
# Clone or download the project
cd model

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Prepare Your Data

1. Place your video files in the `clips/` directory
2. Create a CSV file in `label/` directory with the following format:

```csv
filepath,label
clips/video1.mp4,fighting
clips/video2.mp4,normal
clips/video3.mp4,suspicious
```

3. Save it as `all_labels.csv` in the `label/` directory

### 3. Train the Model

```bash
python train_improved.py
```

This will:
- Split your data into train/validation sets
- Train the 3D CNN model
- Save the best model to `checkpoints/best_model.pt`
- Generate training curves and logs

### 4. Run the Web Application

```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Usage

### Web Interface

1. Open `http://localhost:5000` in your browser
2. Upload a video file (MP4, AVI, MOV, etc.)
3. Click "Analyze Video" to get predictions
4. View the classification results with confidence scores

### API Usage

#### Health Check
```bash
curl http://localhost:5000/health
```

#### Model Information
```bash
curl http://localhost:5000/model_info
```

#### Video Classification
```bash
curl -X POST -F "video=@your_video.mp4" http://localhost:5000/predict
```

Response format:
```json
{
  "success": true,
  "prediction": "fighting",
  "confidence": 0.85,
  "top_predictions": [
    {"class": "fighting", "confidence": 0.85},
    {"class": "suspicious", "confidence": 0.10},
    {"class": "normal", "confidence": 0.05}
  ],
  "processing_time": "2024-01-01T12:00:00"
}
```

## Model Architecture

The system uses a 3D Convolutional Neural Network with the following architecture:

- **Input**: Video clips (16 frames, 224x224 pixels, 3 channels)
- **Conv3D Layers**: 3D convolutions for spatiotemporal feature extraction
- **Batch Normalization**: Stabilizes training
- **Max Pooling**: Reduces spatial/temporal dimensions
- **Global Pooling**: Produces fixed-size feature vector
- **Fully Connected Layer**: Final classification

## Configuration

### Training Parameters

You can modify training parameters in `train_improved.py`:

```python
config = Config()
config.batch_size = 4
config.frames_per_clip = 16
config.num_epochs = 20
config.lr = 1e-4
```

### Model Parameters

- **Input Size**: 224x224 pixels
- **Frames per Clip**: 16 (configurable)
- **Number of Classes**: Determined from your dataset
- **Device**: Automatically uses GPU if available

## Performance

### Hardware Requirements

**Minimum Requirements:**
- CPU: 4+ cores
- RAM: 8GB
- Storage: 5GB free space

**Recommended for Training:**
- GPU: NVIDIA GTX 1060 or better
- VRAM: 4GB+
- RAM: 16GB
- Storage: SSD with 20GB+ free space

### Benchmarks

- **Inference Time**: ~2-5 seconds per video (GPU)
- **Model Size**: ~50MB
- **Supported Video Formats**: MP4, AVI, MOV, MKV, WMV, FLV
- **Max File Size**: 100MB (configurable)

## Troubleshooting

### Common Issues

1. **CUDA Out of Memory**
   - Reduce batch size in training
   - Use smaller frame resolution
   - Close other GPU applications

2. **Video Processing Errors**
   - Ensure video files are not corrupted
   - Check file format support
   - Verify file permissions

3. **Model Loading Errors**
   - Check if model file exists in `checkpoints/`
   - Verify model architecture matches checkpoint
   - Ensure all dependencies are installed

### Logs and Debugging

- Training logs are saved in `logs/training_history.json`
- Training curves are saved in `logs/training_curves.png`
- Flask logs are printed to console

## Scaling and Production

For production deployment and scaling, refer to `BACKEND_UPGRADE_GUIDE.md` which includes:

- Containerization with Docker
- Migration to FastAPI
- Load balancing and horizontal scaling
- Message queues for async processing
- Cloud deployment strategies
- Monitoring and security best practices

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the backend upgrade guide
3. Create an issue with detailed information about your problem

## Acknowledgments

- PyTorch team for the deep learning framework
- OpenCV for video processing
- Flask team for the web framework
- Scikit-learn for data utilities
