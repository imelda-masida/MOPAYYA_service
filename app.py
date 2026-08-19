from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'votre_cle_secrete_ici'  # Nécessaire pour gérer les sessions

# Décorateur pour vérifier la connexion admin
def admin_requis(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_connecte'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Route Racines (Borne d'accueil ou Redirection Admin)
@app.route('/')
def home():
    # Si tu veux que la borne d'accueil s'affiche :
    return render_template('index.html')
    # Si tu préférais tout rediriger vers l'admin, remplace par :
    # return redirect(url_for('admin_dashboard'))

# Route Connexion Admin
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        identifiant = request.form.get('identifiant')
        mot_de_passe = request.form.get('mot_de_passe')
        
        # Vérification des identifiants
        if identifiant == 'admin' and mot_de_passe == 'admin123':
            session['admin_connecte'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('login.html', erreur="Identifiant ou mot de passe incorrect.")
            
    return render_template('login.html')

# Route Déconnexion Admin
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_connecte', None)
    return redirect(url_for('admin_login'))

# Dashboard Admin Protégé
@app.route('/admin')
@admin_requis
def admin_dashboard():
    return render_template('admin.html')

# Routes API Protégées (données sensibles + téléchargements)
@app.route('/api/admin/visites')
@admin_requis
def api_admin_visites():
    # Logique pour retourner les visites
    pass

@app.route('/api/admin/stats')
@admin_requis
def api_admin_stats():
    # Logique pour retourner les statistiques
    pass

@app.route('/api/rapport/semaine')
@admin_requis
def exporter_rapport():
    # Logique de téléchargement CSV / PDF
    pass

# Lancement du serveur (A METTRE TOUJOURS À LA TOUTE FIN DU FICHIER)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)