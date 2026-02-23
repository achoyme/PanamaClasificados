class ListingAIAssistant {
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
