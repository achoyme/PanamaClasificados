class FraudDetectionService:
    def assess_fraud_risk(self, listing, image_score, has_stock, has_contact, has_suspicious):
        # Sistema de puntaje de riesgo
        score = 5.0  # Base de riesgo
        
        if has_suspicious:
            score += 50.0
        if has_stock:
            score += 20.0
        if has_contact:
            score += 15.0
            
        # Determinar el nivel de riesgo
        if score >= 60:
            level = 'Critical'
        elif score >= 40:
            level = 'High'
        elif score >= 20:
            level = 'Medium'
        else:
            level = 'Low'
            
        return {
            'risk_score': score,
            'risk_level': level
        }