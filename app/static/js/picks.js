/* ─── LottoEdge Picks Page JS ─────────────────────────────────────────────── */

async function generatePicks() {
    const game = document.getElementById('gameSelect').value;
    const count = parseInt(document.getElementById('countSelect').value);
    const resultsEl = document.getElementById('picksResults');
    const riskPanel = document.getElementById('riskPanel');

    resultsEl.innerHTML = `
        <div class="card card-le text-center py-5">
            <div class="card-body">
                <div class="spinner-border text-warning mb-3"></div>
                <p class="text-secondary">Running analysis engine...</p>
            </div>
        </div>`;

    const payload = {
        game,
        count,
        include_era2: false,
        weight_frequency:   parseInt(document.getElementById('weight_frequency').value),
        weight_positional:  parseInt(document.getElementById('weight_positional').value),
        weight_cluster:     parseInt(document.getElementById('weight_cluster').value),
        weight_due_score:   parseInt(document.getElementById('weight_due_score').value),
        weight_momentum:    parseInt(document.getElementById('weight_momentum').value),
        weight_heat:        parseInt(document.getElementById('weight_heat').value),
        weight_group:       parseInt(document.getElementById('weight_group').value),
        weight_lstm:        parseInt(document.getElementById('weight_lstm').value),
        weight_ensemble:    parseInt(document.getElementById('weight_ensemble').value),
        weight_monte_carlo: parseInt(document.getElementById('weight_monte_carlo').value),
        weight_coverage:    parseInt(document.getElementById('weight_coverage').value),
    };

    try {
        const resp = await fetch('/api/picks/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const data = await resp.json();

        if (data.error) {
            resultsEl.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
            return;
        }

        renderPicks(data, resultsEl, game);
        renderRiskPanel(data.odds, game, riskPanel);
    } catch (e) {
        resultsEl.innerHTML = `<div class="alert alert-danger">Error: ${e.message}</div>`;
    }
}


function renderPicks(data, container, game) {
    const gameName = { lotto: 'Texas Lotto', twostep: 'Texas Two Step', powerball: 'Powerball' }[game];

    let html = `<div class="d-flex align-items-center justify-content-between mb-3">
        <h5 class="fw-bold mb-0">${gameName} — Top Picks</h5>
        <small class="text-secondary">${data.draws_used} draws analysed</small>
    </div>`;

    data.picks.forEach((pick, i) => {
        const rank = i + 1;
        const passClass = pick.passes_sum_gate ? 'text-success' : 'text-danger';
        const numBadges = pick.numbers.map(n => numberBadge(n, 'number-badge-lg')).join('');
        const bonusBadge = pick.bonus !== undefined
            ? `<span class="number-badge number-badge-bonus number-badge-lg ms-2">${pick.bonus}</span>`
            : '';

        html += `<div class="pick-card">
            <div class="d-flex align-items-center justify-content-between mb-2">
                <span class="pick-rank">#${rank}</span>
                <div class="d-flex align-items-center gap-2">
                    <span class="mono small text-secondary">Score: <span class="text-warning">${pick.composite_score}</span></span>
                    <span class="mono small text-secondary">Sum: <span class="${passClass}">${pick.sum_value}</span></span>
                    <span class="mono small text-secondary">${pick.odd}o/${pick.even}e · ${pick.high}h/${pick.low}l</span>
                </div>
            </div>
            <div class="d-flex align-items-center flex-wrap">
                ${numBadges}${bonusBadge}
            </div>`;

        if (pick.filter_notes && pick.filter_notes.length > 0) {
            html += `<div class="mt-2">
                ${pick.filter_notes.map(n => `<span class="badge bg-warning text-dark small me-1">${n}</span>`).join('')}
            </div>`;
        }
        html += `</div>`;
    });

    container.innerHTML = html;
}


function numberBadge(n, extraClass = '') {
    return `<span class="number-badge ${extraClass}">${n}</span>`;
}


function renderRiskPanel(odds, game, panelEl) {
    if (!panelEl || !odds) return;
    panelEl.style.display = '';

    const riskContent = document.getElementById('riskContent');
    const gameName = { lotto: 'Texas Lotto', twostep: 'Texas Two Step', powerball: 'Powerball' }[game];
    const cost = { lotto: 1, twostep: 1, powerball: 2 }[game];

    let html = `<p class="text-secondary small mb-3">
        Exact probabilities for <strong>${gameName}</strong>. These are identical whether you use LottoEdge picks or a random quick pick.
        The lottery is a negative expected value game.
    </p>`;

    html += `<div class="table-responsive"><table class="table table-le table-sm">
        <thead><tr><th>Match</th><th>Prize</th><th>Odds</th><th>Probability</th></tr></thead><tbody>`;

    for (const tier of odds) {
        const prob = tier.probability;
        html += `<tr>
            <td>${tier.match}</td>
            <td>${tier.prize}</td>
            <td class="mono">${tier.odds}</td>
            <td class="mono">${(prob * 100).toExponential(4)}%</td>
        </tr>`;
    }
    html += `</tbody></table></div>`;

    html += `<div class="alert mt-3" style="background:rgba(248,113,113,.1);border:1px solid var(--accent-rose);border-radius:8px;">
        <i class="bi bi-exclamation-triangle me-2 text-danger"></i>
        <strong>Important:</strong> No statistical system can predict random lottery outcomes.
        LottoEdge identifies historical patterns for entertainment and analysis purposes.
        Never spend more than you can afford to lose.
    </div>`;

    riskContent.innerHTML = html;
}
