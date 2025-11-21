async function mintToken() {
    const title = document.getElementById('token-title').value.trim();
    const duration = parseInt(document.getElementById('token-duration').value);
    const value = parseInt(document.getElementById('token-value').value);
    
    if (!title) {
        alert('Veuillez entrer un titre');
        return;
    }
    
    const resultDiv = document.getElementById('mint-result');
    resultDiv.classList.remove('hidden');
    resultDiv.innerHTML = '<p>⏳ Création du token...</p>';
    
    try {
        const response = await fetch('/api/monetizer/mint', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: title,
                duration_min: duration,
                value_cents: value,
                meta: {}
            })
        });
        
            if (!response.ok) {
                // Try to surface Monetizer error details to the user
                let errText = '';
                try {
                    const errBody = await response.json();
                    errText = errBody.error || errBody.detail || JSON.stringify(errBody);
                } catch (e) {
                    errText = await response.text();
                }
                // Show error inline
                const errDiv = document.getElementById('mintError');
                if (errDiv) {
                    errDiv.classList.remove('hidden');
                    errDiv.textContent = `Erreur Monetizer: ${errText || response.status}`;
                }
                throw new Error(`HTTP ${response.status} - ${errText}`);
            }

            const result = await response.json();
            if (result && result.ok === false) {
                const errDiv = document.getElementById('mintError');
                if (errDiv) {
                    errDiv.classList.remove('hidden');
                    errDiv.textContent = result.error || result.detail || JSON.stringify(result);
                }
                throw new Error('Mint failed');
            }
        
        if (result.ok) {
            resultDiv.innerHTML = `
                <div style="background: var(--bg-card); padding: 1.5rem; border-radius: 0.5rem; border: 1px solid var(--success);">
                    <h4 style="color: var(--success); margin-bottom: 1rem;">✅ Token créé!</h4>
                    <p><strong>Code:</strong> ${result.code}</p>
                    <p><strong>Token:</strong> <code style="font-size: 0.85rem; word-break: break-all;">${result.token}</code></p>
                    <p><strong>Unlock URL:</strong><br><a href="${result.unlock_url}" target="_blank" style="color: var(--primary);">${result.unlock_url}</a></p>
                    <p><strong>Durée:</strong> ${result.duration_min} minutes</p>
                </div>
            `;
            
            // Recharger la liste des tokens
            loadTokens();
            
            // Reset form
            document.getElementById('token-title').value = '';
            document.getElementById('token-value').value = '1000';
        } else {
            resultDiv.innerHTML = `<p style="color: var(--error);">❌ Erreur: ${result.error || 'Inconnue'}</p>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<p style="color: var(--error);">❌ Erreur: ${error.message}</p>`;
        const errDiv = document.getElementById('mintError');
        if (errDiv && !errDiv.textContent) {
            errDiv.classList.remove('hidden');
            errDiv.textContent = error.message || 'Erreur inconnue';
        }
    }
}

async function loadTokens() {
    try {
        const response = await fetch('/api/monetizer/tokens');
        const data = await response.json();
        
        // ✅ FIX: Extract tokens array from response
        const tokens = Array.isArray(data) ? data : (data.tokens || []);
        
        tokensGrid.innerHTML = '';
        
        if (tokens.length === 0) {
            tokensGrid.innerHTML = '<p style="color: var(--text-muted);">Aucun token créé</p>';
            return;
        }
        
        tokens.forEach(token => {
            const card = document.createElement('div');
            card.className = 'service-card';
            card.style.textAlign = 'left';
            
            const statusColors = {
                fresh: 'var(--primary)',
                activated: 'var(--success)',
                expired: 'var(--error)',
                revoked: 'var(--error)'
            };
            
            // Utiliser les noms de colonnes de la base de données
            const codeVisible = token.title || token.code_visible || 'N/A';
            const tokenStatus = token.status || 'unknown';
            const expiresAt = token.expires_at ? `Expire: ${new Date(token.expires_at).toLocaleString()}` : 'Pas encore activé';
            const unlockUrl = token.unlock_url || '#';

            card.innerHTML = `
                <h4 style="margin-bottom: 0.5rem;">${codeVisible}</h4>
                <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.5rem;">
                    <span style="color: ${statusColors[tokenStatus] || 'var(--text)'};">
                        ${tokenStatus}
                    </span>
                </p>
                <p style="font-size: 0.8rem; color: var(--text-muted);">
                    ${expiresAt}
                </p>
                <a href="${unlockUrl}" target="_blank" 
                   style="display: inline-block; margin-top: 0.5rem; color: var(--primary); font-size: 0.85rem;">
                    Voir QR
                </a>
            `;
            
            tokensGrid.appendChild(card);
        });
        
    } catch (error) {
        console.error('Erreur chargement tokens:', error);
        tokensGrid.innerHTML = '<p style="color: var(--error);">Erreur de chargement des tokens</p>';
    }
}

// Chargement initial
document.addEventListener('DOMContentLoaded', loadTokens);

// Auto-refresh toutes les 10 secondes
setInterval(loadTokens, 10000);
