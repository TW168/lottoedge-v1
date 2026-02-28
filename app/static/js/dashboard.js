/* ─── LottoEdge Dashboard JS ──────────────────────────────────────────────── */

const CHART_DEFAULTS = {
    color: '#e8eaed',
    gridColor: 'rgba(255,255,255,0.08)',
    fontMono: "'JetBrains Mono', monospace",
    accent: {
        gold:    '#f5c842',
        emerald: '#34d399',
        rose:    '#f87171',
        blue:    '#60a5fa',
        purple:  '#a78bfa',
        amber:   '#fbbf24',
    },
    heat: {
        cold:    '#3b82f6',
        cool:    '#6366f1',
        neutral: '#8b5cf6',
        warm:    '#f59e0b',
        hot:     '#ef4444',
    },
};

Chart.defaults.color = CHART_DEFAULTS.color;
Chart.defaults.borderColor = CHART_DEFAULTS.gridColor;
Chart.defaults.font.family = "'IBM Plex Sans', sans-serif";


/* ── Main loader ─────────────────────────────────────────────────────────── */

async function loadDashboard(game, includeEra2 = false) {
    try {
        const resp = await fetch(`/api/analysis/${game}?include_era2=${includeEra2}`);
        const data = await resp.json();
        if (!data || data.draws === 0) return;

        renderHeatmap(data.frequency, game);
        renderPositional(data.positional);
        renderPairs(data.clusters);
        renderSkipChart(data.frequency, game);
        renderSumChart(data.sum_range);
        renderBalance(data.balance);
        renderGroupChart(data.groups);
    } catch (e) {
        console.error('Dashboard load error:', e);
    }
}


/* ── Heatmap ─────────────────────────────────────────────────────────────── */

function heatColor(classification, dueScore) {
    if (classification === 'hot')     return CHART_DEFAULTS.heat.hot;
    if (classification === 'cold')    return CHART_DEFAULTS.heat.cold;
    if (classification === 'overdue') return CHART_DEFAULTS.heat.warm;
    return CHART_DEFAULTS.heat.neutral;
}

function renderHeatmap(freqData, game) {
    const container = document.getElementById('heatmapContainer');
    if (!container || !freqData) return;

    container.innerHTML = '';
    const poolMax = game === 'lotto' ? 54 : game === 'twostep' ? 35 : 69;

    for (let n = 1; n <= poolMax; n++) {
        const fd = freqData[n] || {};
        const cls = fd.classification || 'neutral';
        const color = heatColor(cls, fd.due_score);
        const badge = document.createElement('div');
        badge.className = 'number-badge';
        badge.style.borderColor = color;
        badge.style.color = color;
        badge.style.backgroundColor = hexToRgba(color, 0.12);
        badge.textContent = n;
        badge.title = `#${n} | ${cls} | heat: ${fd.heat_score?.toFixed(1) || 0} | skip: ${fd.current_skip || 0}/${fd.avg_skip?.toFixed(1) || 0}`;
        container.appendChild(badge);
    }
}

function hexToRgba(hex, alpha) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r},${g},${b},${alpha})`;
}


/* ── Positional leaders table ────────────────────────────────────────────── */

function renderPositional(posData) {
    const container = document.getElementById('positionalTable');
    if (!container || !posData?.leaders) return;

    const leaders = posData.leaders;
    const positions = Object.keys(leaders).map(Number).sort((a, b) => a - b);

    let html = '<table class="table table-le table-sm mb-0"><thead><tr>';
    html += '<th>Pos</th>';
    for (let i = 1; i <= 5; i++) html += `<th>#${i}</th>`;
    html += '</tr></thead><tbody>';

    for (const pos of positions) {
        html += `<tr><td class="text-secondary">P${pos}</td>`;
        const topNums = leaders[pos] || [];
        for (const entry of topNums.slice(0, 5)) {
            html += `<td><span class="number-badge" style="width:32px;height:32px;font-size:.75rem">${entry.number}</span> <small class="text-secondary">${entry.count}</small></td>`;
        }
        const pad = 5 - topNums.length;
        for (let i = 0; i < pad; i++) html += '<td>—</td>';
        html += '</tr>';
    }

    html += '</tbody></table>';
    container.innerHTML = html;
}


/* ── Top pairs ───────────────────────────────────────────────────────────── */

function renderPairs(clusterData) {
    const container = document.getElementById('pairsContainer');
    if (!container || !clusterData?.pairs) return;

    const pairs = clusterData.pairs.slice(0, 12);
    let html = '';
    for (const p of pairs) {
        const aff = p.affinity;
        const color = aff >= 1.5 ? CHART_DEFAULTS.heat.hot : aff >= 1.0 ? CHART_DEFAULTS.heat.warm : CHART_DEFAULTS.heat.neutral;
        html += `<div class="d-flex align-items-center justify-content-between mb-2">
            <div>
                <span class="number-badge" style="border-color:${color};color:${color}">${p.pair[0]}</span>
                <span class="number-badge" style="border-color:${color};color:${color}">${p.pair[1]}</span>
            </div>
            <div class="text-end">
                <span class="mono small text-secondary">${p.count}x</span>
                <span class="mono small ms-2" style="color:${color}">×${aff}</span>
            </div>
        </div>`;
    }
    container.innerHTML = html || '<p class="text-secondary small">No pair data yet.</p>';
}


/* ── Skip chart ──────────────────────────────────────────────────────────── */

function renderSkipChart(freqData, game) {
    const canvas = document.getElementById('skipChart');
    if (!canvas || !freqData) return;

    const poolMax = game === 'lotto' ? 54 : game === 'twostep' ? 35 : 69;
    const labels = [], currentSkips = [], avgSkips = [];

    // Show top 20 by due score
    const sorted = Object.entries(freqData)
        .sort(([, a], [, b]) => (b.due_score || 0) - (a.due_score || 0))
        .slice(0, 25);

    for (const [num, fd] of sorted) {
        labels.push(num);
        currentSkips.push(fd.current_skip || 0);
        avgSkips.push(+(fd.avg_skip || 0).toFixed(1));
    }

    destroyChart('skipChart');
    new Chart(canvas, {
        type: 'bar',
        data: {
            labels,
            datasets: [
                {
                    label: 'Current Skip',
                    data: currentSkips,
                    backgroundColor: CHART_DEFAULTS.accent.amber + '99',
                    borderColor: CHART_DEFAULTS.accent.amber,
                    borderWidth: 1,
                },
                {
                    label: 'Avg Skip',
                    data: avgSkips,
                    type: 'line',
                    borderColor: CHART_DEFAULTS.accent.rose,
                    borderWidth: 2,
                    pointRadius: 3,
                    fill: false,
                    tension: 0.3,
                },
            ],
        },
        options: chartOptions('Skip (draws since last appearance)', 'Number'),
    });
}


/* ── Sum histogram ───────────────────────────────────────────────────────── */

function renderSumChart(sumData) {
    const canvas = document.getElementById('sumChart');
    if (!canvas || !sumData?.histogram) return;

    const { counts, edges } = sumData.histogram;
    const labels = edges.slice(0, -1).map((e, i) => `${Math.round(e)}–${Math.round(edges[i + 1])}`);
    const p15 = sumData.p15;
    const p85 = sumData.p85;

    const bgColors = edges.slice(0, -1).map((e, i) => {
        const mid = (e + edges[i + 1]) / 2;
        return mid >= p15 && mid <= p85
            ? CHART_DEFAULTS.accent.emerald + 'aa'
            : CHART_DEFAULTS.accent.rose + '55';
    });

    destroyChart('sumChart');
    new Chart(canvas, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Draws',
                data: counts,
                backgroundColor: bgColors,
                borderWidth: 0,
            }],
        },
        options: {
            ...chartOptions('Frequency', 'Sum Range'),
            plugins: {
                ...chartOptions().plugins,
                annotation: {
                    annotations: {
                        p15Line: {
                            type: 'line',
                            xMin: labels.findIndex(l => parseFloat(l) >= p15),
                            xMax: labels.findIndex(l => parseFloat(l) >= p15),
                            borderColor: CHART_DEFAULTS.accent.emerald,
                            borderWidth: 2,
                            label: { content: '15th %', enabled: true },
                        },
                    }
                }
            }
        },
    });
}


/* ── Balance display ─────────────────────────────────────────────────────── */

function renderBalance(balData) {
    const container = document.getElementById('balanceContainer');
    if (!container || !balData) return;

    const preferred_oe = balData.preferred_oe || [];
    let html = '<div class="row g-2">';

    html += '<div class="col-6"><h6 class="small text-secondary text-uppercase mb-2">Odd/Even</h6>';
    for (const [key, val] of Object.entries(balData.odd_even || {}).slice(0, 6)) {
        const isPreferred = preferred_oe.includes(key);
        html += `<div class="d-flex justify-content-between align-items-center mb-1">
            <span class="small ${isPreferred ? 'text-emerald fw-bold' : 'text-secondary'}">${key}</span>
            <div class="d-flex align-items-center gap-2">
                <div class="progress" style="width:60px;height:6px;background:var(--bg-tertiary)">
                    <div class="progress-bar" style="width:${val.pct}%;background:${isPreferred ? 'var(--accent-emerald)' : 'var(--border-subtle)'}"></div>
                </div>
                <span class="mono small text-secondary">${val.pct}%</span>
            </div>
        </div>`;
    }
    html += '</div>';

    html += '<div class="col-6"><h6 class="small text-secondary text-uppercase mb-2">High/Low</h6>';
    for (const [key, val] of Object.entries(balData.high_low || {}).slice(0, 6)) {
        const isPreferred = (balData.preferred_hl || []).includes(key);
        html += `<div class="d-flex justify-content-between align-items-center mb-1">
            <span class="small ${isPreferred ? 'text-amber fw-bold' : 'text-secondary'}">${key}</span>
            <div class="d-flex align-items-center gap-2">
                <div class="progress" style="width:60px;height:6px;background:var(--bg-tertiary)">
                    <div class="progress-bar" style="width:${val.pct}%;background:${isPreferred ? 'var(--accent-amber)' : 'var(--border-subtle)'}"></div>
                </div>
                <span class="mono small text-secondary">${val.pct}%</span>
            </div>
        </div>`;
    }
    html += '</div></div>';
    container.innerHTML = html;
}


/* ── Group chart ─────────────────────────────────────────────────────────── */

function renderGroupChart(groupData) {
    const canvas = document.getElementById('groupChart');
    if (!canvas || !groupData?.groups) return;

    const labels = groupData.groups;
    const counts = labels.map(g => groupData.group_freq?.[g] || 0);

    destroyChart('groupChart');
    new Chart(canvas, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Appearances',
                data: counts,
                backgroundColor: [
                    CHART_DEFAULTS.accent.gold,
                    CHART_DEFAULTS.accent.emerald,
                    CHART_DEFAULTS.accent.blue,
                    CHART_DEFAULTS.accent.purple,
                    CHART_DEFAULTS.accent.amber,
                    CHART_DEFAULTS.accent.rose,
                    '#7dd3fc',
                ].slice(0, labels.length),
                borderWidth: 0,
                borderRadius: 4,
            }],
        },
        options: chartOptions('Appearances', 'Number Group'),
    });
}


/* ── Chart helpers ───────────────────────────────────────────────────────── */

function chartOptions(yLabel = '', xLabel = '') {
    return {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: { display: false },
        },
        scales: {
            x: {
                ticks: {
                    color: CHART_DEFAULTS.color,
                    font: { family: CHART_DEFAULTS.fontMono, size: 10 },
                    maxTicksLimit: 20,
                },
                grid: { color: CHART_DEFAULTS.gridColor },
                title: { display: !!xLabel, text: xLabel, color: '#9aa0a8' },
            },
            y: {
                ticks: {
                    color: CHART_DEFAULTS.color,
                    font: { family: CHART_DEFAULTS.fontMono, size: 10 },
                },
                grid: { color: CHART_DEFAULTS.gridColor },
                title: { display: !!yLabel, text: yLabel, color: '#9aa0a8' },
            },
        },
    };
}

const _chartInstances = {};

function destroyChart(id) {
    if (_chartInstances[id]) {
        _chartInstances[id].destroy();
    }
}

// Patch Chart constructor to track instances
const _OrigChart = Chart;
window.Chart = function(el, config) {
    const id = typeof el === 'string' ? el : el.id;
    const inst = new _OrigChart(el, config);
    if (id) _chartInstances[id] = inst;
    return inst;
};
Object.assign(window.Chart, _OrigChart);
