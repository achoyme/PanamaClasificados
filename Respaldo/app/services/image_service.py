import os
import time
from werkzeug.utils import secure_filename

class ImageService:
    def upload_image(self, image_file):
        if not image_file or image_file.filename == '':
            return "https://via.placeholder.com/400x300?text=Sin+Imagen"
            
        upload_dir = os.path.join('app', 'static', 'images', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        filename = secure_filename(f"{int(time.time())}_{image_file.filename}")
        file_path = os.path.join(upload_dir, filename)
        image_file.save(file_path)
        
        return f"/static/images/uploads/{filename}"
