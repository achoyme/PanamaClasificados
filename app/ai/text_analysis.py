import re

class TextAnalysisService:
    def analyze_text(self, text):
        if not text:
            return {'quality': 'Poor', 'has_contact_info': False, 'has_suspicious_keywords': False}
        
        text_lower = text.lower()
        
        # 1. Detectar info de contacto (emails o teléfonos de Panamá ej. 6xxx-xxxx)
        has_phone = bool(re.search(r'(\+?507)?\s*6\d{3}[-\s]?\d{4}', text))
        has_email = bool(re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text))
        
        # 2. Detectar palabras de riesgo o fraude
        suspicious = ['depósito previo', 'transferencia western', 'envía dinero', 'urge vender viaje', 'western union']
        has_suspicious = any(word in text_lower for word in suspicious)
        
        # 3. Calidad basada en la longitud de la descripción
        length = len(text)
        if length > 250:
            quality = 'Excellent'
        elif length > 120:
            quality = 'Good'
        elif length > 50:
            quality = 'Fair'
        else:
            quality = 'Poor'
        
        return {
            'quality': quality,
            'has_contact_info': has_phone or has_email,
            'has_suspicious_keywords': has_suspicious
        }
        
    def generate_title_suggestion(self, title, description):
        return f"Oferta: {title}"