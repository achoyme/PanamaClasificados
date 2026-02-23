import random

class PricePredictionService:
    def predict_price(self, category_id, title, description, province=None):
        # Genera un precio sugerido simulado basado en una curva matemática
        base_price = random.uniform(50.0, 450.0)
        
        suggested = round(base_price, 2)
        market_min = round(base_price * 0.85, 2)  # 15% menos
        market_max = round(base_price * 1.15, 2)  # 15% más
        
        return {
            'suggested_price': suggested,
            'confidence': 78.5,
            'market_min': market_min,
            'market_max': market_max
        }