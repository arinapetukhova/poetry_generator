const API_BASE = 'https://poetry-generator-ku0q.onrender.com';

const generateButton = document.getElementById('generateButton');
const generateQuery = document.getElementById('generateQuery');
const generateTopK = document.getElementById('generateTopK');
const generateResults = document.getElementById('generateResults');

async function generateLyrics() {
    const query = generateQuery.value.trim();
    
    if (!query) {
        showError('Please describe the song you want to generate');
        return;
    }
    
    if (query.length < 10) {
        showError('Please provide a more detailed description (at least 10 characters)');
        return;
    }
    
    const topK = parseInt(generateTopK.value);
    
    setLoadingState(true);
    
    try {
        console.log('Sending request to:', `${API_BASE}/generate`);
        
        const response = await fetch(`${API_BASE}/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                top_k: topK
            })
        });
        
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        displayGeneratedLyrics(data);
        
    } catch (error) {
        console.error('Generation error:', error);
        showError(`Failed to generate lyrics: ${error.message}`);
    } finally {
        setLoadingState(false);
    }
}

function displayGeneratedLyrics(data) {

    if (data.reasoning) {
        html = `
            <div class="result-item reasoning-result">
                <div class="result-header">
                    <h3>🤔 AI Reasoning Process</h3>
                </div>
                <div class="reasoning-content">${formatReasoning(data.reasoning)}</div>
            </div>
        `;
    }
    
    html += `
        <div class="result-item lyrics-result">
            <div class="result-header">
                <h3>🎵 Your Generated Lyrics</h3>
            </div>
            <div class="lyrics-content">${formatLyrics(data.lyrics)}</div>
        </div>
        
        <div class="result-item context-result">
            <div class="result-header">
                <h3>📚 Musical Inspiration Used</h3>
                <span class="similarity-badge">${data.context.split('### Example').length - 1} examples analyzed</span>
            </div>
            <div class="result-content">
                ${formatContext(data.context)}
            </div>
        </div>
    `;
    
    generateResults.innerHTML = html;
    
    generateResults.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function formatReasoning(reasoning) {
    return escapeHtml(reasoning)
        .replace(/\n\n/g, '<br><br>')
        .replace(/\n/g, '<br>')
        .replace(/(\*\*(.*?)\*\*)/g, '<strong>$2</strong>')
        .replace(/(\*(.*?)\*)/g, '<em>$2</em>');
}

function formatLyrics(lyrics) {
    return escapeHtml(lyrics)
        .replace(/\n\n/g, '<br><br>')
        .replace(/\n/g, '<br>')
        .replace(/(\[.*?\])/g, '<em>$1</em>')
        .replace(/(Verse \d+|Chorus|Bridge|Outro)/g, '<strong>$1</strong>');
}

function formatContext(context) {
    const examples = context.split('### Example');
    let html = '';
    
    examples.forEach((example, index) => {
        if (index === 0) return;
        
        const lines = example.split('\n');
        const header = lines[0]?.trim() || `Example ${index}`;
        const content = lines.slice(1).join('\n').trim();
        
        if (content) {
            html += `
                <div class="context-item">
                    <div class="context-header">
                        <span>${header}</span>
                    </div>
                    <div class="context-text">${escapeHtml(content)}</div>
                </div>
            `;
        }
    });
    
    return html || '<p>No context examples available.</p>';
}

function setLoadingState(isLoading) {
    const buttonText = generateButton.querySelector('.button-text');
    const spinner = generateButton.querySelector('.loading-spinner');
    
    if (isLoading) {
        buttonText.textContent = 'Generating...';
        spinner.style.display = 'inline-block';
        generateButton.disabled = true;
        
        generateResults.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <h3>Creating Your Lyrics</h3>
                <p>Searching musical database and generating original content...</p>
                <p>This usually takes 10-20 seconds</p>
            </div>
        `;
    } else {
        buttonText.textContent = 'Generate Lyrics';
        spinner.style.display = 'none';
        generateButton.disabled = false;
    }
}

function showError(message) {
    generateResults.innerHTML = `
        <div class="error">
            <h3>❌ Error</h3>
            <p>${escapeHtml(message)}</p>
            <button onclick="clearError()" class="retry-button">Try Again</button>
        </div>
    `;
}

function clearError() {
    generateResults.innerHTML = `
        <div class="welcome-message">
            <h3>🎶 Create Original Lyrics</h3>
            <p>Describe the genre, artist, or theme you want to emulate, and AI will generate unique lyrics inspired by real musical examples from the database.</p>
            <div class="features">
                <div class="feature">
                    <strong>🎵 Style Matching</strong>
                    <p>Finds similar musical patterns and structures</p>
                </div>
                <div class="feature">
                    <strong>📝 Original Content</strong>
                    <p>Creates new lyrics without copying texts from references</p>
                </div>
                <div class="feature">
                    <strong>🎼 Professional Quality</strong>
                    <p>16-24 line songs with proper structure</p>
                </div>
            </div>
        </div>
    `;
}

function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

generateQuery.addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && e.ctrlKey) {
        generateLyrics();
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const welcomeMessage = document.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.style.cursor = 'pointer';
        welcomeMessage.addEventListener('click', function() {
            generateQuery.focus();
        });
    }
});