from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
from flask_login import login_required, current_user
from app.models.user import User
from app.models import Listing, Report
from app.extensions import db
from app.utils.decorators import admin_required
from datetime import datetime, timedelta
import csv
import io

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    now = datetime.utcnow()
    
    # ✅ CORRECCIÓN: Agrupamos todo en el diccionario 'stats' que pide el HTML
    stats = {
        'total_users': User.query.count(),
        'active_users': User.query.filter_by(is_active=True, is_banned=False).count(),
        'banned_users': User.query.filter_by(is_banned=True).count(),
        'total_listings': Listing.query.count(),
        'active_listings': Listing.query.filter_by(status='Active').filter(Listing.expires_at > now).count(),
        'pending_reports': Report.query.filter_by(status='Pending').count(),
        'total_reports': Report.query.count(),
        'resolved_reports': Report.query.filter_by(status='Resolved').count(),
        'new_users_week': User.query.filter(User.created_at >= now - timedelta(days=7)).count()
    }
    
    # ✅ Agrupamos la actividad reciente
    recent_activity = {
        'new_users': User.query.order_by(User.created_at.desc()).limit(5).all()
    }
    
    return render_template('admin/dashboard.html',
        stats=stats,
        recent_activity=recent_activity)

@admin_bp.route('/users')
@login_required
@admin_required
def users_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status = request.args.get('status', 'all')
    
    query = User.query
    
    if search:
        query = query.filter(
            (User.email.ilike(f'%{search}%')) |
            (User.first_name.ilike(f'%{search}%')) |
            (User.last_name.ilike(f'%{search}%'))
        )
    
    if status == 'active':
        query = query.filter_by(is_active=True, is_banned=False)
    elif status == 'banned':
        query = query.filter_by(is_banned=True)
    elif status == 'admin':
        query = query.filter_by(is_admin=True)
    
    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/users.html',
        users=pagination.items,
        pagination=pagination,
        search=search,
        status=status)

@admin_bp.route('/users/<int:user_id>')
@login_required
@admin_required
def user_detail(user_id):
    user = User.query.get_or_404(user_id)
    user_listings = Listing.query.filter_by(user_id=user.id).order_by(Listing.created_at.desc()).limit(10).all()
    user_reports = Report.query.filter_by(reported_by_user_id=user.id).order_by(Report.created_at.desc()).limit(10).all()
    reports_against = Report.query.join(Listing).filter(Listing.user_id==user.id).order_by(Report.created_at.desc()).limit(10).all()
    
    return render_template('admin/user_detail.html',
        user=user,
        listings=user_listings,
        reports_made=user_reports,
        reports_against=reports_against)

@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def admin_reset_password(user_id):
    import secrets
    user = User.query.get_or_404(user_id)
    temp_password = secrets.token_urlsafe(12)
    user.set_password(temp_password)
    db.session.commit()
    
    flash(f'Contraseña restablecida. Temporal: {temp_password}', 'warning')
    return redirect(url_for('admin.user_detail', user_id=user_id))

@admin_bp.route('/users/<int:user_id>/toggle-ban', methods=['POST'])
@login_required
@admin_required
def toggle_ban(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.is_admin:
        flash('No puedes suspender a un administrador.', 'error')
        return redirect(url_for('admin.user_detail', user_id=user_id))
    
    user.is_banned = not user.is_banned
    user.banned_date = datetime.utcnow() if user.is_banned else None
    user.banned_reason = request.form.get('reason', '') if user.is_banned else ''
    
    db.session.commit()
    
    if user.is_banned:
        flash(f'Usuario {user.email} SUSPENDIDO.', 'warning')
    else:
        flash(f'Usuario {user.email} ACTIVADO.', 'success')
    
    return redirect(url_for('admin.user_detail', user_id=user_id))

@admin_bp.route('/users/<int:user_id>/toggle-verify', methods=['POST'])
@login_required
@admin_required
def toggle_verify(user_id):
    user = User.query.get_or_404(user_id)
    user.is_verified = not user.is_verified
    user.verification_date = datetime.utcnow() if user.is_verified else None
    db.session.commit()
    
    flash(f'Verificación actualizada para {user.email}', 'success')
    return redirect(url_for('admin.user_detail', user_id=user_id))

@admin_bp.route('/users/<int:user_id>/add-credits', methods=['POST'])
@login_required
@admin_required
def add_credits(user_id):
    user = User.query.get_or_404(user_id)
    
    prof_credits = request.form.get('prof_credits', 0, type=int)
    prem_credits = request.form.get('prem_credits', 0, type=int)
    
    if prof_credits > 0:
        user.prof_credits = (user.prof_credits or 0) + prof_credits
    if prem_credits > 0:
        user.prem_credits = (user.prem_credits or 0) + prem_credits
    
    db.session.commit()
    
    flash(f'Añadidos {prof_credits} Prof y {prem_credits} Prem a {user.email}', 'success')
    return redirect(url_for('admin.user_detail', user_id=user_id))

@admin_bp.route('/users/export')
@login_required
@admin_required
def export_users():
    users = User.query.all()
    
    def generate():
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Email', 'Nombre', 'Apellido', 'Teléfono', 
                        'Provincia', 'Verificado', 'Suspendido', 'Admin', 
                        'Créditos Prof', 'Créditos Prem', 'Fecha Registro'])
        
        for user in users:
            writer.writerow([
                user.id, user.email, user.first_name, user.last_name,
                user.phone_number or '', user.province or '',
                'Sí' if user.is_verified else 'No',
                'Sí' if user.is_banned else 'No',
                'Sí' if user.is_admin else 'No',
                user.prof_credits or 0, user.prem_credits or 0,
                user.created_at.strftime('%Y-%m-%d %H:%M')
            ])
        
        return output.getvalue()
    
    return Response(
        generate(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=usuarios_panamaclassifieds.csv"}
    )