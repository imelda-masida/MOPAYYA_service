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


    

 