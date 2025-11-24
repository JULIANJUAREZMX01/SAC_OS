/**
 * ===============================================================
 * SAC Dashboard - JavaScript Principal
 * CEDIS Chedraui Cancún 427
 * ===============================================================
 *
 * Funcionalidades principales del dashboard
 *
 * Desarrollado por: Julián Alexander Juárez Alvarado (ADMJAJA)
 * Jefe de Sistemas - CEDIS Chedraui Logística Cancún
 * ===============================================================
 */

// ===============================================================
// CONFIGURACIÓN GLOBAL
// ===============================================================

const SAC = {
    config: {
        autoRefreshInterval: 60, // segundos
        toastDuration: 5000,     // milisegundos
        apiBaseUrl: '',
    },
    state: {
        autoRefreshTimer: null,
        isLoading: false,
    }
};

// ===============================================================
// FUNCIONES DE UI
// ===============================================================

/**
 * Muestra el overlay de carga
 */
function showLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.add('show');
        SAC.state.isLoading = true;
    }
}

/**
 * Oculta el overlay de carga
 */
function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.remove('show');
        SAC.state.isLoading = false;
    }
}

/**
 * Muestra una notificación toast
 * @param {string} message - Mensaje a mostrar
 * @param {string} type - Tipo: success, error, warning, info
 */
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toastId = 'toast-' + Date.now();
    const bgClass = {
        'success': 'bg-success',
        'error': 'bg-danger',
        'warning': 'bg-warning text-dark',
        'info': 'bg-info'
    }[type] || 'bg-secondary';

    const iconClass = {
        'success': 'bi-check-circle',
        'error': 'bi-x-circle',
        'warning': 'bi-exclamation-triangle',
        'info': 'bi-info-circle'
    }[type] || 'bi-bell';

    const toastHtml = `
        <div id="${toastId}" class="toast ${bgClass} text-white" role="alert">
            <div class="d-flex align-items-center">
                <i class="bi ${iconClass} me-2 ms-2"></i>
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;

    container.insertAdjacentHTML('beforeend', toastHtml);
    const toastEl = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastEl, { delay: SAC.config.toastDuration });
    toast.show();
    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}

// ===============================================================
// FUNCIONES DE RELOJ
// ===============================================================

/**
 * Actualiza el reloj en el navbar
 */
function updateClock() {
    const now = new Date();
    const timeStr = now.toLocaleString('es-MX', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
    const clockEl = document.getElementById('currentTime');
    if (clockEl) {
        clockEl.innerHTML = '<i class="bi bi-clock"></i> ' + timeStr;
    }
}

// ===============================================================
// AUTO-REFRESH
// ===============================================================

/**
 * Inicia el auto-refresh de datos
 * @param {number} seconds - Intervalo en segundos
 */
function startAutoRefresh(seconds = 60) {
    stopAutoRefresh();
    SAC.config.autoRefreshInterval = seconds;
    SAC.state.autoRefreshTimer = setInterval(() => {
        if (typeof refreshData === 'function') {
            refreshData();
        }
    }, seconds * 1000);
    console.log(`Auto-refresh iniciado: cada ${seconds} segundos`);
}

/**
 * Detiene el auto-refresh
 */
function stopAutoRefresh() {
    if (SAC.state.autoRefreshTimer) {
        clearInterval(SAC.state.autoRefreshTimer);
        SAC.state.autoRefreshTimer = null;
        console.log('Auto-refresh detenido');
    }
}

// ===============================================================
// API HELPERS
// ===============================================================

/**
 * Realiza una petición GET a la API
 * @param {string} endpoint - Endpoint de la API
 * @returns {Promise<Object>} - Respuesta JSON
 */
async function apiGet(endpoint) {
    try {
        const response = await fetch(SAC.config.apiBaseUrl + endpoint);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error en API GET:', error);
        throw error;
    }
}

/**
 * Realiza una petición POST a la API
 * @param {string} endpoint - Endpoint de la API
 * @param {Object} data - Datos a enviar
 * @returns {Promise<Object>} - Respuesta JSON
 */
async function apiPost(endpoint, data) {
    try {
        const response = await fetch(SAC.config.apiBaseUrl + endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error en API POST:', error);
        throw error;
    }
}

/**
 * Realiza una petición DELETE a la API
 * @param {string} endpoint - Endpoint de la API
 * @returns {Promise<Object>} - Respuesta JSON
 */
async function apiDelete(endpoint) {
    try {
        const response = await fetch(SAC.config.apiBaseUrl + endpoint, {
            method: 'DELETE'
        });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error en API DELETE:', error);
        throw error;
    }
}

// ===============================================================
// FUNCIONES DE VALIDACIÓN
// ===============================================================

/**
 * Valida una OC
 * @param {string} ocNumero - Número de OC
 * @returns {Promise<Object>} - Resultado de validación
 */
async function validarOC(ocNumero) {
    showLoading();
    try {
        const resultado = await apiPost('/api/validar-oc', { oc_numero: ocNumero });
        hideLoading();
        return resultado;
    } catch (error) {
        hideLoading();
        showToast('Error al validar OC: ' + error.message, 'error');
        throw error;
    }
}

// ===============================================================
// FUNCIONES DE REPORTES
// ===============================================================

/**
 * Genera un reporte
 * @param {string} tipo - Tipo de reporte
 * @param {Object} opciones - Opciones adicionales
 */
async function generarReporte(tipo, opciones = {}) {
    showLoading();
    try {
        const data = { tipo, ...opciones };
        const resultado = await apiPost('/api/generar-reporte', data);
        hideLoading();

        if (resultado.success) {
            showToast('Reporte generado: ' + resultado.archivo, 'success');
            if (resultado.url) {
                window.open(resultado.url, '_blank');
            }
        } else {
            showToast('Error: ' + resultado.error, 'error');
        }
        return resultado;
    } catch (error) {
        hideLoading();
        showToast('Error al generar reporte', 'error');
        throw error;
    }
}

/**
 * Genera reporte diario
 */
async function generarReporteDiario() {
    return generarReporte('diario');
}

/**
 * Descarga un archivo
 * @param {string} filename - Nombre del archivo
 */
function descargarArchivo(filename) {
    window.open(`/api/descargar/${filename}`, '_blank');
}

/**
 * Elimina un reporte
 * @param {string} filename - Nombre del archivo
 */
async function eliminarReporte(filename) {
    if (!confirm(`¿Eliminar el archivo ${filename}?`)) {
        return;
    }

    showLoading();
    try {
        const resultado = await apiDelete(`/api/reportes/${filename}`);
        hideLoading();

        if (resultado.success) {
            showToast('Archivo eliminado', 'success');
            location.reload();
        } else {
            showToast('Error: ' + resultado.error, 'error');
        }
    } catch (error) {
        hideLoading();
        showToast('Error al eliminar archivo', 'error');
    }
}

// ===============================================================
// FUNCIONES DE ERRORES
// ===============================================================

/**
 * Marca un error como resuelto
 * @param {number} errorId - ID del error
 */
async function resolverError(errorId) {
    if (!confirm('¿Marcar este error como resuelto?')) {
        return;
    }

    showLoading();
    try {
        const resultado = await apiPost(`/api/errores/${errorId}/resolver`, {});
        hideLoading();

        if (resultado.success) {
            showToast('Error marcado como resuelto', 'success');
            location.reload();
        } else {
            showToast('Error: ' + resultado.error, 'error');
        }
    } catch (error) {
        hideLoading();
        showToast('Error al resolver', 'error');
    }
}

// ===============================================================
// FUNCIONES DE CONFIGURACIÓN
// ===============================================================

/**
 * Prueba la conexión a DB2
 */
async function probarConexionDB() {
    showLoading();
    try {
        const resultado = await apiGet('/api/test-db');
        hideLoading();

        if (resultado.success) {
            showToast(resultado.message, 'success');
        } else {
            showToast('Error: ' + resultado.error, 'error');
        }
    } catch (error) {
        hideLoading();
        showToast('Error al probar conexión', 'error');
    }
}

/**
 * Envía email de prueba
 * @param {string} email - Dirección de email
 */
async function enviarEmailPrueba(email) {
    if (!email) {
        showToast('Ingrese un email', 'warning');
        return;
    }

    showLoading();
    try {
        const resultado = await apiPost('/api/test-email', { email });
        hideLoading();

        if (resultado.success) {
            showToast(resultado.message, 'success');
        } else {
            showToast('Error: ' + resultado.error, 'error');
        }
    } catch (error) {
        hideLoading();
        showToast('Error al enviar email', 'error');
    }
}

/**
 * Envía mensaje de prueba a Telegram
 */
async function enviarTelegramPrueba() {
    showLoading();
    try {
        const resultado = await apiPost('/api/test-telegram', {});
        hideLoading();

        if (resultado.success) {
            showToast(resultado.message, 'success');
        } else {
            showToast('Error: ' + resultado.error, 'error');
        }
    } catch (error) {
        hideLoading();
        showToast('Error al enviar mensaje', 'error');
    }
}

/**
 * Limpia el historial antiguo
 * @param {number} dias - Días a mantener
 */
async function limpiarHistorial(dias = 90) {
    if (!confirm(`¿Eliminar registros anteriores a ${dias} días?`)) {
        return;
    }

    showLoading();
    try {
        const resultado = await apiPost('/api/limpiar-historial', { dias });
        hideLoading();

        if (resultado.success) {
            showToast(`${resultado.registros_eliminados} registros eliminados`, 'success');
        } else {
            showToast('Error: ' + resultado.error, 'error');
        }
    } catch (error) {
        hideLoading();
        showToast('Error al limpiar historial', 'error');
    }
}

// ===============================================================
// FUNCIONES DE UTILIDAD
// ===============================================================

/**
 * Formatea un número con separadores de miles
 * @param {number} num - Número a formatear
 * @returns {string} - Número formateado
 */
function formatNumber(num) {
    return new Intl.NumberFormat('es-MX').format(num);
}

/**
 * Formatea una fecha
 * @param {string} dateStr - Fecha en formato ISO
 * @returns {string} - Fecha formateada
 */
function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleString('es-MX', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Copia texto al portapapeles
 * @param {string} text - Texto a copiar
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showToast('Copiado al portapapeles', 'success');
    } catch (error) {
        showToast('Error al copiar', 'error');
    }
}

// ===============================================================
// HEALTH CHECK
// ===============================================================

/**
 * Verifica el estado del sistema
 */
async function verificarSistema() {
    try {
        const resultado = await apiGet('/api/health-check');
        console.log('Health Check:', resultado);
        return resultado;
    } catch (error) {
        console.error('Error en health check:', error);
        return null;
    }
}

// ===============================================================
// INICIALIZACIÓN
// ===============================================================

document.addEventListener('DOMContentLoaded', function() {
    // Actualizar reloj cada minuto
    updateClock();
    setInterval(updateClock, 60000);

    // Log de inicialización
    console.log('SAC Dashboard inicializado');
    console.log('Versión: 1.0.0');
});

// Exportar funciones globalmente
window.SAC = SAC;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.showToast = showToast;
window.startAutoRefresh = startAutoRefresh;
window.stopAutoRefresh = stopAutoRefresh;
window.validarOC = validarOC;
window.generarReporte = generarReporte;
window.generarReporteDiario = generarReporteDiario;
window.descargarArchivo = descargarArchivo;
window.eliminarReporte = eliminarReporte;
window.resolverError = resolverError;
window.probarConexionDB = probarConexionDB;
window.enviarEmailPrueba = enviarEmailPrueba;
window.enviarTelegramPrueba = enviarTelegramPrueba;
window.limpiarHistorial = limpiarHistorial;
window.formatNumber = formatNumber;
window.formatDate = formatDate;
window.copyToClipboard = copyToClipboard;
window.verificarSistema = verificarSistema;
