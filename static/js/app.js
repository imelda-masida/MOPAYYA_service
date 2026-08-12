// État global de l'application
let langueActive = 'fr';
let listeMembres = [];
let membreSelectionne = null;

// Dictionnaire de traduction
const traductions = {
    fr: {
        actionTitle: "Que souhaitez-vous faire ?",
        btnEntree: "Entrée",
        btnSortie: "Sortie",
        hoteTitle: "Qui venez-vous visiter ?",
        btnSuivant: "Suivant",
        btnBadgeOk: "J'ai pris mon badge / OK",
        formTitle: "Vos Coordonnées",
        genreDefault: "-- Sélectionner le genre --",
        genreM: "Masculin",
        genreF: "Féminin",
        btnSave: "Enregistrer l'entrée",
        sortieTitle: "Enregistrement de votre sortie",
        btnValiderSortie: "Valider la sortie",
        finalBienvenue: "Bienvenue ! Veuillez suivre les indications des agents de sécurité. À votre sortie, veillez à enregistrer la restitution de votre badge.",
        finalAuRevoir: "Merci pour votre visite. Bonne continuation !"
    },
    en: {
        actionTitle: "What would you like to do?",
        btnEntree: "Entry",
        btnSortie: "Exit",
        hoteTitle: "Who are you visiting?",
        btnSuivant: "Next",
        btnBadgeOk: "I picked up my badge / OK",
        formTitle: "Your Contact Details",
        genreDefault: "-- Select Gender --",
        genreM: "Male",
        genreF: "Female",
        btnSave: "Check In",
        sortieTitle: "Check Out",
        btnValiderSortie: "Confirm Exit",
        finalBienvenue: "Welcome! Please follow the security officers' instructions. Upon departure, remember to check out your badge.",
        finalAuRevoir: "Thank you for visiting. Have a great day!"
    }
};

// 1. Choix de la langue
function choisirLangue(lang) {
    langueActive = lang;
    appliquerTraductions();
    masquerToutesLesEtapes();
    document.getElementById('step-action').classList.remove('hidden');
    chargerMembres(); // Charger la liste depuis l'API Flask
}

function appliquerTraductions() {
    const t = traductions[langueActive];
    document.getElementById('txt-action-title').innerText = t.actionTitle;
    document.getElementById('btn-entree').innerText = t.btnEntree;
    document.getElementById('btn-sortie').innerText = t.btnSortie;
    document.getElementById('txt-hote-title').innerText = t.hoteTitle;
    document.getElementById('btn-confirm-hote').innerText = t.btnSuivant;
    document.getElementById('btn-confirm-badge').innerText = t.btnBadgeOk;
    document.getElementById('txt-form-title').innerText = t.formTitle;
    document.getElementById('opt-genre-default').innerText = t.genreDefault;
    document.getElementById('opt-genre-m').innerText = t.genreM;
    document.getElementById('opt-genre-f').innerText = t.genreF;
    document.getElementById('btn-save').innerText = t.btnSave;
    document.getElementById('txt-sortie-title').innerText = t.sortieTitle;
    document.getElementById('btn-valider-sortie').innerText = t.btnValiderSortie;
}

// 2. Charger les membres via l'API Flask (Jour 1)
async function chargerMembres() {
    try {
        const reponse = await fetch('/api/membres');
        listeMembres = await reponse.json();
        
        const select = document.getElementById('select-hote');
        select.innerHTML = '<option value="">-- Sélectionnez la personne --</option>';
        
        listeMembres.forEach(m => {
            const opt = document.createElement('option');
            opt.value = m.id;
            opt.innerText = `${m.nom_complet} (${m.departement})`;
            select.appendChild(opt);
        });
    } catch (err) {
        console.error("Erreur lors du chargement des membres :", err);
    }
}

// 3. Traitement Entrée
function demarrerEntree() {
    masquerToutesLesEtapes();
    document.getElementById('step-hote').classList.remove('hidden');
}

function validerHote() {
    const membreId = document.getElementById('select-hote').value;
    if (!membreId) return alert("Veuillez sélectionner un membre.");

    membreSelectionne = listeMembres.find(m => m.id == membreId);
    
    masquerToutesLesEtapes();
    document.getElementById('step-badge').classList.remove('hidden');

    const msg = langueActive === 'fr' 
        ? `Veuillez prendre un badge de couleur <b>${membreSelectionne.couleur_badge}</b> accroché au mur.`
        : `Please take a <b>${membreSelectionne.couleur_badge}</b> badge hanging on the wall.`;

    document.getElementById('txt-badge-instruction').innerHTML = msg;
}

function afficherFormulaireVisiteur() {
    masquerToutesLesEtapes();
    document.getElementById('step-form').classList.remove('hidden');
}

async function soumettreEntree() {
    const payload = {
        nom: document.getElementById('nom').value,
        tel: document.getElementById('tel').value,
        fonction: document.getElementById('fonction').value,
        adresse: document.getElementById('adresse').value,
        genre: document.getElementById('genre').value,
        membre_id: membreSelectionne.id,
        dept_id: membreSelectionne.dept_id
    };

    if (!payload.nom) return alert("Veuillez saisir votre nom.");

    try {
        const res = await fetch('/api/entree', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (res.ok) {
            masquerToutesLesEtapes();
            document.getElementById('step-final').classList.remove('hidden');
            document.getElementById('txt-final-msg').innerText = traductions[langueActive].finalBienvenue;
        } else {
            alert(data.message || "Erreur lors de l'enregistrement");
        }
    } catch (err) {
        alert("Impossible de contacter le serveur.");
    }
}

// 4. Traitement Sortie
function demarrerSortie() {
    masquerToutesLesEtapes();
    document.getElementById('step-sortie').classList.remove('hidden');
}

async function soumettreSortie() {
    const badgeLettre = document.getElementById('badge-code').value;
    if (!badgeLettre) return alert("Veuillez entrer le code du badge.");

    try {
        const res = await fetch('/api/sortie', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ badge_lettre: badgeLettre })
        });

        const data = await res.json();

        if (res.ok) {
            masquerToutesLesEtapes();
            document.getElementById('step-final').classList.remove('hidden');
            document.getElementById('txt-final-msg').innerText = traductions[langueActive].finalAuRevoir;
        } else {
            alert(data.message || "Badge non reconnu ou non actif");
        }
    } catch (err) {
        alert("Erreur réseau.");
    }
}

// Utilitaires
function masquerToutesLesEtapes() {
    document.querySelectorAll('.step').forEach(el => el.classList.add('hidden'));
}

function reinitialiserApp() {
    location.reload();
}