from app import db
from app.models import Transaction
from decimal import Decimal

class EscrowService:
    PLATFORM_FEE_PERCENT = Decimal('5.00')  # 5% comisión
    PREMIUM_FEE_PERCENT = Decimal('2.50')   # 2.5% para usuarios premium
    
    def create_transaction(self, buyer_id, seller_id, listing_id, amount):
        """Crear transacción con escrow"""
        
        # Calcular comisión
        fee_percent = self._get_fee_percent(seller_id)
        platform_fee = amount * (fee_percent / Decimal('100'))
        seller_amount = amount - platform_fee
        
        transaction = Transaction(
            buyer_id=buyer_id,
            seller_id=seller_id,
            listing_id=listing_id,
            amount=amount,
            platform_fee=platform_fee,
            seller_amount=seller_amount,
            status='Pending'  # Pendiente de entrega
        )
        
        # Retener fondos del comprador (integración con pasarela de pago)
        
        db.session.add(transaction)
        db.session.commit()
        
        return transaction
    
    def release_payment(self, transaction_id):
        """Liberar pago al vendedor después de confirmar entrega"""
        transaction = Transaction.query.get(transaction_id)
        
        if transaction.status != 'Pending':
            return False
        
        # Transferir a wallet del vendedor (menos comisión)
        seller = User.query.get(transaction.seller_id)
        seller.wallet_balance += transaction.seller_amount
        
        # La comisión va a la plataforma
        # TODO: Registrar ingreso de la plataforma
        
        transaction.status = 'Completed'
        transaction.completed_at = datetime.utcnow()
        
        db.session.commit()
        
        # Notificar a ambas partes
        return True
    
    def refund(self, transaction_id, reason):
        """Reembolsar al comprador en caso de disputa"""
        transaction = Transaction.query.get(transaction_id)
        transaction.status = 'Refunded'
        transaction.refund_reason = reason
        
        # Procesar reembolso vía pasarela de pago
        
        db.session.commit()
        return True