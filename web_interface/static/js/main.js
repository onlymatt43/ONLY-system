// Vérifier l'état des services
async function checkServices() {
    try {
        const response = await fetch('/api/status');
        const services = await response.json();
        
        const servicesGrid = document.getElementById('services-grid');
        servicesGrid.innerHTML = '';
        
        Object.entries(services).forEach(([name, data]) => {
            const card = document.createElement('div');
            card.className = `service-card ${data.status}`;
            
            const icons = {
                gateway: '🚦',
                narrator: '🧠',
                builder: '📦',
                publisher: '📣',
                sentinel: '📊',
                monetizer: '💰'
            };
            
            card.innerHTML = `
                <div class="service-icon">${icons[name] || '📡'}</div>
                <h4>${name.charAt(0).toUpperCase() + name.slice(1)}</h4>
                <span class="status">${data.status}</span>
            `;
            
            servicesGrid.appendChild(card);
        });
    } catch (error) {
        console.error('Erreur lors de la vérification des services:', error);
    }
}

// Charger les jobs récents
async function loadRecentJobs() {
    try {
        const response = await fetch('/api/jobs?limit=5');
        const jobs = await response.json();
        
        const jobsList = document.getElementById('jobs-list');
        
        // Ensure jobs is an array
        if (!Array.isArray(jobs)) {
            console.warn('Jobs response is not an array:', jobs);
            jobsList.innerHTML = '<p class="loading">Aucun job pour le moment</p>';
            return;
        }
        
        if (jobs.length === 0) {
            jobsList.innerHTML = '<p class="loading">Aucun job pour le moment</p>';
            return;
        }
        
        jobsList.innerHTML = '';
        
        jobs.forEach(job => {
            const jobItem = document.createElement('div');
            jobItem.className = 'job-item';
            
            const fileName = job.file ? job.file.split('/').pop() : 'N/A';
            const link = job.link ? `<a href="${job.link}" target="_blank">Voir</a>` : '-';
            
            jobItem.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>#${job.id}</strong> - ${fileName}
                        <span class="job-status ${job.status}">${job.status}</span>
                    </div>
                    <div style="color: var(--text-muted); font-size: 0.9rem;">
                        ${job.updated_at || job.created_at}
                    </div>
                </div>
            `;
            
            jobsList.appendChild(jobItem);
        });
    } catch (error) {
        console.error('Erreur lors du chargement des jobs:', error);
        document.getElementById('jobs-list').innerHTML = 
            '<p class="loading">Erreur de chargement</p>';
    }
}

// Auto-refresh toutes les 10 secondes
setInterval(() => {
    checkServices();
    loadRecentJobs();
}, 10000);

// Chargement initial
document.addEventListener('DOMContentLoaded', () => {
    checkServices();
    loadRecentJobs();
});
