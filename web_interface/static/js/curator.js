// ...existing code...

async function loadVideos() {
    try {
        const response = await fetch(`/api/curator/videos?limit=200&offset=0`);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `HTTP ${response.status}`);
        }
        
        const videos = await response.json();
        displayVideos(videos);
        
    } catch (error) {
        console.error('Erreur chargement vidéos:', error);
        
        // ✅ FIX: Message clair selon l'erreur
        let errorMsg = '❌ Erreur: ';
        if (error.message.includes('Curator Bot non disponible')) {
            errorMsg += 'Curator Bot non démarré. Démarrez-le avec: cd curator_bot && python3 curator_bot.py';
        } else if (error.message.includes('503')) {
            errorMsg += 'Service Curator non accessible. Vérifiez qu\'il tourne sur le port 5061.';
        } else {
            errorMsg += error.message;
        }
        
        videosGrid.innerHTML = `<p style="color: var(--error);">${errorMsg}</p>`;
    }
}

async function loadCategories() {
    try {
        const response = await fetch('/api/curator/categories');
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `HTTP ${response.status}`);
        }
        
        const categories = await response.json();
        displayCategories(categories);
        
    } catch (error) {
        console.error('Erreur chargement catégories:', error);
        
        // ✅ FIX: Message clair
        if (error.message.includes('Curator Bot non disponible')) {
            console.warn('Curator Bot non démarré - catégories non disponibles');
        }
    }
}

// ...existing code...