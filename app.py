import csv
from datetime import datetime, timedelta
from io import StringIO
import sqlite3
from flask import Flask, Response, jsonify, render_template, request

app = Flask(__name__)
DB_NAME = 'database.db'


def get_db_connection():
  """Crée une connexion à la base de données avec gestion des colonnes par nom."""
  conn = sqlite3.connect(DB_NAME)
  conn.row_factory = sqlite3.Row
  return conn


def init_db():
  """Initialise les tables si elles n'existent pas encore."""
  conn = get_db_connection()
  c = conn.cursor()

  # Table Departements
  c.execute("""
        CREATE TABLE IF NOT EXISTS departements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            couleur_badge TEXT
        )
    """)

  # Table Membres (Hôtes à visiter)
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


# Initialisation au démarrage de l'application
init_db()



# ROUTES HTML

@app.route('/')
def home():
  """Affiche la page d'accueil de la borne."""
  return render_template('index.html')



# API REST



@app.route('/api/membres', methods=['GET'])
def get_membres():
  """Retourne la liste des membres/hôtes et leur département."""
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
  """Enregistre l'arrivée d'un visiteur et lui attribue un badge disponible."""
  try:
    data = request.get_json() or {}

    nom_complet = data.get('nom_complet')
    telephone = data.get('telephone', '')
    membre_id = data.get('membre_id')
    fonction = data.get('fonction', '')
    adresse = data.get('adresse', '')
    genre = data.get('genre', 'M')

    if not nom_complet or not membre_id:
      return (
          jsonify({
              'erreur': (
                  'Le nom du visiteur et le membre à visiter sont'
                  ' obligatoires.'
              )
          }),
          400,
      )

    conn = get_db_connection()
    c = conn.cursor()

    # Vérifier si le membre existe
    membre = c.execute(
        'SELECT departement_id FROM membres WHERE id = ?', (membre_id,)
    ).fetchone()
    if not membre:
      conn.close()
      return jsonify({'erreur': 'Membre sélectionné introuvable.'}), 404

    departement_id = membre['departement_id']

    # Chercher un badge disponible
    badge = c.execute(
        """
            SELECT id, lettre FROM badges 
            WHERE (departement_id = ? OR departement_id IS NULL) AND est_disponible = 1 
            LIMIT 1
        """,
        (departement_id,),
    ).fetchone()

    badge_id = None
    badge_lettre = 'Aucun'

    if badge:
      badge_id = badge['id']
      badge_lettre = badge['lettre']
      c.execute(
          'UPDATE badges SET est_disponible = 0 WHERE id = ?', (badge_id,)
      )

    maintenant = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Insertion sécurisée de la visite
    c.execute(
        """
            INSERT INTO visites (nom_complet, telephone, fonction, adresse, genre, membre_id, badge_id, heure_entree)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            nom_complet,
            telephone,
            fonction,
            adresse,
            genre,
            membre_id,
            badge_id,
            maintenant,
        ),
    )

    conn.commit()
    conn.close()

    return (
        jsonify({
            'message': (
                'Entrée enregistrée avec succès. Badge attribué :'
                f' {badge_lettre}'
            ),
            'badge': badge_lettre,
        }),
        201,
    )

  except Exception as e:
    print(f'Erreur dans /api/visites/entree : {e}')
    return jsonify({'erreur': f'Erreur interne du serveur : {str(e)}'}), 500


@app.route('/api/visites/sortie', methods=['POST'])
def enregistrer_sortie():
  """Enregistre le départ d'un visiteur et libère son badge."""
  try:
    data = request.get_json() or {}
    badge_lettre = data.get('badge_lettre')

    if not badge_lettre:
      return jsonify({'erreur': 'La lettre ou code du badge est requis.'}), 400

    conn = get_db_connection()
    c = conn.cursor()

    badge = c.execute(
        'SELECT id FROM badges WHERE UPPER(lettre) = UPPER(?)', (badge_lettre,)
    ).fetchone()
    if not badge:
      conn.close()
      return jsonify({'erreur': 'Badge introuvable.'}), 404

    badge_id = badge['id']

    visite = c.execute(
        """
            SELECT id FROM visites 
            WHERE badge_id = ? AND heure_sortie IS NULL 
            ORDER BY heure_entree DESC LIMIT 1
        """,
        (badge_id,),
    ).fetchone()

    if not visite:
      conn.close()
      return (
          jsonify({'erreur': 'Aucune visite active associée à ce badge.'}),
          400,
      )

    maintenant = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute(
        'UPDATE visites SET heure_sortie = ? WHERE id = ?',
        (maintenant, visite['id']),
    )
    c.execute('UPDATE badges SET est_disponible = 1 WHERE id = ?', (badge_id,))

    conn.commit()
    conn.close()

    return (
        jsonify(
            {'message': 'Sortie enregistrée avec succès. Merci de votre visite !'}
        ),
        200,
    )

  except Exception as e:
    print(f'Erreur dans /api/visites/sortie : {e}')
    return jsonify({'erreur': f'Erreur interne du serveur : {str(e)}'}), 500


# ROUTE D'EXPORT DU RAPPORT 
@app.route('/api/rapport/semaine', methods=['GET'])
def rapport_semaine():
  """Exporte la liste des visites enregistrées durant les 7 derniers jours."""
  try:
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

    if request.args.get('format') == 'csv':
      output = StringIO()
      writer = csv.writer(output)

      writer.writerow([
          'ID',
          'Visiteur',
          'Téléphone',
          'Fonction',
          'Adresse',
          'Genre',
          'Hôte Visité',
          'Département',
          'Badge',
          'Heure Entrée',
          'Heure Sortie',
      ])

      for row in visites:
        writer.writerow([str(val) if val is not None else '' for val in row])

      output.seek(0)
      filename = f"rapport_visites_{datetime.now().strftime('%Y_%m_%d')}.csv"

      return Response(
          output.getvalue(),
          mimetype='text/csv',
          headers={'Content-Disposition': f'attachment;filename={filename}'},
      )

    return jsonify([dict(row) for row in visites]), 200

  except Exception as e:
    print(f'Erreur dans /api/rapport/semaine : {e}')
    return jsonify({'erreur': str(e)}), 500


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000, debug=True)