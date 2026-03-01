import os
import uuid
import requests  # CAMBIO: Para enviar la imagen a internet
import base64    # CAMBIO: Para codificar la imagen
import io        # CAMBIO: Para manejar la imagen en memoria RAM
from werkzeug.utils import secure_filename
from PIL import Image as PILImage

class ImageService:
    """🖼️ Servicio de gestión de imágenes con validación de seguridad y subida a Imgbb"""
    
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB máximo por imagen
    UPLOAD_FOLDER = 'app/static/images/uploads'
    
    def __init__(self):
        # Mantenemos la carpeta por si acaso, aunque ya no guardaremos aquí
        os.makedirs(self.UPLOAD_FOLDER, exist_ok=True)
    
    def allowed_file(self, filename):
        """✅ Verifica extensión permitida"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS
    
    def upload_image(self, image_file):
        """📤 Optimiza imagen localmente y la sube a la nube (Imgbb)"""
        if not image_file or image_file.filename == '':
            return None
        
        if not self.allowed_file(image_file.filename):
            raise ValueError("Formato no permitido. Usa JPG, PNG o WEBP.")
        
        # ✅ Validar tamaño antes de procesar (Tu código original)
        image_file.seek(0, os.SEEK_END)
        file_length = image_file.tell()
        image_file.seek(0)
        
        if file_length > self.MAX_FILE_SIZE:
            raise ValueError("Imagen demasiado pesada. Máximo 5MB.")
        
        try:
            # 🔄 Optimizar imagen (Tu código original)
            img = PILImage.open(image_file)
            
            # Convertir a RGB (elimina transparencias problemáticas)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # Redimensionar si es muy grande
            max_size = (1200, 1200)
            img.thumbnail(max_size, PILImage.Resampling.LANCZOS)
            
            # ========================================================
            # CAMBIO: En lugar de guardar en disco, guardamos en la RAM
            # ========================================================
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG', quality=80, optimize=True)
            img_byte_arr = img_byte_arr.getvalue()
            
            # Codificamos la imagen optimizada para enviarla por internet
            encoded_image = base64.b64encode(img_byte_arr).decode('utf-8')
            
            # Tu llave de Imgbb
            api_key = "49715855713fc0be16b7b8119364d362"
            
            # Enviamos la foto a los servidores de Imgbb
            response = requests.post(
                "https://api.imgbb.com/1/upload",
                data={
                    'key': api_key,
                    'image': encoded_image
                }
            )
            
            # Si Imgbb responde con éxito (Código 200)
            if response.status_code == 200:
                json_data = response.json()
                cloud_url = json_data['data']['url']
                return cloud_url  # Retorna el link seguro de la nube
            else:
                print(f"Error de Imgbb: {response.text}")
                raise ValueError("Error de comunicación con el servidor de imágenes.")
            
        except Exception as e:
            print(f"Error procesando imagen: {e}")
            raise ValueError("Error al procesar la imagen.")
