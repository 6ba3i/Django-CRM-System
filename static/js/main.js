 // JavaScript functionality for CRM system

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    initializeDragAndDrop();
    initializeCharts();
    initializeRealTimeUpdates();
    initializeSearchAutocomplete();
    initializeNotifications();
    initializeFormValidation();
});

// Drag and Drop for Pipeline
function initializeDragAndDrop() {
    const dealCards = document.querySelectorAll('.deal-card');
    const pipelineStages = document.querySelectorAll('.pipeline-stage');
    
    if (dealCards.length === 0 || pipelineStages.length === 0) return;
    
    dealCards.forEach(card => {
        card.draggable = true;
        
        card.addEventListener('dragstart', (e) => {
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('dealId', card.dataset.dealId);
            card.classList.add('dragging');
        });
        
        card.addEventListener('dragend', () => {
            card.classList.remove('dragging');
        });
    });
    
    pipelineStages.forEach(stage => {
        stage.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            stage.classList.add('drag-over');
        });
        
        stage.addEventListener('dragleave', () => {
            stage.classList.remove('drag-over');
        });
        
        stage.addEventListener('drop', async (e) => {
            e.preventDefault();
            stage.classList.remove('drag-over');
            
            const dealId = e.dataTransfer.getData('dealId');
            const newStage = stage.dataset.stage;
            
            // Move deal to new stage
            try {
                const response = await fetch(`/sales/api/deal/${dealId}/move/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({ stage: newStage })
                });
                
                if (response.ok) {
                    const result = await response.json();
                    // Move card to new stage
                    const card = document.querySelector(`[data-deal-id="${dealId}"]`);
                    stage.querySelector('.pipeline-deals').appendChild(card);
                    
                    // Update stage counts
                    updateStageCounts();
                    
                    // Show success notification
                    showNotification('Deal moved successfully', 'success');
                } else {
                    showNotification('Failed to move deal', 'error');
                }
            } catch (error) {
                console.error('Error moving deal:', error);
                showNotification('An error occurred', 'error');
            }
        });
    });
}

// Initialize Charts
function initializeCharts() {
    // Sales Pipeline Chart
    const pipelineCanvas = document.getElementById('pipelineChart');
    if (pipelineCanvas) {
        const ctx = pipelineCanvas.getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Lead', 'Qualified', 'Proposal', 'Negotiation', 'Won'],
                datasets: [{
                    label: 'Deal Count',
                    data: pipelineCanvas.dataset.counts?.split(',') || [0, 0, 0, 0, 0],
                    backgroundColor: [
                        'rgba(74, 144, 226, 0.5)',
                        'rgba(90, 159, 226, 0.5)',
                        'rgba(106, 175, 226, 0.5)',
                        'rgba(122, 191, 226, 0.5)',
                        'rgba(80, 200, 120, 0.5)'
                    ],
                    borderColor: [
                        'rgba(74, 144, 226, 1)',
                        'rgba(90, 159, 226, 1)',
                        'rgba(106, 175, 226, 1)',
                        'rgba(122, 191, 226, 1)',
                        'rgba(80, 200, 120, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.8)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.8)'
                        }
                    }
                }
            }
        });
    }
    
    // Revenue Trend Chart
    const revenueCanvas = document.getElementById('revenueChart');
    if (revenueCanvas) {
        const ctx = revenueCanvas.getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: revenueCanvas.dataset.labels?.split(',') || [],
                datasets: [{
                    label: 'Revenue',
                    data: revenueCanvas.dataset.values?.split(',') || [],
                    borderColor: 'rgba(80, 200, 120, 1)',
                    backgroundColor: 'rgba(80, 200, 120, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.8)',
                            callback: function(value) {
                                return '$' + (value/1000) + 'K';
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.8)'
                        }
                    }
                }
            }
        });
    }
}

// Real-time Updates using Firebase listeners
function initializeRealTimeUpdates() {
    // This would connect to Firebase for real-time updates
    // For now, we'll use polling as a fallback
    
    if (window.location.pathname.includes('pipeline')) {
        setInterval(async () => {
            try {
                const response = await fetch('/sales/api/pipeline/');
                if (response.ok) {
                    const data = await response.json();
                    updatePipelineDisplay(data);
                }
            } catch (error) {
                console.error('Error fetching pipeline updates:', error);
            }
        }, 30000); // Update every 30 seconds
    }
}

// Search Autocomplete
function initializeSearchAutocomplete() {
    const searchInput = document.querySelector('.search-autocomplete');
    if (!searchInput) return;
    
    let debounceTimer;
    const resultsContainer = document.createElement('div');
    resultsContainer.className = 'search-results glass-panel';
    resultsContainer.style.cssText = 'position: absolute; top: 100%; left: 0; right: 0; margin-top: 8px; display: none; max-height: 300px; overflow-y: auto;';
    searchInput.parentElement.appendChild(resultsContainer);
    
    searchInput.addEventListener('input', (e) => {
        clearTimeout(debounceTimer);
        const query = e.target.value;
        
        if (query.length < 2) {
            resultsContainer.style.display = 'none';
            return;
        }
        
        debounceTimer = setTimeout(async () => {
            try {
                const response = await fetch(`/customers/api/search?q=${encodeURIComponent(query)}`);
                if (response.ok) {
                    const data = await response.json();
                    displaySearchResults(data.results, resultsContainer);
                }
            } catch (error) {
                console.error('Error searching:', error);
            }
        }, 300);
    });
    
    // Click outside to close
    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !resultsContainer.contains(e.target)) {
            resultsContainer.style.display = 'none';
        }
    });
}

function displaySearchResults(results, container) {
    if (results.length === 0) {
        container.innerHTML = '<div style="padding: 12px; opacity: 0.6;">No results found</div>';
        container.style.display = 'block';
        return;
    }
    
    container.innerHTML = results.map(result => `
        <a href="/customers/${result.id}/" class="search-result-item" style="display: block; padding: 12px; text-decoration: none; color: inherit; transition: all 0.3s;">
            <div style="font-weight: 500;">${result.name}</div>
            <div style="font-size: 12px; opacity: 0.6;">${result.company} • ${result.email}</div>
        </a>
    `).join('');
    
    container.style.display = 'block';
}

// Notifications
function initializeNotifications() {
    // Check for new notifications periodically
    setInterval(async () => {
        try {
            const response = await fetch('/api/notifications/');
            if (response.ok) {
                const data = await response.json();
                updateNotificationBadge(data.count);
            }
        } catch (error) {
            console.error('Error checking notifications:', error);
        }
    }, 60000); // Check every minute
}

function updateNotificationBadge(count) {
    const badges = document.querySelectorAll('.notification-badge');
    badges.forEach(badge => {
        if (count > 0) {
            badge.textContent = count;
            badge.style.display = 'block';
        } else {
            badge.style.display = 'none';
        }
    });
}

// Form Validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            
            form.classList.add('was-validated');
        });
        
        // Real-time validation
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', () => {
                if (!input.checkValidity()) {
                    input.classList.add('is-invalid');
                } else {
                    input.classList.remove('is-invalid');
                }
            });
        });
    });
}

// Utility Functions
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `glass-alert ${type}`;
    notification.textContent = message;
    notification.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 3000; min-width: 300px;';
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

function updateStageCounts() {
    const stages = document.querySelectorAll('.pipeline-stage');
    stages.forEach(stage => {
        const count = stage.querySelectorAll('.deal-card').length;
        const countElement = stage.querySelector('.pipeline-stage-count');
        if (countElement) {
            countElement.textContent = count;
        }
    });
}

function updatePipelineDisplay(data) {
    // Update pipeline display with new data
    data.pipeline.forEach(stageData => {
        const stage = document.querySelector(`[data-stage="${stageData.stage}"]`);
        if (stage) {
            const countElement = stage.querySelector('.pipeline-stage-count');
            if (countElement) {
                countElement.textContent = stageData.count;
            }
            
            const valueElement = stage.querySelector('.pipeline-stage-value');
            if (valueElement) {
                valueElement.textContent = `$${(stageData.total_value / 1000).toFixed(0)}K`;
            }
        }
    });
}

// Export functions for use in other scripts
window.CRM = {
    showNotification,
    updateNotificationBadge,
    getCookie,
    initializeDragAndDrop
};

// Animation for glass panels on scroll
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.animation = 'slideIn 0.5s ease forwards';
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

// Observe all glass panels
document.querySelectorAll('.glass-panel, .glass-card').forEach(panel => {
    observer.observe(panel);
});

// Mobile sidebar toggle
const sidebarToggle = document.createElement('button');
sidebarToggle.className = 'sidebar-toggle glass-btn';
sidebarToggle.innerHTML = `
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="3" y1="12" x2="21" y2="12"/>
        <line x1="3" y1="6" x2="21" y2="6"/>
        <line x1="3" y1="18" x2="21" y2="18"/>
    </svg>
`;
sidebarToggle.style.cssText = 'display: none; position: fixed; top: 20px; left: 20px; z-index: 1001; padding: 8px;';

document.body.appendChild(sidebarToggle);

// Show toggle on mobile
if (window.innerWidth <= 768) {
    sidebarToggle.style.display = 'block';
}

sidebarToggle.addEventListener('click', () => {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('active');
});

// Handle window resize
window.addEventListener('resize', () => {
    if (window.innerWidth <= 768) {
        sidebarToggle.style.display = 'block';
    } else {
        sidebarToggle.style.display = 'none';
        document.getElementById('sidebar').classList.remove('active');
    }
});