import re
from datetime import datetime, timedelta
from app import db
from app.models import Listing, Image, AIAnalysis, User, Category
from app.services.image_service import ImageService
from app.ai.image_analysis import ImageAnalysisService
from app.ai.text_analysis import TextAnalysisService
from app.ai.category_prediction import CategoryPredictionService
from app.ai.price_prediction import PricePredictionService
from app.ai.fraud_detection import FraudDetectionService
from sqlalchemy.orm import joinedload
from sqlalchemy import func

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

            # Lectura del nombre de la categoría para no fallar
            category = Category.query.get(data['category_id'])
            cat_name = category.name.lower() if category else ''

            dynamic_attrs = {}
            if 'auto' in cat_name or 'vehículo' in cat_name or 'vehiculo' in cat_name or 'motor' in cat_name:
                dynamic_attrs['marca'] = self._sanitize(data.get('attr_marca', ''))
                dynamic_attrs['modelo'] = self._sanitize(data.get('attr_modelo', ''))
                dynamic_attrs['ano'] = self._sanitize(data.get('attr_ano', ''))
                dynamic_attrs['kilometraje'] = self._sanitize(data.get('attr_kilometraje', ''))
                dynamic_attrs['transmision'] = self._sanitize(data.get('attr_transmision', ''))
            elif 'inmueble' in cat_name or 'bienes' in cat_name or 'raíces' in cat_name or 'raices' in cat_name or 'casa' in cat_name:
                dynamic_attrs['habitaciones'] = self._sanitize(data.get('attr_habitaciones', ''))
                dynamic_attrs['banos'] = self._sanitize(data.get('attr_banos', ''))
                dynamic_attrs['metros_cuadrados'] = self._sanitize(data.get('attr_metros', ''))
                dynamic_attrs['estacionamientos'] = self._sanitize(data.get('attr_estacionamientos', ''))

            listing = Listing(
                user_id=data['user_id'], category_id=data['category_id'],
                title=self._sanitize(data['title']), description=self._sanitize(data['description']), 
                price=float(data['price']), province=self._sanitize(data['province']), 
                district=self._sanitize(data['district']), city=self._sanitize(data.get('city', '')),
                condition=self._sanitize(data.get('condition', '')), 
                is_negotiable=is_negotiable_bool,
                tier=tier, duration_days=duration_days, expires_at=expires_at, status='Active',
                virtual_tour_url=vt_url, attributes=dynamic_attrs
            )
            db.session.add(listing)
            db.session.flush()

            image_urls = []
            if images and images[0].filename != '':
                for idx, img in enumerate(images):
                    url = self.image_service.upload_image(img)
                    if url:
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

            category = Category.query.get(data['category_id'])
            cat_name = category.name.lower() if category else ''

            dynamic_attrs = {}
            if 'auto' in cat_name or 'vehículo' in cat_name or 'vehiculo' in cat_name or 'motor' in cat_name:
                dynamic_attrs['marca'] = self._sanitize(data.get('attr_marca', ''))
                dynamic_attrs['modelo'] = self._sanitize(data.get('attr_modelo', ''))
                dynamic_attrs['ano'] = self._sanitize(data.get('attr_ano', ''))
                dynamic_attrs['kilometraje'] = self._sanitize(data.get('attr_kilometraje', ''))
                dynamic_attrs['transmision'] = self._sanitize(data.get('attr_transmision', ''))
            elif 'inmueble' in cat_name or 'bienes' in cat_name or 'raíces' in cat_name or 'raices' in cat_name or 'casa' in cat_name:
                dynamic_attrs['habitaciones'] = self._sanitize(data.get('attr_habitaciones', ''))
                dynamic_attrs['banos'] = self._sanitize(data.get('attr_banos', ''))
                dynamic_attrs['metros_cuadrados'] = self._sanitize(data.get('attr_metros', ''))
                dynamic_attrs['estacionamientos'] = self._sanitize(data.get('attr_estacionamientos', ''))
            listing.attributes = dynamic_attrs
            
            if virtual_tour_file and virtual_tour_file.filename != '':
                listing.virtual_tour_url = self.image_service.upload_image(virtual_tour_file)
            
            if images and images[0].filename != '':
                current_image_count = len(listing.images)
                for idx, img in enumerate(images):
                    url = self.image_service.upload_image(img)
                    if url: db.session.add(Image(listing_id=listing.id, image_url=url, display_order=current_image_count + idx))
            
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

    def search_listings(self, filters):
        now = datetime.utcnow()
        query = Listing.query.options(
            joinedload(Listing.images),
            joinedload(Listing.category),
            joinedload(Listing.user)
        ).filter(Listing.status.in_(['Active', 'Sold']), Listing.expires_at > now)
        
        # Búsqueda Full-Text rápida y poderosa en PostgreSQL
        search_term = filters.get('search_term', '').strip()
        if search_term:
            sanitized_term = re.sub(r"[^\w\s]", "", search_term)
            if sanitized_term:
                search_vector = func.to_tsvector('spanish', Listing.title + ' ' + Listing.description)
                search_query = func.plainto_tsquery('spanish', sanitized_term)
                query = query.filter(search_vector.op('@@')(search_query))
                query = query.order_by(func.ts_rank(search_vector, search_query).desc())
        else:
            query = query.order_by(Listing.created_at.desc())

        if filters.get('province'):
            query = query.filter(Listing.province.ilike(f"%{self._sanitize(filters['province'])}%"))
        if filters.get('district'):
            query = query.filter(Listing.district.ilike(f"%{self._sanitize(filters['district'])}%"))
        if filters.get('category_id'):
            query = query.filter(Listing.category_id == filters['category_id'])
            
        pagination = query.paginate(
            page=filters.get('page', 1), per_page=20, error_out=False
        )
        
        return {
            'listings': pagination.items, 
            'total': pagination.total, 
            'pages': pagination.pages, 
            'current_page': pagination.page
        }
