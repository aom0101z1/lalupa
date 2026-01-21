// Estado de la aplicacion
let data = {
    categorias: [],
    casos: [],
    estadisticas: {}
};
let filteredCasos = [];

// Elementos del DOM
const statsGrid = document.getElementById('stats-grid');
const casosGrid = document.getElementById('casos-grid');
const casosCount = document.getElementById('casos-count');
const noResults = document.getElementById('no-results');
const filterCategoria = document.getElementById('filter-categoria');
const filterMedio = document.getElementById('filter-medio');
const filterGravedad = document.getElementById('filter-gravedad');
const filterEstado = document.getElementById('filter-estado');
const sortBy = document.getElementById('sort-by');
const searchInput = document.getElementById('search-input');
const modal = document.getElementById('caso-modal');
const modalBody = document.getElementById('modal-body');
const modalClose = document.getElementById('modal-close');
const ultimaActualizacion = document.getElementById('ultima-actualizacion');
const mediosModal = document.getElementById('medios-modal');
const mediosModalClose = document.getElementById('medios-modal-close');
const btnMedios = document.getElementById('btn-medios');
const mediosStats = document.getElementById('medios-stats');
const mediosGrid = document.getElementById('medios-grid');
const violenciaModal = document.getElementById('violencia-modal');
const violenciaModalClose = document.getElementById('violencia-modal-close');
const btnViolencia = document.getElementById('btn-violencia');

// Clasificacion de medios
const mediosInfo = {
    // Medios Colombianos
    'Semana': { tipo: 'nacional', pais: 'Colombia', icon: 'fa-newspaper' },
    'El Tiempo': { tipo: 'nacional', pais: 'Colombia', icon: 'fa-newspaper' },
    'El Espectador': { tipo: 'nacional', pais: 'Colombia', icon: 'fa-newspaper' },
    'La Silla Vacia': { tipo: 'nacional', pais: 'Colombia', icon: 'fa-chair' },
    'El Colombiano': { tipo: 'nacional', pais: 'Colombia', icon: 'fa-newspaper' },
    'Cambio Colombia': { tipo: 'nacional', pais: 'Colombia', icon: 'fa-newspaper' },
    'Vanguardia': { tipo: 'nacional', pais: 'Colombia', icon: 'fa-newspaper' },
    'Portafolio': { tipo: 'nacional', pais: 'Colombia', icon: 'fa-chart-line' },
    'El Pais': { tipo: 'nacional', pais: 'Colombia', icon: 'fa-newspaper' },
    'W Radio': { tipo: 'nacional', pais: 'Colombia', icon: 'fa-broadcast-tower' },
    'Blu Radio': { tipo: 'nacional', pais: 'Colombia', icon: 'fa-broadcast-tower' },
    'RCN': { tipo: 'nacional', pais: 'Colombia', icon: 'fa-tv' },
    'Caracol': { tipo: 'nacional', pais: 'Colombia', icon: 'fa-tv' },
    'El Nuevo Siglo': { tipo: 'nacional', pais: 'Colombia', icon: 'fa-newspaper' },
    'El Heraldo': { tipo: 'nacional', pais: 'Colombia', icon: 'fa-newspaper' },
    'Ambito Juridico': { tipo: 'nacional', pais: 'Colombia', icon: 'fa-balance-scale' },
    'Finance Colombia': { tipo: 'nacional', pais: 'Colombia', icon: 'fa-dollar-sign' },
    'Colombia Reports': { tipo: 'nacional', pais: 'Colombia', icon: 'fa-newspaper' },
    'ColombiaOne': { tipo: 'nacional', pais: 'Colombia', icon: 'fa-newspaper' },
    'Publimetro': { tipo: 'nacional', pais: 'Colombia', icon: 'fa-newspaper' },

    // Verificadores
    'ColombiaCheck': { tipo: 'verificador', pais: 'Colombia', icon: 'fa-check-double' },
    'Transparencia por Colombia': { tipo: 'verificador', pais: 'Colombia', icon: 'fa-search' },

    // Medios Internacionales
    'Infobae': { tipo: 'internacional', pais: 'Argentina', icon: 'fa-globe-americas' },
    'Infobae America': { tipo: 'internacional', pais: 'Argentina', icon: 'fa-globe-americas' },
    'La Nacion': { tipo: 'internacional', pais: 'Argentina', icon: 'fa-globe-americas' },
    'Bloomberg': { tipo: 'internacional', pais: 'EE.UU.', icon: 'fa-chart-bar' },
    'Bloomberg Linea': { tipo: 'internacional', pais: 'EE.UU.', icon: 'fa-chart-bar' },
    'Al Jazeera': { tipo: 'internacional', pais: 'Qatar', icon: 'fa-globe' },
    'Washington Post': { tipo: 'internacional', pais: 'EE.UU.', icon: 'fa-newspaper' },
    'France 24': { tipo: 'internacional', pais: 'Francia', icon: 'fa-globe-europe' },
    'CNN': { tipo: 'internacional', pais: 'EE.UU.', icon: 'fa-tv' },
    'CNN Espanol': { tipo: 'internacional', pais: 'EE.UU.', icon: 'fa-tv' },
    'NPR': { tipo: 'internacional', pais: 'EE.UU.', icon: 'fa-broadcast-tower' },
    'VOA News': { tipo: 'internacional', pais: 'EE.UU.', icon: 'fa-broadcast-tower' },
    'Reuters': { tipo: 'internacional', pais: 'Reino Unido', icon: 'fa-globe' },
    'AP': { tipo: 'internacional', pais: 'EE.UU.', icon: 'fa-globe' },
    'BBC': { tipo: 'internacional', pais: 'Reino Unido', icon: 'fa-globe-europe' },
    'The Guardian': { tipo: 'internacional', pais: 'Reino Unido', icon: 'fa-newspaper' },
    'New York Times': { tipo: 'internacional', pais: 'EE.UU.', icon: 'fa-newspaper' },
    'Euronews': { tipo: 'internacional', pais: 'Europa', icon: 'fa-globe-europe' },
    'La Tercera': { tipo: 'internacional', pais: 'Chile', icon: 'fa-globe-americas' },
    'El Mercurio': { tipo: 'internacional', pais: 'Chile', icon: 'fa-globe-americas' },
    'EMOL': { tipo: 'internacional', pais: 'Chile', icon: 'fa-globe-americas' },
    'Milenio': { tipo: 'internacional', pais: 'Mexico', icon: 'fa-globe-americas' },
    'El Universal': { tipo: 'internacional', pais: 'Mexico', icon: 'fa-globe-americas' },
    'Univision': { tipo: 'internacional', pais: 'EE.UU.', icon: 'fa-tv' },
    'Foreign Policy': { tipo: 'internacional', pais: 'EE.UU.', icon: 'fa-landmark' },
    'The Economist': { tipo: 'internacional', pais: 'Reino Unido', icon: 'fa-chart-line' },
    'Americas Quarterly': { tipo: 'internacional', pais: 'EE.UU.', icon: 'fa-globe-americas' },
    'CryptoNews': { tipo: 'internacional', pais: 'Internacional', icon: 'fa-coins' },
    'PBS News': { tipo: 'internacional', pais: 'EE.UU.', icon: 'fa-tv' },
    'ABC News': { tipo: 'internacional', pais: 'EE.UU.', icon: 'fa-tv' },
    'Human Rights Watch': { tipo: 'internacional', pais: 'Internacional', icon: 'fa-hands-helping' },
    'Freedom House': { tipo: 'internacional', pais: 'EE.UU.', icon: 'fa-landmark' },
    'Publico.es': { tipo: 'internacional', pais: 'Espana', icon: 'fa-globe-europe' },
    'La Jornada': { tipo: 'internacional', pais: 'Mexico', icon: 'fa-newspaper' },
    'Latinus': { tipo: 'internacional', pais: 'Mexico', icon: 'fa-tv' },
    'Jamaica Observer': { tipo: 'internacional', pais: 'Jamaica', icon: 'fa-globe-americas' },

    // Fuentes Oficiales
    'U.S. Treasury': { tipo: 'oficial', pais: 'EE.UU.', icon: 'fa-landmark' },
    'State Department': { tipo: 'oficial', pais: 'EE.UU.', icon: 'fa-flag-usa' },
    'Council on Foreign Relations': { tipo: 'oficial', pais: 'EE.UU.', icon: 'fa-university' },
    'International Crisis Group': { tipo: 'oficial', pais: 'Internacional', icon: 'fa-globe' },
    'Oxford Analytica': { tipo: 'oficial', pais: 'Reino Unido', icon: 'fa-university' },
    'Atlantic Council': { tipo: 'oficial', pais: 'EE.UU.', icon: 'fa-landmark' },
    'Wilson Center': { tipo: 'oficial', pais: 'EE.UU.', icon: 'fa-university' },
    'Inter-American Dialogue': { tipo: 'oficial', pais: 'EE.UU.', icon: 'fa-globe-americas' }
};

// Inicializar la aplicacion
async function init() {
    try {
        console.log('Iniciando carga de datos...');
        const response = await fetch('data.json');

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        data = await response.json();
        console.log('Datos cargados:', data.casos ? data.casos.length + ' casos' : 'sin casos');

        // Verify data structure
        if (!data.categorias || !Array.isArray(data.categorias)) {
            console.error('data.categorias no es un array valido');
            data.categorias = [];
        }
        if (!data.casos || !Array.isArray(data.casos)) {
            console.error('data.casos no es un array valido');
            data.casos = [];
        }

        populateFilters();
        renderStats();
        filterAndRenderCasos();

        if (data.estadisticas && data.estadisticas.ultima_actualizacion && ultimaActualizacion) {
            ultimaActualizacion.textContent = formatDate(data.estadisticas.ultima_actualizacion);
        }

        console.log('Inicializacion completada. Casos filtrados:', filteredCasos.length);
    } catch (error) {
        console.error('Error cargando datos:', error);
        if (casosGrid) {
            casosGrid.innerHTML = `
                <div class="no-results">
                    <i class="fas fa-exclamation-circle"></i>
                    <p>Error al cargar los datos. Verifica que el archivo data.json existe.</p>
                    <p style="font-size: 0.8em; color: #999;">${error.message}</p>
                </div>
            `;
        }
    }
}

// Poblar filtros de categoria y medios
function populateFilters() {
    // Poblar categorias
    data.categorias.forEach(cat => {
        const option = document.createElement('option');
        option.value = cat.id;
        option.textContent = cat.nombre;
        filterCategoria.appendChild(option);
    });

    // Poblar medios
    populateMediosFilter();
}

// Poblar filtro de medios
function populateMediosFilter() {
    const mediosCount = extractMedios();
    const mediosList = Object.entries(mediosCount)
        .sort((a, b) => b[1].count - a[1].count);

    mediosList.forEach(([nombre, info]) => {
        const option = document.createElement('option');
        option.value = nombre;
        option.textContent = `${nombre} (${info.count})`;
        filterMedio.appendChild(option);
    });
}

// Renderizar estadisticas
function renderStats() {
    const totalCasos = data.casos.length;

    // Calcular estadisticas dinamicamente
    const statsPorCategoria = {};
    data.categorias.forEach(cat => {
        statsPorCategoria[cat.id] = 0;
    });

    data.casos.forEach(caso => {
        if (statsPorCategoria[caso.categoria] !== undefined) {
            statsPorCategoria[caso.categoria]++;
        }
    });

    // Card de total
    let html = `
        <div class="stat-card" style="border-left-color: var(--primary)">
            <i class="fas fa-folder-open" style="color: var(--primary)"></i>
            <span class="stat-number">${totalCasos}</span>
            <span class="stat-label">Total Casos</span>
        </div>
    `;

    // Cards por categoria
    data.categorias.forEach(cat => {
        const count = statsPorCategoria[cat.id] || 0;
        if (count > 0) {
            html += `
                <div class="stat-card" style="border-left-color: ${cat.color}">
                    <i class="fas ${cat.icono}" style="color: ${cat.color}"></i>
                    <span class="stat-number">${count}</span>
                    <span class="stat-label">${cat.nombre}</span>
                </div>
            `;
        }
    });

    statsGrid.innerHTML = html;
}

// Filtrar y renderizar casos
function filterAndRenderCasos() {
    const searchTerm = searchInput.value.toLowerCase();
    const categoriaFilter = filterCategoria.value;
    const medioFilter = filterMedio.value;
    const gravedadFilter = filterGravedad.value;
    const estadoFilter = filterEstado.value;
    const sortValue = sortBy.value;

    // Filtrar
    filteredCasos = data.casos.filter(caso => {
        // Busqueda
        if (searchTerm) {
            const searchFields = [
                caso.titulo,
                caso.descripcion,
                caso.afirmacion_original,
                caso.evidencia,
                caso.entidad,
                ...(caso.personas_involucradas || [])
            ].join(' ').toLowerCase();

            if (!searchFields.includes(searchTerm)) {
                return false;
            }
        }

        // Filtro de categoria
        if (categoriaFilter && caso.categoria !== categoriaFilter) {
            return false;
        }

        // Filtro de medio
        if (medioFilter) {
            const tieneMedio = caso.fuentes && caso.fuentes.some(f => f.nombre === medioFilter);
            if (!tieneMedio) {
                return false;
            }
        }

        // Filtro de gravedad
        if (gravedadFilter && caso.gravedad !== gravedadFilter) {
            return false;
        }

        // Filtro de estado
        if (estadoFilter && caso.estado !== estadoFilter) {
            return false;
        }

        return true;
    });

    // Ordenar
    filteredCasos.sort((a, b) => {
        switch (sortValue) {
            case 'fecha-desc':
                return new Date(b.fecha) - new Date(a.fecha);
            case 'fecha-asc':
                return new Date(a.fecha) - new Date(b.fecha);
            case 'gravedad':
                const gravedadOrder = { alta: 0, media: 1, baja: 2 };
                return (gravedadOrder[a.gravedad] || 2) - (gravedadOrder[b.gravedad] || 2);
            default:
                return 0;
        }
    });

    renderCasos();
}

// Renderizar casos
function renderCasos() {
    if (filteredCasos.length === 0) {
        casosGrid.innerHTML = '';
        noResults.style.display = 'block';
        casosCount.textContent = '0 casos';
        return;
    }

    noResults.style.display = 'none';
    casosCount.textContent = `${filteredCasos.length} caso${filteredCasos.length !== 1 ? 's' : ''}`;

    const html = filteredCasos.map(caso => {
        const categoria = data.categorias.find(c => c.id === caso.categoria) || {
            nombre: caso.categoria,
            color: '#95a5a6',
            icono: 'fa-circle'
        };

        return `
            <div class="caso-card" data-id="${caso.id}">
                <div class="caso-card-header">
                    <span class="caso-categoria" style="background: ${categoria.color}">
                        <i class="fas ${categoria.icono}"></i>
                        ${categoria.nombre}
                    </span>
                    <span class="caso-fecha">
                        <i class="far fa-calendar"></i>
                        ${formatDate(caso.fecha)}
                    </span>
                </div>
                <div class="caso-card-body">
                    <h3 class="caso-titulo">${escapeHtml(caso.titulo)}</h3>
                    <p class="caso-descripcion">${escapeHtml(caso.descripcion)}</p>
                    <div class="caso-meta">
                        ${caso.entidad ? `
                            <span class="caso-meta-item">
                                <i class="fas fa-building"></i>
                                ${escapeHtml(caso.entidad)}
                            </span>
                        ` : ''}
                        ${caso.gravedad ? `
                            <span class="caso-gravedad ${caso.gravedad}">${caso.gravedad}</span>
                        ` : ''}
                        ${caso.estado ? `
                            <span class="caso-estado ${caso.estado.toLowerCase().replace(/ /g, '')}">${escapeHtml(caso.estado)}</span>
                        ` : ''}
                        <span class="caso-meta-item">
                            <i class="fas fa-link"></i>
                            ${caso.fuentes ? caso.fuentes.length : 0} fuente${caso.fuentes && caso.fuentes.length !== 1 ? 's' : ''}
                        </span>
                    </div>
                </div>
            </div>
        `;
    }).join('');

    casosGrid.innerHTML = html;

    // Agregar event listeners a las cards
    document.querySelectorAll('.caso-card').forEach(card => {
        card.addEventListener('click', () => {
            const id = parseInt(card.dataset.id);
            openModal(id);
        });
    });
}

// Abrir modal con detalle del caso
function openModal(id) {
    const caso = data.casos.find(c => c.id === id);
    if (!caso) return;

    const categoria = data.categorias.find(c => c.id === caso.categoria) || {
        nombre: caso.categoria,
        color: '#95a5a6',
        icono: 'fa-circle'
    };

    modalBody.innerHTML = `
        <div class="modal-header">
            <span class="caso-categoria" style="background: ${categoria.color}">
                <i class="fas ${categoria.icono}"></i>
                ${categoria.nombre}
            </span>
            <h2>${escapeHtml(caso.titulo)}</h2>
            <div class="meta-row">
                <span><i class="far fa-calendar"></i> ${formatDate(caso.fecha)}</span>
                ${caso.entidad ? `<span><i class="fas fa-building"></i> ${escapeHtml(caso.entidad)}</span>` : ''}
                ${caso.gravedad ? `<span class="caso-gravedad ${caso.gravedad}">${caso.gravedad}</span>` : ''}
                ${caso.estado ? `<span class="caso-estado ${caso.estado.toLowerCase().replace(/ /g, '')}">${escapeHtml(caso.estado)}</span>` : ''}
            </div>
        </div>

        <div class="modal-section">
            <h3><i class="fas fa-file-alt"></i> Descripcion</h3>
            <p>${escapeHtml(caso.descripcion)}</p>
        </div>

        ${caso.afirmacion_original ? `
            <div class="modal-section">
                <h3><i class="fas fa-quote-left"></i> Afirmacion Original</h3>
                <p><em>"${escapeHtml(caso.afirmacion_original)}"</em></p>
            </div>
        ` : ''}

        ${caso.evidencia ? `
            <div class="modal-section">
                <h3><i class="fas fa-search"></i> Evidencia</h3>
                <p>${escapeHtml(caso.evidencia)}</p>
            </div>
        ` : ''}

        ${caso.personas_involucradas && caso.personas_involucradas.length > 0 ? `
            <div class="modal-section">
                <h3><i class="fas fa-users"></i> Personas Involucradas</h3>
                <div class="personas-list">
                    ${caso.personas_involucradas.map(p => `<span class="persona-tag">${escapeHtml(p)}</span>`).join('')}
                </div>
            </div>
        ` : ''}

        ${caso.fuentes && caso.fuentes.length > 0 ? `
            <div class="modal-section">
                <h3><i class="fas fa-link"></i> Fuentes</h3>
                <ul class="fuentes-list">
                    ${caso.fuentes.map(f => `
                        <li>
                            <a href="${escapeHtml(f.url)}" target="_blank" rel="noopener noreferrer">
                                <i class="fas fa-external-link-alt"></i>
                                ${escapeHtml(f.nombre)}
                            </a>
                            ${f.fecha ? `<span class="fuente-fecha">(${formatDate(f.fecha)})</span>` : ''}
                        </li>
                    `).join('')}
                </ul>
            </div>
        ` : ''}

        <div id="rating-container"></div>
        <div id="comments-container"></div>
    `;

    modal.classList.add('active');
    document.body.style.overflow = 'hidden';

    // Load rating and comments asynchronously
    loadRatingAndComments(id);
}

// Load rating and comments for the modal
async function loadRatingAndComments(caseId) {
    // Load rating
    const ratingData = await loadRating(caseId);
    const ratingContainer = document.getElementById('rating-container');
    if (ratingContainer) {
        ratingContainer.innerHTML = renderRatingSection(caseId, ratingData);
    }

    // Load comments
    const comments = await loadComments(caseId);
    const commentsContainer = document.getElementById('comments-container');
    if (commentsContainer) {
        commentsContainer.innerHTML = renderCommentsSection(caseId, comments);
    }
}

// Cerrar modal
function closeModal() {
    modal.classList.remove('active');
    document.body.style.overflow = '';
}

// Formatear fecha
function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return date.toLocaleDateString('es-CO', options);
}

// Escapar HTML para prevenir XSS
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Event listeners
filterCategoria.addEventListener('change', filterAndRenderCasos);
filterMedio.addEventListener('change', filterAndRenderCasos);
filterGravedad.addEventListener('change', filterAndRenderCasos);
filterEstado.addEventListener('change', filterAndRenderCasos);
sortBy.addEventListener('change', filterAndRenderCasos);
searchInput.addEventListener('input', debounce(filterAndRenderCasos, 300));
modalClose.addEventListener('click', closeModal);
modal.addEventListener('click', (e) => {
    if (e.target === modal) closeModal();
});
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeModal();
        closeMediosModal();
        if (violenciaModal) closeViolenciaModal();
    }
});

// Debounce para busqueda
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Extraer medios de los casos
function extractMedios() {
    const mediosCount = {};

    data.casos.forEach(caso => {
        if (caso.fuentes && caso.fuentes.length > 0) {
            caso.fuentes.forEach(fuente => {
                const nombre = fuente.nombre;
                if (!mediosCount[nombre]) {
                    mediosCount[nombre] = {
                        count: 0,
                        urls: []
                    };
                }
                mediosCount[nombre].count++;
                if (fuente.url && !mediosCount[nombre].urls.includes(fuente.url)) {
                    mediosCount[nombre].urls.push(fuente.url);
                }
            });
        }
    });

    return mediosCount;
}

// Renderizar modal de medios
function renderMediosModal() {
    const mediosCount = extractMedios();
    const mediosList = Object.entries(mediosCount)
        .sort((a, b) => b[1].count - a[1].count);

    // Calcular estadisticas
    const totalMedios = mediosList.length;
    const totalFuentes = mediosList.reduce((acc, [_, info]) => acc + info.count, 0);

    let nacionales = 0, internacionales = 0, verificadores = 0, oficiales = 0;
    mediosList.forEach(([nombre, _]) => {
        const info = mediosInfo[nombre];
        if (info) {
            if (info.tipo === 'nacional') nacionales++;
            else if (info.tipo === 'internacional') internacionales++;
            else if (info.tipo === 'verificador') verificadores++;
            else if (info.tipo === 'oficial') oficiales++;
        } else {
            nacionales++; // Default a nacional si no esta clasificado
        }
    });

    // Renderizar estadisticas
    mediosStats.innerHTML = `
        <div class="medios-stat-card">
            <span class="stat-number">${totalMedios}</span>
            <span class="stat-label">Medios Diferentes</span>
        </div>
        <div class="medios-stat-card">
            <span class="stat-number">${totalFuentes}</span>
            <span class="stat-label">Referencias Totales</span>
        </div>
        <div class="medios-stat-card">
            <span class="stat-number">${nacionales}</span>
            <span class="stat-label">Medios Nacionales</span>
        </div>
        <div class="medios-stat-card">
            <span class="stat-number">${internacionales}</span>
            <span class="stat-label">Medios Internacionales</span>
        </div>
    `;

    // Renderizar lista de medios
    let mediosHtml = '';
    mediosList.forEach(([nombre, info]) => {
        const medioInfo = mediosInfo[nombre] || { tipo: 'nacional', pais: 'Colombia', icon: 'fa-newspaper' };
        const tipoClass = medioInfo.tipo;
        const tipoLabel = {
            'nacional': 'Medio Nacional',
            'internacional': `Internacional - ${medioInfo.pais}`,
            'verificador': 'Verificador de Hechos',
            'oficial': 'Fuente Oficial'
        }[tipoClass] || 'Medio';

        mediosHtml += `
            <div class="medio-card ${tipoClass}" data-medio="${escapeHtml(nombre)}" title="Click para ver casos de ${escapeHtml(nombre)}">
                <div class="medio-icon">
                    <i class="fas ${medioInfo.icon}"></i>
                </div>
                <div class="medio-info">
                    <div class="medio-name">${escapeHtml(nombre)}</div>
                    <div class="medio-type">${tipoLabel}</div>
                </div>
                <span class="medio-count">${info.count} <i class="fas fa-chevron-right"></i></span>
            </div>
        `;
    });

    mediosGrid.innerHTML = mediosHtml;

    // Agregar event listeners a las tarjetas de medios
    document.querySelectorAll('.medio-card').forEach(card => {
        card.addEventListener('click', () => {
            const medioNombre = card.dataset.medio;
            filterByMedio(medioNombre);
        });
    });

    // Agregar leyenda
    const legendHtml = `
        <div class="medios-legend">
            <div class="legend-item">
                <div class="legend-color nacional"></div>
                <span>Nacional</span>
            </div>
            <div class="legend-item">
                <div class="legend-color internacional"></div>
                <span>Internacional</span>
            </div>
            <div class="legend-item">
                <div class="legend-color verificador"></div>
                <span>Verificador</span>
            </div>
            <div class="legend-item">
                <div class="legend-color oficial"></div>
                <span>Fuente Oficial</span>
            </div>
        </div>
    `;
    mediosGrid.insertAdjacentHTML('afterend', legendHtml);
}

// Abrir modal de medios
function openMediosModal() {
    // Limpiar leyenda anterior si existe
    const oldLegend = document.querySelector('.medios-legend');
    if (oldLegend) oldLegend.remove();

    renderMediosModal();
    mediosModal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

// Cerrar modal de medios
function closeMediosModal() {
    mediosModal.classList.remove('active');
    document.body.style.overflow = '';
}

// Filtrar por medio desde el modal de medios
function filterByMedio(medioNombre) {
    // Cerrar el modal
    closeMediosModal();

    // Establecer el filtro de medio
    filterMedio.value = medioNombre;

    // Aplicar el filtro
    filterAndRenderCasos();

    // Hacer scroll a la seccion de casos
    document.getElementById('casos').scrollIntoView({ behavior: 'smooth' });
}

// Event listeners para modal de medios
if (btnMedios) {
    btnMedios.addEventListener('click', (e) => {
        e.preventDefault();
        openMediosModal();
    });
}
if (mediosModalClose) {
    mediosModalClose.addEventListener('click', closeMediosModal);
}
if (mediosModal) {
    mediosModal.addEventListener('click', (e) => {
        if (e.target === mediosModal) closeMediosModal();
    });
}

// Modal de violencia
function openViolenciaModal() {
    if (violenciaModal) {
        violenciaModal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeViolenciaModal() {
    if (violenciaModal) {
        violenciaModal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// Event listeners para modal de violencia
if (btnViolencia) {
    btnViolencia.addEventListener('click', (e) => {
        e.preventDefault();
        openViolenciaModal();
    });
}
if (violenciaModalClose) {
    violenciaModalClose.addEventListener('click', closeViolenciaModal);
}
if (violenciaModal) {
    violenciaModal.addEventListener('click', (e) => {
        if (e.target === violenciaModal) closeViolenciaModal();
    });
}

// Iniciar
init();

// ================================
// AUTHENTICATION HANDLERS
// ================================

// Handle login form submission
async function handleLogin(event) {
    event.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    try {
        await signInWithEmail(email, password);
    } catch (error) {
        console.error('Login error:', error);
    }
}

// Handle register form submission
async function handleRegister(event) {
    event.preventDefault();
    const name = document.getElementById('register-name').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;

    try {
        await signUpWithEmail(email, password, name);
    } catch (error) {
        console.error('Register error:', error);
    }
}

// Handle forgot password
async function handleForgotPassword(event) {
    event.preventDefault();
    const email = document.getElementById('login-email').value;

    if (!email) {
        showNotification('Ingresa tu correo electronico primero', 'error');
        return;
    }

    await sendPasswordReset(email);
}

// ================================
// COMMENTS SYSTEM
// ================================

let currentCaseId = null;

// Load comments for a case
async function loadComments(caseId) {
    try {
        const commentsRef = db.collection('comments')
            .where('caseId', '==', caseId)
            .where('isHidden', '==', false)
            .orderBy('createdAt', 'desc');

        const snapshot = await commentsRef.get();
        const comments = [];

        snapshot.forEach(doc => {
            comments.push({ id: doc.id, ...doc.data() });
        });

        return comments;
    } catch (error) {
        console.error('Error loading comments:', error);
        return [];
    }
}

// Add a comment
async function addComment(caseId, content) {
    if (!currentUser) {
        showNotification('Debes iniciar sesion para comentar', 'error');
        openAuthModal();
        return false;
    }

    if (userIsBlocked) {
        showNotification('Tu cuenta ha sido bloqueada y no puedes comentar', 'error');
        return false;
    }

    try {
        await db.collection('comments').add({
            caseId: caseId,
            userId: currentUser.uid,
            userName: currentUser.displayName || currentUser.email.split('@')[0],
            content: content,
            createdAt: firebase.firestore.FieldValue.serverTimestamp(),
            isHidden: false
        });

        showNotification('Comentario agregado', 'success');
        return true;
    } catch (error) {
        console.error('Error adding comment:', error);
        showNotification('Error al agregar comentario', 'error');
        return false;
    }
}

// Delete a comment (admin only)
async function deleteComment(commentId) {
    if (!isAdmin) {
        showNotification('No tienes permisos', 'error');
        return false;
    }

    try {
        await db.collection('comments').doc(commentId).update({
            isHidden: true
        });

        showNotification('Comentario eliminado', 'success');
        return true;
    } catch (error) {
        console.error('Error deleting comment:', error);
        showNotification('Error al eliminar comentario', 'error');
        return false;
    }
}

// Render comments section HTML
function renderCommentsSection(caseId, comments) {
    currentCaseId = caseId;

    let html = `
        <div class="comments-section">
            <div class="comments-header">
                <h3><i class="fas fa-comments"></i> Comentarios</h3>
                <span class="comments-count">${comments.length} comentario${comments.length !== 1 ? 's' : ''}</span>
            </div>
    `;

    // Show blocked message if user is blocked
    if (userIsBlocked) {
        html += `
            <div class="user-blocked-message">
                <i class="fas fa-ban"></i> Tu cuenta ha sido bloqueada y no puedes comentar
            </div>
        `;
    }
    // Comment form (if logged in and not blocked)
    else if (currentUser) {
        html += `
            <div class="comment-form">
                <textarea id="comment-input" placeholder="Escribe tu comentario..."></textarea>
                <div class="comment-form-actions">
                    <button class="btn-comment-submit" onclick="submitComment(${caseId})">
                        <i class="fas fa-paper-plane"></i> Enviar
                    </button>
                </div>
            </div>
        `;
    } else {
        html += `
            <div class="comment-login-prompt">
                <p>Inicia sesion para dejar un comentario</p>
                <button onclick="openAuthModal()">
                    <i class="fas fa-sign-in-alt"></i> Iniciar Sesion
                </button>
            </div>
        `;
    }

    // Comments list
    if (comments.length > 0) {
        html += '<div class="comments-list">';
        comments.forEach(comment => {
            const date = comment.createdAt ? new Date(comment.createdAt.toDate()).toLocaleDateString('es-CO', {
                year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
            }) : 'Ahora';

            const initials = comment.userName.substring(0, 2).toUpperCase();

            html += `
                <div class="comment-item" data-comment-id="${comment.id}">
                    <div class="comment-header">
                        <div class="comment-author">
                            <div class="comment-avatar">${initials}</div>
                            <div class="comment-author-info">
                                <strong>${escapeHtml(comment.userName)}</strong>
                                <small>${date}</small>
                            </div>
                        </div>
                        ${isAdmin ? `
                            <div class="comment-actions">
                                <button class="comment-delete" onclick="handleDeleteComment('${comment.id}', ${caseId})">
                                    <i class="fas fa-trash"></i> Eliminar
                                </button>
                            </div>
                        ` : ''}
                    </div>
                    <div class="comment-content">${escapeHtml(comment.content)}</div>
                </div>
            `;
        });
        html += '</div>';
    } else {
        html += `
            <div class="no-comments">
                <i class="fas fa-comment-slash"></i>
                <p>No hay comentarios aun. Se el primero en comentar!</p>
            </div>
        `;
    }

    html += '</div>';
    return html;
}

// Submit comment handler
async function submitComment(caseId) {
    const input = document.getElementById('comment-input');
    const content = input.value.trim();

    if (!content) {
        showNotification('Escribe un comentario', 'error');
        return;
    }

    const success = await addComment(caseId, content);
    if (success) {
        input.value = '';
        // Reload comments
        const comments = await loadComments(caseId);
        const commentsContainer = document.querySelector('.comments-section');
        if (commentsContainer) {
            commentsContainer.outerHTML = renderCommentsSection(caseId, comments);
        }
    }
}

// Handle delete comment
async function handleDeleteComment(commentId, caseId) {
    if (confirm('Estas seguro de eliminar este comentario?')) {
        const success = await deleteComment(commentId);
        if (success) {
            const comments = await loadComments(caseId);
            const commentsContainer = document.querySelector('.comments-section');
            if (commentsContainer) {
                commentsContainer.outerHTML = renderCommentsSection(caseId, comments);
            }
        }
    }
}

// Update comment section when auth state changes
function updateCommentSection() {
    if (currentCaseId && document.querySelector('.comments-section')) {
        loadComments(currentCaseId).then(comments => {
            const commentsContainer = document.querySelector('.comments-section');
            if (commentsContainer) {
                commentsContainer.outerHTML = renderCommentsSection(currentCaseId, comments);
            }
        });
    }
}

// ================================
// RATINGS SYSTEM
// ================================

// Load rating for a case
async function loadRating(caseId) {
    try {
        const ratingDoc = await db.collection('ratings').doc(String(caseId)).get();

        if (ratingDoc.exists) {
            return ratingDoc.data();
        }

        return { totalRatings: 0, averageRating: 0, userRatings: {} };
    } catch (error) {
        console.error('Error loading rating:', error);
        return { totalRatings: 0, averageRating: 0, userRatings: {} };
    }
}

// Submit rating
async function submitRating(caseId, rating) {
    if (!currentUser) {
        showNotification('Debes iniciar sesion para calificar', 'error');
        openAuthModal();
        return false;
    }

    if (userIsBlocked) {
        showNotification('Tu cuenta ha sido bloqueada', 'error');
        return false;
    }

    try {
        const ratingRef = db.collection('ratings').doc(String(caseId));
        const ratingDoc = await ratingRef.get();

        let data = ratingDoc.exists ? ratingDoc.data() : {
            totalRatings: 0,
            averageRating: 0,
            userRatings: {}
        };

        const previousRating = data.userRatings[currentUser.uid];

        // Update user rating
        data.userRatings[currentUser.uid] = rating;

        // Recalculate average
        const ratings = Object.values(data.userRatings);
        data.totalRatings = ratings.length;
        data.averageRating = ratings.reduce((a, b) => a + b, 0) / ratings.length;

        await ratingRef.set(data);

        showNotification(previousRating ? 'Calificacion actualizada' : 'Gracias por tu calificacion!', 'success');
        return true;
    } catch (error) {
        console.error('Error submitting rating:', error);
        showNotification('Error al guardar calificacion', 'error');
        return false;
    }
}

// Render rating section HTML
function renderRatingSection(caseId, ratingData) {
    const userRating = currentUser ? ratingData.userRatings[currentUser.uid] : null;

    let starsHtml = '';
    for (let i = 1; i <= 5; i++) {
        starsHtml += `<i class="fas fa-star"></i>`;
    }

    const avgStarsHtml = renderStars(ratingData.averageRating);

    let html = `
        <div class="rating-section" data-case-id="${caseId}">
            <div class="rating-header">
                <h4><i class="fas fa-star"></i> Califica este caso</h4>
                ${ratingData.totalRatings > 0 ? `
                    <div class="rating-average">
                        <span class="stars">${avgStarsHtml}</span>
                        <span>${ratingData.averageRating.toFixed(1)}</span>
                        <small>(${ratingData.totalRatings} voto${ratingData.totalRatings !== 1 ? 's' : ''})</small>
                    </div>
                ` : ''}
            </div>
    `;

    if (userIsBlocked) {
        html += `<p class="rating-login-prompt">Tu cuenta ha sido bloqueada</p>`;
    } else if (currentUser) {
        html += `
            <div class="star-rating" data-case-id="${caseId}">
                ${[1,2,3,4,5].map(i => `
                    <i class="fas fa-star star ${userRating && i <= userRating ? 'active' : ''}"
                       data-rating="${i}"
                       onclick="handleRating(${caseId}, ${i})"
                       onmouseenter="highlightStars(${i})"
                       onmouseleave="resetStars(${userRating || 0})"></i>
                `).join('')}
            </div>
            ${userRating ? `<p class="rating-submitted"><i class="fas fa-check"></i> Tu calificacion: ${userRating} estrella${userRating !== 1 ? 's' : ''}</p>` : ''}
        `;
    } else {
        html += `
            <p class="rating-login-prompt">
                <a href="#" onclick="openAuthModal(); return false;">Inicia sesion</a> para calificar
            </p>
        `;
    }

    html += '</div>';
    return html;
}

// Render star icons based on rating
function renderStars(rating) {
    let html = '';
    for (let i = 1; i <= 5; i++) {
        if (i <= rating) {
            html += '<i class="fas fa-star"></i>';
        } else if (i - 0.5 <= rating) {
            html += '<i class="fas fa-star-half-alt"></i>';
        } else {
            html += '<i class="far fa-star"></i>';
        }
    }
    return html;
}

// Handle rating click
async function handleRating(caseId, rating) {
    const success = await submitRating(caseId, rating);
    if (success) {
        const ratingData = await loadRating(caseId);
        const ratingContainer = document.querySelector('.rating-section');
        if (ratingContainer) {
            ratingContainer.outerHTML = renderRatingSection(caseId, ratingData);
        }
    }
}

// Highlight stars on hover
function highlightStars(rating) {
    const stars = document.querySelectorAll('.star-rating .star');
    stars.forEach((star, index) => {
        if (index < rating) {
            star.classList.add('hovered');
        } else {
            star.classList.remove('hovered');
        }
    });
}

// Reset stars on mouse leave
function resetStars(userRating) {
    const stars = document.querySelectorAll('.star-rating .star');
    stars.forEach((star, index) => {
        star.classList.remove('hovered');
        if (index < userRating) {
            star.classList.add('active');
        } else {
            star.classList.remove('active');
        }
    });
}

// ================================
// ADMIN PANEL
// ================================

// Open admin panel
function openAdminPanel() {
    closeUserMenu();
    const modal = document.getElementById('admin-modal');
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
        showAdminTab('users');
    }
}

// Close admin panel
function closeAdminPanel() {
    const modal = document.getElementById('admin-modal');
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// Show admin tab
async function showAdminTab(tab) {
    // Update tab buttons
    document.querySelectorAll('.admin-tab').forEach(btn => {
        btn.classList.remove('active');
        if (btn.textContent.toLowerCase().includes(tab === 'users' ? 'usuario' : tab === 'comments' ? 'comentario' : 'bloqueado')) {
            btn.classList.add('active');
        }
    });

    const content = document.getElementById('admin-content');
    content.innerHTML = '<div class="admin-loading"><i class="fas fa-spinner fa-spin"></i> Cargando...</div>';

    try {
        if (tab === 'users') {
            const users = await loadAllUsers();
            content.innerHTML = renderUsersTable(users);
        } else if (tab === 'comments') {
            const comments = await loadAllComments();
            content.innerHTML = renderCommentsTable(comments);
        } else if (tab === 'blocked') {
            const users = await loadBlockedUsers();
            content.innerHTML = renderBlockedTable(users);
        }
    } catch (error) {
        console.error('Error loading admin data:', error);
        content.innerHTML = '<div class="admin-empty"><i class="fas fa-exclamation-circle"></i><p>Error al cargar datos</p></div>';
    }
}

// Load all users
async function loadAllUsers() {
    const snapshot = await db.collection('users').orderBy('lastLogin', 'desc').limit(50).get();
    const users = [];
    snapshot.forEach(doc => users.push({ id: doc.id, ...doc.data() }));
    return users;
}

// Load all comments (admin)
async function loadAllComments() {
    const snapshot = await db.collection('comments')
        .where('isHidden', '==', false)
        .orderBy('createdAt', 'desc')
        .limit(50)
        .get();
    const comments = [];
    snapshot.forEach(doc => comments.push({ id: doc.id, ...doc.data() }));
    return comments;
}

// Load blocked users
async function loadBlockedUsers() {
    const snapshot = await db.collection('users').where('isBlocked', '==', true).get();
    const users = [];
    snapshot.forEach(doc => users.push({ id: doc.id, ...doc.data() }));
    return users;
}

// Render users table
function renderUsersTable(users) {
    if (users.length === 0) {
        return '<div class="admin-empty"><i class="fas fa-users"></i><p>No hay usuarios registrados</p></div>';
    }

    let html = `
        <table class="admin-table">
            <thead>
                <tr>
                    <th>Usuario</th>
                    <th>Email</th>
                    <th>Estado</th>
                    <th>Acciones</th>
                </tr>
            </thead>
            <tbody>
    `;

    users.forEach(user => {
        const initials = (user.displayName || user.email || 'U').substring(0, 2).toUpperCase();
        html += `
            <tr>
                <td>
                    <div class="user-cell">
                        <div class="user-avatar">${initials}</div>
                        <span>${escapeHtml(user.displayName || 'Sin nombre')}</span>
                    </div>
                </td>
                <td>${escapeHtml(user.email)}</td>
                <td>
                    <span class="status-badge ${user.isBlocked ? 'blocked' : 'active'}">
                        ${user.isBlocked ? 'Bloqueado' : 'Activo'}
                    </span>
                </td>
                <td>
                    ${user.email !== ADMIN_EMAIL ? (
                        user.isBlocked ?
                        `<button class="btn-unblock" onclick="unblockUser('${user.id}')">Desbloquear</button>` :
                        `<button class="btn-block" onclick="blockUser('${user.id}')">Bloquear</button>`
                    ) : '<span style="color: var(--text-muted)">Admin</span>'}
                </td>
            </tr>
        `;
    });

    html += '</tbody></table>';
    return html;
}

// Render comments table
function renderCommentsTable(comments) {
    if (comments.length === 0) {
        return '<div class="admin-empty"><i class="fas fa-comments"></i><p>No hay comentarios</p></div>';
    }

    let html = `
        <table class="admin-table">
            <thead>
                <tr>
                    <th>Usuario</th>
                    <th>Comentario</th>
                    <th>Caso ID</th>
                    <th>Acciones</th>
                </tr>
            </thead>
            <tbody>
    `;

    comments.forEach(comment => {
        const initials = (comment.userName || 'U').substring(0, 2).toUpperCase();
        const truncatedContent = comment.content.length > 50 ?
            comment.content.substring(0, 50) + '...' : comment.content;

        html += `
            <tr>
                <td>
                    <div class="user-cell">
                        <div class="user-avatar">${initials}</div>
                        <span>${escapeHtml(comment.userName)}</span>
                    </div>
                </td>
                <td>${escapeHtml(truncatedContent)}</td>
                <td>#${comment.caseId}</td>
                <td>
                    <button class="btn-block" onclick="adminDeleteComment('${comment.id}')">Eliminar</button>
                </td>
            </tr>
        `;
    });

    html += '</tbody></table>';
    return html;
}

// Render blocked users table
function renderBlockedTable(users) {
    if (users.length === 0) {
        return '<div class="admin-empty"><i class="fas fa-user-slash"></i><p>No hay usuarios bloqueados</p></div>';
    }

    let html = `
        <table class="admin-table">
            <thead>
                <tr>
                    <th>Usuario</th>
                    <th>Email</th>
                    <th>Razon</th>
                    <th>Acciones</th>
                </tr>
            </thead>
            <tbody>
    `;

    users.forEach(user => {
        const initials = (user.displayName || user.email || 'U').substring(0, 2).toUpperCase();
        html += `
            <tr>
                <td>
                    <div class="user-cell">
                        <div class="user-avatar">${initials}</div>
                        <span>${escapeHtml(user.displayName || 'Sin nombre')}</span>
                    </div>
                </td>
                <td>${escapeHtml(user.email)}</td>
                <td>${escapeHtml(user.blockedReason || 'No especificada')}</td>
                <td>
                    <button class="btn-unblock" onclick="unblockUser('${user.id}')">Desbloquear</button>
                </td>
            </tr>
        `;
    });

    html += '</tbody></table>';
    return html;
}

// Block user
async function blockUser(userId) {
    const reason = prompt('Razon del bloqueo (opcional):');

    try {
        await db.collection('users').doc(userId).update({
            isBlocked: true,
            blockedAt: firebase.firestore.FieldValue.serverTimestamp(),
            blockedReason: reason || ''
        });

        showNotification('Usuario bloqueado', 'success');
        showAdminTab('users');
    } catch (error) {
        console.error('Error blocking user:', error);
        showNotification('Error al bloquear usuario', 'error');
    }
}

// Unblock user
async function unblockUser(userId) {
    try {
        await db.collection('users').doc(userId).update({
            isBlocked: false,
            blockedAt: null,
            blockedReason: ''
        });

        showNotification('Usuario desbloqueado', 'success');
        showAdminTab('blocked');
    } catch (error) {
        console.error('Error unblocking user:', error);
        showNotification('Error al desbloquear usuario', 'error');
    }
}

// Admin delete comment
async function adminDeleteComment(commentId) {
    if (confirm('Estas seguro de eliminar este comentario?')) {
        try {
            await db.collection('comments').doc(commentId).update({
                isHidden: true
            });
            showNotification('Comentario eliminado', 'success');
            showAdminTab('comments');
        } catch (error) {
            console.error('Error deleting comment:', error);
            showNotification('Error al eliminar comentario', 'error');
        }
    }
}

// ================================
// DRAG AND DROP FOR CASES
// ================================

let isEditMode = false;
let casesOrder = [];
let originalOrder = [];

// Toggle edit mode
function toggleEditMode() {
    isEditMode = !isEditMode;
    const casosGrid = document.getElementById('casos-grid');
    const editBtn = document.getElementById('edit-mode-btn');

    if (isEditMode) {
        casosGrid.classList.add('edit-mode-active');
        editBtn.innerHTML = '<i class="fas fa-check"></i> Guardar';
        editBtn.style.background = 'linear-gradient(135deg, #10b981, #059669)';

        // Store original order
        originalOrder = [...filteredCasos.map(c => c.id)];
        casesOrder = [...originalOrder];

        enableCasesDragAndDrop();
        showSaveOrderBar();
        showNotification('Modo edicion activado. Arrastra los casos para reordenar.', 'info');
    } else {
        casosGrid.classList.remove('edit-mode-active');
        editBtn.innerHTML = '<i class="fas fa-arrows-alt"></i> Editar';
        editBtn.style.background = '';

        disableCasesDragAndDrop();
        hideSaveOrderBar();
    }
}

// Enable drag and drop for cases
function enableCasesDragAndDrop() {
    const cards = document.querySelectorAll('.caso-card');
    cards.forEach(card => {
        card.setAttribute('draggable', 'true');
        card.addEventListener('dragstart', handleCaseDragStart);
        card.addEventListener('dragend', handleCaseDragEnd);
        card.addEventListener('dragover', handleCaseDragOver);
        card.addEventListener('drop', handleCaseDrop);
        card.addEventListener('dragenter', handleCaseDragEnter);
        card.addEventListener('dragleave', handleCaseDragLeave);
    });
}

// Disable drag and drop for cases
function disableCasesDragAndDrop() {
    const cards = document.querySelectorAll('.caso-card');
    cards.forEach(card => {
        card.setAttribute('draggable', 'false');
        card.removeEventListener('dragstart', handleCaseDragStart);
        card.removeEventListener('dragend', handleCaseDragEnd);
        card.removeEventListener('dragover', handleCaseDragOver);
        card.removeEventListener('drop', handleCaseDrop);
        card.removeEventListener('dragenter', handleCaseDragEnter);
        card.removeEventListener('dragleave', handleCaseDragLeave);
    });
}

let draggedCase = null;

function handleCaseDragStart(e) {
    draggedCase = this;
    this.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
}

function handleCaseDragEnd(e) {
    this.classList.remove('dragging');
    document.querySelectorAll('.caso-card').forEach(card => {
        card.classList.remove('drag-over');
    });
}

function handleCaseDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
}

function handleCaseDragEnter(e) {
    e.preventDefault();
    if (this !== draggedCase) {
        this.classList.add('drag-over');
    }
}

function handleCaseDragLeave(e) {
    this.classList.remove('drag-over');
}

function handleCaseDrop(e) {
    e.preventDefault();
    if (this !== draggedCase) {
        const grid = document.getElementById('casos-grid');
        const allCards = [...grid.querySelectorAll('.caso-card')];
        const draggedIndex = allCards.indexOf(draggedCase);
        const droppedIndex = allCards.indexOf(this);

        if (draggedIndex < droppedIndex) {
            this.parentNode.insertBefore(draggedCase, this.nextSibling);
        } else {
            this.parentNode.insertBefore(draggedCase, this);
        }

        // Update order array
        casesOrder = [...grid.querySelectorAll('.caso-card')].map(card => parseInt(card.dataset.id));
    }
    this.classList.remove('drag-over');
}

// Show save order bar
function showSaveOrderBar() {
    let bar = document.getElementById('save-order-bar');
    if (!bar) {
        bar = document.createElement('div');
        bar.id = 'save-order-bar';
        bar.className = 'save-order-bar';
        bar.innerHTML = `
            <p><i class="fas fa-info-circle"></i> Arrastra los casos para cambiar el orden</p>
            <button class="btn-save-order" onclick="saveOrderToFirestore()">
                <i class="fas fa-save"></i> Guardar Orden
            </button>
            <button class="btn-cancel-order" onclick="cancelOrderChanges()">
                <i class="fas fa-times"></i> Cancelar
            </button>
        `;
        document.body.appendChild(bar);
    }

    setTimeout(() => bar.classList.add('visible'), 10);
}

// Hide save order bar
function hideSaveOrderBar() {
    const bar = document.getElementById('save-order-bar');
    if (bar) {
        bar.classList.remove('visible');
        setTimeout(() => bar.remove(), 300);
    }
}

// Save order to Firestore
async function saveOrderToFirestore() {
    try {
        await db.collection('settings').doc('casesOrder').set({
            order: casesOrder,
            updatedAt: firebase.firestore.FieldValue.serverTimestamp(),
            updatedBy: currentUser.email
        });

        showNotification('Orden guardado exitosamente!', 'success');
        toggleEditMode();
    } catch (error) {
        console.error('Error saving order:', error);
        showNotification('Error al guardar el orden', 'error');
    }
}

// Cancel order changes
function cancelOrderChanges() {
    // Restore original order
    casesOrder = [...originalOrder];
    renderCasos();
    toggleEditMode();
    showNotification('Cambios cancelados', 'info');
}

// Load order from Firestore
async function loadOrderFromFirestore() {
    try {
        const doc = await db.collection('settings').doc('casesOrder').get();
        if (doc.exists) {
            return doc.data().order || [];
        }
        return [];
    } catch (error) {
        console.error('Error loading order:', error);
        return [];
    }
}

// Event listener for edit mode button
document.getElementById('edit-mode-btn')?.addEventListener('click', toggleEditMode);

// Event listener for admin panel button
document.getElementById('admin-panel-btn')?.addEventListener('click', openAdminPanel);

// Close admin modal on background click
document.getElementById('admin-modal')?.addEventListener('click', (e) => {
    if (e.target.id === 'admin-modal') closeAdminPanel();
});

// Close auth modal on background click
document.getElementById('auth-modal')?.addEventListener('click', (e) => {
    if (e.target.id === 'auth-modal') closeAuthModal();
});

// ================================
// TEMAS ACCORDION & DRAG-AND-DROP
// ================================

let temasEditMode = false;
let temasOrder = [];
let originalTemasOrder = [];

// Initialize temas accordion functionality
function initTemasAccordion() {
    const temaCards = document.querySelectorAll('.tema-card');

    temaCards.forEach(card => {
        const header = card.querySelector('.tema-header');
        const content = card.querySelector('.tema-content');

        if (!header || !content) return;

        // Add collapsed class initially (all collapsed by default)
        content.classList.add('tema-content-collapsed');
        card.classList.add('tema-collapsed');

        // Add toggle icon if not exists
        if (!header.querySelector('.tema-toggle-icon')) {
            const toggleIcon = document.createElement('span');
            toggleIcon.className = 'tema-toggle-icon';
            toggleIcon.innerHTML = '<i class="fas fa-chevron-down"></i>';
            header.appendChild(toggleIcon);
        }

        // Make header clickable
        header.style.cursor = 'pointer';
        header.addEventListener('click', (e) => {
            // Don't toggle if dragging
            if (temasEditMode && e.target.closest('.tema-drag-handle')) return;
            toggleTemaContent(card);
        });
    });
}

// Toggle tema content visibility
function toggleTemaContent(card) {
    const content = card.querySelector('.tema-content');
    const icon = card.querySelector('.tema-toggle-icon i');

    if (content.classList.contains('tema-content-collapsed')) {
        // Expand
        content.classList.remove('tema-content-collapsed');
        card.classList.remove('tema-collapsed');
        if (icon) {
            icon.classList.remove('fa-chevron-down');
            icon.classList.add('fa-chevron-up');
        }
    } else {
        // Collapse
        content.classList.add('tema-content-collapsed');
        card.classList.add('tema-collapsed');
        if (icon) {
            icon.classList.remove('fa-chevron-up');
            icon.classList.add('fa-chevron-down');
        }
    }
}

// Toggle temas edit mode (admin only)
function toggleTemasEditMode() {
    if (!isAdmin) {
        showNotification('Solo administradores pueden editar', 'error');
        return;
    }

    temasEditMode = !temasEditMode;
    const temasGrid = document.getElementById('temas-grid-sortable');
    const adminToggle = document.getElementById('admin-toggle');

    if (temasEditMode) {
        temasGrid.classList.add('temas-edit-mode');
        adminToggle.innerHTML = '<i class="fas fa-check"></i> Guardar Orden';
        adminToggle.style.background = 'linear-gradient(135deg, #10b981, #059669)';

        // Store original order
        originalTemasOrder = [...document.querySelectorAll('.tema-card')].map(c => c.id);
        temasOrder = [...originalTemasOrder];

        // Add drag handles to each tema
        addTemasDragHandles();
        enableTemasDragAndDrop();
        showTemasOrderBar();
        showNotification('Modo edicion de temas activado. Arrastra para reordenar.', 'info');
    } else {
        temasGrid.classList.remove('temas-edit-mode');
        adminToggle.innerHTML = '<i class="fas fa-arrows-alt"></i> Modo Admin: Reorganizar';
        adminToggle.style.background = '';

        removeTemasDragHandles();
        disableTemasDragAndDrop();
        hideTemasOrderBar();
    }
}

// Add drag handles to temas
function addTemasDragHandles() {
    document.querySelectorAll('.tema-card').forEach(card => {
        const header = card.querySelector('.tema-header');
        if (header && !header.querySelector('.tema-drag-handle')) {
            const handle = document.createElement('div');
            handle.className = 'tema-drag-handle';
            handle.innerHTML = '<i class="fas fa-grip-vertical"></i>';
            header.insertBefore(handle, header.firstChild);
        }
    });
}

// Remove drag handles from temas
function removeTemasDragHandles() {
    document.querySelectorAll('.tema-drag-handle').forEach(handle => handle.remove());
}

// Enable drag and drop for temas
function enableTemasDragAndDrop() {
    const cards = document.querySelectorAll('.tema-card');
    cards.forEach(card => {
        card.setAttribute('draggable', 'true');
        card.addEventListener('dragstart', handleTemaDragStart);
        card.addEventListener('dragend', handleTemaDragEnd);
        card.addEventListener('dragover', handleTemaDragOver);
        card.addEventListener('drop', handleTemaDrop);
        card.addEventListener('dragenter', handleTemaDragEnter);
        card.addEventListener('dragleave', handleTemaDragLeave);
    });
}

// Disable drag and drop for temas
function disableTemasDragAndDrop() {
    const cards = document.querySelectorAll('.tema-card');
    cards.forEach(card => {
        card.setAttribute('draggable', 'false');
        card.removeEventListener('dragstart', handleTemaDragStart);
        card.removeEventListener('dragend', handleTemaDragEnd);
        card.removeEventListener('dragover', handleTemaDragOver);
        card.removeEventListener('drop', handleTemaDrop);
        card.removeEventListener('dragenter', handleTemaDragEnter);
        card.removeEventListener('dragleave', handleTemaDragLeave);
    });
}

let draggedTema = null;

function handleTemaDragStart(e) {
    draggedTema = this;
    this.classList.add('tema-dragging');
    e.dataTransfer.effectAllowed = 'move';
}

function handleTemaDragEnd(e) {
    this.classList.remove('tema-dragging');
    document.querySelectorAll('.tema-card').forEach(card => {
        card.classList.remove('tema-drag-over');
    });
}

function handleTemaDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
}

function handleTemaDragEnter(e) {
    e.preventDefault();
    if (this !== draggedTema) {
        this.classList.add('tema-drag-over');
    }
}

function handleTemaDragLeave(e) {
    this.classList.remove('tema-drag-over');
}

function handleTemaDrop(e) {
    e.preventDefault();
    if (this !== draggedTema) {
        const grid = document.getElementById('temas-grid-sortable');
        const allCards = [...grid.querySelectorAll('.tema-card')];
        const draggedIndex = allCards.indexOf(draggedTema);
        const droppedIndex = allCards.indexOf(this);

        if (draggedIndex < droppedIndex) {
            this.parentNode.insertBefore(draggedTema, this.nextSibling);
        } else {
            this.parentNode.insertBefore(draggedTema, this);
        }

        // Update order array
        temasOrder = [...grid.querySelectorAll('.tema-card')].map(card => card.id);
    }
    this.classList.remove('tema-drag-over');
}

// Show temas order bar
function showTemasOrderBar() {
    let bar = document.getElementById('temas-order-bar');
    if (!bar) {
        bar = document.createElement('div');
        bar.id = 'temas-order-bar';
        bar.className = 'save-order-bar temas-bar';
        bar.innerHTML = `
            <p><i class="fas fa-info-circle"></i> Arrastra los articulos de opinion para cambiar el orden</p>
            <button class="btn-save-order" onclick="saveTemasOrderToFirestore()">
                <i class="fas fa-save"></i> Guardar Orden
            </button>
            <button class="btn-cancel-order" onclick="cancelTemasOrderChanges()">
                <i class="fas fa-times"></i> Cancelar
            </button>
        `;
        document.body.appendChild(bar);
    }

    setTimeout(() => bar.classList.add('visible'), 10);
}

// Hide temas order bar
function hideTemasOrderBar() {
    const bar = document.getElementById('temas-order-bar');
    if (bar) {
        bar.classList.remove('visible');
        setTimeout(() => bar.remove(), 300);
    }
}

// Save temas order to Firestore
async function saveTemasOrderToFirestore() {
    try {
        await db.collection('settings').doc('temasOrder').set({
            order: temasOrder,
            updatedAt: firebase.firestore.FieldValue.serverTimestamp(),
            updatedBy: currentUser.email
        });

        showNotification('Orden de temas guardado!', 'success');
        toggleTemasEditMode();
    } catch (error) {
        console.error('Error saving temas order:', error);
        showNotification('Error al guardar el orden', 'error');
    }
}

// Cancel temas order changes
function cancelTemasOrderChanges() {
    // Restore original order
    const grid = document.getElementById('temas-grid-sortable');
    originalTemasOrder.forEach(id => {
        const card = document.getElementById(id);
        if (card) grid.appendChild(card);
    });

    toggleTemasEditMode();
    showNotification('Cambios cancelados', 'info');
}

// Load temas order from Firestore
async function loadTemasOrderFromFirestore() {
    try {
        const doc = await db.collection('settings').doc('temasOrder').get();
        if (doc.exists) {
            const order = doc.data().order || [];
            applyTemasOrder(order);
        }
    } catch (error) {
        console.error('Error loading temas order:', error);
    }
}

// Apply temas order to DOM
function applyTemasOrder(order) {
    const grid = document.getElementById('temas-grid-sortable');
    if (!grid || order.length === 0) return;

    order.forEach(id => {
        const card = document.getElementById(id);
        if (card) grid.appendChild(card);
    });
}

// Update admin toggle visibility based on auth
function updateTemasAdminUI() {
    const adminToggle = document.getElementById('admin-toggle');
    if (adminToggle) {
        adminToggle.style.display = isAdmin ? 'inline-flex' : 'none';
    }
}

// Event listener for temas admin toggle
document.getElementById('admin-toggle')?.addEventListener('click', toggleTemasEditMode);

// Initialize temas on page load (after auth is ready)
function initTemas() {
    initTemasAccordion();
    updateTemasAdminUI();

    // Load saved order if logged in
    if (typeof db !== 'undefined') {
        loadTemasOrderFromFirestore();
    }
}

// Call initTemas after a delay to ensure Firebase is ready
setTimeout(initTemas, 1000);

// Also update temas UI when auth state changes
if (typeof auth !== 'undefined') {
    auth.onAuthStateChanged(() => {
        updateTemasAdminUI();
        if (isAdmin) {
            loadTemasOrderFromFirestore();
        }
    });
}
