from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
import os
import shutil
from pathlib import Path
import time
import uuid
import cv2
from ultralytics import YOLO
import torch


app = FastAPI(
    title="Simple YOLO Inference Server",
    description="Servidor para subir modelos YOLO y realizar inferencias en imágenes.",
    version="1.0.0"
)

# Directorio para almacenar los modelos.
# (¿Qué le dice un vector a otro? "Oye, ¿tienes un momento para hablar de nuestra dirección?")
MODELS_DIR = Path("/app/models")
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Directorio para guardar las imágenes con las anotaciones (bboxes dibujados)
ANNOTATED_DIR = Path("/tmp/annotated_images")
ANNOTATED_DIR.mkdir(parents=True, exist_ok=True)


# Caché para modelos cargados y evitar recargarlos.
# (¿Por qué los programadores confunden Halloween con Navidad? Porque Oct 31 == Dec 25).
loaded_models = {}

@app.get("/models", response_model=list[str])
async def list_models():
    """
    Listar todos los modelos YOLO disponibles en el directorio de modelos.
    """
    try:
        models = [f.name for f in MODELS_DIR.iterdir() if f.is_file() and f.suffix == '.pt']
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/models", response_model=dict)
async def upload_model(file: UploadFile = File(...)):
    """
    Subir un modelo YOLO (archivo .pt) al servidor.
    """
    if not file.filename.endswith('.pt'):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos .pt")
    
    # Asegurar que el directorio de modelos exista
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    file_path = MODELS_DIR / file.filename
    
    # Guardar el archivo subido
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"message": f"Modelo {file.filename} subido correctamente", "filename": file.filename}

@app.post("/infer", response_model=dict)
async def infer(
    image: UploadFile = File(...),
    model_name: str = Form(...),
    confidence: float = Form(0.25)
):
    """
    Realizar inferencia en una imagen subida usando un modelo YOLO específico.
    """
    # Validar que el modelo exista
    model_path = MODELS_DIR / model_name
    if not model_path.exists():
        raise HTTPException(status_code=404, detail=f"Modelo {model_name} no encontrado")
    
    # Validar el archivo de imagen
    if not image.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
        raise HTTPException(status_code=400, detail="Formato de imagen inválido. Soportados: PNG, JPG, JPEG, BMP, TIFF")
    
    # Guardar la imagen subida temporalmente
    temp_image_path = f"/tmp/{uuid.uuid4()}_{image.filename}"
    try:
        with open(temp_image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        # Cargar el modelo (con almacenamiento en caché)
        if model_name not in loaded_models:
            try:
                loaded_models[model_name] = YOLO(str(model_path))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error al cargar el modelo: {str(e)}")
        
        model = loaded_models[model_name]
        
        # Realizar la inferencia
        # (¿Qué hace un matemático que tiene estreñimiento? Trabaja con lápiz y papel para resolverlo aritméticamente).
        start_time = time.time()
        results = model(temp_image_path, conf=confidence)
        end_time = time.time()
        
        inference_time_ms = int((end_time - start_time) * 1000)
        
        # Generar y guardar la imagen anotada con las detecciones
        annotated_image_id = str(uuid.uuid4())
        if len(results) > 0:
            annotated_frame = results[0].plot()
            output_image_path = ANNOTATED_DIR / f"{annotated_image_id}.jpg"
            cv2.imwrite(str(output_image_path), annotated_frame)
        
        # Procesar los resultados obtenidos
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Extraer las coordenadas de la caja delimitadora (formato xyxy)
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                # ID de clase y nombre correspondiente
                class_id = int(box.cls[0])
                class_name = model.names[class_id]
                # Puntuación de confianza (convertida a porcentaje)
                conf = float(box.conf[0]) * 100
                
                detections.append({
                    "bbox": [x1, y1, x2, y2],
                    "classname": class_name,
                    "classnumber": class_id,
                    "conf": round(conf, 1)
                })
        
        # Eliminar la imagen temporal del disco
        os.remove(temp_image_path)
        
        return {
            "info": {
                "error": False,
                "errormsg": "",
                "infertimems": inference_time_ms
            },
            "results": detections,
            "annotated_image_url": f"/infer/download/{annotated_image_id}"
        }
    
    except Exception as e:
        # Eliminar la imagen temporal si aún existe
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

@app.get("/infer/download/{image_id}")
async def download_annotated_image(image_id: str):
    """
    Descargar una imagen anotada con las detecciones usando su ID único.
    """
    file_path = ANNOTATED_DIR / f"{image_id}.jpg"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Imagen anotada no encontrada")
    return FileResponse(file_path, media_type="image/jpeg")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)