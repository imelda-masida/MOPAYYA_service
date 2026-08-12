import os
import sqlite3
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'mopaya.db')

def obtenir_connexion():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# 1. EXPORT CSV AVEC PANDAS
def exporter_visites_csv(fichier_sortie="rapport_visites.csv"):
    conn = obtenir_connexion()
    query = """
        SELECT 
            v.id AS Visite_ID,
            v.nom AS Visiteur,
            v.telephone AS Telephone,
            v.fonction AS Fonction,
            v.genre AS Genre,
            m.nom_complet AS Hote_Visite,
            v.badge_lettre AS Badge,
            v.heure_arrivee AS Arrivee,
            v.heure_sortie AS Sortie,
            v.statut AS Statut
        FROM visites v
        LEFT JOIN membres m ON v.membre_id = m.id
        ORDER BY v.heure_arrivee DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Génération du fichier CSV
    df.to_csv(fichier_sortie, index=False, encoding='utf-8-sig')
    return fichier_sortie

# 2. EXPORT PDF AVEC REPORTLAB
def generer_rapport_pdf(fichier_pdf="rapport_visites.pdf"):
    conn = obtenir_connexion()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT v.nom, v.telephone, m.nom_complet, v.badge_lettre, v.heure_arrivee, v.statut
        FROM visites v
        LEFT JOIN membres m ON v.membre_id = m.id
        ORDER BY v.heure_arrivee DESC
    """)
    visites = cursor.fetchall()
    conn.close()

    # Construction du document PDF
    doc = SimpleDocTemplate(fichier_pdf, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    
    styles = getSampleStyleSheet()
    titre_style = ParagraphStyle(
        'TitreRapport',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#0d6efd'),
        spaceAfter=12
    )
    
    # En-tête du document
    elements.append(Paragraph("MOPAYA - Rapport des Visites", titre_style))
    elements.append(Spacer(1, 15))

    # Tableau des données
    data = [["Visiteur", "Téléphone", "Hôte", "Badge", "Arrivée", "Statut"]]
    
    for v in visites:
        data.append([
            v["nom"] or "-",
            v["telephone"] or "-",
            v["nom_complet"] or "-",
            v["badge_lettre"] or "-",
            v["heure_arrivee"] or "-",
            v["statut"] or "-"
        ])

    tableau = Table(data, colWidths=[110, 80, 110, 50, 120, 60])
    tableau.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ced4da')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    
    elements.append(tableau)
    doc.build(elements)
    return fichier_pdf