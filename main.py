from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
import os
import shutil
from pathlib import Path
import time
import uuid
from ultralytics import YOLO
import torch

app = FastAPI(
    title="Simple YOLO Inference Server",
    description="A server for uploading YOLO models and performing inference on images.",
    version="1.0.0"
)

# Directory for storing models
MODELS_DIR = Path("/app/models")
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Cache for loaded models to avoid reloading
loaded_models = {}

@app.get("/models", response_model=list[str])
async def list_models():
    """
    List all available YOLO models in the models directory.
    """
    try:
        models = [f.name for f in MODELS_DIR.iterdir() if f.is_file() and f.suffix == '.pt']
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/models", response_model=dict)
async def upload_model(file: UploadFile = File(...)):
    """
    Upload a YOLO model (.pt file) to the server.
    """
    if not file.filename.endswith('.pt'):
        raise HTTPException(status_code=400, detail="Only .pt files are allowed")
    
    # Ensure the models directory exists
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    file_path = MODELS_DIR / file.filename
    
    # Save the uploaded file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"message": f"Model {file.filename} uploaded successfully", "filename": file.filename}

@app.post("/infer", response_model=dict)
async def infer(
    image: UploadFile = File(...),
    model_name: str = Form(...),
    confidence: float = Form(0.25)
):
    """
    Perform inference on an uploaded image using a specified YOLO model.
    """
    # Validate model exists
    model_path = MODELS_DIR / model_name
    if not model_path.exists():
        raise HTTPException(status_code=404, detail=f"Model {model_name} not found")
    
    # Validate image file
    if not image.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
        raise HTTPException(status_code=400, detail="Invalid image format. Supported formats: PNG, JPG, JPEG, BMP, TIFF")
    
    # Save uploaded image temporarily
    temp_image_path = f"/tmp/{uuid.uuid4()}_{image.filename}"
    try:
        with open(temp_image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        # Load model (with caching)
        if model_name not in loaded_models:
            try:
                loaded_models[model_name] = YOLO(str(model_path))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")
        
        model = loaded_models[model_name]
        
        # Perform inference
        start_time = time.time()
        results = model(temp_image_path, conf=confidence)
        end_time = time.time()
        
        inference_time_ms = int((end_time - start_time) * 1000)
        
        # Process results
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Extract box coordinates (xyxy format)
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                # Class ID and name
                class_id = int(box.cls[0])
                class_name = model.names[class_id]
                # Confidence score
                conf = float(box.conf[0]) * 100  # Convert to percentage
                
                detections.append({
                    "bbox": [x1, y1, x2, y2],
                    "classname": class_name,
                    "classnumber": class_id,
                    "conf": round(conf, 1)
                })
        
        # Clean up temporary image
        os.remove(temp_image_path)
        
        return {
            "info": {
                "error": False,
                "errormsg": "",
                "infertimems": inference_time_ms
            },
            "results": detections
        }
    
    except Exception as e:
        # Clean up temporary image if it exists
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)
        
        return {
            "info": {
                "error": True,
                "errormsg": str(e),
                "infertimems": -1
            },
            "results": []
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)