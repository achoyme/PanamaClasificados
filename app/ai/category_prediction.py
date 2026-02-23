class CategoryPredictionService:
    def predict_category(self, title, description, image_url=None):
        text = f"{title} {description}".lower()
        
        # Lógica heurística: buscar palabras clave comunes para predecir la categoría
        if any(w in text for w in ['iphone', 'samsung', 'celular', 'laptop', 'pc', 'tablet', 'tv', 'camara']):
            cat_id = 1  # Asumiendo que 1 es Electrónica
            confidence = 95.5
        elif any(w in text for w in ['auto', 'toyota', 'nissan', 'honda', 'carro', 'moto', 'llantas', 'motor']):
            cat_id = 2  # Asumiendo que 2 es Vehículos
            confidence = 92.0
        elif any(w in text for w in ['casa', 'apartamento', 'alquiler', 'cuarto', 'terreno', 'local']):
            cat_id = 3  # Asumiendo que 3 es Inmuebles
            confidence = 90.0
        elif any(w in text for w in ['ropa', 'zapatos', 'camisa', 'pantalon', 'moda', 'vestido']):
            cat_id = 4  # Moda
            confidence = 88.0
        elif any(w in text for w in ['silla', 'mesa', 'mueble', 'cama', 'sofa', 'comedor']):
            cat_id = 5  # Hogar
            confidence = 85.0
        else:
            cat_id = 1  # Categoría por defecto si no encuentra coincidencias
            confidence = 60.0
            
        return {
            'category_id': cat_id,
            'confidence': confidence
        }