import os
import uuid
from werkzeug.utils import secure_filename
from PIL import Image as PILImage

class ImageService:
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'avif'}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # Límite estricto de 5 MB
    UPLOAD_FOLDER = 'app/static/images/uploads'

    def __init__(self):
        # Asegurarnos de que la carpeta de subidas exista
        os.makedirs(self.UPLOAD_FOLDER, exist_ok=True)

    def allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS

    def upload_image(self, image_file):
        if not image_file or image_file.filename == '':
            return None
        
        if not self.allowed_file(image_file.filename):
            raise ValueError("Formato de imagen no permitido. Usa JPG, PNG o WEBP.")

        # Validar el tamaño del archivo en memoria antes de procesarlo
        image_file.seek(0, os.SEEK_END)
        file_length = image_file.tell()
        image_file.seek(0)
        
        if file_length > self.MAX_FILE_SIZE:
            raise ValueError("La imagen es demasiado pesada. Máximo 5MB permitidos.")

        try:
            # Abrir la imagen con Pillow
            img = PILImage.open(image_file)
            
            # Convertir a RGB (Elimina transparencias de PNG/WEBP para poder comprimir en JPEG)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # Redimensionar si la imagen es gigantesca (Max 1200x1200px)
            max_size = (1200, 1200)
            img.thumbnail(max_size, PILImage.Resampling.LANCZOS)

            # Generar un nombre único y seguro
            ext = "jpg" # Forzamos el formato a JPEG optimizado
            unique_filename = f"{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(self.UPLOAD_FOLDER, unique_filename)
            
            # Guardar la imagen optimizada (Reduce drásticamente el peso)
            img.save(filepath, format='JPEG', quality=80, optimize=True)

            # Retornar la ruta web para la base de datos
            return f"/static/images/uploads/{unique_filename}"
            
        except Exception as e:
            print(f"Error procesando imagen: {e}")
            raise ValueError("Error interno al procesar o comprimir la imagen.")
