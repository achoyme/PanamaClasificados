from datetime import datetime
from app import db
from app.models import Listing, Image, AIAnalysis, Category
from app.services.image_service import ImageService
from app.ai.image_analysis import ImageAnalysisService
from app.ai.text_analysis import TextAnalysisService
from app.ai.category_prediction import CategoryPredictionService
from app.ai.price_prediction import PricePredictionService
from app.ai.fraud_detection import FraudDetectionService

class ListingService:
    def __init__(self):
        self.image_service = ImageService()
        self.text_analysis = TextAnalysisService()
        self.category_prediction = CategoryPredictionService()
        self.price_prediction = PricePredictionService()

    def create_listing(self, data, images):
        try:
            listing = Listing(
                user_id=data['user_id'], category_id=data['category_id'],
                title=data['title'], description=data['description'], price=data['price'],
                province=data['province'], district=data['district'], city=data.get('city'),
                condition=data.get('condition'), is_negotiable=data.get('is_negotiable', True)
            )
            db.session.add(listing)
            db.session.flush()

            image_urls = []
            if images and images[0].filename != '':
                for idx, img in enumerate(images):
                    url = self.image_service.upload_image(img)
                    image_urls.append(url)
                    db.session.add(Image(listing_id=listing.id, image_url=url, display_order=idx, is_primary=(idx == 0)))

            if data.get('image_url_link'):
                db.session.add(Image(listing_id=listing.id, image_url=data['image_url_link'], display_order=len(image_urls), is_primary=(len(image_urls) == 0)))

            ai_analysis = AIAnalysis(listing_id=listing.id)
            db.session.add(ai_analysis)
            db.session.commit()
            return {'success': True, 'listing': {'id': listing.id}}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    def get_realtime_analysis(self, title, description, image_urls=None):
        text_result = self.text_analysis.analyze_text(description)
        cat_result = self.category_prediction.predict_category(title, description)
        price_result = self.price_prediction.predict_price(cat_result['category_id'], title, description)
        return {
            'suggested_category_id': cat_result['category_id'],
            'category_confidence': cat_result['confidence'],
            'suggested_price': price_result['suggested_price'],
            'description_quality': text_result['quality'],
            'has_contact_info': text_result['has_contact_info']
        }

    def get_listing_by_id(self, listing_id):
        listing = Listing.query.get(listing_id)
        if listing:
            listing.view_count += 1
            db.session.commit()
        return listing

    def search_listings(self, filters):
        query = Listing.query.filter_by(status='Active')
        if filters.get('search_term'):
            query = query.filter(Listing.title.ilike(f"%{filters['search_term']}%"))
        pagination = query.order_by(Listing.created_at.desc()).paginate(page=filters.get('page', 1), per_page=20, error_out=False)
        return {'listings': pagination.items, 'total': pagination.total, 'pages': pagination.pages, 'current_page': pagination.page}
