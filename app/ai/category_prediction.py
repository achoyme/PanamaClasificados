class CategoryPredictionService:
    def __init__(self):
        # Diccionario de palabras clave estructurado
        self.keywords = {
            1: ['telefono', 'celular', 'laptop', 'computadora', 'tv', 'consola', 'iphone', 'samsung', 'pantalla', 'audio'],
            2: ['auto', 'carro', 'camioneta', 'moto', 'nissan', 'toyota', 'honda', 'llantas', 'motor', 'sedan'],
            3: ['casa', 'apartamento', 'terreno', 'alquiler', 'venta', 'cuarto', 'ph', 'recamaras', 'edificio', 'lote'],
            4: ['camisa', 'pantalon', 'zapatos', 'vestido', 'zapatillas', 'ropa', 'reloj', 'lentes', 'cartera', 'talla'],
            5: ['sofa', 'cama', 'mesa', 'silla', 'nevera', 'estufa', 'mueble', 'colchon', 'comedor', 'licuadora']
        }

    def predict_category(self, title, description):
        text = f"{title} {description}".lower()
        
        best_match_id = 1 # Por defecto (Electrónica / Otros)
        max_matches = 0
        
        # Lógica determinista: Gana la categoría con más palabras clave encontradas
        for cat_id, words in self.keywords.items():
            matches = sum(1 for word in words if word in text)
            if matches > max_matches:
                max_matches = matches
                best_match_id = cat_id
                
        # Calculamos la confianza en base a la cantidad de coincidencias
        confidence = 50.0 + (max_matches * 10.0)
        if confidence > 95.0: confidence = 95.0
        if max_matches == 0: confidence = 40.0
        
        return {
            'category_id': best_match_id,
            'confidence': round(confidence, 1)
        }