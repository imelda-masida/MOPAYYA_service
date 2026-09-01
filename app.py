import csv
import io
import json
import os
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Flask,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

# Traitement d'image et requêtes réseau pour le logo PDF
import requests
from PIL import Image as PILImage

# Imports pour la génération PDF (ReportLab)
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image as RLImage, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# --- CONFIGURATION INITIALE ---

app = Flask(__name__)
app.secret_key = 'votre_cle_secrete_ici'

FICHIER_MEMBRES = 'membres.json'
FICHIER_VISITES = 'visites.json'

# Mappage des services/départements aux lettres de badge
DEPARTEMENT_PREFIXES = {
    'IT': 'A',
    'Ressources Humaines': 'B',
    'Comptabilité': 'C',
    'Direction': 'D',
    'Logistique': 'E'
}

MAX_BADGES_PAR_DEPT = 20


# DÉCORATEUR SÉCURITÉ ADMIN 

def admin_requis(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_connecte'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


# GESTION DES FICHIERS JSON 

def lire_membres():
    """Lit la liste des membres depuis membres.json."""
    if not os.path.exists(FICHIER_MEMBRES):
        membres_defaut = [
            {"id": 1, "nom": "Jean Dupont", "service": "Informatique"},
            {"id": 2, "nom": "Sarah Kabangu", "service": "Ressources Humaines"},
            {"id": 3, "nom": "Marc Kabora", "service": "Comptabilité"}
        ]
        sauvegarder_membres(membres_defaut)
        return membres_defaut

    try:
        with open(FICHIER_MEMBRES, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def sauvegarder_membres(liste_membres):
    """Enregistre la liste des membres dans membres.json."""
    with open(FICHIER_MEMBRES, 'w', encoding='utf-8') as f:
        json.dump(liste_membres, f, indent=4, ensure_ascii=False)

def lire_visites():
    """Lit toutes les visites enregistrées dans visites.json."""
    if not os.path.exists(FICHIER_VISITES):
        sauvegarder_visites([])
        return []

    try:
        with open(FICHIER_VISITES, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def sauvegarder_visites(liste_visites):
    """Enregistre la liste des visites dans visites.json."""
    with open(FICHIER_VISITES, 'w', encoding='utf-8') as f:
        json.dump(liste_visites, f, indent=4, ensure_ascii=False)


# LOGIQUE D'ATTRIBUTION DES BADGES & TRAITEMENT D'IMAGE 

def generer_badge_pour_service(nom_service):
    """Génère un badge unique (ex: A1, A2...) pour un service donné."""
    prefixe = DEPARTEMENT_PREFIXES.get(nom_service, 'X')
    visites = lire_visites()

    badges_occupes = [
        v.get('badge') for v in visites 
        if v.get('heure_sortie') is None and v.get('badge', '').startswith(prefixe)
    ]

    numeros_occupes = []
    for b in badges_occupes:
        num_str = b.replace(prefixe, '')
        if num_str.isdigit():
            numeros_occupes.append(int(num_str))

    for i in range(1, MAX_BADGES_PAR_DEPT + 1):
        if i not in numeros_occupes:
            return f"{prefixe}{i}"

    return None

def obtenir_logo_bleu_buffer(url_logo, couleur_hex="#051059"):
    """Télécharge l'image PNG distante et la recolore en bleu."""
    try:
        response = requests.get(url_logo, timeout=5)
        if response.status_code == 200:
            img = PILImage.open(io.BytesIO(response.content)).convert("RGBA")
            hex_val = couleur_hex.lstrip('#')
            target_rgb = tuple(int(hex_val[i:i+2], 16) for i in (0, 2, 4))
            
            _, _, _, alpha = img.split()
            nouvelle_img = PILImage.new("RGBA", img.size, target_rgb + (255,))
            nouvelle_img.putalpha(alpha)
            
            buffer_img = io.BytesIO()
            nouvelle_img.save(buffer_img, format="PNG")
            buffer_img.seek(0)
            return buffer_img
    except Exception as e:
        print(f"Erreur de traitement du logo : {e}")
    return None




@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/membres', methods=['GET'])
def get_membres():
    return jsonify(lire_membres())

@app.route('/api/visites/entree', methods=['POST'])
def enregistrer_entree():
    data = request.get_json() or {}
    visites = lire_visites()
    membres = lire_membres()

    membre_id = data.get("membre_id")
    hôte = next((m for m in membres if str(m.get("id")) == str(membre_id)), None)

    if not hôte:
        return jsonify({"erreur": "Hôte introuvable."}), 400

    service_hôte = hôte.get("service", "")
    badge = generer_badge_pour_service(service_hôte)

    if not badge:
        return jsonify({
            "erreur": f"Tous les badges du service {service_hôte} sont actuellement attribués."
        }), 400

    nouveau_id = max([v.get('id', 0) for v in visites], default=0) + 1

    nouvelle_visite = {
        "id": nouveau_id,
        "nom_complet": data.get("nom_complet"),
        "telephone": data.get("telephone"),
        "fonction": data.get("fonction"),
        "adresse": data.get("adresse"),
        "genre": data.get("genre"),
        "membre_id": membre_id,
        "badge": badge,
        "heure_entree": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "heure_sortie": None
    }

    visites.append(nouvelle_visite)
    sauvegarder_visites(visites)

    return jsonify({
        "message": f"Bienvenue ! Votre badge est le {badge}.",
        "badge": badge
    }), 201

@app.route('/api/visites/sortie', methods=['POST'])
def enregistrer_sortie():
    data = request.get_json() or {}
    badge_cherche = data.get("badge_lettre", "").strip().upper()

    visites = lire_visites()
    trouve = False

    for v in visites:
        if v.get("badge", "").upper() == badge_cherche and v.get("heure_sortie") is None:
            v["heure_sortie"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            trouve = True
            break

    if trouve:
        sauvegarder_visites(visites)
        return jsonify({"message": "Sortie enregistrée avec succès."})

    return jsonify({"erreur": "Aucun visiteur actif trouvé avec ce badge."}), 404



@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        identifiant = request.form.get('identifiant')
        mot_de_passe = request.form.get('mot_de_passe')

        if identifiant == 'admin' and mot_de_passe == 'admin123':
            session['admin_connecte'] = True
            return redirect(url_for('admin_dashboard'))
        return render_template('login.html', erreur="Identifiant ou mot de passe incorrect.")

    return render_template('login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_connecte', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
@admin_requis
def admin_dashboard():
    return render_template('admin.html')

@app.route('/admin/membres/ajouter', methods=['POST'])
@admin_requis
def ajouter_membre():
    nom = request.form.get('nom')
    service = request.form.get('service')

    if nom and service:
        membres = lire_membres()
        nouveau_id = max([m.get('id', 0) for m in membres], default=0) + 1

        membres.append({
            "id": nouveau_id,
            "nom": nom,
            "service": service
        })
        sauvegarder_membres(membres)

    return redirect(url_for('admin_dashboard'))

@app.route('/api/admin/membres/supprimer/<int:membre_id>', methods=['DELETE'])
@admin_requis
def supprimer_membre(membre_id):
    membres = lire_membres()
    membres_filtrés = [m for m in membres if str(m.get('id')) != str(membre_id)]

    if len(membres_filtrés) == len(membres):
        return jsonify({"erreur": "Membre non trouvé."}), 404

    sauvegarder_membres(membres_filtrés)
    return jsonify({"message": "Membre supprimé avec succès."}), 200




@app.route('/api/admin/stats', methods=['GET'])
@admin_requis
def api_admin_stats():
    visites = lire_visites()
    aujourdhui_str = datetime.now().strftime('%Y-%m-%d')

    total_aujourdhui = sum(1 for v in visites if v.get('heure_entree', '').startswith(aujourdhui_str))
    sur_site = sum(1 for v in visites if not v.get('heure_sortie'))

    compte_tels = {}
    for v in visites:
        tel = v.get('telephone')
        if tel:
            compte_tels[tel] = compte_tels.get(tel, 0) + 1

    visiteurs_recurrents = sum(1 for count in compte_tels.values() if count > 1)

    return jsonify({
        'total_aujourdhui': total_aujourdhui,
        'sur_site': sur_site,
        'visiteurs_recurrents': visiteurs_recurrents
    })

@app.route('/api/admin/visites', methods=['GET'])
@admin_requis
def api_admin_visites():
    visites = lire_visites()
    membres = {str(m['id']): m['nom'] for m in lire_membres()}

    query = request.args.get('q', '').lower().strip()
    hote_id = request.args.get('hote_id', '').strip()

    historique_tels = {}
    for v in visites:
        tel = v.get('telephone')
        if tel:
            historique_tels[tel] = historique_tels.get(tel, 0) + 1

    resultats = []
    for v in visites:
        tel = v.get('telephone', '')
        nom_hote = membres.get(str(v.get('membre_id')), 'Hôte inconnu')

        if hote_id and str(v.get('membre_id')) != hote_id:
            continue

        visiteur = v.get('nom_complet', '')
        fonction = v.get('fonction', '')

        if query:
            match = (
                query in visiteur.lower() or
                query in tel.lower() or
                query in fonction.lower() or
                query in nom_hote.lower()
            )
            if not match:
                continue

        resultats.append({
            'id': v.get('id'),
            'visiteur': visiteur,
            'telephone': tel,
            'fonction': fonction,
            'hote': nom_hote,
            'badge': v.get('badge', 'N/A'),
            'heure_entree': v.get('heure_entree', ''),
            'heure_sortie': v.get('heure_sortie', None),
            'total_visites_perso': historique_tels.get(tel, 1)
        })

    resultats.reverse()
    return jsonify(resultats)

@app.route('/api/rapport/semaine', methods=['GET'])
@admin_requis
def exporter_rapport():
    fmt = request.args.get('format', 'csv').lower()
    visites = lire_visites()
    membres = {str(m['id']): m['nom'] for m in lire_membres()}

     
    maintenant = datetime.now()
    debut_semaine = maintenant.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=maintenant.weekday())

    visites_semaine = []

    for v in visites:
        h_entree = v.get('heure_entree', '')
        if h_entree:
            try:
                dt_entree = datetime.strptime(h_entree, '%Y-%m-%d %H:%M:%S')
                if dt_entree >= debut_semaine:
                    visites_semaine.append(v)
            except ValueError:
                continue

    if fmt == 'csv':
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')
        writer.writerow(['ID', 'Visiteur', 'Téléphone', 'Fonction', 'Hôte Visité', 'Badge', 'Entrée', 'Sortie'])

        for v in visites_semaine:
            nom_hote = membres.get(str(v.get('membre_id')), 'Hôte inconnu')
            writer.writerow([
                v.get('id', ''),
                v.get('nom_complet', ''),
                v.get('telephone', ''),
                v.get('fonction', ''),
                nom_hote,
                v.get('badge', ''),
                v.get('heure_entree', ''),
                v.get('heure_sortie') or 'En cours'
            ])

        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = f"attachment; filename=rapport_visites_{datetime.now().strftime('%Y%m%d')}.csv"
        response.headers["Content-type"] = "text/csv; charset=utf-8"
        return response

    elif fmt == 'pdf':
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        elements = []

        # En-tête : Logo en bleu
        url_logo = "https://group-tia.com/wp-content/uploads/2024/04/logo-GROUP-tia-inverse.png"
        logo_buffer = obtenir_logo_bleu_buffer(url_logo, couleur_hex="#051059")

        if logo_buffer:
            img_logo = RLImage(logo_buffer, width=140, height=45)
            img_logo.hAlign = 'LEFT'
            elements.append(img_logo)
            elements.append(Spacer(1, 10))

        styles = getSampleStyleSheet()
        titre_style = ParagraphStyle(
            'TitreStyle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor("#051059"),
            spaceAfter=6
        )

        elements.append(Paragraph("MOPAYA - Rapport Hebdomadaire des Visites", titre_style))
        elements.append(Paragraph(f"Généré le : {datetime.now().strftime('%d/%m/%Y à %H:%M')}", styles['Normal']))
        elements.append(Spacer(1, 15))

        data = [['Visiteur', 'Téléphone', 'Hôte', 'Badge', 'Entrée', 'Sortie']]

        for v in visites_semaine:
            nom_hote = membres.get(str(v.get('membre_id')), 'Inconnu')
            data.append([
                v.get('nom_complet', '-'),
                v.get('telephone', '-'),
                nom_hote,
                v.get('badge', '-'),
                v.get('heure_entree', '-')[11:16] if v.get('heure_entree') else '-',
                v.get('heure_sortie')[11:16] if v.get('heure_sortie') else 'Sur site'
            ])

        t = Table(data, colWidths=[110, 80, 110, 60, 80, 80])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#051059")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f8f9fa")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))

        elements.append(t)
        doc.build(elements)

        buffer.seek(0)
        response = make_response(buffer.getvalue())
        response.headers["Content-Disposition"] = f"attachment; filename=rapport_visites_{datetime.now().strftime('%Y%m%d')}.pdf"
        response.headers["Content-type"] = "application/pdf"
        return response

    return jsonify({"erreur": "Format non supporté"}), 400




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)