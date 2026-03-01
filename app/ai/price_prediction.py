import random

class PricePredictionService:
    def __init__(self):
        # Valores promedio estáticos por categoría (Provisional)
        # TODO: Implementar RandomForestRegressor cuando tengamos datos históricos reales.
        self.base_prices = {
            1: 150.00,    # Electrónica
            2: 8500.00,   # Vehículos
            3: 120000.00, # Inmuebles
            4: 25.00,     # Moda
            5: 60.00      # Hogar
        }

    def predict_price(self, category_id, title, description, province=None):
        try:
            # Obtenemos el precio base según la categoría, por defecto $100
            suggested = self.base_prices.get(int(category_id), 100.00)
            
            # Ajuste básico por palabras clave en la condición o título
            title_lower = str(title).lower()
            if "nuevo" in title_lower or "sellado" in title_lower:
                suggested *= 1.2  # 20% más si parece nuevo
            elif "dañado" in title_lower or "reparar" in title_lower:
                suggested *= 0.5  # 50% menos si está dañado
                
            return {
                'suggested_price': round(suggested, 2),
                'confidence': 60.0, # Confianza media por ser un cálculo estático
                'market_min': round(suggested * 0.8, 2),
                'market_max': round(suggested * 1.2, 2)
            }
        except Exception:
            return {'suggested_price': 0, 'confidence': 0}