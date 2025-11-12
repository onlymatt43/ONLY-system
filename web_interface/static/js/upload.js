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
        
        const result = await response.json();
        
        if (result.ok) {
            statusContent.innerHTML = `
                <p>✅ Vidéo ajoutée avec succès!</p>
                <p><strong>Job ID:</strong> ${result.enqueued_job_id}</p>
                <p>La vidéo sera traitée automatiquement.</p>
                <a href="/jobs" class="btn btn-primary">Voir les jobs</a>
            `;
        } else {
            statusContent.innerHTML = `
                <p>⚠️ ${result.message || 'Erreur inconnue'}</p>
                ${result.job_id ? `<p>Job existant: #${result.job_id}</p>` : ''}
            `;
        }
    } catch (error) {
        statusContent.innerHTML = `
            <p>❌ Erreur: ${error.message}</p>
        `;
    }
}
