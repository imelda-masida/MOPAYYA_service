let sessionData = {
    langue: 'fr',
    action: null,       
    hote_id: null
};

const traductions = {
    fr: {
        titleAction: "Que souhaitez-vous faire ?",
        btnEntree: "Enregistrer une Entrée",
        btnSortie: "Enregistrer une Sortie",
        titleHote: "Qui venez-vous visiter ?",
        optionDefaultHote: "-- Choisissez un membre --",
        btnSuivant: "Suivant",
        titleForm: "Vos Informations",
        lblNom: "Nom complet ",
        lblTel: "Numéro de téléphone ",
        lblFonction: "Fonction | Entreprise",
        lblAdresse: "Adresse",
        lblGenre: "Genre ",
        optionM: "Masculin",
        optionF: "Féminin",
        btnValiderEntree: "Valider l'Entrée",
        titleSortie: "Enregistrer votre Départ",
        lblBadgeCode: "Entrez la lettre | code de votre badge ",
        btnValiderSortie: "Restituer le badge & Sortir",
        msgAlertHote: "Veuillez sélectionner le membre que vous venez visiter.",
        confEntreeTitre: "Entrée enregistrée !",
        confEntreeMsg: "Bienvenue ! Votre badge vous a été attribué.",
        confSortieTitre: "Sortie enregistrée !",
        confSortieMsg: "Merci de votre visite et à bientôt !",
        btnRetour: "Retour à l'accueil"
    },
    en: {
        titleAction: "What would you like to do?",
        btnEntree: "Check In (Entry)",
        btnSortie: "Check Out (Exit)",
        titleHote: "Who are you visiting?",
        optionDefaultHote: "-- Choose a member --",
        btnSuivant: "Next",
        titleForm: "Your Details",
        lblNom: "Full Name ",
        lblTel: "Phone Number ",
        lblFonction: "Job Title | Company",
        lblAdresse: "Address",
        lblGenre: "Gender ",
        optionM: "Male",
        optionF: "Female",
        btnValiderEntree: "Confirm Entry",
        titleSortie: "Check Out Departure",
        lblBadgeCode: "Enter your badge letter | code ",
        btnValiderSortie: "Return badge & Exit",
        msgAlertHote: "Please select the member you are visiting.",
        confEntreeTitre: "Entry Recorded!",
        confEntreeMsg: "Welcome! Your badge has been assigned.",
        confSortieTitre: "Check Out Recorded!",
        confSortieMsg: "Thank you for your visit and see you soon!",
        btnRetour: "Back to Home"
    }
};



function appliquerTraduction() {
    const lang = sessionData.langue || 'fr';
    const t = traductions[lang];

    
    const txtAction = document.getElementById('txt-action-title');
    if (txtAction) txtAction.textContent = t.titleAction;
    const btnEntree = document.querySelector("#step-action .btn-entre");
    if (btnEntree) btnEntree.textContent = t.btnEntree;
    const btnSortie = document.querySelector("#step-action .btn-sortie");
    if (btnSortie) btnSortie.textContent = t.btnSortie;

    
    const titleHote = document.querySelector("#step-hote h3");
    if (titleHote) titleHote.textContent = t.titleHote;
    const btnSuivantHote = document.querySelector("#step-hote button");
    if (btnSuivantHote) btnSuivantHote.textContent = t.btnSuivant;

    
    const titleForm = document.querySelector("#step-form h3");
    if (titleForm) titleForm.textContent = t.titleForm;
    const labelsForm = document.querySelectorAll("#step-form .form-label");
    if (labelsForm.length >= 5) {
        labelsForm[0].textContent = t.lblNom;
        labelsForm[1].textContent = t.lblTel;
        labelsForm[2].textContent = t.lblFonction;
        labelsForm[3].textContent = t.lblAdresse;
        labelsForm[4].textContent = t.lblGenre;
    }
    const selectGenre = document.getElementById('genre');
    if (selectGenre && selectGenre.options.length >= 2) {
        selectGenre.options[0].textContent = t.optionM;
        selectGenre.options[1].textContent = t.optionF;
    }
    const btnSubmitEntree = document.querySelector("#form-visiteur button[type='submit']");
    if (btnSubmitEntree) btnSubmitEntree.textContent = t.btnValiderEntree;

    // Sortie
    const titleSortie = document.querySelector("#step-sortie h3");
    if (titleSortie) titleSortie.textContent = t.titleSortie;
    const lblBadge = document.querySelector("#step-sortie .form-label");
    if (lblBadge) lblBadge.textContent = t.lblBadgeCode;
    const btnSubmitSortie = document.querySelector("#form-sortie button[type='submit']");
    if (btnSubmitSortie) btnSubmitSortie.textContent = t.btnValiderSortie;

    // Confirmation
    const btnRetour = document.querySelector("#step-confirmation button");
    if (btnRetour) btnRetour.textContent = t.btnRetour;
}

// navigation

function afficherEtape(stepId) {
    const steps = document.querySelectorAll('.step');
    steps.forEach(step => step.classList.add('hidden'));

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

    const formVisiteur = document.getElementById('form-visiteur');
    if (formVisiteur) formVisiteur.reset();

    const formSortie = document.getElementById('form-sortie');
    if (formSortie) formSortie.reset();

    const selectHote = document.getElementById('select-hote');
    if (selectHote) selectHote.value = '';

    afficherEtape('step-lang');
}



function choisirLangue(lang) {
    sessionData.langue = lang;
    appliquerTraduction();
    afficherEtape('step-action');
}

function choisirAction(action) {
    sessionData.action = action;

    if (action === 'entree') {
        chargerMembres();
        afficherEtape('step-hote');
    } else if (action === 'sortie') {
        afficherEtape('step-sortie');
    }
}

function validerHote() {
    const select = document.getElementById('select-hote');
    if (!select || !select.value) {
        const t = traductions[sessionData.langue || 'fr'];
        alert(t.msgAlertHote);
        return;
    }
    sessionData.hote_id = select.value;
    afficherEtape('step-form');
}

//REQUÊTES API (FETCH) 

// Charge les membres depuis Flask /api/membres
async function chargerMembres() {
    const select = document.getElementById('select-hote');
    if (!select) return;

    const t = traductions[sessionData.langue || 'fr'];
    select.innerHTML = `<option value="" selected disabled>${t.optionDefaultHote}</option>`;

    try {
        const response = await fetch('/api/membres');
        if (!response.ok) throw new Error("Erreur réseau");
        
        const membres = await response.json();
        
        select.innerHTML = `<option value="" selected disabled>${t.optionDefaultHote}</option>`;
        membres.forEach(membre => {
            const option = document.createElement('option');
            option.value = membre.id;
            

            option.textContent = `${membre.nom} (${membre.service || 'Général'})`;
            select.appendChild(option);
        });
    } catch (erreur) {
        console.error("Erreur lors du chargement des membres :", erreur);
        select.innerHTML = '<option value="" selected disabled>Erreur / Error</option>';
    }
}


async function soumettreEntree(event) {
    event.preventDefault();
    const t = traductions[sessionData.langue || 'fr'];

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
            document.getElementById('conf-titre').textContent = t.confEntreeTitre;
            document.getElementById('conf-message').textContent = result.message || t.confEntreeMsg;
            
            document.getElementById('form-visiteur').reset();
            afficherEtape('step-confirmation');
        } else {
            alert(result.erreur || "Erreur de traitement.");
        }
    } catch (erreur) {
        console.error("Erreur d'entrée :", erreur);
        alert("Erreur serveur / Server error.");
    }
}


async function soumettreSortie(event) {
    event.preventDefault();
    const t = traductions[sessionData.langue || 'fr'];

    const badgeLettre = document.getElementById('badge-lettre').value.trim().toUpperCase();

    try {
        const response = await fetch('/api/visites/sortie', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ badge_lettre: badgeLettre })
        });

        const result = await response.json();

        if (response.ok) {
            document.getElementById('conf-titre').textContent = t.confSortieTitre;
            document.getElementById('conf-message').textContent = result.message || t.confSortieMsg;
            
            document.getElementById('form-sortie').reset();
            afficherEtape('step-confirmation');
        } else {
            alert(result.erreur || "Badge introuvable.");
        }
    } catch (erreur) {
        console.error("Erreur de sortie :", erreur);
        alert("Erreur serveur / Server error.");
    }
}

// Écouteur d'événement pour le bouton de rapport
document.addEventListener('DOMContentLoaded', () => {
    const btnRapport = document.getElementById('btn-rapport');
    if (btnRapport) {
        btnRapport.addEventListener('click', () => {
            setTimeout(() => {
                reinitialiser();
            }, 500);
        });
    }
});