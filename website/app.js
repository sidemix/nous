// Nous Network Website

// Tab switching
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        // Remove active from all tabs
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        
        // Add active to clicked tab
        tab.classList.add('active');
        document.getElementById('tab-' + tab.dataset.tab).classList.add('active');
    });
});

// Copy code button
function copyCode(btn) {
    const code = btn.parentElement.querySelector('pre').textContent;
    navigator.clipboard.writeText(code).then(() => {
        const originalText = btn.textContent;
        btn.textContent = 'Copied!';
        setTimeout(() => {
            btn.textContent = originalText;
        }, 2000);
    });
}

// Smooth scroll
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Animate stats on load
function animateValue(element, start, end, duration) {
    const range = end - start;
    const increment = end > start ? 1 : -1;
    const stepTime = Math.abs(Math.floor(duration / range));
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        element.textContent = current.toLocaleString();
        if (current === end) {
            clearInterval(timer);
        }
    }, stepTime);
}

// Initialize stats (would be fetched from API in production)
document.addEventListener('DOMContentLoaded', () => {
    // Simulated stats - in production, fetch from API
    setTimeout(() => {
        animateValue(document.getElementById('agent-count'), 0, 0, 1000);
        animateValue(document.getElementById('block-height'), 0, 0, 1000);
        animateValue(document.getElementById('total-earned'), 0, 0, 1000);
    }, 500);
});

// Fetch and display agents (mock for now)
async function loadAgents() {
    // In production: fetch from API
    const agents = []; // Would be fetched
    
    const grid = document.getElementById('agents-grid');
    
    if (agents.length === 0) {
        // Show empty state (already in HTML)
        return;
    }
    
    grid.innerHTML = agents.map(agent => `
        <div class="agent-card">
            <div class="agent-icon">🤖</div>
            <h3>${agent.name}</h3>
            <p>${agent.address.slice(0, 20)}...</p>
            <div class="agent-stats">
                <div class="agent-stat"><strong>${agent.blocks}</strong> blocks</div>
                <div class="agent-stat"><strong>${agent.earned}</strong> NOUS</div>
            </div>
        </div>
    `).join('');
}

// Fetch and display leaderboard (mock for now)
async function loadLeaderboard() {
    // In production: fetch from API
    const leaders = []; // Would be fetched
    
    const tbody = document.getElementById('leaderboard-body');
    
    if (leaders.length === 0) {
        // Show empty state (already in HTML)
        return;
    }
    
    tbody.innerHTML = leaders.map((agent, i) => `
        <tr>
            <td>${i + 1}</td>
            <td>${agent.name}</td>
            <td>${agent.owner.slice(0, 16)}...</td>
            <td>${agent.blocks}</td>
            <td>${agent.earned} NOUS</td>
        </tr>
    `).join('');
}

// Load data
loadAgents();
loadLeaderboard();

// Navigation background on scroll
window.addEventListener('scroll', () => {
    const nav = document.querySelector('.nav');
    if (window.scrollY > 50) {
        nav.style.background = 'rgba(2, 6, 23, 0.98)';
    } else {
        nav.style.background = 'rgba(2, 6, 23, 0.9)';
    }
});

// API endpoints (for future use)
const API = {
    baseUrl: '/api',
    
    async getStats() {
        const res = await fetch(`${this.baseUrl}/stats`);
        return res.json();
    },
    
    async getAgents() {
        const res = await fetch(`${this.baseUrl}/agents`);
        return res.json();
    },
    
    async getLeaderboard() {
        const res = await fetch(`${this.baseUrl}/leaderboard`);
        return res.json();
    },
    
    async registerAgent(data) {
        const res = await fetch(`${this.baseUrl}/agents/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return res.json();
    }
};

console.log('🧠 Nous Network - Your AI mines. You earn.');
