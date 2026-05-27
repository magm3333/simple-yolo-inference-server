# Simple YOLO Inference Server

A FastAPI server for uploading YOLO models and performing inference on images.

## Features

- List available YOLO models (`GET /models`)
- Upload new YOLO models (`POST /models`)
- Perform inference on images with specified model and confidence threshold (`POST /infer`)
- Automatic Swagger documentation at `/docs`

## Project Structure

```
simple-yolo-inference-server/
├── app/
│   └── models/           # Directory for storing YOLO model files (.pt)
├── main.py               # FastAPI application
├── requirements.txt      # Python dependencies
├── Dockerfile            # Docker build instructions
├── docker-compose.yml    # Docker compose configuration
└── README.md             # This file
```

## Installation and Usage

### Prerequisites

- Docker and Docker Compose (for containerized deployment)
- Or Python 3.9+ and pip (for local development)

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/magm3333/simple-yolo-inference-server.git
   cd simple-yolo-inference-server
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the server:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

4. Access the API documentation at http://localhost:8000/docs

### Docker Deployment

1. Build and run with Docker Compose:
   ```bash
   docker-compose up --build
   ```

2. The server will be available at http://localhost:8000

3. Models are persisted in the `./app/models` directory on the host.

### Manual Docker Build and Run

```bash
# Build the image
docker build - magm3333/simple-yolo-inference-server .

# Run the container
docker run -p 8000:8000 -v $(pwd)/app/models:/app/models magm3333/simple-yolo-inference-server
```

## API Endpoints

### GET /models
Returns a list of available YOLO model files in the `/app/models` directory.

**Response:**
```json
["yolo11n.pt", "yolo11s.pt"]
```

### POST /models
Upload a new YOLO model (.pt file).

**Parameters:**
- `file`: The YOLO model file to upload (must have .pt extension)

**Response:**
```json
{
  "message": "Model yolo11n.pt uploaded successfully",
  "filename": "yolo11n.pt"
}
```

### POST /infer
Perform inference on an image using a specified YOLO model.

**Parameters:**
- `image`: The image file to process (PNG, JPG, JPEG, BMP, TIFF)
- `model_name`: The name of the YOLO model file (must exist in `/app/models`)
- `confidence`: Minimum confidence threshold for detections (default: 0.25)

**Response (Success):**
```json
{
  "info": {
    "error": false,
    "errormsg": "",
    "infertimems": 205
  },
  "results": [
    {
      "bbox": [100, 150, 200, 300],
      "classname": "person",
      "classnumber": 0,
      "conf": 84.4
    }
  ]
}
```

**Response (Error):**
```json
{
  "info": {
    "error": true,
    "errormsg": "Model not found",
    "infertimems": -1
  },
  "results": []
}
```

## Docker Image

The Docker image is available on Docker Hub: `magm3333/simple-yolo-inference-server`

To pull and run:
```bash
docker pull magm3333/simple-yolo-inference-server
docker run -p 8000:8000 -v /path/to/models:/app/models magm3333/simple-yolo-inference-server
```

## Model Storage

Models are stored in the `/app/models` directory inside the container.
When using Docker Compose or volume mounting, this maps to `./app/models` on the host.

## Notes

- The server uses Ultralytics YOLO for inference.
- The first time a model is used, it will be loaded into memory and cached for subsequent requests.
- The server is designed to be lightweight and efficient.

## License

This project is proprietary and created by magm.