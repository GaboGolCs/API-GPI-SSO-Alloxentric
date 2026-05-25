import os
import asyncio # <--- Importante para manejar el bloqueo
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url
from dotenv import load_dotenv

load_dotenv()

cloudinary.config(
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key    = os.getenv("CLOUDINARY_API_KEY"),
    api_secret = os.getenv("CLOUDINARY_API_SECRET"),
    secure     = True,
)

# Creamos una función interna puramente síncrona para Cloudinary
def _sync_upload(file_bytes: bytes, folder_path: str, public_id: str):
    return cloudinary.uploader.upload(
        file_bytes,
        folder        = folder_path,
        public_id     = public_id,
        overwrite     = True,
        resource_type = "image",
    )

async def upload_image(file_bytes: bytes, report_id: str) -> str:
    """
    Sube una imagen a Cloudinary de forma asíncrona (sin bloquear el microservicio)
    y devuelve la URL pública.
    """
    folder_path = f"sso-reports/{report_id}"
    public_id = f"evidence_{report_id}"
    
    try:
        # Ejecutamos la función síncrona en un hilo separado de forma asíncrona
        result = await asyncio.to_thread(
            _sync_upload, 
            file_bytes, 
            folder_path, 
            public_id
        )
        return result["secure_url"]
        
    except Exception as e:
        # Aquí puedes manejar errores de conexión o credenciales de Cloudinary
        print(f"Error al subir imagen a Cloudinary: {e}")
        raise e
async def upload_image(file_bytes: bytes, report_id: str) -> str:
    folder_path = f"sso-reports/{report_id}"
    public_id = f"evidence_{report_id}"
    
    print(f"--- [DEBUG] Intentando subir imagen para el reporte: {report_id} ---")
    try:
        result = await asyncio.to_thread(_sync_upload, file_bytes, folder_path, public_id)
        print(f"--- [DEBUG] Éxito en Cloudinary! URL: {result.get('secure_url')} ---")
        return result["secure_url"]
    except Exception as e:
        print(f"--- [DEBUG] ERROR CRÍTICO EN CLOUDINARY: {e} ---")
        raise e