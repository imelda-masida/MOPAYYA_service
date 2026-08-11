from flask import Flask, render_template, redirect, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB_NAME = 'database.db'

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()


    cursor.execute('''
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
                couleur_badge TEXT NOT NULL
            )
        ''')

    cursor.execute('''
            CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name_complet TEXT NOT NULL,
                department_id INTEGER NOT NULL,
                FOREIGN KEY (department_id) REFERENCES departments (id)
            )
        ''')


    cursor.execute('''
        CREATE TABLE IF NOT EXISTS badges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lettre TEXT NOT NULL,
            departement_id INTEGER,
            est_disponible INTEGER DEFAULT 1,
            FOREIGN KEY (departement_id) REFERENCES departements(id)
        )
     ''') 

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS visites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visiteur_nom TEXT NOT NULL,
            visiteur_tel TEXT,
            visiteur_fonction TEXT,
            visiteur_adresse TEXT,
            visiteur_genre TEXT,
            membre_id INTEGER,
            badge_id INTEGER,
            heure_entree TEXT,
            heure_sortie TEXT,
            FOREIGN KEY (membre_id) REFERENCES membres(id),
            FOREIGN KEY (badge_id) REFERENCES badges(id)
        )
    ''')

    conn.commit()
    conn.close()


    
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/membres', methods=['GET'])
def get_membres():
    conn = get_db()
    cursor = conn.cursor()
    membres = cursor.execute('''
        SELECT m.id, m.nom_complet, d.nom as departement, d.couleur_badge, d.id as dept_id 
        FROM membres m 
        JOIN departements d ON m.departement_id = d.id
    ''').fetchall()
    conn.close()
    return jsonify([dict(m) for m in membres])


@app.route('/api/entree', methods=['POST'])
def enregistrer_entree():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    
    badge = cursor.execute('''
        SELECT id, lettre FROM badges 
        WHERE departement_id = ? AND est_disponible = 1 
        LIMIT 1
    ''', (data['dept_id'],)).fetchone()
    
    if not badge:
        conn.close()
        return jsonify({'status': 'error', 'message': 'Aucun badge disponible pour ce département'}), 400
    
    heure_actuelle = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    
    cursor.execute('''
        INSERT INTO visites (visiteur_nom, visiteur_tel, visiteur_fonction, visiteur_adresse, visiteur_genre, membre_id, badge_id, heure_entree)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (data['nom'], data['tel'], data['fonction'], data['adresse'], data['genre'], data['membre_id'], badge['id'], heure_actuelle))
    
    
    cursor.execute('UPDATE badges SET est_disponible = 0 WHERE id = ?', (badge['id'],))
    
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'badge': badge['lettre'], 'heure': heure_actuelle})


@app.route('/api/sortie', methods=['POST'])
def enregistrer_sortie():
    data = request.json
    lettre_badge = data['badge_lettre'].strip().upper()
    heure_actuelle = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn = get_db()
    cursor = conn.cursor()
    
    
    badge = cursor.execute('SELECT id FROM badges WHERE lettre = ?', (lettre_badge,)).fetchone()
    if not badge:
        conn.close()
        return jsonify({'status': 'error', 'message': 'Badge introuvable'}), 404
        
    visite = cursor.execute('''
        SELECT id FROM visites 
        WHERE badge_id = ? AND heure_sortie IS NULL 
        ORDER BY id DESC LIMIT 1
    ''', (badge['id'],)).fetchone()
    
    if not visite:
        conn.close()
        return jsonify({'status': 'error', 'message': 'Aucune visite active trouvée pour ce badge'}), 404
    
    
    cursor.execute('UPDATE visites SET heure_sortie = ? WHERE id = ?', (heure_actuelle, visite['id']))
    cursor.execute('UPDATE badges SET est_disponible = 1 WHERE id = ?', (badge['id'],))
    
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'heure': heure_actuelle})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)

 