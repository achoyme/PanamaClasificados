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

        this.csrfToken = document.querySelector('input[name="csrf_token"]')?.value || '';

        // Archivos normales
        this.fileInput = document.getElementById('images');
        this.dropZone = document.getElementById('drop-zone');
        this.previewContainer = document.getElementById('image-preview');
        this.dataTransfer = new DataTransfer(); 
        
        // Archivo 360° (NUEVO)
        this.vtInput = document.getElementById('virtual_tour');
        this.vtPreviewBox = document.getElementById('vt-live-preview');
        
        this.initEvents();
    }

    initEvents() {
        if(this.titleInput) this.titleInput.addEventListener('input', () => this.scheduleAnalysis());
        if(this.descriptionInput) this.descriptionInput.addEventListener('input', () => this.scheduleAnalysis());
        
        // VISTA PREVIA TEMPORAL EN VIVO DEL TOUR 360
        if(this.vtInput) {
            this.vtInput.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if(file) {
                    // Muestra el div contenedor
                    this.vtPreviewBox.classList.remove('hidden');
                    
                    // Crea una URL temporal en memoria del navegador ultra-rápida (ideal para .avif grandes)
                    const tempUrl = URL.createObjectURL(file);
                    
                    // Si ya había un visor, lo destruye para poner el nuevo
                    if (window.liveVtViewer) {
                        window.liveVtViewer.destroy();
                    }
                    
                    // Inicializa la magia 360 en el formulario
                    window.liveVtViewer = pannellum.viewer('vt-live-preview', {
                        "type": "equirectangular",
                        "panorama": tempUrl,
                        "autoLoad": true,
                        "compass": true,
                        "showZoomCtrl": false,
                        "mouseZoom": false,
                        "autoRotate": -2
                    });
                }
            });
        }

        // Galería Normal
        if(this.fileInput) {
            this.fileInput.addEventListener('change', (e) => {
                let newFilesAdded = false;
                for(let file of e.target.files) {
                    if (file.type.startsWith('image/')) {
                        this.dataTransfer.items.add(file);
                        newFilesAdded = true;
                    }
                }
                if (newFilesAdded) {
                    this.fileInput.files = this.dataTransfer.files;
                    this.handleFiles(this.fileInput.files);
                }
            });
        }

        document.addEventListener('paste', (e) => {
            if(!this.fileInput) return;
            const items = (e.clipboardData || e.originalEvent.clipboardData).items;
            let filesAdded = false;
            
            for (let item of items) {
                if (item.type.indexOf('image') === 0) {
                    let file = item.getAsFile();
                    const uniqueName = `pegado_${Date.now()}_${Math.floor(Math.random() * 1000)}.png`;
                    const newFile = new File([file], uniqueName, { type: file.type });
                    this.dataTransfer.items.add(newFile);
                    filesAdded = true;
                }
            }
            if (filesAdded) {
                this.fileInput.files = this.dataTransfer.files;
                this.handleFiles(this.fileInput.files);
            }
        });

        if(this.dropZone) {
            this.dropZone.addEventListener('dragover', (e) => { e.preventDefault(); this.dropZone.classList.add('bg-gray-200'); });
            this.dropZone.addEventListener('dragleave', () => { this.dropZone.classList.remove('bg-gray-200'); });
            this.dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                this.dropZone.classList.remove('bg-gray-200');
                let filesAdded = false;
                if (e.dataTransfer.files.length) {
                    for(let file of e.dataTransfer.files) {
                        if (file.type.startsWith('image/')) { 
                            this.dataTransfer.items.add(file); 
                            filesAdded = true;
                        }
                    }
                    if (filesAdded) {
                        this.fileInput.files = this.dataTransfer.files;
                        this.handleFiles(this.fileInput.files);
                    }
                }
            });
        }
    }

    handleFiles(files) {
        if(!this.previewContainer) return;
        this.previewContainer.innerHTML = '';
        Array.from(files).forEach((file, index) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                const div = document.createElement('div');
                div.className = "relative w-24 h-24 flex-shrink-0 rounded-md overflow-hidden shadow-sm border border-gray-200";
                div.innerHTML = `
                    <img src="${e.target.result}" class="w-full h-full object-cover">
                    <span class="absolute bottom-0 left-0 w-full bg-black/60 text-white text-[10px] text-center py-1 truncate px-1">Img ${index+1}</span>
                `;
                this.previewContainer.appendChild(div);
            };
            reader.readAsDataURL(file);
        });
    }

    scheduleAnalysis() {
        clearTimeout(this.debounceTimer);
        if(this.loader) this.loader.classList.remove('hidden');
        this.debounceTimer = setTimeout(() => this.performRealtimeAnalysis(), 1000);
    }

    async performRealtimeAnalysis() {
        if(!this.titleInput || !this.descriptionInput) return;
        const title = this.titleInput.value.trim();
        const desc = this.descriptionInput.value.trim();
        if (!title && !desc) return;

        try {
            const res = await fetch('/listings/api/realtime-analysis', {
                method: 'POST', 
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({title: title, description: desc})
            });
            
            if(!res.ok) throw new Error("Fallo en red o seguridad");
            const result = await res.json();
            
            if(this.loader) this.loader.classList.add('hidden');

            if (result.success && this.aiContainer && result.data) {
                this.aiContainer.classList.remove('hidden');
                
                if(this.catBadge && result.data.suggested_category_id) {
                    const catOption = this.categorySelect.querySelector(`option[value="${result.data.suggested_category_id}"]`);
                    const catName = catOption ? catOption.textContent : 'Sugerida';
                    this.catBadge.innerHTML = `<p class="text-xs text-gray-500 mb-1">Categoría Sugerida</p><p class="font-bold text-gray-900">${catName}</p><button type="button" onclick="document.getElementById('category_id').value='${result.data.suggested_category_id}'" class="mt-2 w-full text-xs bg-gray-100 text-gray-700 py-1.5 rounded-md hover:bg-gray-200 font-bold border border-gray-300 transition-colors">Aplicar</button>`;
                    this.catBadge.classList.remove('hidden');
                }

                if(this.priceBadge && result.data.suggested_price) {
                    this.priceBadge.innerHTML = `<p class="text-xs text-gray-500 mb-1">Precio Mercado</p><p class="font-bold text-green-700">$${result.data.suggested_price}</p><button type="button" onclick="document.getElementById('price').value='${result.data.suggested_price}'" class="mt-2 w-full text-xs bg-gray-100 text-gray-700 py-1.5 rounded-md hover:bg-gray-200 font-bold border border-gray-300 transition-colors">Aplicar</button>`;
                    this.priceBadge.classList.remove('hidden');
                }

                if(this.feedbackBadge && result.data.description_quality) {
                    this.feedbackBadge.innerHTML = result.data.description_quality === 'Good' || result.data.description_quality === 'Excellent' ? '✅ Buena descripción' : '⚠️ Añade más detalles a tu anuncio';
                    this.feedbackBadge.classList.remove('hidden');
                }
            }
        } catch (e) { 
            console.error("Servicio protegido o no disponible", e);
            if(this.loader) this.loader.classList.add('hidden');
        }
    }
}

document.addEventListener('DOMContentLoaded', () => window.listingAI = new ListingAIAssistant());