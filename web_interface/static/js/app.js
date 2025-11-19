// ...existing code...

async function uploadVideo() {
    const url = document.getElementById('videoUrl').value;
    const title = document.getElementById('videoTitle').value;
    
    if (!url) {
        alert('⚠️ URL vidéo requise');
        return;
    }
    
    // Show loading
    const button = document.querySelector('button[onclick="uploadVideo()"]');
    const originalText = button.innerHTML;
    button.innerHTML = '⏳ Traitement...';
    button.disabled = true;
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({url, title})
        });
        
        // ✅ FIX: Meilleure gestion erreurs
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.ok) {
            alert(`✅ Job créé: ${data.job_id}`);
            document.getElementById('videoUrl').value = '';
            document.getElementById('videoTitle').value = '';
            loadJobs(); // Refresh jobs list
        } else {
            throw new Error(data.message || 'Erreur inconnue');
        }
        
    } catch (error) {
        console.error('Upload error:', error);
        
        // ✅ FIX: Message d'erreur détaillé
        let errorMsg = '❌ Erreur: ';
        if (error.message.includes('Gateway non disponible')) {
            errorMsg += 'Gateway non démarré. Lance ./start_all.sh';
        } else if (error.message.includes('timeout')) {
            errorMsg += 'Gateway timeout. Vérifie les logs.';
        } else {
            errorMsg += error.message;
        }
        
        alert(errorMsg);
        
    } finally {
        // Restore button
        button.innerHTML = originalText;
        button.disabled = false;
    }
}

// ...existing code...