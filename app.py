import csv
from datetime import datetime
from io import BytesIO, StringIO
import sqlite3
from flask import Flask, Response, jsonify, render_template, request

# Importations ReportLab pour la génération du PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

app = Flask(__name__)
DB_NAME = 'database.db'


def get_db_connection():
    """Crée une connexion à la base de données SQLite."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialise la structure de la base de données."""
    conn = get_db_connection()
    c = conn.cursor()

    # Table Départements
    c.execute("""
        CREATE TABLE IF NOT EXISTS departements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            couleur_badge TEXT
        )
    """)

    # Table Membres (Hôtes)
    c.execute("""
        CREATE TABLE IF NOT EXISTS membres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_complet TEXT NOT NULL,
            departement_id INTEGER,
            FOREIGN KEY (departement_id) REFERENCES departements(id)
        )
    """)

    # Table Badges
    c.execute("""
        CREATE TABLE IF NOT EXISTS badges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lettre TEXT UNIQUE NOT NULL,
            departement_id INTEGER,
            est_disponible INTEGER DEFAULT 1,
            FOREIGN KEY (departement_id) REFERENCES departements(id)
        )
    """)

    # Table Visites
    c.execute("""
        CREATE TABLE IF NOT EXISTS visites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_complet TEXT NOT NULL,
            telephone TEXT,
            fonction TEXT,
            adresse TEXT,
            genre TEXT,
            membre_id INTEGER,
            badge_id INTEGER,
            heure_entree DATETIME,
            heure_sortie DATETIME,
            FOREIGN KEY (membre_id) REFERENCES membres(id),
            FOREIGN KEY (badge_id) REFERENCES badges(id)
        )
    """)

    conn.commit()
    conn.close()


init_db()



# ROUTES HTML


@app.route('/')
def home():
    """Affiche la page d'accueil de la borne."""
    return render_template('index.html')



# API REST


@app.route('/api/membres', methods=['GET'])
def get_membres():
    """Retourne la liste des hôtes et leurs départements."""
    conn = get_db_connection()
    membres = conn.execute("""
        SELECT m.id, m.nom_complet, d.nom AS departement_nom 
        FROM membres m
        LEFT JOIN departements d ON m.departement_id = d.id
        ORDER BY m.nom_complet ASC
    """).fetchall()
    conn.close()

    resultat = [dict(membre) for membre in membres]
    return jsonify(resultat), 200


@app.route('/api/visites/entree', methods=['POST'])
def enregistrer_entree():
    """Enregistre l'arrivée d'un visiteur et lui attribue automatiquement un badge."""
    try:
        data = request.get_json() or {}

        nom_complet = data.get('nom_complet')
        telephone = data.get('telephone', '')
        membre_id = data.get('membre_id')
        fonction = data.get('fonction', '')
        adresse = data.get('adresse', '')
        genre = data.get('genre', 'M')

        if not nom_complet or not membre_id:
            return jsonify({'erreur': 'Le nom du visiteur et l\'hôte sont obligatoires.'}), 400

        conn = get_db_connection()
        c = conn.cursor()

        membre = c.execute('SELECT departement_id FROM membres WHERE id = ?', (membre_id,)).fetchone()
        if not membre:
            conn.close()
            return jsonify({'erreur': 'Membre sélectionné introuvable.'}), 404

        departement_id = membre['departement_id']

        # Attribution automatique du premier badge disponible du département
        badge = c.execute("""
            SELECT id, lettre FROM badges 
            WHERE (departement_id = ? OR departement_id IS NULL) AND est_disponible = 1 
            LIMIT 1
        """, (departement_id,)).fetchone()

        badge_id = None
        badge_lettre = 'Aucun'

        if badge:
            badge_id = badge['id']
            badge_lettre = badge['lettre']
            c.execute('UPDATE badges SET est_disponible = 0 WHERE id = ?', (badge_id,))

        maintenant = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        c.execute("""
            INSERT INTO visites (nom_complet, telephone, fonction, adresse, genre, membre_id, badge_id, heure_entree)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (nom_complet, telephone, fonction, adresse, genre, membre_id, badge_id, maintenant))

        conn.commit()
        conn.close()

        return jsonify({
            'message': f'Entrée enregistrée avec succès. Votre badge attribué : {badge_lettre}',
            'badge': badge_lettre
        }), 201

    except Exception as e:
        print(f"Erreur dans /api/visites/entree : {e}")
        return jsonify({'erreur': f'Erreur interne du serveur : {str(e)}'}), 500


@app.route('/api/visites/sortie', methods=['POST'])
def enregistrer_sortie():
    """Enregistre le départ et libère le badge."""
    try:
        data = request.get_json() or {}
        badge_lettre = data.get('badge_lettre')

        if not badge_lettre:
            return jsonify({'erreur': 'Le code du badge est requis.'}), 400

        conn = get_db_connection()
        c = conn.cursor()

        badge = c.execute('SELECT id FROM badges WHERE UPPER(lettre) = UPPER(?)', (badge_lettre,)).fetchone()
        if not badge:
            conn.close()
            return jsonify({'erreur': 'Badge introuvable.'}), 404

        badge_id = badge['id']

        visite = c.execute("""
            SELECT id FROM visites 
            WHERE badge_id = ? AND heure_sortie IS NULL 
            ORDER BY heure_entree DESC LIMIT 1
        """, (badge_id,)).fetchone()

        if not visite:
            conn.close()
            return jsonify({'erreur': 'Aucune visite active associée à ce badge.'}), 400

        maintenant = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute('UPDATE visites SET heure_sortie = ? WHERE id = ?', (maintenant, visite['id']))
        c.execute('UPDATE badges SET est_disponible = 1 WHERE id = ?', (badge_id,))

        conn.commit()
        conn.close()

        return jsonify({'message': 'Sortie enregistrée avec succès. Merci de votre visite !'}), 200

    except Exception as e:
        print(f"Erreur dans /api/visites/sortie : {e}")
        return jsonify({'erreur': f'Erreur interne du serveur : {str(e)}'}), 500


# EXPORT DES RAPPORTS (CSV, PDF, JSON)


@app.route('/api/rapport/semaine', methods=['GET'])
def rapport_semaine():
    """Exporte les visites des 7 derniers jours en JSON, CSV ou PDF."""
    try:
        format_req = request.args.get('format', 'json').lower()
        conn = get_db_connection()
        c = conn.cursor()

        query = """
            SELECT 
                v.id,
                v.nom_complet AS visiteur,
                COALESCE(v.telephone, '') AS telephone,
                COALESCE(v.fonction, '') AS fonction,
                COALESCE(v.adresse, '') AS adresse,
                COALESCE(v.genre, '') AS genre,
                COALESCE(m.nom_complet, 'N/A') AS hote,
                COALESCE(d.nom, 'N/A') AS departement,
                COALESCE(b.lettre, 'N/A') AS badge,
                COALESCE(v.heure_entree, '') AS heure_entree,
                COALESCE(v.heure_sortie, '') AS heure_sortie
            FROM visites v
            LEFT JOIN membres m ON v.membre_id = m.id
            LEFT JOIN departements d ON m.departement_id = d.id
            LEFT JOIN badges b ON v.badge_id = b.id
            WHERE v.heure_entree >= datetime('now', '-7 days') OR v.heure_entree IS NULL
            ORDER BY v.heure_entree DESC
        """
        c.execute(query)
        visites = c.fetchall()
        conn.close()

        date_str = datetime.now().strftime('%Y_%m_%d')

        # EXPORT CSV
        if format_req == 'csv':
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(['ID', 'Visiteur', 'Téléphone', 'Fonction', 'Adresse', 'Genre', 'Hôte Visité', 'Département', 'Badge', 'Heure Entrée', 'Heure Sortie'])

            for row in visites:
                writer.writerow([str(val) if val is not None else '' for val in row])

            output.seek(0)
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment;filename=rapport_visites_{date_str}.csv'}
            )

        # EXPORT PDF
        elif format_req == 'pdf':
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
            elements = []

            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'TitleStyle',
                parent=styles['Heading1'],
                fontSize=16,
                textColor=colors.HexColor('#0d6efd'),
                spaceAfter=15
            )
            cell_style = ParagraphStyle('CellStyle', fontSize=8, leading=10)

            # Titre du rapport
            titre = f"Rapport des Visites (7 Derniers Jours) - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            elements.append(Paragraph(titre, title_style))
            elements.append(Spacer(1, 10))

            # En-têtes et préparation des données
            headers = ['ID', 'Visiteur', 'Téléphone', 'Fonction', 'Genre', 'Hôte', 'Département', 'Badge', 'Entrée', 'Sortie']
            table_data = [[Paragraph(f"<b>{h}</b>", cell_style) for h in headers]]

            for r in visites:
                row_cells = [
                    Paragraph(str(r['id']), cell_style),
                    Paragraph(r['visiteur'], cell_style),
                    Paragraph(r['telephone'], cell_style),
                    Paragraph(r['fonction'], cell_style),
                    Paragraph(r['genre'], cell_style),
                    Paragraph(r['hote'], cell_style),
                    Paragraph(r['departement'], cell_style),
                    Paragraph(r['badge'], cell_style),
                    Paragraph(r['heure_entree'], cell_style),
                    Paragraph(r['heure_sortie'] if r['heure_sortie'] else 'En cours', cell_style),
                ]
                table_data.append(row_cells)

            # Styles du tableau
            table = Table(table_data, colWidths=[25, 110, 80, 90, 40, 110, 90, 45, 105, 105])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e9ecef')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))

            elements.append(table)
            doc.build(elements)
            buffer.seek(0)

            return Response(
                buffer.getvalue(),
                mimetype='application/pdf',
                headers={'Content-Disposition': f'attachment;filename=rapport_visites_{date_str}.pdf'}
            )

       # RETOUR JSON PAR DÉFAUT
        return jsonify([dict(row) for row in visites]), 200

    except Exception as e:
        print(f"Erreur dans /api/rapport/semaine : {e}")
        return jsonify({'erreur': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)