import os

print("🚀 Aplicando mejoras finales: Imágenes dinámicas, IA, Portada Pública y Accesibilidad...")

archivos = {
    "app/services/image_service.py": """import os
import time
from werkzeug.utils import secure_filename

class ImageService:
    def upload_image(self, image_file):
        if not image_file or image_file.filename == '':
            return "https://via.placeholder.com/400x300?text=Sin+Imagen"
            
        upload_dir = os.path.join('app', 'static', 'images', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        filename = secure_filename(f"{int(time.time())}_{image_file.filename}")
        file_path = os.path.join(upload_dir, filename)
        image_file.save(file_path)
        
        return f"/static/images/uploads/{filename}"
""",

    "app/routes/main.py": """from flask import Blueprint, render_template
from app.models import Listing

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    recent_listings = Listing.query.filter_by(status='Active').order_by(Listing.created_at.desc()).limit(8).all()
    return render_template('index.html', listings=recent_listings)
""",

    "app/routes/listings.py": """from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.services.listing_service import ListingService
from app.models import Category, Listing
from app import db

listings_bp = Blueprint('listings', __name__, url_prefix='/listings')
listing_service = ListingService()

@listings_bp.route('/')
def index():
    filters = {'search_term': request.args.get('search'), 'category_id': request.args.get('category_id', type=int), 'page': request.args.get('page', 1, type=int)}
    result = listing_service.search_listings(filters)
    return render_template('listings/index.html', listings=result['listings'], filters=filters)

@listings_bp.route('/<int:listing_id>')
def details(listing_id):
    listing = listing_service.get_listing_by_id(listing_id)
    if not listing: return redirect(url_for('listings.index'))
    return render_template('listings/details.html', listing=listing)

@listings_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'GET':
        categories = Category.query.filter_by(is_active=True).all()
        return render_template('listings/create.html', categories=categories)
    
    data = {
        'user_id': current_user.id, 'category_id': request.form.get('category_id', type=int),
        'title': request.form.get('title'), 'description': request.form.get('description'),
        'price': request.form.get('price', type=float), 'province': request.form.get('province'),
        'district': request.form.get('district'), 'city': request.form.get('city'),
        'condition': request.form.get('condition'), 'is_negotiable': request.form.get('is_negotiable') == 'on',
        'image_url_link': request.form.get('image_url_link')
    }
    images = request.files.getlist('images')
    result = listing_service.create_listing(data, images)
    
    if result['success']: return redirect(url_for('listings.details', listing_id=result['listing']['id']))
    return redirect(url_for('listings.create'))

@listings_bp.route('/api/realtime-analysis', methods=['POST'])
@login_required
def realtime_analysis():
    data = request.get_json()
    analysis = listing_service.get_realtime_analysis(data.get('title', ''), data.get('description', ''), data.get('image_urls', []))
    return jsonify({'success': True, 'data': analysis})

@listings_bp.route('/my-listings')
@login_required
def my_listings():
    listings = Listing.query.filter_by(user_id=current_user.id).order_by(Listing.created_at.desc()).all()
    return render_template('listings/my_listings.html', listings=listings)

@listings_bp.route('/<int:listing_id>/delete', methods=['POST'])
@login_required
def delete(listing_id):
    listing = Listing.query.get(listing_id)
    if listing and listing.user_id == current_user.id:
        listing.status = 'Deleted'
        db.session.commit()
    return redirect(url_for('listings.my_listings'))
""",

    "app/services/listing_service.py": """from datetime import datetime
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
""",

    "app/templates/index.html": """{% extends "base.html" %}
{% block title %}Inicio{% endblock %}
{% block content %}
<div class="text-center py-12 mb-8 bg-white dark:bg-gray-800 rounded-3xl shadow-sm border border-gray-100 dark:border-gray-700">
    <h1 class="text-4xl font-extrabold text-gray-900 dark:text-white sm:text-5xl sm:tracking-tight lg:text-6xl">
        Mercado Libre de <span class="text-blue-600">Panamá</span>
    </h1>
    <p class="max-w-xl mt-5 mx-auto text-xl text-gray-500 dark:text-gray-400">
        Compra y vende lo que quieras de forma rápida, impulsado por IA.
    </p>
    <div class="mt-8 flex justify-center gap-4">
        {% if current_user.is_authenticated %}
        <a href="{{ url_for('listings.create') }}" class="px-8 py-3 bg-blue-600 text-white rounded-xl font-bold shadow-lg shadow-blue-600/30 hover:scale-105 transition-transform">Publicar Anuncio</a>
        {% else %}
        <a href="{{ url_for('auth.login') }}" class="px-8 py-3 bg-blue-600 text-white rounded-xl font-bold shadow-lg shadow-blue-600/30 hover:scale-105 transition-transform">Vender Ahora</a>
        {% endif %}
    </div>
</div>

<div class="max-w-7xl mx-auto">
    <div class="flex justify-between items-center mb-6">
        <h2 class="text-2xl font-bold">Últimos Anuncios</h2>
        <a href="{{ url_for('listings.index') }}" class="text-blue-600 font-semibold hover:underline">Ver todos →</a>
    </div>

    {% if listings %}
    <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
        {% for listing in listings %}
        <a href="{{ url_for('listings.details', listing_id=listing.id) }}" class="bg-white dark:bg-gray-800 rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-shadow border border-gray-100 dark:border-gray-700 block group">
            <div class="relative h-48 overflow-hidden">
                <img src="{{ listing.images[0].image_url if listing.images else 'https://via.placeholder.com/400x300?text=Sin+Imagen' }}" 
                     alt="Imagen de {{ listing.title }}"
                     onerror="this.src='https://via.placeholder.com/400x300?text=Sin+Imagen'"
                     class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300">
            </div>
            <div class="p-4">
                <h3 class="font-bold text-lg mb-1 truncate text-gray-800 dark:text-white">{{ listing.title }}</h3>
                <p class="text-blue-600 font-extrabold text-xl mb-2">${{ listing.price }}</p>
                <div class="text-xs text-gray-500">{{ listing.province }}</div>
            </div>
        </a>
        {% endfor %}
    </div>
    {% else %}
    <div class="text-center py-12 text-gray-500 bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700">
        <span class="material-icons-round text-6xl mb-3 text-gray-300">inventory_2</span>
        <p class="font-bold">Aún no hay anuncios públicos. ¡Sé el primero en publicar!</p>
    </div>
    {% endif %}
</div>
{% endblock %}
""",

    "app/templates/listings/create.html": """{% extends "base.html" %}
{% block title %}Nueva Publicación{% endblock %}
{% block content %}
<div class="max-w-3xl mx-auto">
    <h1 class="text-3xl font-bold mb-8">Publicar un Anuncio</h1>
    
    <form id="listing-form" method="POST" enctype="multipart/form-data" class="space-y-6">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

        <!-- PANEL IA -->
        <div class="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 p-5 rounded-2xl border border-blue-200 dark:border-blue-800 transition-all duration-300" id="ai-analysis-container">
            <h3 class="font-bold text-blue-800 dark:text-blue-300 flex items-center gap-2 mb-3">
                <span class="material-icons-round text-blue-600 animate-pulse">auto_awesome</span> Asistente Inteligente
                <span id="ai-loading" class="hidden text-xs text-blue-500 font-normal ml-2">Analizando...</span>
            </h3>
            <div class="grid grid-cols-2 gap-4">
                <div id="ai-suggested-category" class="bg-white dark:bg-gray-800 p-3 rounded-xl shadow-sm text-sm hidden"></div>
                <div id="ai-suggested-price" class="bg-white dark:bg-gray-800 p-3 rounded-xl shadow-sm text-sm hidden"></div>
            </div>
            <div id="ai-quality-feedback" class="mt-3 text-xs font-semibold text-gray-600 hidden"></div>
        </div>

        <div class="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-sm space-y-5">
            <div>
                <label for="title" class="text-sm font-bold text-gray-600 mb-1 block">Título</label>
                <input type="text" id="title" name="title" required title="Título del anuncio" aria-label="Título del anuncio" class="w-full px-4 py-3 rounded-xl border border-gray-300">
            </div>
            <div>
                <label for="description" class="text-sm font-bold text-gray-600 mb-1 block">Descripción</label>
                <textarea id="description" name="description" rows="4" required title="Descripción" aria-label="Descripción" class="w-full px-4 py-3 rounded-xl border border-gray-300"></textarea>
            </div>
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <label for="category_id" class="text-sm font-bold text-gray-600 mb-1 block">Categoría</label>
                    <select id="category_id" name="category_id" required title="Seleccionar categoría" aria-label="Categoría" class="w-full px-4 py-3 rounded-xl border border-gray-300">
                        {% for c in categories %}<option value="{{ c.id }}">{{ c.name }}</option>{% endfor %}
                    </select>
                </div>
                <div>
                    <label for="price" class="text-sm font-bold text-gray-600 mb-1 block">Precio ($)</label>
                    <input type="number" id="price" name="price" required title="Precio" aria-label="Precio" class="w-full px-4 py-3 rounded-xl border border-gray-300">
                </div>
            </div>
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <label for="province" class="text-sm font-bold text-gray-600 mb-1 block">Provincia</label>
                    <input type="text" id="province" name="province" required title="Provincia" aria-label="Provincia" class="w-full px-4 py-3 rounded-xl border border-gray-300">
                </div>
                <div>
                    <label for="district" class="text-sm font-bold text-gray-600 mb-1 block">Distrito</label>
                    <input type="text" id="district" name="district" required title="Distrito" aria-label="Distrito" class="w-full px-4 py-3 rounded-xl border border-gray-300">
                </div>
            </div>
        </div>

        <!-- ZONA DE IMÁGENES -->
        <div class="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-sm">
            <h3 class="font-bold mb-4">Fotos del producto</h3>
            <div class="mb-4">
                <label for="image_url_link" class="text-sm text-gray-500 mb-1 block">Pegar un enlace de imagen (URL)</label>
                <input type="url" name="image_url_link" id="image_url_link" title="Enlace web" aria-label="Enlace web" placeholder="https://ejemplo.com/imagen.jpg" class="w-full px-4 py-3 rounded-xl border border-gray-300">
            </div>
            <div class="text-center text-sm font-bold text-gray-400 mb-2">--- Ó ---</div>
            <label id="drop-zone" for="images" class="block w-full p-8 border-2 border-dashed border-blue-400 rounded-xl bg-blue-50/50 hover:bg-blue-50 cursor-pointer text-center">
                <span class="material-icons-round text-blue-500 text-4xl mb-2">cloud_upload</span>
                <p class="font-bold text-blue-800">Haz clic, arrastra o presiona Ctrl+V para pegar imágenes</p>
                <input type="file" id="images" name="images" multiple accept="image/*" class="hidden" title="Subir imágenes" aria-label="Subir imágenes">
            </label>
            <div id="image-preview" class="flex gap-4 mt-4 overflow-x-auto pb-2"></div>
        </div>
        
        <button type="submit" class="w-full bg-blue-600 text-white py-4 rounded-xl font-bold hover:bg-blue-700 transition-all">Publicar Anuncio</button>
    </form>
</div>
{% endblock %}
{% block extra_js %}<script src="{{ url_for('static', filename='js/listing-create.js') }}"></script>{% endblock %}
""",

    "app/templates/listings/details.html": """{% extends "base.html" %}
{% block title %}{{ listing.title }}{% endblock %}
{% block content %}
<div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
    <div class="lg:col-span-2 space-y-6">
        <div class="bg-white dark:bg-gray-800 rounded-2xl overflow-hidden shadow-sm border border-gray-100">
            <img id="main-image" src="{{ listing.images[0].image_url if listing.images else 'https://via.placeholder.com/600x400?text=Sin+Imagen' }}" alt="Imagen de {{ listing.title }}" onerror="this.src='https://via.placeholder.com/600x400?text=Sin+Imagen'" class="w-full h-96 object-cover">
        </div>
        <div class="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-sm border border-gray-100">
            <h2 class="text-xl font-bold mb-4">Descripción</h2>
            <p class="text-gray-700 dark:text-gray-300 whitespace-pre-line">{{ listing.description }}</p>
        </div>
    </div>
    
    <div class="space-y-6">
        <div class="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-sm border border-gray-100">
            <h1 class="text-2xl font-bold mb-2">{{ listing.title }}</h1>
            <p class="text-3xl font-bold text-blue-600 mb-6">${{ listing.price }}</p>
            <div class="flex items-center gap-2 text-gray-600 mb-6"><span class="material-icons-round">location_on</span><span>{{ listing.district }}, {{ listing.province }}</span></div>
            {% if current_user.is_authenticated and current_user.id != listing.user_id %}
            <a href="{{ url_for('chat.start_chat', listing_id=listing.id) }}" class="flex items-center justify-center gap-2 w-full bg-blue-600 text-white py-3 rounded-xl font-bold mb-3 hover:bg-blue-700"><span class="material-icons-round">chat</span> Chatear</a>
            <button onclick="document.getElementById('report-modal').classList.remove('hidden')" class="flex items-center justify-center gap-2 w-full border-2 border-red-500/20 text-red-500 py-3 rounded-xl font-bold hover:bg-red-50"><span class="material-icons-round">report</span> Reportar</button>
            {% endif %}
        </div>
    </div>
</div>

<div id="report-modal" class="hidden fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
    <div class="bg-white p-6 rounded-xl w-full max-w-md shadow-xl">
        <h2 class="text-xl font-bold mb-4 text-black">Reportar Anuncio</h2>
        <form id="report-form" class="space-y-4">
            <select name="report_type" aria-label="Motivo del reporte" title="Motivo del reporte" class="w-full p-3 border border-gray-300 rounded-lg text-black focus:ring-2 focus:ring-red-500">
                <option value="FakePrice">Precio Falso / Engañoso</option>
                <option value="SuspiciousSeller">Vendedor Sospechoso</option>
                <option value="IllegalContent">Contenido Inapropiado</option>
            </select>
            <button type="submit" class="w-full bg-red-600 text-white py-3 rounded-xl font-bold hover:bg-red-700">Enviar Reporte</button>
            <button type="button" onclick="document.getElementById('report-modal').classList.add('hidden')" class="w-full py-2 text-gray-500 hover:text-gray-800 font-bold">Cancelar</button>
        </form>
    </div>
</div>
<script>
document.getElementById('report-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {listing_id: {{ listing.id }}, report_type: e.target.report_type.value};
    const res = await fetch('{{ url_for("reports.create") }}', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)});
    const result = await res.json();
    alert(result.message || result.error);
    document.getElementById('report-modal').classList.add('hidden');
});
</script>
{% endblock %}
""",

    "app/templates/reports/review.html": """{% extends "base.html" %}
{% block title %}Revisar Reporte{% endblock %}
{% block content %}
<div class="max-w-4xl mx-auto">
    <a href="{{ url_for('reports.moderation') }}" class="text-blue-600 hover:underline mb-6 inline-block font-bold">← Volver al Panel</a>
    <h1 class="text-3xl font-bold mb-8">Revisar Reporte #{{ report.id }}</h1>
    
    <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 text-black">
        <form method="POST" action="{{ url_for('reports.review', report_id=report.id) }}" class="space-y-5">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
            <div>
                <label for="action_taken" class="block text-sm font-bold text-gray-700 mb-2">Decisión a tomar:</label>
                <select id="action_taken" name="action_taken" required title="Seleccionar acción" aria-label="Acción a tomar" class="w-full p-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500">
                    <option value="">-- Elige una acción --</option>
                    <option value="ListingRemoved">Eliminar Anuncio Definitivamente</option>
                    <option value="NoAction">No hacer nada (Falsa Alarma)</option>
                    <option value="UserBanned">Suspender Usuario</option>
                </select>
            </div>
            <div>
                <label for="status" class="block text-sm font-bold text-gray-700 mb-2">Estado final del reporte:</label>
                <select id="status" name="status" required title="Estado del reporte" aria-label="Estado del reporte" class="w-full p-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500">
                    <option value="Resolved">Marcar como Resuelto</option>
                    <option value="Dismissed">Descartar Reporte (Inválido)</option>
                </select>
            </div>
            <button type="submit" class="w-full bg-blue-600 text-white py-3.5 rounded-xl font-bold hover:bg-blue-700 shadow-lg shadow-blue-600/30">Ejecutar Decisión</button>
        </form>
    </div>
</div>
{% endblock %}
""",

    "app/static/js/listing-create.js": """class ListingAIAssistant {
    constructor() {
        this.titleInput = document.getElementById('title');
        this.descriptionInput = document.getElementById('description');
        this.categorySelect = document.getElementById('category_id');
        this.priceInput = document.getElementById('price');
        
        this.aiContainer = document.getElementById('ai-analysis-container');
        this.catBadge = document.getElementById('ai-suggested-category');
        this.priceBadge = document.getElementById('ai-suggested-price');
        this.feedbackBadge = document.getElementById('ai-quality-feedback');
        this.loader = document.getElementById('ai-loading');
        this.debounceTimer = null;

        this.fileInput = document.getElementById('images');
        this.dropZone = document.getElementById('drop-zone');
        this.previewContainer = document.getElementById('image-preview');
        this.dataTransfer = new DataTransfer(); 
        
        this.initEvents();
    }

    initEvents() {
        this.titleInput.addEventListener('input', () => this.scheduleAnalysis());
        this.descriptionInput.addEventListener('input', () => this.scheduleAnalysis());
        this.fileInput.addEventListener('change', (e) => this.handleFiles(e.target.files));

        document.addEventListener('paste', (e) => {
            const items = (e.clipboardData || e.originalEvent.clipboardData).items;
            let filesAdded = false;
            for (let item of items) {
                if (item.type.indexOf('image') === 0) {
                    this.dataTransfer.items.add(item.getAsFile());
                    filesAdded = true;
                }
            }
            if (filesAdded) {
                this.fileInput.files = this.dataTransfer.files;
                this.handleFiles(this.fileInput.files);
            }
        });

        this.dropZone.addEventListener('dragover', (e) => { e.preventDefault(); this.dropZone.classList.add('bg-blue-100'); });
        this.dropZone.addEventListener('dragleave', () => this.dropZone.classList.remove('bg-blue-100'));
        this.dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            this.dropZone.classList.remove('bg-blue-100');
            if (e.dataTransfer.files.length) {
                for(let file of e.dataTransfer.files) {
                    if (file.type.startsWith('image/')) this.dataTransfer.items.add(file);
                }
                this.fileInput.files = this.dataTransfer.files;
                this.handleFiles(this.fileInput.files);
            }
        });
    }

    handleFiles(files) {
        this.previewContainer.innerHTML = '';
        Array.from(files).forEach((file, index) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                this.previewContainer.innerHTML += `<div class="relative w-24 h-24 flex-shrink-0 rounded-xl overflow-hidden shadow-sm border border-gray-200"><img src="${e.target.result}" class="w-full h-full object-cover"><span class="absolute bottom-0 left-0 w-full bg-black/50 text-white text-[10px] text-center py-1">Img ${index+1}</span></div>`;
            };
            reader.readAsDataURL(file);
        });
    }

    scheduleAnalysis() {
        clearTimeout(this.debounceTimer);
        this.loader.classList.remove('hidden');
        this.debounceTimer = setTimeout(() => this.performRealtimeAnalysis(), 1000);
    }

    async performRealtimeAnalysis() {
        const title = this.titleInput.value.trim();
        const desc = this.descriptionInput.value.trim();
        if (!title && !desc) return;

        try {
            const res = await fetch('/listings/api/realtime-analysis', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({title: title, description: desc})
            });
            const result = await res.json();
            this.loader.classList.add('hidden');

            if (result.success) {
                const catOption = this.categorySelect.querySelector(`option[value="${result.data.suggested_category_id}"]`);
                const catName = catOption ? catOption.textContent : 'Recomendada';
                this.catBadge.innerHTML = `<p class="text-xs text-gray-500 mb-1">Categoría</p><p class="font-bold text-blue-700">${catName}</p><button type="button" onclick="document.getElementById('category_id').value='${result.data.suggested_category_id}'" class="mt-2 w-full text-xs bg-blue-100 text-blue-700 py-1 rounded hover:bg-blue-200 font-bold">Aplicar</button>`;
                this.catBadge.classList.remove('hidden');

                this.priceBadge.innerHTML = `<p class="text-xs text-gray-500 mb-1">Precio Mercado</p><p class="font-bold text-green-700">$${result.data.suggested_price}</p><button type="button" onclick="document.getElementById('price').value='${result.data.suggested_price}'" class="mt-2 w-full text-xs bg-green-100 text-green-700 py-1 rounded hover:bg-green-200 font-bold">Aplicar</button>`;
                this.priceBadge.classList.remove('hidden');

                this.feedbackBadge.innerHTML = result.data.description_quality === 'Good' ? '✅ Buena descripción' : '⚠️ Añade más detalles';
                this.feedbackBadge.classList.remove('hidden');
            }
        } catch (e) { this.loader.classList.add('hidden'); }
    }
}
document.addEventListener('DOMContentLoaded', () => window.listingAI = new ListingAIAssistant());
"""
}

for ruta, contenido in archivos.items():
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(contenido)
    print(f"✅ Archivo actualizado y corregido: {ruta}")

print("\n🎉 ¡Listo! El proyecto está perfecto, accesible y funcional.")