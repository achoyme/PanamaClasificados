from flask import Blueprint, render_template, jsonify, Response, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Listing, Report, User, ContactMessage
from app import db
import json
from datetime import datetime, timedelta
from decimal import Decimal
from app.utils.decorators import moderator_required, admin_required

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """🏠 Página principal con listados recientes"""
    now = datetime.utcnow()
    recent_listings = Listing.query.filter(
        # ✅ CORRECCIÓN: Permitir que las subastas se vean en el Home
        Listing.status.in_(['Active', 'Auction']), 
        Listing.expires_at > now
    ).order_by(Listing.created_at.desc()).limit(12).all()
    return render_template('index.html', listings=recent_listings)

@main_bp.route('/privacy')
def privacy():
    """📄 Política de Privacidad"""
    return render_template('privacy.html')

@main_bp.route('/pricing')
def pricing():
    """💰 Página de precios y paquetes"""
    return render_template('pricing.html')

@main_bp.route('/ayuda')
def help():
    """❓ Centro de Ayuda"""
    return render_template('main/help.html')

@main_bp.route('/terminos')
def terms():
    """📋 Términos y Condiciones"""
    return render_template('main/terms.html')

@main_bp.route('/consejos-seguridad')
def security_tips():
    """🛡️ Consejos de Seguridad"""
    return render_template('main/security_tips.html')

@main_bp.route('/soporte')
def support():
    """📞 Contactar Soporte"""
    return render_template('main/support.html')

@main_bp.route('/reportar-fraude')
def report_fraud():
    """🚨 Reportar Fraude"""
    return render_template('main/report_fraud.html')

@main_bp.route('/perfil/<int:user_id>')
def seller_profile(user_id):
    """👤 Perfil público del vendedor"""
    from app.models import Review
    seller = User.query.get_or_404(user_id)
    now = datetime.utcnow()
    
    active_listings = Listing.query.filter(
        Listing.user_id == seller.id, 
        # ✅ CORRECCIÓN: Permitir subastas en el perfil del vendedor
        Listing.status.in_(['Active', 'Auction'])
    ).filter(
        Listing.expires_at > now
    ).order_by(
        Listing.created_at.desc()
    ).all()
    
    # Calcular promedio de reseñas
    reviews = seller.reviews_received.all() if hasattr(seller, 'reviews_received') else []
    total_reviews = len(reviews)
    average_rating = sum(r.rating for r in reviews) / total_reviews if total_reviews > 0 else 0
    
    # Verificar si el usuario actual ya dejó reseña
    user_review = None
    if current_user.is_authenticated:
        user_review = Review.query.filter_by(
            reviewer_id=current_user.id,
            reviewed_id=user_id
        ).first() if hasattr(Review, 'query') else None
    
    return render_template('seller_profile.html', 
        seller=seller, 
        listings=active_listings, 
        now=now,
        reviews=reviews,
        avg_rating=round(average_rating, 1),
        user_review=user_review)

@main_bp.route('/mi-perfil', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """✏️ Editar perfil de usuario"""
    if request.method == 'POST':
        user = User.query.get(current_user.id)
        user.first_name = request.form.get('first_name', user.first_name)
        user.last_name = request.form.get('last_name', user.last_name)
        user.phone_number = request.form.get('phone_number', user.phone_number)
        user.province = request.form.get('province', user.province)
        user.district = request.form.get('district', user.district)
        user.city = request.form.get('city', user.city)
        
        # Guardar opciones de logística
        user.has_physical_store = request.form.get('has_physical_store') == 'on'
        user.store_address = request.form.get('store_address', '')
        user.delivery_methods = request.form.get('delivery_methods', '')
        
        db.session.commit()
        flash('¡Tu perfil y opciones de entrega han sido actualizados!', 'success')
        return redirect(url_for('main.edit_profile'))
    
    return render_template('profile_edit.html')

@main_bp.route('/billetera')
@login_required
def wallet():
    """💰 Página de billetera"""
    return render_template('wallet.html')

@main_bp.route('/inbox')
@login_required
def inbox():
    """📧 Bandeja de entrada de mensajes"""
    user_listings_ids = [l.id for l in current_user.listings]
    messages = ContactMessage.query.filter(
        ContactMessage.listing_id.in_(user_listings_ids)
    ).order_by(ContactMessage.created_at.desc()).all()
    return render_template('inbox.html', messages=messages)

@main_bp.route('/inbox/read/<int:msg_id>', methods=['POST'])
@login_required
def mark_read(msg_id):
    """✅ Marcar mensaje como leído"""
    msg = ContactMessage.query.get_or_404(msg_id)
    if msg.listing.user_id == current_user.id:
        msg.is_read = True
        db.session.commit()
    return redirect(url_for('main.inbox'))

@main_bp.route('/checkout/<package_id>', methods=['GET', 'POST'])
@login_required
def checkout(package_id):
    """💳 Proceso de compra de paquetes con métodos de pago"""
    packages = {
        'emprendedor': {
            'id': 'emprendedor', 
            'name': 'Emprendedor', 
            'price': 4.99, 
            'prof': 5, 
            'prem': 1, 
            'desc': 'Ideal para ventas rápidas.'
        },
        'negocio': {
            'id': 'negocio', 
            'name': 'Negocio', 
            'price': 12.99, 
            'prof': 15, 
            'prem': 4, 
            'desc': 'Perfecto para PYMES.'
        },
        'agencia': {
            'id': 'agencia', 
            'name': 'Agencia VIP', 
            'price': 24.99, 
            'prof': 40, 
            'prem': 10, 
            'desc': 'Domina el mercado.'
        }
    }
    
    pkg = packages.get(package_id)
    if not pkg:
        flash('Paquete no encontrado.', 'error')
        return redirect(url_for('main.pricing'))
    
    if request.method == 'POST':
        payment_method = request.form.get('payment_method', 'yappy')
        
        user = User.query.get(current_user.id)
        user.package_name = pkg['name']
        user.prof_credits = (user.prof_credits or 0) + pkg['prof']
        user.prem_credits = (user.prem_credits or 0) + pkg['prem']
        
        if package_id == 'agencia':
            user.account_type = 'Tienda / Promotor'
        
        from app.models import Transaction
        transaction = Transaction(
            user_id=current_user.id,
            amount=Decimal(str(pkg['price'])),
            transaction_type='Compra Paquete',
            currency='USD',
            description=f"Paquete {pkg['name']} - Pago vía {payment_method}"
        )
        db.session.add(transaction)
        db.session.commit()
        
        flash(f'¡Pago verificado! Se añadieron {pkg["prof"]} créditos Profesionales y {pkg["prem"]} Premium.', 'success')
        return redirect(url_for('listings.create'))
    
    return render_template('checkout.html', package=pkg)

@main_bp.route('/export-data')
@login_required
def export_data():
    """📥 Exportar datos personales (GDPR)"""
    user_data = {
        "informacion_personal": current_user.to_dict(),
        "listings": [l.to_dict() for l in current_user.listings],
        "export_date": datetime.utcnow().isoformat()
    }
    json_data = json.dumps(user_data, indent=4, ensure_ascii=False)
    return Response(
        json_data,
        mimetype="application/json",
        headers={"Content-disposition": f"attachment; filename=datos_panamaclassifieds_{current_user.id}.json"}
    )

@main_bp.route('/seller/<int:user_id>')
def seller_profile_alias(user_id):
    """🔄 Alias para perfil de vendedor"""
    from app.models import Review
    seller = User.query.get_or_404(user_id)
    now = datetime.utcnow()
    
    active_listings = Listing.query.filter(
        Listing.user_id == user_id, 
        # ✅ CORRECCIÓN: Permitir subastas en el perfil del vendedor
        Listing.status.in_(['Active', 'Auction'])
    ).filter(
        Listing.expires_at > now
    ).order_by(
        Listing.created_at.desc()
    ).all()
    
    reviews = seller.reviews_received.all() if hasattr(seller, 'reviews_received') else []
    total_reviews = len(reviews)
    average_rating = sum(r.rating for r in reviews) / total_reviews if total_reviews > 0 else 0
    
    user_review = None
    if current_user.is_authenticated:
        user_review = Review.query.filter_by(
            reviewer_id=current_user.id,
            reviewed_id=user_id
        ).first() if hasattr(Review, 'query') else None
    
    return render_template('main/seller_profile.html',
        seller=seller,
        listings=active_listings,
        reviews=reviews,
        avg_rating=round(average_rating, 1),
        user_review=user_review
    )

@main_bp.route('/seller/<int:user_id>/review', methods=['POST'])
@login_required
def leave_review(user_id):
    """⭐ Dejar reseña a vendedor"""
    from app.models import Review
    
    if current_user.id == user_id:
        flash("No puedes calificarte a ti mismo.", "error")
        return redirect(url_for('main.seller_profile', user_id=user_id))
    
    rating = request.form.get('rating', type=int)
    comment = request.form.get('comment', '').strip()
    
    if not rating or rating < 1 or rating > 5:
        flash("Por favor selecciona una calificación de 1 a 5 estrellas.", "error")
        return redirect(url_for('main.seller_profile', user_id=user_id))
    
    existing_review = Review.query.filter_by(
        reviewer_id=current_user.id,
        reviewed_id=user_id
    ).first() if hasattr(Review, 'query') else None
    
    if existing_review:
        existing_review.rating = rating
        existing_review.comment = comment
        flash("Tu calificación ha sido actualizada.", "success")
    else:
        new_review = Review(
            reviewer_id=current_user.id,
            reviewed_id=user_id,
            rating=rating,
            comment=comment
        )
        db.session.add(new_review)
        flash("¡Gracias por calificar a este vendedor!", "success")
    
    db.session.commit()
    return redirect(url_for('main.seller_profile', user_id=user_id))

# ==========================================
# MÉTODOS DE PAGO (Información)
# ==========================================
@main_bp.route('/pagos/yappy')
def payment_yappy():
    """📱 Información de pago con Yappy"""
    return render_template('payments/yappy.html')

@main_bp.route('/pagos/ach')
def payment_ach():
    """🏦 Información de pago con ACH"""
    return render_template('payments/ach.html')

@main_bp.route('/pagos/tarjetas')
def payment_cards():
    """💳 Información de pago con Tarjetas"""
    return render_template('payments/cards.html')