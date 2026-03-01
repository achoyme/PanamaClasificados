import os
import uuid
from werkzeug.utils import secure_filename
from PIL import Image as PILImage

class ImageService:
    """🖼️ Servicio de gestión de imágenes con validación de seguridad"""
    
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB máximo por imagen
    UPLOAD_FOLDER = 'app/static/images/uploads'
    
    def __init__(self):
        os.makedirs(self.UPLOAD_FOLDER, exist_ok=True)
    
    def allowed_file(self, filename):
        """✅ Verifica extensión permitida"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS
    
    def upload_image(self, image_file):
        """📤 Sube y optimiza imagen con validaciones de seguridad"""
        if not image_file or image_file.filename == '':
            return None
        
        if not self.allowed_file(image_file.filename):
            raise ValueError("Formato no permitido. Usa JPG, PNG o WEBP.")
        
        # ✅ Validar tamaño antes de procesar
        image_file.seek(0, os.SEEK_END)
        file_length = image_file.tell()
        image_file.seek(0)
        
        if file_length > self.MAX_FILE_SIZE:
            raise ValueError("Imagen demasiado pesada. Máximo 5MB.")
        
        try:
            # 🔄 Optimizar imagen
            img = PILImage.open(image_file)
            
            # Convertir a RGB (elimina transparencias problemáticas)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # Redimensionar si es muy grande
            max_size = (1200, 1200)
            img.thumbnail(max_size, PILImage.Resampling.LANCZOS)
            
            # Nombre único y seguro
            ext = "jpg"
            unique_filename = f"{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(self.UPLOAD_FOLDER, unique_filename)
            
            # Guardar optimizado
            img.save(filepath, format='JPEG', quality=80, optimize=True)
            
            return f"/static/images/uploads/{unique_filename}"
            
        except Exception as e:
            print(f"Error procesando imagen: {e}")
            raise ValueError("Error al procesar la imagen.")