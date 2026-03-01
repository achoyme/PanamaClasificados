from app import db
from app.models import User, Listing

class GamificationService:
    """Sistema de logros y recompensas para retener usuarios"""
    
    ACHIEVEMENTS = {
        'first_sale': {'name': 'Primer Venta', 'description': 'Vende tu primer artículo', 'reward': 5.00},
        'power_seller': {'name': 'Vendedor Power', 'description': '10 ventas en 30 días', 'reward': 25.00},
        'social_butterfly': {'name': 'Social', 'description': 'Comparte 5 anuncios en redes', 'reward': 10.00},
        'fast_responder': {'name': 'Flash', 'description': 'Responde en menos de 5 min', 'reward': 5.00},
        'top_rated': {'name': '5 Estrellas', 'description': 'Recibe 10 reseñas 5 estrellas', 'reward': 50.00},
    }
    
    def check_achievements(self, user_id):
        """Verificar y otorgar logros"""
        user = User.query.get(user_id)
        new_achievements = []
        
        # Verificar primer venta
        if user.total_sales == 1 and not self.has_achievement(user_id, 'first_sale'):
            new_achievements.append(self.grant_achievement(user_id, 'first_sale'))
        
        # Verificar power seller
        if user.total_sales >= 10 and not self.has_achievement(user_id, 'power_seller'):
            # Verificar que sean en 30 días...
            new_achievements.append(self.grant_achievement(user_id, 'power_seller'))
        
        return new_achievements
    
    def grant_achievement(self, user_id, achievement_key):
        """Otorgar logro y recompensa"""
        achievement = self.ACHIEVEMENTS[achievement_key]
        
        # Agregar a tabla de logros
        user_achievement = UserAchievement(
            user_id=user_id,
            achievement_key=achievement_key,
            reward_amount=achievement['reward']
        )
        
        # Acreditar recompensa a wallet
        user = User.query.get(user_id)
        user.wallet_balance += achievement['reward']
        
        db.session.add(user_achievement)
        db.session.commit()
        
        # Enviar notificación push/email
        NotificationService().notify_user(
            user_id=user_id,
            title=f"🎉 ¡Logro desbloqueado: {achievement['name']}!",
            message=f"Ganaste ${achievement['reward']} por: {achievement['description']}"
        )
        
        return user_achievement