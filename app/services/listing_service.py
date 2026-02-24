import re
from datetime import datetime, timedelta
from app import db
from app.models import Listing, Image, AIAnalysis, User
from app.services.image_service import ImageService
from app.ai.image_analysis import ImageAnalysisService
from app.ai.text_analysis import TextAnalysisService
from app.ai.category_prediction import CategoryPredictionService
from app.ai.price_prediction import PricePredictionService
from app.ai.fraud_detection import FraudDetectionService

# NUEVO: Importamos las herramientas de optimización (Eager Loading)
from sqlalchemy.orm import joinedload

class ListingService:
    def __init__(self):
        self.image_service = ImageService()
        self.text_analysis = TextAnalysisService()
        self.category_prediction = CategoryPredictionService()
        self.price_prediction = PricePredictionService()

    def _sanitize(self, text):
        if not text: return ""
        return re.sub(r'<[^>]*>', '', str(text)).strip()

    def create_listing(self, data, images, virtual_tour_file=None):
        try:
            tier = data.get('tier', 'Gratis')
            user = User.query.get(data['user_id'])
            
            if tier == 'Premium':
                if user.prem_credits <= 0: return {'success': False, 'error': 'No tienes créditos Premium.'}
                user.prem_credits -= 1
            elif tier == 'Profesional':
                if user.prof_credits <= 0: return {'success': False, 'error': 'No tienes créditos Profesionales.'}
                user.prof_credits -= 1

            duration_days = int(data.get('duration_days', 20))
            expires_at = datetime.utcnow() + timedelta(days=duration_days)
            
            vt_url = None
            if virtual_tour_file and virtual_tour_file.filename != '':
                vt_url = self.image_service.upload_image(virtual_tour_file)

            is_negotiable_bool = str(data.get('is_negotiable', '')).lower() in ['true', 'on', '1']

            listing = Listing(
                user_id=data['user_id'], category_id=data['category_id'],
                title=self._sanitize(data['title']), description=self._sanitize(data['description']), 
                price=float(data['price']), province=self._sanitize(data['province']), 
                district=self._sanitize(data['district']), city=self._sanitize(data.get('city', '')),
                condition=self._sanitize(data.get('condition', '')), 
                is_negotiable=is_negotiable_bool,
                tier=tier, duration_days=duration_days, expires_at=expires_at, status='Active',
                virtual_tour_url=vt_url 
            )
            db.session.add(listing)
            db.session.flush()

            image_urls = []
            if images and images[0].filename != '':
                for idx, img in enumerate(images):
                    url = self.image_service.upload_image(img)
                    image_urls.append(url)
                    db.session.add(Image(listing_id=listing.id, image_url=url, display_order=idx, is_primary=(idx == 0)))

            db.session.add(AIAnalysis(listing_id=listing.id))
            db.session.commit()
            return {'success': True, 'listing': {'id': listing.id}}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    def update_listing(self, listing_id, user_id, data, images, virtual_tour_file=None):
        try:
            listing = Listing.query.get(listing_id)
            user = User.query.get(user_id)
            if not listing or listing.user_id != user_id:
                return {'success': False, 'error': 'No autorizado'}
            
            new_tier = data.get('tier', listing.tier)
            if new_tier != listing.tier:
                if new_tier == 'Premium':
                    if user.prem_credits <= 0: return {'success': False, 'error': 'No tienes créditos Premium.'}
                    user.prem_credits -= 1
                elif new_tier == 'Profesional':
                    if user.prof_credits <= 0: return {'success': False, 'error': 'No tienes créditos Profesionales.'}
                    user.prof_credits -= 1
                    
            listing.tier = new_tier
            listing.category_id = data['category_id']
            listing.title = self._sanitize(data['title'])
            listing.description = self._sanitize(data['description'])
            listing.price = float(data['price'])
            listing.province = self._sanitize(data['province'])
            listing.district = self._sanitize(data['district'])
            listing.condition = self._sanitize(data.get('condition'))
            listing.is_negotiable = str(data.get('is_negotiable', '')).lower() in ['true', 'on', '1']
            listing.duration_days = int(data.get('duration_days', listing.duration_days))
            listing.expires_at = datetime.utcnow() + timedelta(days=listing.duration_days)
            listing.status = 'Active' 
            
            if virtual_tour_file and virtual_tour_file.filename != '':
                listing.virtual_tour_url = self.image_service.upload_image(virtual_tour_file)
            
            if images and images[0].filename != '':
                current_image_count = len(listing.images)
                for idx, img in enumerate(images):
                    url = self.image_service.upload_image(img)
                    db.session.add(Image(listing_id=listing.id, image_url=url, display_order=current_image_count + idx))
            
            db.session.commit()
            return {'success': True, 'listing': {'id': listing.id}}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    def delete_image(self, image_id, user_id):
        try:
            image = Image.query.get(image_id)
            if image and image.listing.user_id == user_id:
                db.session.delete(image)
                db.session.commit()
                return True
            return False
        except Exception:
            db.session.rollback()
            return False

    def get_realtime_analysis(self, title, description, image_urls=None):
        try:
            title_clean = self._sanitize(title)
            desc_clean = self._sanitize(description)
            text_result = self.text_analysis.analyze_text(desc_clean) if desc_clean else {'quality': 'Good', 'has_contact_info': False, 'has_suspicious_keywords': False}
            cat_result = self.category_prediction.predict_category(title_clean, desc_clean) if title_clean or desc_clean else {'category_id': 1, 'confidence': 85.0}
            price_result = self.price_prediction.predict_price(cat_result.get('category_id', 1), title_clean, desc_clean) if title_clean or desc_clean else {'suggested_price': 100.0}
            return {
                'suggested_category_id': cat_result.get('category_id', 1), 'category_confidence': cat_result.get('confidence', 85.0),
                'suggested_price': price_result.get('suggested_price', 100.0), 'description_quality': text_result.get('quality', 'Good'),
                'has_contact_info': text_result.get('has_contact_info', False)
            }
        except Exception as e:
            return {'suggested_category_id': 1, 'category_confidence': 90.0, 'suggested_price': 150.0, 'description_quality': 'Good', 'has_contact_info': False}

    def get_listing_by_id(self, listing_id):
        listing = Listing.query.get(listing_id)
        if listing:
            listing.view_count += 1
            db.session.commit()
        return listing

    # ==========================================
    # CORRECCIÓN DE EFICIENCIA N+1 (CRÍTICA)
    # ==========================================
    def search_listings(self, filters):
        now = datetime.utcnow()
        
        # Aplicamos joinedload() para traer Imágenes, Categoría y Usuario en la misma consulta
        query = Listing.query.options(
            joinedload(Listing.images),
            joinedload(Listing.category),
            joinedload(Listing.user)
        ).filter(Listing.status.in_(['Active', 'Sold']), Listing.expires_at > now)
        
        if filters.get('search_term'):
            term = self._sanitize(filters['search_term'])
            query = query.filter(Listing.title.ilike(f"%{term}%"))
        if filters.get('province'):
            query = query.filter(Listing.province.ilike(f"%{self._sanitize(filters['province'])}%"))
        if filters.get('district'):
            query = query.filter(Listing.district.ilike(f"%{self._sanitize(filters['district'])}%"))
        if filters.get('category_id'):
            query = query.filter(Listing.category_id == filters['category_id'])
            
        pagination = query.order_by(Listing.created_at.desc()).paginate(
            page=filters.get('page', 1), per_page=20, error_out=False
        )
        
        return {
            'listings': pagination.items, 
            'total': pagination.total, 
            'pages': pagination.pages, 
            'current_page': pagination.page
        }import re
from datetime import datetime, timedelta
from app import db
from app.models import Listing, Image, AIAnalysis, User
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

    def _sanitize(self, text):
        if not text: return ""
        return re.sub(r'<[^>]*>', '', str(text)).strip()

    def create_listing(self, data, images, virtual_tour_file=None):
        try:
            tier = data.get('tier', 'Gratis')
            user = User.query.get(data['user_id'])
            
            if tier == 'Premium':
                if user.prem_credits <= 0: return {'success': False, 'error': 'No tienes créditos Premium.'}
                user.prem_credits -= 1
            elif tier == 'Profesional':
                if user.prof_credits <= 0: return {'success': False, 'error': 'No tienes créditos Profesionales.'}
                user.prof_credits -= 1

            duration_days = int(data.get('duration_days', 20))
            expires_at = datetime.utcnow() + timedelta(days=duration_days)
            
            vt_url = None
            if virtual_tour_file and virtual_tour_file.filename != '':
                vt_url = self.image_service.upload_image(virtual_tour_file)

            # CORRECCIÓN: Convertir el texto de HTML a un Boolean estricto de Python
            is_negotiable_bool = str(data.get('is_negotiable', '')).lower() in ['true', 'on', '1']

            listing = Listing(
                user_id=data['user_id'], category_id=data['category_id'],
                title=self._sanitize(data['title']), description=self._sanitize(data['description']), 
                price=float(data['price']), province=self._sanitize(data['province']), 
                district=self._sanitize(data['district']), city=self._sanitize(data.get('city', '')),
                condition=self._sanitize(data.get('condition', '')), 
                is_negotiable=is_negotiable_bool, # Aplicamos el Boolean matemático
                tier=tier, duration_days=duration_days, expires_at=expires_at, status='Active',
                virtual_tour_url=vt_url 
            )
            db.session.add(listing)
            db.session.flush()

            image_urls = []
            if images and images[0].filename != '':
                for idx, img in enumerate(images):
                    url = self.image_service.upload_image(img)
                    image_urls.append(url)
                    db.session.add(Image(listing_id=listing.id, image_url=url, display_order=idx, is_primary=(idx == 0)))

            db.session.add(AIAnalysis(listing_id=listing.id))
            db.session.commit()
            return {'success': True, 'listing': {'id': listing.id}}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    def update_listing(self, listing_id, user_id, data, images, virtual_tour_file=None):
        try:
            listing = Listing.query.get(listing_id)
            user = User.query.get(user_id)
            if not listing or listing.user_id != user_id:
                return {'success': False, 'error': 'No autorizado'}
            
            new_tier = data.get('tier', listing.tier)
            if new_tier != listing.tier:
                if new_tier == 'Premium':
                    if user.prem_credits <= 0: return {'success': False, 'error': 'No tienes créditos Premium.'}
                    user.prem_credits -= 1
                elif new_tier == 'Profesional':
                    if user.prof_credits <= 0: return {'success': False, 'error': 'No tienes créditos Profesionales.'}
                    user.prof_credits -= 1
                    
            listing.tier = new_tier
            listing.category_id = data['category_id']
            listing.title = self._sanitize(data['title'])
            listing.description = self._sanitize(data['description'])
            listing.price = float(data['price'])
            listing.province = self._sanitize(data['province'])
            listing.district = self._sanitize(data['district'])
            listing.condition = self._sanitize(data.get('condition'))
            
            # CORRECCIÓN: Convertir el texto de HTML a un Boolean estricto de Python
            listing.is_negotiable = str(data.get('is_negotiable', '')).lower() in ['true', 'on', '1']
            
            listing.duration_days = int(data.get('duration_days', listing.duration_days))
            listing.expires_at = datetime.utcnow() + timedelta(days=listing.duration_days)
            listing.status = 'Active' 
            
            if virtual_tour_file and virtual_tour_file.filename != '':
                listing.virtual_tour_url = self.image_service.upload_image(virtual_tour_file)
            
            if images and images[0].filename != '':
                current_image_count = len(listing.images)
                for idx, img in enumerate(images):
                    url = self.image_service.upload_image(img)
                    db.session.add(Image(listing_id=listing.id, image_url=url, display_order=current_image_count + idx))
            
            db.session.commit()
            return {'success': True, 'listing': {'id': listing.id}}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    def get_realtime_analysis(self, title, description, image_urls=None):
        try:
            title_clean = self._sanitize(title)
            desc_clean = self._sanitize(description)
            text_result = self.text_analysis.analyze_text(desc_clean) if desc_clean else {'quality': 'Good', 'has_contact_info': False, 'has_suspicious_keywords': False}
            cat_result = self.category_prediction.predict_category(title_clean, desc_clean) if title_clean or desc_clean else {'category_id': 1, 'confidence': 85.0}
            price_result = self.price_prediction.predict_price(cat_result.get('category_id', 1), title_clean, desc_clean) if title_clean or desc_clean else {'suggested_price': 100.0}
            return {
                'suggested_category_id': cat_result.get('category_id', 1), 'category_confidence': cat_result.get('confidence', 85.0),
                'suggested_price': price_result.get('suggested_price', 100.0), 'description_quality': text_result.get('quality', 'Good'),
                'has_contact_info': text_result.get('has_contact_info', False)
            }
        except Exception as e:
            return {'suggested_category_id': 1, 'category_confidence': 90.0, 'suggested_price': 150.0, 'description_quality': 'Good', 'has_contact_info': False}

    def get_listing_by_id(self, listing_id):
        listing = Listing.query.get(listing_id)
        if listing:
            listing.view_count += 1
            db.session.commit()
        return listing

    def search_listings(self, filters):
        now = datetime.utcnow()
        query = Listing.query.filter(Listing.status == 'Active', Listing.expires_at > now)
        if filters.get('search_term'):
            query = query.filter(Listing.title.ilike(f"%{self._sanitize(filters['search_term'])}%"))
        if filters.get('province'):
            query = query.filter(Listing.province.ilike(f"%{self._sanitize(filters['province'])}%"))
        if filters.get('district'):
            query = query.filter(Listing.district.ilike(f"%{self._sanitize(filters['district'])}%"))
        if filters.get('category_id'):
            query = query.filter(Listing.category_id == filters['category_id'])
            
        pagination = query.order_by(Listing.created_at.desc()).paginate(page=filters.get('page', 1), per_page=20, error_out=False)
        return {'listings': pagination.items, 'total': pagination.total, 'pages': pagination.pages, 'current_page': pagination.page}
