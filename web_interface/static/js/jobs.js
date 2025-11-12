async function loadJobs() {
    try {
        const response = await fetch('/api/jobs?limit=100');
        const jobs = await response.json();
        
        const tbody = document.getElementById('jobs-tbody');
        
        if (!jobs || jobs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6">Aucun job</td></tr>';
            return;
        }
        
        tbody.innerHTML = '';
        
        jobs.forEach(job => {
            const row = document.createElement('tr');
            
            const fileName = job.file ? job.file.split('/').pop() : 'N/A';
            const link = job.link 
                ? `<a href="${job.link}" target="_blank" style="color: var(--primary)">Ouvrir</a>` 
                : '-';
            
            row.innerHTML = `
                <td>#${job.id}</td>
                <td title="${job.file}">${fileName}</td>
                <td><span class="job-status ${job.status}">${job.status}</span></td>
                <td>${link}</td>
                <td>${job.created_at || '-'}</td>
                <td>${job.updated_at || '-'}</td>
            `;
            
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Erreur:', error);
        document.getElementById('jobs-tbody').innerHTML = 
            '<tr><td colspan="6">Erreur de chargement</td></tr>';
    }
}

function refreshJobs() {
    loadJobs();
}

// Auto-refresh toutes les 5 secondes
setInterval(loadJobs, 5000);

// Chargement initial
document.addEventListener('DOMContentLoaded', loadJobs);
