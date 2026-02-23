import os
import time
import uuid
from werkzeug.utils import secure_filename

class ImageService:
    def upload_image(self, image_file):
        # Si no hay archivo, devolvemos un placeholder
        if not image_file or image_file.filename == '':
            return "https://placehold.co/400x300?text=Sin+Imagen"
            
        # Crear la carpeta si no existe
        upload_dir = os.path.join('app', 'static', 'images', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generamos un identificador único (UUID) corto para que los 'Ctrl+V' no se sobreescriban
        unique_id = uuid.uuid4().hex[:8]
        
        # Unimos: timestamp + uuid + nombre original (limpio)
        filename = secure_filename(f"{int(time.time())}_{unique_id}_{image_file.filename}")
        file_path = os.path.join(upload_dir, filename)
        
        # Guardamos el archivo físicamente
        image_file.save(file_path)
        
        return f"/static/images/uploads/{filename}"