async function loadAnalytics() {
    try {
        // Charger les jobs
        const jobsResponse = await fetch('/api/jobs?limit=1000');
        const jobs = await jobsResponse.json();
        
        // Charger les tokens
        const tokensResponse = await fetch('/api/monetizer/tokens?limit=1000');
        const tokens = await tokensResponse.json();
        
        // Calculer les stats
        const totalJobs = jobs.length;
        const completedJobs = jobs.filter(j => j.status === 'done').length;
        const totalTokens = tokens.length;
        const activeTokens = tokens.filter(t => t.status === 'activated').length;
        
        // Afficher les stats
        document.getElementById('total-jobs').textContent = totalJobs;
        document.getElementById('completed-jobs').textContent = completedJobs;
        document.getElementById('total-tokens').textContent = totalTokens;
        document.getElementById('active-tokens').textContent = activeTokens;
        
    } catch (error) {
        console.error('Erreur lors du chargement des analytics:', error);
    }
}

// Chargement initial
document.addEventListener('DOMContentLoaded', loadAnalytics);

// Auto-refresh toutes les 30 secondes
setInterval(loadAnalytics, 30000);
