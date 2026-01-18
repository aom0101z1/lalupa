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
        const response = await fetch('data.json');
        data = await response.json();

        populateFilters();
        renderStats();
        filterAndRenderCasos();

        if (data.estadisticas.ultima_actualizacion) {
            ultimaActualizacion.textContent = formatDate(data.estadisticas.ultima_actualizacion);
        }
    } catch (error) {
        console.error('Error cargando datos:', error);
        casosGrid.innerHTML = `
            <div class="no-results">
                <i class="fas fa-exclamation-circle"></i>
                <p>Error al cargar los datos. Verifica que el archivo data.json existe.</p>
            </div>
        `;
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
    `;

    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
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
btnMedios.addEventListener('click', (e) => {
    e.preventDefault();
    openMediosModal();
});
mediosModalClose.addEventListener('click', closeMediosModal);
mediosModal.addEventListener('click', (e) => {
    if (e.target === mediosModal) closeMediosModal();
});

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
