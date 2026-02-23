from flask import Blueprint, render_template, jsonify, Response, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Listing, Report, User
from app import db
import json
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    now = datetime.utcnow()
    recent_listings = Listing.query.filter(Listing.status == 'Active', Listing.expires_at > now).order_by(Listing.created_at.desc()).limit(12).all()
    return render_template('index.html', listings=recent_listings)

@main_bp.route('/privacy')
def privacy():
    return render_template('privacy.html')

@main_bp.route('/export-data')
@login_required
def export_data():
    user_data = {
        "informacion_personal": current_user.to_dict(),
        "estadisticas_uso": {
            "total_anuncios_publicados": Listing.query.filter_by(user_id=current_user.id).count()
        }
    }
    json_data = json.dumps(user_data, indent=4, ensure_ascii=False)
    return Response(json_data, mimetype="application/json", headers={"Content-disposition": f"attachment; filename=datos_panamaclassifieds_{current_user.id}.json"})

# ===============================================
# PASARELA DE PAGOS Y PAQUETES
# ===============================================
@main_bp.route('/pricing')
def pricing():
    return render_template('pricing.html')

@main_bp.route('/checkout/<package_id>', methods=['GET', 'POST'])
@login_required
def checkout(package_id):
    packages = {
        'emprendedor': {'id': 'emprendedor', 'name': 'Emprendedor', 'price': 4.99, 'prof': 5, 'prem': 1, 'desc': 'Ideal para ventas rápidas. Menos de $1 por anuncio.'},
        'negocio': {'id': 'negocio', 'name': 'Negocio', 'price': 12.99, 'prof': 15, 'prem': 4, 'desc': 'Perfecto para PYMES. El precio que otros cobran por 1 anuncio.'},
        'agencia': {'id': 'agencia', 'name': 'Agencia VIP', 'price': 24.99, 'prof': 40, 'prem': 10, 'desc': 'Domina el mercado. Costo ridículamente bajo para bienes raíces o autos.'}
    }
    
    pkg = packages.get(package_id)
    if not pkg:
        return redirect(url_for('main.pricing'))
        
    if request.method == 'POST':
        # SIMULACIÓN: Confirmación Automática (Prueba)
        user = User.query.get(current_user.id)
        user.package_name = pkg['name']
        
        # SOLUCIÓN: Si es 'None' lo convertimos a 0 antes de sumar los créditos
        user.prof_credits = (user.prof_credits or 0) + pkg['prof']
        user.prem_credits = (user.prem_credits or 0) + pkg['prem']
        
        db.session.commit()
        
        flash(f'¡Pago verificado automáticamente! Se han añadido {pkg["prof"]} créditos Profesionales y {pkg["prem"]} Premium a tu cuenta.', 'success')
        return redirect(url_for('listings.create'))
        
    return render_template('checkout.html', package=pkg)