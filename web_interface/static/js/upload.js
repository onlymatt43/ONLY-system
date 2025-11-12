async function triggerUpload() {
    const videoUrl = document.getElementById('video-url').value.trim();
    const videoTitle = document.getElementById('video-title').value.trim();
    
    if (!videoUrl) {
        alert('Veuillez entrer une URL de vidéo');
        return;
    }
    
    const statusDiv = document.getElementById('upload-status');
    const statusContent = document.getElementById('status-content');
    
    statusDiv.classList.remove('hidden');
    statusContent.innerHTML = '<p>⏳ Traitement en cours...</p>';
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                event: 'new_video',
                file: videoUrl,
                title: videoTitle || undefined,
                timestamp: new Date().toISOString()
            })
        });
        
        // Check if response is ok (status 200-299)
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        // Handle error field from backend
        if (result.error) {
            statusContent.innerHTML = `
                <p>❌ Erreur backend:</p>
                <pre style="background: #1e293b; padding: 1rem; border-radius: 0.5rem; overflow-x: auto;">${result.error}</pre>
            `;
            return;
        }
        
        // Check for successful response
        if (result.ok) {
            statusContent.innerHTML = `
                <p>✅ Vidéo ajoutée avec succès!</p>
                <p><strong>Job ID:</strong> ${result.enqueued_job_id || result.job_id}</p>
                ${result.message ? `<p>${result.message}</p>` : ''}
                ${result.status ? `<p>Status: ${result.status}</p>` : ''}
                ${result.link ? `<p><a href="${result.link}" target="_blank">Voir le contenu</a></p>` : ''}
                <a href="/jobs" class="btn btn-primary" style="margin-top: 1rem;">Voir les jobs</a>
            `;
        } else {
            // Gateway returned ok:false
            statusContent.innerHTML = `
                <p>⚠️ ${result.message || result.error || 'Erreur inconnue'}</p>
                ${result.job_id ? `<p>Job existant: #${result.job_id}</p>` : ''}
            `;
        }
    } catch (error) {
        console.error('Upload error:', error);
        statusContent.innerHTML = `
            <p>❌ Erreur de connexion:</p>
            <p>${error.message}</p>
            <p style="font-size: 0.875rem; color: #64748b;">Vérifiez que les services sont en ligne</p>
        `;
    }
}
