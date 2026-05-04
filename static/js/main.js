// =============================================
// StockAI Pro - Main JavaScript (FIXED)
// =============================================

let priceChart = null;
let predChart = null;
let compareChart = null;
let currentSymbol = 'AAPL';
let currentPeriod = '1mo';

// ========== INITIALIZATION ==========
document.addEventListener('DOMContentLoaded', () => {
    updateClock();
    setInterval(updateClock, 30000);
    loadTicker();
    setInterval(loadTicker, 60000);
    
    // Avatar dropdown
    const avatarBtn = document.getElementById('avatarBtn');
    const dropdown = document.getElementById('userDropdown');
    if (avatarBtn && dropdown) {
        avatarBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdown.classList.toggle('show');
        });
        document.addEventListener('click', () => dropdown.classList.remove('show'));
    }
    
    // Show initial page
    const page = document.body.getAttribute('data-page') || 'dashboard';
    showPage(page);
    
    // Setup all search inputs
    setupSearch('quickSearch', 'quickDrop');
    setupSearch('predictSymbol', 'predictDrop');
    setupSearch('insightSymbol', 'insightDrop');
    
    // Load ONLY ticker on dashboard, NOT chart
    if (page === 'dashboard') {
        // Don't auto-load chart - wait for user to click Analyze
    }
    
    // Auto-dismiss flash messages
    setTimeout(() => {
        document.querySelectorAll('.flash-msg').forEach(f => {
            f.style.opacity = '0';
            f.style.transition = 'opacity 0.3s';
            setTimeout(() => f.remove(), 300);
        });
    }, 5000);
});

// ========== NAVIGATION ==========
function showPage(page) {
    document.querySelectorAll('.side-link').forEach(l => l.classList.remove('active'));
    const link = document.querySelector(`[data-page="${page}"]`);
    if (link) link.classList.add('active');
    
    document.querySelectorAll('.page-section').forEach(s => s.classList.remove('active'));
    const section = document.getElementById(page + 'Section');
    if (section) section.classList.add('active');
}

// ========== CLOCK ==========
function updateClock() {
    const el = document.getElementById('liveClock');
    if (!el) return;
    const now = new Date();
    el.textContent = now.toLocaleString('en-US', {
        weekday: 'short', month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit'
    });
}

// ========== MARKET TICKER ==========
async function loadTicker() {
    try {
        const res = await fetch('/api/market/indices');
        const data = await res.json();
        const track = document.getElementById('tickerTrack');
        if (!track) return;
        
        let html = '';
        for (const [name, info] of Object.entries(data)) {
            const cls = info.change >= 0 ? 'up' : 'down';
            const arrow = info.change >= 0 ? '▲' : '▼';
            html += `<span class="ticker-item"><strong>${name}</strong> ${info.price} <span class="${cls}">${arrow} ${Math.abs(info.change).toFixed(2)}%</span></span>`;
        }
        track.innerHTML = html + html;
    } catch (e) {}
}

// ========== TOAST ==========
function showToast(msg, type = 'info') {
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        container.id = 'toastContainer';
        document.body.appendChild(container);
    }
    const t = document.createElement('div');
    t.className = `toast ${type}`;
    t.textContent = msg;
    container.appendChild(t);
    setTimeout(() => { t.style.opacity = '0'; t.style.transition = 'all 0.3s'; setTimeout(() => t.remove(), 300); }, 3000);
}

// ========== HELPERS ==========
function fmtPrice(v) {
    if (v === null || v === undefined || isNaN(v)) return '--';
    return '$' + Number(v).toFixed(2);
}

function fmtVol(v) {
    if (!v || isNaN(v)) return '--';
    if (v >= 1e9) return (v/1e9).toFixed(1) + 'B';
    if (v >= 1e6) return (v/1e6).toFixed(1) + 'M';
    return v.toLocaleString();
}

function debounce(fn, d) { let t; return function(...a) { clearTimeout(t); t = setTimeout(() => fn.apply(this, a), d); }; }

// ========== SEARCH (FIXED - No Auto-load) ==========
function setupSearch(inputId, dropId) {
    const input = document.getElementById(inputId);
    const drop = document.getElementById(dropId);
    if (!input || !drop) return;
    
    input.addEventListener('input', debounce(async function() {
        const q = this.value.trim().toUpperCase();
        if (q.length < 1) { drop.classList.remove('show'); return; }
        
        try {
            const res = await fetch('/api/stock/search', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({query: q})
            });
            const data = await res.json();
            
            if (data.results.length > 0) {
                drop.innerHTML = data.results.map(s => `
                    <div class="drop-item" data-symbol="${s.symbol}" style="cursor:pointer;padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.05);">
                        <strong>${s.symbol}</strong> - ${s.name}
                    </div>
                `).join('');
                
                drop.querySelectorAll('.drop-item').forEach(item => {
                    item.addEventListener('click', function(e) {
                        e.stopPropagation();
                        const symbol = this.dataset.symbol;
                        input.value = symbol;
                        drop.classList.remove('show');
                        currentSymbol = symbol;
                        // NO AUTO-LOAD - user must click button
                    });
                });
                drop.classList.add('show');
            } else {
                drop.classList.remove('show');
            }
        } catch (e) {}
    }, 300));
    
    // Close dropdown
    document.addEventListener('click', (e) => {
        if (!e.target.closest(`#${inputId}`) && !e.target.closest(`#${dropId}`)) {
            drop.classList.remove('show');
        }
    });
    
    // Enter key
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            drop.classList.remove('show');
            currentSymbol = input.value.trim().toUpperCase() || 'AAPL';
            if (inputId === 'quickSearch') quickAnalyze();
            if (inputId === 'insightSymbol') generateInsights();
        }
    });
}

// ========== DASHBOARD (FIXED - Only on button click) ==========
async function quickAnalyze() {
    const input = document.getElementById('quickSearch');
    const sym = input?.value?.trim().toUpperCase() || 'AAPL';
    currentSymbol = sym;
    document.getElementById('quickDrop')?.classList.remove('show');
    
    showToast('Loading ' + sym + ' data...', 'info');
    await loadChart(sym);
}

async function loadChart(symbol) {
    if (!symbol) symbol = 'AAPL';
    
    try {
        // Get quote
        const qRes = await fetch('/api/stock/quote', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({symbol})
        });
        const qData = await qRes.json();
        
        if (qData.success && qData.data) {
            const q = qData.data;
            document.getElementById('statPrice').textContent = fmtPrice(q.price);
            const chg = document.getElementById('statChange');
            if (chg) {
                chg.textContent = (q.change >= 0 ? '+' : '') + q.change + '%';
                chg.className = 'stat-change ' + (q.change >= 0 ? 'up' : 'down');
            }
            document.getElementById('statHigh').textContent = fmtPrice(q.high);
            document.getElementById('statLow').textContent = fmtPrice(q.low);
            document.getElementById('statVol').textContent = fmtVol(q.volume);
        }
        
        // Get history
        const hRes = await fetch('/api/stock/history', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({symbol, period: currentPeriod})
        });
        const hData = await hRes.json();
        
        if (hData.success && hData.data && hData.data.length > 0) {
            const ctx = document.getElementById('quickChart')?.getContext('2d');
            if (!ctx) return;
            
            if (priceChart) priceChart.destroy();
            
            const closes = hData.data.map(d => d.close);
            const labels = hData.data.map(d => {
                const date = new Date(d.date);
                return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            });
            
            priceChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels,
                    datasets: [{
                        label: symbol,
                        data: closes,
                        borderColor: '#6366f1',
                        backgroundColor: 'rgba(99,102,241,0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.3,
                        pointRadius: 0,
                        pointHoverRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { grid: {color:'rgba(255,255,255,0.03)'}, ticks: {color:'#64748b', maxTicksLimit:8} },
                        y: { grid: {color:'rgba(255,255,255,0.03)'}, ticks: {color:'#64748b', callback:v=>'$'+v.toFixed(2)} }
                    }
                }
            });
            
            showToast('✅ ' + symbol + ' data loaded', 'success');
        } else {
            showToast('No data available for ' + symbol, 'error');
        }
    } catch (e) {
        console.error('Chart error:', e);
        showToast('Error loading data', 'error');
    }
}

function changePeriod(period) {
    currentPeriod = period;
    document.querySelectorAll('#dashboardSection .time-btn').forEach(b => b.classList.remove('active'));
    if (event && event.target) event.target.classList.add('active');
    if (currentSymbol) quickAnalyze();
}

// ========== PREDICTION ==========
async function runPrediction() {
    const sym = document.getElementById('predictSymbol')?.value?.trim().toUpperCase() || 'AAPL';
    const days = parseInt(document.getElementById('predictDays')?.value) || 30;
    
    showToast('🤖 Training AI on ' + sym + '... (20-30 sec)', 'info');
    
    try {
        const res = await fetch('/api/predict', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({symbol: sym, days})
        });
        const data = await res.json();
        
        if (!data.success) {
            showToast(data.error || 'Prediction failed', 'error');
            return;
        }
        
        const ctx = document.getElementById('predChart')?.getContext('2d');
        if (!ctx) return;
        
        if (predChart) predChart.destroy();
        
        predChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.dates,
                datasets: [{
                    label: sym + ' Prediction',
                    data: data.predictions,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16,185,129,0.1)',
                    borderWidth: 2.5,
                    fill: true,
                    tension: 0.3,
                    pointRadius: 2,
                    pointBackgroundColor: '#10b981'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: {color:'#94a3b8'} } },
                scales: {
                    x: { grid: {color:'rgba(255,255,255,0.03)'}, ticks: {color:'#64748b', maxTicksLimit:10} },
                    y: { grid: {color:'rgba(255,255,255,0.03)'}, ticks: {color:'#64748b', callback:v=>'$'+v.toFixed(2)} }
                }
            }
        });
        
        document.getElementById('confTag').style.display = 'inline-block';
        document.getElementById('confVal').textContent = data.confidence + '%';
        
        document.getElementById('predSummary').innerHTML = `
            <div class="pred-item"><span class="label">Current</span><span class="value">${fmtPrice(data.current_price)}</span></div>
            <div class="pred-item"><span class="label">Target</span><span class="value">${fmtPrice(data.target_price)}</span></div>
            <div class="pred-item"><span class="label">Change</span><span class="value ${data.change_percent>=0?'up':'down'}">${data.change_percent>=0?'+':''}${data.change_percent.toFixed(2)}%</span></div>
            <div class="pred-item"><span class="label">Trend</span><span class="value ${data.trend==='Bullish'?'up':'down'}">${data.trend}</span></div>
        `;
        
        showToast('✅ Prediction ready!', 'success');
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}

// ========== INSIGHTS (FIXED) ==========
async function generateInsights() {
    const sym = document.getElementById('insightSymbol')?.value?.trim().toUpperCase() || 'AAPL';
    currentSymbol = sym;
    document.getElementById('insightDrop')?.classList.remove('show');
    
    showToast('🧠 Analyzing ' + sym + '...', 'info');
    
    // Show loading
    document.getElementById('recPanel').innerHTML = '<div style="text-align:center;padding:30px;"><div class="spinner"></div><p style="color:#94a3b8;margin-top:10px;">Analyzing...</p></div>';
    document.getElementById('signalsPanel').innerHTML = '';
    document.getElementById('summaryPanel').innerHTML = '';
    
    try {
        // Show stock info
        const qRes = await fetch('/api/stock/quote', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({symbol: sym})
        });
        const qData = await qRes.json();
        
        const infoDiv = document.getElementById('insightStockInfo');
        if (qData.success && qData.data && infoDiv) {
            infoDiv.style.display = 'block';
            const q = qData.data;
            document.getElementById('insightStockName').textContent = q.name + ' (' + sym + ')';
            document.getElementById('insightStockPrice').innerHTML = '<strong>$' + q.price?.toFixed(2) + '</strong> (' + (q.change>=0?'+':'') + q.change + '%)';
        }
        
        // Get insights from API
        const res = await fetch('/api/insights', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({symbol: sym})
        });
        const data = await res.json();
        
        console.log('Insights response:', data); // Debug
        
        if (!data.success) {
            document.getElementById('recPanel').innerHTML = '<p style="color:#ef4444;text-align:center;padding:20px;">❌ ' + (data.error || 'Failed') + '</p>';
            showToast(data.error || 'Could not analyze', 'error');
            return;
        }
        
        // Update RSI/Risk
        document.getElementById('insightRSI').textContent = 'RSI: ' + (data.rsi || '--');
        document.getElementById('insightRisk').textContent = 'Risk: ' + (data.risk || '--');
        
        // Recommendation
        const rec = data.recommendation || {action:'HOLD', color:'#f59e0b', confidence:50};
        document.getElementById('recPanel').innerHTML = `
            <div class="rec-box" style="border:2px solid ${rec.color}; background:${rec.color}15;">
                <div class="rec-action" style="color:${rec.color};">${rec.action}</div>
                <div class="rec-conf">Confidence: ${rec.confidence}%</div>
            </div>
        `;
        
        // Summary
        const summary = data.summary || {trend:'Neutral', emoji:'📊'};
        document.getElementById('summaryPanel').innerHTML = `
            <div style="text-align:center;padding:20px;">
                <div style="font-size:3em;">${summary.emoji}</div>
                <h3>${summary.trend}</h3>
                <p style="color:#94a3b8;">${sym} showing ${summary.trend.toLowerCase()} momentum</p>
            </div>
        `;
        
        // Signals
        const signals = data.signals || [];
        if (signals.length > 0) {
            document.getElementById('signalsPanel').innerHTML = signals.map(s => {
                const cls = s.type === 'positive' || s.type === 'opportunity' ? 'bullish' : 
                           s.type === 'warning' ? 'bearish' : 'neutral';
                return `<div class="signal-item ${cls}"><strong>${s.msg}</strong><small style="display:block;color:#94a3b8;">→ ${s.action}</small></div>`;
            }).join('');
        } else {
            document.getElementById('signalsPanel').innerHTML = '<p style="color:#94a3b8;text-align:center;">No significant signals</p>';
        }
        
        showToast('✅ Analysis complete!', 'success');
        
    } catch (e) {
        console.error('Insights error:', e);
        document.getElementById('recPanel').innerHTML = '<p style="color:#ef4444;text-align:center;padding:20px;">Error: ' + e.message + '</p>';
        showToast('Error: ' + e.message, 'error');
    }
}

// ========== COMPARE ==========
async function runCompare() {
    const symbols = [];
    for (let i = 1; i <= 4; i++) {
        const val = document.getElementById('comp'+i)?.value?.trim().toUpperCase();
        if (val) symbols.push(val);
    }
    
    if (symbols.length < 2) {
        showToast('Enter at least 2 stocks', 'error');
        return;
    }
    
    showToast('Comparing...', 'info');
    
    try {
        const res = await fetch('/api/compare', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({symbols})
        });
        const data = await res.json();
        
        const ctx = document.getElementById('compareChart')?.getContext('2d');
        if (!ctx) return;
        
        if (compareChart) compareChart.destroy();
        
        const colors = ['#6366f1', '#10b981', '#f59e0b', '#ef4444'];
        const datasets = Object.entries(data).map(([sym, info], i) => ({
            label: sym, data: info.normalized,
            borderColor: colors[i], backgroundColor: colors[i]+'20',
            borderWidth: 2, tension: 0.3, fill: true, pointRadius: 0
        }));
        
        compareChart = new Chart(ctx, {
            type: 'line',
            data: { labels: data[Object.keys(data)[0]]?.dates || [], datasets },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { labels: {color:'#94a3b8'} } },
                scales: {
                    x: { grid: {color:'rgba(255,255,255,0.03)'}, ticks: {color:'#64748b'} },
                    y: { grid: {color:'rgba(255,255,255,0.03)'}, ticks: {color:'#64748b', callback:v=>v.toFixed(1)+'%'} }
                }
            }
        });
        
        showToast('✅ Done!', 'success');
    } catch (e) {
        showToast('Error comparing', 'error');
    }
}

console.log('🚀 StockAI Pro Ready');