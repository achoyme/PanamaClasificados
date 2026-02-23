class NotificationService:
    def notify_moderators_urgent(self, message): print(f"[URGENTE] {message}")
    def notify_moderators(self, message): print(f"[MODERADORES] {message}")
    def notify_user(self, user_id, title, message): print(f"[NOTIFICACIÓN] {title}: {message}")