document.addEventListener('DOMContentLoaded', () => {
    chargerStats();
    chargerMembresGestion();
    chargerHotesFiltre();
    chargerVisites();

    const inputRecherche = document.getElementById('filtre-recherche');
    const selectHote = document.getElementById('filtre-hote');

    if (inputRecherche) inputRecherche.addEventListener('input', chargerVisites);
    if (selectHote) selectHote.addEventListener('change', chargerVisites);
});

// Charger les statistiques depuis /api/admin/stats
async function chargerStats() {
    try {
        const res = await fetch('/api/admin/stats');
        if (res.ok) {
            const data = await res.json();
            document.getElementById('stat-aujourdhui').textContent = data.total_aujourdhui || 0;
            document.getElementById('stat-sur-site').textContent = data.sur_site || 0;
            document.getElementById('stat-recurrents').textContent = data.visiteurs_recurrents || 0;
        }
    } catch (e) {
        console.error("Erreur chargement stats:", e);
    }
}

// Charger la liste des membres dans le tableau de gestion + bouton suppression
async function chargerMembresGestion() {
    const tbody = document.getElementById('table-membres-body');
    if (!tbody) return;

    try {
        const res = await fetch('/api/membres');
        if (res.ok) {
            const membres = await res.json();
            tbody.innerHTML = '';

            if (membres.length === 0) {
                tbody.innerHTML = '<tr><td colspan="3" class="text-center text-muted">Aucun membre enregistré.</td></tr>';
                return;
            }

            membres.forEach(m => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong>${m.nom}</strong></td>
                    <td><span class="badge bg-light text-dark border">${m.service || 'Général'}</span></td>
                    <td class="text-end">
                        <button class="btn btn-outline-danger btn-sm" onclick="supprimerMembre(${m.id}, '${m.nom.replace(/'/g, "\\'")}')">
                            Supprimer
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (e) {
        console.error("Erreur chargement tableau membres:", e);
    }
}

// Supprimer un membre
async function supprimerMembre(id, nom) {
    if (!confirm(`Voulez-vous vraiment supprimer le membre "${nom}" ?`)) {
        return;
    }

    try {
        const res = await fetch(`/api/admin/membres/supprimer/${id}`, {
            method: 'DELETE'
        });

        if (res.ok) {
            chargerMembresGestion();
            chargerHotesFiltre();
            chargerVisites();
        } else {
            const data = await res.json();
            alert(data.erreur || "Erreur lors de la suppression.");
        }
    } catch (e) {
        console.error("Erreur lors de la suppression du membre:", e);
        alert("Erreur serveur lors de la suppression.");
    }
}

// Remplir le filtre déroulant des hôtes
async function chargerHotesFiltre() {
    const select = document.getElementById('filtre-hote');
    if (!select) return;

    try {
        const res = await fetch('/api/membres');
        if (res.ok) {
            const membres = await res.json();
            select.innerHTML = '<option value="">Tous les hôtes visités</option>';
            
            membres.forEach(m => {
                const opt = document.createElement('option');
                opt.value = m.id;
                opt.textContent = `${m.nom} (${m.service || 'Général'})`;
                select.appendChild(opt);
            });
        }
    } catch (e) {
        console.error("Erreur hôtes:", e);
    }
}

// Charger et filtrer la liste des visites
async function chargerVisites() {
    const inputRecherche = document.getElementById('filtre-recherche');
    const selectHote = document.getElementById('filtre-hote');
    const tbody = document.getElementById('table-visites-body');

    if (!tbody) return;

    const q = inputRecherche ? inputRecherche.value.trim() : '';
    const hoteId = selectHote ? selectHote.value : '';

    try {
        const url = new URL('/api/admin/visites', window.location.origin);
        if (q) url.searchParams.append('q', q);
        if (hoteId) url.searchParams.append('hote_id', hoteId);

        const res = await fetch(url);
        if (!res.ok) return;

        const visites = await res.json();
        tbody.innerHTML = '';

        if (!Array.isArray(visites) || visites.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">Aucune visite trouvée.</td></tr>';
            return;
        }

        visites.forEach(v => {
            const tr = document.createElement('tr');

            let badgeRecurrent = '';
            if (v.total_visites_perso && v.total_visites_perso > 1) {
                badgeRecurrent = `<span class="badge bg-warning text-dark ms-1" title="Visiteur récurrent">${v.total_visites_perso} visites</span>`;
            }

            const statut = v.heure_sortie 
                ? '<span class="badge bg-secondary">Parti</span>' 
                : '<span class="badge bg-success">Sur site</span>';

            tr.innerHTML = `
                <td><strong>${v.visiteur || '-'}</strong> ${badgeRecurrent}</td>
                <td>${v.telephone || '-'}</td>
                <td>${v.fonction || '-'}</td>
                <td>${v.hote || '-'}</td>
                <td><span class="badge bg-info text-dark">${v.badge || '-'}</span></td>
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