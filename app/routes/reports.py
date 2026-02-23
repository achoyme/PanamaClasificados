from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from app.services.report_service import ReportService
from app.utils.decorators import moderator_required
from app.models import Report

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')
report_service = ReportService()

@reports_bp.route('/create', methods=['POST'])
@login_required
def create():
    result = report_service.create_report(request.get_json(), current_user.id)
    if result['success']: return jsonify({'success': True, 'message': 'Reporte enviado.'})
    return jsonify({'success': False, 'error': result['error']}), 400

@reports_bp.route('/moderation')
@login_required
@moderator_required
def moderation():
    return render_template('reports/moderation.html', pending_reports=report_service.get_pending_reports(), statistics=report_service.get_report_statistics())

@reports_bp.route('/<int:report_id>/review', methods=['GET', 'POST'])
@login_required
@moderator_required
def review(report_id):
    report = Report.query.get_or_404(report_id)
    if request.method == 'GET': return render_template('reports/review.html', report=report)
    review_data = {'status': request.form.get('status'), 'action_taken': request.form.get('action_taken'), 'review_notes': request.form.get('review_notes')}
    report_service.review_report(report_id, review_data, current_user.id)
    return redirect(url_for('reports.moderation'))