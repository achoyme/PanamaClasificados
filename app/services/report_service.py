from app.models import Report, Listing, User
from app.services.notification_service import NotificationService
from datetime import datetime
from app import db

class ReportService:
    def __init__(self):
        self.notification_service = NotificationService()

    def create_report(self, data, reported_by_user_id):
        try:
            listing = Listing.query.get(data['listing_id'])
            if not listing or listing.status == 'Deleted':
                return {'success': False, 'error': 'Publicación inválida'}
            existing = Report.query.filter_by(listing_id=data['listing_id'], reported_by_user_id=reported_by_user_id).first()
            if existing: return {'success': False, 'error': 'Ya reportaste esto'}
            
            report = Report(listing_id=data['listing_id'], reported_by_user_id=reported_by_user_id, report_type=data['report_type'], details=data.get('details'))
            db.session.add(report)
            db.session.commit()
            
            if Report.query.filter_by(listing_id=data['listing_id']).count() >= 3:
                listing.status = 'Pending'
                db.session.commit()
            return {'success': True, 'report': {'id': report.id}}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    def review_report(self, report_id, review_data, moderator_id):
        try:
            report = Report.query.get(report_id)
            report.status = review_data['status']
            report.reviewed_by_user_id = moderator_id
            report.reviewed_at = datetime.utcnow()
            db.session.commit()
            return {'success': True}
        except Exception as e:
            db.session.rollback()
            return {'success': False}

    def get_pending_reports(self):
        return Report.query.filter_by(status='Pending').order_by(Report.created_at.desc()).all()

    def get_report_statistics(self):
        return {
            'total_reports': Report.query.count(),
            'pending_reports': Report.query.filter_by(status='Pending').count(),
            'resolved_reports': Report.query.filter_by(status='Resolved').count(),
            'dismissed_reports': Report.query.filter_by(status='Dismissed').count()
        }