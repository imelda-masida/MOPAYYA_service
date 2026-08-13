// Variable globale pour stocker les choix en cours
let sessionData = {
    langue: 'fr',
    action: null,       // 'entree' ou 'sortie'
    hote_id: null
};

// ==========================================
// 1. GESTION DE LA NAVIGATION ENTRE ÉTAPES
// ==========================================

function afficherEtape(stepId) {
    // Masque toutes les étapes
    const steps = document.querySelectorAll('.step');
    steps.forEach(step => step.classList.add('hidden'));

    // Affiche l'étape demandée
    const targetStep = document.getElementById(stepId);
    if (targetStep) {
        targetStep.classList.remove('hidden');
    }
}

function reinitialiser() {
    sessionData = {
        langue: 'fr',
        action: null,
        hote_id: null
    };
    // Réinitialise les formulaires
    document.getElementById('form-visiteur').reset();
    document.getElementById('form-sortie').reset();
    // Retour à l'écran de sélection de langue
    afficherEtape('step-lang');
}


// ==========================================
// 2. ÉTAPES DU FLUX D'ACCUEIL
// ==========================================

// ÉTAPE 1 : Choix de la langue
function choisirLangue(lang) {
    sessionData.langue = lang;
    afficherEtape('step-action');
}

// ÉTAPE 2 : Choix de l'action (Entrée ou Sortie)
function choisirAction(action) {
    sessionData.action = action;

    if (action === 'entree') {
        chargerMembres(); // Récupère les hôtes depuis Flask
        afficherEtape('step-hote');
    } else if (action === 'sortie') {
        afficherEtape('step-sortie');
    }
}

// ÉTAPE 3 : Validation de l'hôte sélectionné
function validerHote() {
    const select = document.getElementById('select-hote');
    if (!select.value) {
        alert("Veuillez sélectionner le membre que vous venez visiter.");
        return;
    }
    sessionData.hote_id = select.value;
    afficherEtape('step-badge');
}

// ÉTAPE 4 : Validation de la prise de badge
function validerBadge() {
    afficherEtape('step-form');
}


// ==========================================
// 3. REQUÊTES API (FETCH)
// ==========================================

// Charger la liste des membres depuis /api/membres
async function chargerMembres() {
    const select = document.getElementById('select-hote');
    select.innerHTML = '<option value="" selected disabled>Chargement...</option>';

    try {
        const response = await fetch('/api/membres');
        if (!response.ok) throw new Error("Erreur réseau");
        
        const membres = await response.json();
        
        select.innerHTML = '<option value="" selected disabled>-- Choisissez un membre --</option>';
        membres.forEach(membre => {
            const option = document.createElement('option');
            option.value = membre.id;
            option.textContent = `${membre.nom_complet} (${membre.departement_nom || 'Général'})`;
            select.appendChild(option);
        });
    } catch (erreur) {
        console.error("Erreur lors du chargement des membres :", erreur);
        select.innerHTML = '<option value="" selected disabled>Erreur de chargement</option>';
    }
}

// Soumission du formulaire d'ENTRÉE
async function soumettreEntree(event) {
    event.preventDefault(); // Empêche le rechargement de la page

    const payload = {
        nom_complet: document.getElementById('nom').value.trim(),
        telephone: document.getElementById('tel').value.trim(),
        fonction: document.getElementById('fonction').value.trim(),
        adresse: document.getElementById('adresse').value.trim(),
        genre: document.getElementById('genre').value,
        membre_id: sessionData.hote_id,
        langue: sessionData.langue
    };

    try {
        const response = await fetch('/api/visites/entree', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (response.ok) {
            document.getElementById('conf-titre').textContent = "Entrée enregistrée !";
            document.getElementById('conf-message').textContent = result.message || `Bienvenue ! Votre badge vous a été attribué.`;
            afficherEtape('step-confirmation');
        } else {
            alert(result.erreur || "Une erreur est survenue lors de l'enregistrement.");
        }
    } catch (erreur) {
        console.error("Erreur d'entrée :", erreur);
        alert("Impossible de communiquer avec le serveur.");
    }
}

// Soumission du formulaire de SORTIE
async function soumettreSortie(event) {
    event.preventDefault();

    const badgeLettre = document.getElementById('badge-lettre').value.trim().toUpperCase();

    try {
        const response = await fetch('/api/visites/sortie', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ badge_lettre: badgeLettre })
        });

        const result = await response.json();

        if (response.ok) {
            document.getElementById('conf-titre').textContent = "Sortie enregistrée !";
            document.getElementById('conf-message').textContent = result.message || "Merci de votre visite et à bientôt !";
            afficherEtape('step-confirmation');
        } else {
            alert(result.erreur || "Badge introuvable ou aucune visite active associée.");
        }
    } catch (erreur) {
        console.error("Erreur de sortie :", erreur);
        alert("Impossible de communiquer avec le serveur.");
    }
}