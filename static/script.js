// Verificar se estamos no estoque.html
if (window.location.pathname === '/estoque' || window.location.pathname.includes('/estoque')) {
    // Inicializar tooltips
    document.addEventListener('DOMContentLoaded', function() {
        // Tooltips
        const tooltips = document.querySelectorAll('[data-tooltip]');
        tooltips.forEach(element => {
            element.addEventListener('mouseenter', function() {
                const tooltip = document.createElement('div');
                tooltip.className = 'tooltip';
                tooltip.textContent = this.getAttribute('data-tooltip');
                tooltip.style.position = 'absolute';
                tooltip.style.background = 'var(--dark)';
                tooltip.style.color = 'white';
                tooltip.style.padding = '5px 10px';
                tooltip.style.borderRadius = '4px';
                tooltip.style.fontSize = '12px';
                tooltip.style.zIndex = '1000';
                tooltip.style.whiteSpace = 'nowrap';
                
                const rect = this.getBoundingClientRect();
                tooltip.style.top = (rect.top - 30) + 'px';
                tooltip.style.left = (rect.left + rect.width/2) + 'px';
                tooltip.style.transform = 'translateX(-50%)';
                
                document.body.appendChild(tooltip);
                this._tooltip = tooltip;
            });
            
            element.addEventListener('mouseleave', function() {
                if (this._tooltip) {
                    document.body.removeChild(this._tooltip);
                    delete this._tooltip;
                }
            });
        });
    });
}
// Data atual no header
function updateCurrentDate() {
    const now = new Date();
    const options = { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    const dateElement = document.getElementById('current-date');
    if (dateElement) {
        dateElement.textContent = now.toLocaleDateString('pt-BR', options);
    }
}

// Inicializar tooltips
function initTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(element => {
        element.addEventListener('mouseenter', function() {
            this.setAttribute('title', this.getAttribute('data-tooltip'));
        });
    });
}

// Modal functions
let currentProductId = null;

function openEditModal(id, currentData = '') {
    currentProductId = id;
    const modal = document.getElementById('editDateModal');
    const input = document.getElementById('editDateInput');
    
    if (currentData && currentData !== '-') {
        input.value = currentData;
    } else {
        input.value = '';
    }
    
    modal.classList.add('active');
}

function closeModal() {
    const modal = document.getElementById('editDateModal');
    modal.classList.remove('active');
    currentProductId = null;
}

function saveDate() {
    if (!currentProductId) return;
    
    const input = document.getElementById('editDateInput');
    const dateValue = input.value;
    
    fetch(`/atualizar_data_saida/${currentProductId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ data_saida: dateValue || null })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('Erro ao salvar data');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        alert('Erro ao salvar data');
    });
}

function clearDate() {
    if (!currentProductId) return;
    
    if (confirm('Deseja realmente limpar a data de saída?')) {
        fetch(`/atualizar_data_saida/${currentProductId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ data_saida: null })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            }
        });
    }
}

// Exportar CSV com formatação melhorada
function exportToCSV() {
    fetch('/exportar_csv')
        .then(response => response.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `estoque_${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        })
        .catch(error => {
            console.error('Erro ao exportar:', error);
            alert('Erro ao exportar CSV');
        });
}

// Atualizar quantidade via AJAX
function updateQuantity(id, currentQty) {
    const newQty = prompt('Nova quantidade:', currentQty);
    
    if (newQty !== null && !isNaN(newQty) && newQty >= 0) {
        fetch(`/atualizar_estoque/${id}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ quantidade: parseInt(newQty) })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            }
        });
    }
}

// Filtrar tabela
function filterTable() {
    const searchInput = document.getElementById('searchInput');
    const table = document.getElementById('productsTable');
    const rows = table.getElementsByTagName('tr');
    const filter = searchInput.value.toLowerCase();
    
    for (let i = 1; i < rows.length; i++) {
        const cells = rows[i].getElementsByTagName('td');
        let found = false;
        
        for (let j = 0; j < cells.length; j++) {
            const cellText = cells[j].textContent.toLowerCase();
            if (cellText.includes(filter)) {
                found = true;
                break;
            }
        }
        
        rows[i].style.display = found ? '' : 'none';
    }
}

// Toggle sidebar em mobile
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('active');
}

// Confirmar exclusão com SweetAlert style
function confirmDelete(id, name) {
    if (confirm(`Deseja realmente excluir o produto "${name}"?`)) {
        window.location.href = `/excluir/${id}`;
    }
}

// Inicializar tudo quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    updateCurrentDate();
    initTooltips();
    
    // Atualizar data a cada minuto
    setInterval(updateCurrentDate, 60000);
    
    // Fechar modal com ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeModal();
        }
    });
    
    // Fechar modal ao clicar fora
    document.addEventListener('click', function(e) {
        const modal = document.getElementById('editDateModal');
        if (modal && modal.classList.contains('active') && e.target === modal) {
            closeModal();
        }
    });
});

// Animações de entrada
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Aplicar animação a elementos com a classe 'animate'
document.querySelectorAll('.animate').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    observer.observe(el);
});