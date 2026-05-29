# Servidor de Inferencia YOLO Simple

Un servidor FastAPI para subir modelos YOLO y realizar inferencia en imágenes.

## Características

- Lista modelos YOLO disponibles (`GET /models`)
- Sube nuevos modelos YOLO (`POST /models`)
- Realiza inferencia en imágenes con modelo y umbral de confianza especificados (`POST /infer`)
- Documentación Swagger automática en `/docs`

## Estructura del Proyecto

```
simple-yolo-inference-server/
├── app/
│   └── models/           # Directorio para almacenar archivos de modelos YOLO (.pt)
├── main.py               # Aplicación FastAPI
├── requirements.txt      # Dependencias de Python
├── Dockerfile            # Instrucciones de construcción de Docker
├── docker-compose.yml    # Configuración de docker-compose
└── README.md             # Este archivo
```

## Instalación y Uso

### Prerrequisitos

- Docker y Docker Compose (para despliegue contenedorizado)
- O Python 3.9+ y pip (para desarrollo local)

### Desarrollo Local

1. Clona el repositorio:
   ```bash
   git clone https://github.com/magm3333/simple-yolo-inference-server.git
   cd simple-yolo-inference-server
   ```

2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Ejecuta el servidor:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

4. Accede a la documentación de la API en http://localhost:8000/docs

### Despliegue con Docker

1. Construye y ejecuta con Docker Compose:
   ```bash
   docker-compose up --build
   ```

2. El servidor estará disponible en http://localhost:8000

3. Los modelos se persisten en el directorio `./app/models` del host.

### Construcción y Ejecución Manual de Docker

```bash
# Construir la imagen
docker build -t magm3333/simple-yolo-inference-server .

# Ejecutar el contenedor
docker run -p 8000:8000 -v $(pwd)/app/models:/app/models magm3333/simple-yolo-inference-server
```

## Endpoints de la API

### GET /models
Devuelve una lista de archivos de modelos YOLO disponibles en el directorio `/app/models`.

**Respuesta:**
```json
["yolo11n.pt", "yolo11s.pt"]
```

### POST /models
Sube un nuevo modelo YOLO (.pt file).

**Parámetros:**
- `file`: El archivo de modelo YOLO para subir (debe tener extensión .pt)

**Respuesta:**
```json
{
  "message": "Model yolo11n.pt uploaded successfully",
  "filename": "yolo11n.pt"
}
```

### POST /infer
Realiza inferencia en una imagen utilizando un modelo YOLO especificado. Además, genera una versión anotada de la imagen con los bounding boxes dibujados en el servidor, devolviendo un ID para su posterior descarga.

**Parámetros:**
- `image`: El archivo de imagen para procesar (PNG, JPG, JPEG, BMP, TIFF)
- `model_name`: El nombre del archivo de modelo YOLO (debe existir en `/app/models`)
- `confidence`: Umbral mínimo de confianza para detecciones (por defecto: 0.25)

**Respuesta (Éxito):**
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
  ],
  "annotated_image_url": "/infer/download/1b35d41c-b50d-4a44-8a24-ba1d08107fb9"
}
```

**Respuesta (Error):**
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

### GET /infer/download/{image_id}
Permite descargar la imagen original procesada con las cajas delimitadoras (bounding boxes), nombres de clase y porcentajes de confianza dibujados sobre ella.

**Parámetros de ruta:**
- `image_id`: El identificador único UUID devuelto por el endpoint `/infer` en el campo `annotated_image_url`.

**Respuesta:**
- Retorna un archivo de imagen en formato JPEG (`image/jpeg`). Si la imagen no existe, devuelve una respuesta HTTP `404 Not Found`.


## Imagen de Docker

La imagen de Docker se construye y se envía automáticamente a Docker Hub desde este repositorio.

**Nombre de la Imagen:** `magm3333/simple-yolo-inference-server`
**Etiqueta:** `latest` (actualizada automáticamente en cada commit a main)

### Para usar la imagen pre-construida desde Docker Hub:

1. Extrae la imagen:
```bash
docker pull magm3333/simple-yolo-inference-server:latest
```

2. Ejecuta el contenedor (monta tu directorio de modelos para persistencia):
```bash
docker run -d \
  --name yolo-inference \
  -p 8000:8000 \
  -v /tu/ruta/local/de/modelos:/app/models \
  magm3333/simple-yolo-inference-server:latest
```

3. Accede a la API en http://localhost:8000
   - Documentación Swagger: http://localhost:8000/docs
   - Verificación de salud: http://localhost:8000/models

### Para construir y ejecutar localmente (alternativa):

```bash
# Construir la imagen
docker build -t magm3333/simple-yolo-inference-server .

# Ejecutar el contenedor
docker run -d \
  --name yolo-inference \
  -p 8000:8000 \
  -v $(pwd)/app/models:/app/models \
  magm3333/simple-yolo-inference-server
```

### Script de Automatización de Build y Push:

Se incluye un script `build.sh` para automatizar la construcción de la imagen y su publicación en Docker Hub:

```bash
# Otorgar permisos de ejecución si no los tiene
chmod +x build.sh

# Construir la imagen local y subirla a Docker Hub
./build.sh
```


## Ejecución directa con GPU

Para ejecutar el servidor directamente en una máquina con GPU NVIDIA, asegúrate de tener los drivers y la versión de CUDA apropiada instalada. Luego, instala las dependencias con soporte para CUDA:

```bash
# Instalar PyTorch con CUDA (ejemplo para CUDA 12.1)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
```

Luego ejecuta como de costumbre:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Docker Compose con GPU

Para usar Docker Compose con soporte GPU, asegúrate de tener instalado el [runtime de NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html). Luego, modifica tu archivo `docker-compose.yml` de la siguiente manera:

```yaml
version: '3.8'

services:
  yolo-inference:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./app/models:/app/models
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - NVIDIA_DRIVER_CAPABILITIES=compute,utility
    restart: unless-stopped
```

Luego ejecuta:

```bash
docker-compose up --build
```

Nota: La imagen base `python:3.9-slim` no incluye drivers de NVIDIA; al usar el runtime `nvidia`, el contenedor accederá a los drivers del host.

## Almacenamiento de Modelos

Los modelos se almacenan en el directorio `/app/models` dentro del contenedor.
Al usar Docker Compose o montaje de volúmenes, esto se asigna a `./app/models` en el host.

## Notas

- El servidor utiliza Ultralytics YOLO para la inferencia.
- La primera vez que se utiliza un modelo, se cargará en memoria y se almacenará en caché para solicitudes posteriores.
- El servidor está diseñado para ser ligero y eficiente.

## Licencia

Este proyecto es para uso académico y fue creado por Magm.