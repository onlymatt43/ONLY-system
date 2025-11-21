const MONETIZER_API = window.location.origin; // Same origin as public interface

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadTokens();
    setupCreateForm();
});

// Load tokens from API
async function loadTokens() {
    const tokensGrid = document.getElementById('tokensGrid');
    
    if (!tokensGrid) {
        console.error('tokensGrid element not found');
        return;
    }

    try {
        tokensGrid.innerHTML = '<p class="loading">Loading tokens...</p>';
        
        const response = await fetch(`${MONETIZER_API}/api/tokens`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        const tokens = data.tokens || [];
        
        if (tokens.length === 0) {
            tokensGrid.innerHTML = '<p class="no-tokens">No tokens yet. Create your first one!</p>';
            return;
        }
        
        tokensGrid.innerHTML = tokens.map(token => createTokenCard(token)).join('');
        
    } catch (error) {
        console.error('Failed to load tokens:', error);
        tokensGrid.innerHTML = '<p class="error">Failed to load tokens. Please try again.</p>';
    }
}

// Create token card HTML
function createTokenCard(token) {
    const expiryDate = new Date(token.expires_at);
    const isExpired = expiryDate < new Date();
    const daysLeft = Math.ceil((expiryDate - new Date()) / (1000 * 60 * 60 * 24));
    
    return `
        <div class="token-card ${isExpired ? 'expired' : ''}">
            <div class="token-header">
                <span class="token-code">${token.code}</span>
                <span class="token-badge ${token.access_level}">${token.access_level.toUpperCase()}</span>
            </div>
            
            <div class="token-details">
                <p class="token-title">${token.title || 'Untitled Token'}</p>
                ${token.video_id ? `<p class="token-video">Video: ${token.video_id}</p>` : ''}
                <p class="token-expiry ${isExpired ? 'expired' : ''}">
                    ${isExpired ? '⚠️ Expired' : `✅ ${daysLeft} days left`}
                </p>
            </div>
            
            <div class="token-actions">
                <button onclick="copyToken('${token.code}')" class="btn-copy">Copy Code</button>
                ${!isExpired ? `<button onclick="revokeToken('${token.token}')" class="btn-revoke">Revoke</button>` : ''}
            </div>
        </div>
    `;
}

// Setup create token form
function setupCreateForm() {
    const form = document.getElementById('createTokenForm');
    
    if (!form) {
        console.error('createTokenForm not found');
        return;
    }
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(form);
        const data = {
            title: formData.get('title'),
            access_level: formData.get('access_level'),
            duration_days: parseInt(formData.get('duration_days')),
            video_id: formData.get('video_id') || null
        };
        
        try {
            const response = await fetch(`${MONETIZER_API}/api/tokens/mint`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const result = await response.json();
            
            alert(`✅ Token created!\nCode: ${result.code}\n\nCopied to clipboard.`);
            navigator.clipboard.writeText(result.code);
            
            form.reset();
            loadTokens(); // Reload list
            
        } catch (error) {
            console.error('Failed to create token:', error);
            alert('❌ Failed to create token. Check console for details.');
        }
    });
}

// Copy token to clipboard
function copyToken(code) {
    navigator.clipboard.writeText(code);
    alert(`✅ Token copied: ${code}`);
}

// Revoke token
async function revokeToken(token) {
    if (!confirm('Are you sure you want to revoke this token?')) {
        return;
    }
    
    try {
        const response = await fetch(`${MONETIZER_API}/api/tokens/revoke`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        alert('✅ Token revoked');
        loadTokens(); // Reload list
        
    } catch (error) {
        console.error('Failed to revoke token:', error);
        alert('❌ Failed to revoke token');
    }
}
