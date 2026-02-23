class PricePredictionService:
    def predict_price(self, cid, t, d, p=None): return {'suggested_price': 100.0, 'confidence': 90.0, 'market_min': 80.0, 'market_max': 120.0}