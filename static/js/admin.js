document.addEventListener('DOMContentLoaded', () => {
    chargerStats();
    chargerHotesFiltre();
    chargerVisites();

    // Écouteurs pour le filtrage dynamique en direct
    document.getElementById('filtre-recherche').addEventListener('input', chargerVisites);
    document.getElementById('filtre-hote').addEventListener('change', chargerVisites);
});

async function chargerStats() {
    try {
        const res = await fetch('/api/admin/stats');
        if (res.ok) {
            const data = await res.json();
            document.getElementById('stat-aujourdhui').textContent = data.total_aujourdhui;
            document.getElementById('stat-sur-site').textContent = data.sur_site;
            document.getElementById('stat-recurrents').textContent = data.visiteurs_recurrents;
        }
    } catch (e) {
        console.error("Erreur chargement stats:", e);
    }
}

async function chargerHotesFiltre() {
    const select = document.getElementById('filtre-hote');
    try {
        const res = await fetch('/api/membres');
        if (res.ok) {
            const membres = await res.json();
            membres.forEach(m => {
                const opt = document.createElement('option');
                opt.value = m.id;
                opt.textContent = m.nom_complet;
                select.appendChild(opt);
            });
        }
    } catch (e) {
        console.error("Erreur hôtes:", e);
    }
}

async function chargerVisites() {
    const q = document.getElementById('filtre-recherche').value;
    const hoteId = document.getElementById('filtre-hote').value;
    const tbody = document.getElementById('table-visites-body');

    try {
        const url = new URL('/api/admin/visites', window.location.origin);
        if (q) url.searchParams.append('q', q);
        if (hoteId) url.searchParams.append('hote_id', hoteId);

        const res = await fetch(url);
        if (!res.ok) return;

        const visites = await res.json();
        tbody.innerHTML = '';

        if (visites.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">Aucune visite trouvée.</td></tr>';
            return;
        }

        visites.forEach(v => {
            const tr = document.createElement('tr');

            // Indicateur de visiteur récurrent
            let badgeRecurrent = '';
            if (v.total_visites_perso > 1) {
                badgeRecurrent = `<span class="badge bg-warning text-dark ms-1" title="Visiteur récurrent">${v.total_visites_perso} visites</span>`;
            }

            // Statut Présent / Parti
            const statut = v.heure_sortie 
                ? '<span class="badge bg-secondary">Parti</span>' 
                : '<span class="badge bg-success">Sur site</span>';

            tr.innerHTML = `
                <td><strong>${v.visiteur}</strong> ${badgeRecurrent}</td>
                <td>${v.telephone || '-'}</td>
                <td>${v.fonction || '-'}</td>
                <td>${v.hote}</td>
                <td><span class="badge bg-info text-dark">${v.badge}</span></td>
                <td><small>${v.heure_entree || '-'}</small></td>
                <td><small>${v.heure_sortie || '-'}</small></td>
                <td>${statut}</td>
            `;
            tbody.appendChild(tr);
        });

    } catch (e) {
        console.error("Erreur chargement visites:", e);
    }
}