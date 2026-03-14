# -*- coding: utf-8 -*-
"""
maintenance_predictive_app.py
Application Streamlit pour la maintenance prédictive
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import hashlib
import sqlite3
import time
from PIL import Image
import requests
from io import BytesIO

# Configuration de la page
st.set_page_config(
    page_title="Maintenance Prédictive",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Styles CSS personnalisés
st.markdown("""
<style>
    /* Style global - arrière-plan gris clair */
    .stApp {
        background-color: #f5f5f5;
    }
    
    /* Augmentation de la taille de police de base (encore plus grande) */
    html, body, [class*="css"] {
        font-size: 18px;
    }
    
    /* Conteneur principal */
    .main-container {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.05);
        margin: 1rem auto;
    }
    
    /* Titres */
    .title {
        color: #2c3e50;
        font-size: 2.8rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        text-align: left;
        background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .subtitle {
        color: #7f8c8d;
        font-size: 1.2rem;
        text-align: left;
        margin-bottom: 2rem;
    }
    
    /* Formulaire */
    .login-form {
        background: white;
        padding: 2.5rem;
        border-radius: 20px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.03);
        border: 1px solid #e0e0e0;
    }
    
    .form-title {
        color: #2c3e50;
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    /* Boutons */
    .stButton > button {
        background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(52, 152, 219, 0.3);
    }
    
    /* Onglets Connexion / Inscription - encore plus grands et en noir */
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 1.4rem !important;
        color: black !important;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        color: black !important;
    }
    
    /* Description page */
    .page-description {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        border-left: 5px solid #3498db;
        box-shadow: 0 2px 10px rgba(0,0,0,0.02);
    }
    
    .page-title {
        color: #2c3e50;
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 1rem;
    }
    
    .page-desc-text {
        color: #5f6b7a;
        font-size: 1.1rem;
        line-height: 1.6;
    }
    
    /* Signature */
    .signature {
        text-align: center;
        margin-top: 2rem;
        padding: 1rem;
        color: #7f8c8d;
        font-size: 0.9rem;
        border-top: 1px solid #e0e0e0;
    }
    
    .signature strong {
        color: #3498db;
        font-weight: 600;
    }
    
    /* Cartes statistiques */
    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.02);
        text-align: center;
        border: 1px solid #e0e0e0;
        transition: all 0.3s ease;
    }
    
    .stat-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 5px 20px rgba(0,0,0,0.05);
    }
    
    .stat-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #3498db;
        margin: 0.5rem 0;
    }
    
    .stat-label {
        color: #7f8c8d;
        font-size: 1rem;
    }
    
    /* Pied de page */
    .footer {
        text-align: center;
        padding: 2rem;
        color: #7f8c8d;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialisation de la base de données
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         username TEXT UNIQUE NOT NULL,
         email TEXT UNIQUE NOT NULL,
         password TEXT NOT NULL,
         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    ''')
    conn.commit()
    conn.close()

# Fonction de hachage
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Création d'utilisateur
def create_user(username, email, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                  (username, email, hash_password(password)))
        conn.commit()
        return True, "Compte créé avec succès !"
    except sqlite3.IntegrityError as e:
        if "username" in str(e):
            return False, "Ce nom d'utilisateur est déjà pris"
        else:
            return False, "Cet email est déjà utilisé"
    finally:
        conn.close()

# Vérification des identifiants
def verify_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?",
              (username, hash_password(password)))
    user = c.fetchone()
    conn.close()
    return user is not None

# Chargement de l'image
@st.cache_data
def load_image():
    try:
        # URL de l'image
        image_url = "https://i.pinimg.com/1200x/e3/a2/a4/e3a2a403906fefa78cb86db8aef6cc7c.jpg"
        
        # En-têtes pour imiter un navigateur
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(image_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            return img
        else:
            return None
    except:
        return None

# Génération des données pour l'historique
@st.cache_data
def generate_history_data():
    np.random.seed(42)  # Pour avoir des données reproductibles
    machines = ['Machine A', 'Machine B', 'Machine C']
    types_panne = ['Mécanique', 'Électrique', 'Thermique', 'Vibration', 'Usure']
    actions = ['Inspection', 'Réparation', 'Remplacement', 'Calibration', 'Maintenance']
    
    data = []
    for i in range(100):  # Génère 100 entrées
        date = pd.Timestamp('2024-01-01') + pd.Timedelta(days=np.random.randint(0, 90))
        machine = np.random.choice(machines)
        type_panne = np.random.choice(types_panne)
        prob = np.random.random()
        action = np.random.choice(actions)
        statut = '✅ Résolu' if prob < 0.7 else '⚠️ En cours'
        
        data.append({
            'Date': date,
            'Machine': machine,
            'Type de panne': type_panne,
            'Probabilité': prob,
            'Action menée': action,
            'Statut': statut
        })
    
    return pd.DataFrame(data).sort_values('Date', ascending=False)

# Descriptions des pages
page_descriptions = {
    "🏠 Accueil": {
        "title": "Tableau de bord principal",
        "desc": "Visualisez en temps réel l'état de vos équipements et les indicateurs clés de performance. Surveillez les alertes et consultez les statistiques globales de votre parc machine."
    },
    "🔮 Prédictions": {
        "title": "Prédictions de pannes",
        "desc": "Utilisez notre modèle d'intelligence artificielle pour prédire les risques de panne. Entrez les paramètres de votre machine et obtenez une probabilité de défaillance avec des recommandations personnalisées."
    },
    "📊 Analyses": {
        "title": "Analyses approfondies",
        "desc": "Explorez les données historiques, identifiez les tendances et les patterns de défaillance. Des graphiques interactifs pour une compréhension optimale de vos équipements."
    },
    "📁 Historique": {
        "title": "Historique des interventions",
        "desc": "Consultez l'ensemble des prédictions et interventions passées. Filtrez par date, machine ou type de panne pour une traçabilité complète."
    },
    "⚙️ Paramètres": {
        "title": "Configuration du système",
        "desc": "Personnalisez votre espace de travail, gérez les notifications et configurez les alertes selon vos préférences."
    }
}

# Page de login
def login_page():
    with st.container():
        col1, col2 = st.columns([1, 1], gap="large")
        
        with col1:
            st.markdown('<h1 class="title">🔧 Predictive Maintenance</h1>', unsafe_allow_html=True)
            st.markdown('<p class="subtitle">Système intelligent de maintenance prédictive basé sur l\'IA</p>', unsafe_allow_html=True)
            
            st.markdown('<div class="login-form">', unsafe_allow_html=True)
            
            # Onglets
            tab1, tab2 = st.tabs(["🔐 Connexion", "📝 Inscription"])
            
            with tab1:
                st.markdown('<p class="form-title">Bienvenue !</p>', unsafe_allow_html=True)
                
                username = st.text_input("Nom d'utilisateur", placeholder="Entrez votre nom d'utilisateur", key="login_user")
                password = st.text_input("Mot de passe", type="password", placeholder="Entrez votre mot de passe", key="login_pass")
                
                if st.button("Se connecter", key="login_btn", use_container_width=True):
                    if username and password:
                        if verify_user(username, password):
                            st.session_state['authenticated'] = True
                            st.session_state['username'] = username
                            st.session_state['login_time'] = datetime.now().strftime("%H:%M:%S")
                            st.success("✅ Connexion réussie !")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Identifiants incorrects")
                    else:
                        st.warning("⚠️ Veuillez remplir tous les champs")
                
               
            
            with tab2:
                st.markdown('<p class="form-title">Créez votre compte</p>', unsafe_allow_html=True)
                
                new_username = st.text_input("Nom d'utilisateur", placeholder="Choisissez un nom d'utilisateur", key="signup_user")
                new_email = st.text_input("Email", placeholder="Entrez votre email", key="signup_email")
                new_password = st.text_input("Mot de passe", type="password", placeholder="Choisissez un mot de passe", key="signup_pass")
                confirm_pass = st.text_input("Confirmez le mot de passe", type="password", placeholder="Confirmez votre mot de passe", key="confirm_pass")
                
                if st.button("Créer mon compte", key="signup_btn", use_container_width=True):
                    if new_username and new_email and new_password and confirm_pass:
                        if new_password == confirm_pass:
                            if len(new_password) >= 6:
                                success, message = create_user(new_username, new_email, new_password)
                                if success:
                                    st.success(f"✅ {message}")
                                else:
                                    st.error(f"❌ {message}")
                            else:
                                st.error("❌ Le mot de passe doit contenir au moins 6 caractères")
                        else:
                            st.error("❌ Les mots de passe ne correspondent pas")
                    else:
                        st.warning("⚠️ Veuillez remplir tous les champs")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Signature
            st.markdown("""
            <div class="signature">
                Réalisé par <strong>KHAIROUR Ikram</strong> © 2024
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Image
            img = load_image()
            if img:
                st.image(img, use_container_width=True)
            else:
                st.markdown("<h1 style='text-align: center; font-size: 8rem;'>🏭</h1>", unsafe_allow_html=True)
                st.markdown("<p style='text-align: center; color: #7f8c8d;'>Maintenance prédictive industrielle 4.0</p>", unsafe_allow_html=True)

# Dashboard principal
def dashboard():
    # Menu horizontal
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
        <h1 style="color: #2c3e50; margin: 0;">🔧 Predictive Maintenance</h1>
        <div style="background: white; padding: 0.5rem 1.5rem; border-radius: 50px; border: 1px solid #e0e0e0;">
            👤 {} | {} ⏰
        </div>
    </div>
    """.format(st.session_state['username'], st.session_state.get('login_time', '')), unsafe_allow_html=True)
    
    # Menu horizontal
    col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 1])
    
    with col1:
        if st.button("🏠 Accueil", use_container_width=True):
            st.session_state['page'] = "🏠 Accueil"
    with col2:
        if st.button("🔮 Prédictions", use_container_width=True):
            st.session_state['page'] = "🔮 Prédictions"
    with col3:
        if st.button("📊 Analyses", use_container_width=True):
            st.session_state['page'] = "📊 Analyses"
    with col4:
        if st.button("📁 Historique", use_container_width=True):
            st.session_state['page'] = "📁 Historique"
    with col5:
        if st.button("⚙️ Paramètres", use_container_width=True):
            st.session_state['page'] = "⚙️ Paramètres"
    with col6:
        if st.button("🚪 Déconnexion", use_container_width=True):
            st.session_state['authenticated'] = False
            st.rerun()
    
    # Initialiser la page si non définie
    if 'page' not in st.session_state:
        st.session_state['page'] = "🏠 Accueil"
    
    # Description de la page
    current_page = st.session_state['page']
    if current_page in page_descriptions:
        st.markdown(f"""
        <div class="page-description">
            <div class="page-title">{page_descriptions[current_page]['title']}</div>
            <div class="page-desc-text">{page_descriptions[current_page]['desc']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Contenu des pages
    if current_page == "🏠 Accueil":
        # Statistiques
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="stat-card">
                <div style="font-size: 2rem;">🏭</div>
                <div class="stat-value">24</div>
                <div class="stat-label">Machines surveillées</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="stat-card">
                <div style="font-size: 2rem;">⚠️</div>
                <div class="stat-value">3</div>
                <div class="stat-label">Alertes critiques</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="stat-card">
                <div style="font-size: 2rem;">✅</div>
                <div class="stat-value">98%</div>
                <div class="stat-label">Précision</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div class="stat-card">
                <div style="font-size: 2rem;">📅</div>
                <div class="stat-value">12</div>
                <div class="stat-label">Maintenances</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Graphiques
        col1, col2 = st.columns(2)
        
        with col1:
            dates = pd.date_range(start='2024-01-01', periods=7, freq='D')
            values = np.random.randint(50, 150, size=7)
            
            fig = px.line(x=dates, y=values, title="Évolution des prédictions")
            fig.update_layout(
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(size=12)
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            labels = ['Faible risque', 'Risque modéré', 'Risque élevé']
            values = [45, 30, 25]
            colors = ['#2ecc71', '#f1c40f', '#e74c3c']
            
            fig = go.Figure(data=[go.Pie(labels=labels, values=values, marker=dict(colors=colors))])
            fig.update_layout(
                title="Distribution des risques",
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    elif current_page == "🔮 Prédictions":
        with st.form("prediction_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                vibration = st.number_input("Vibration RMS (mm/s)", min_value=0.0, max_value=100.0, value=5.0)
                temperature = st.number_input("Température moteur (°C)", min_value=0.0, max_value=200.0, value=75.0)
                current = st.number_input("Courant phase (A)", min_value=0.0, max_value=500.0, value=150.0)
            
            with col2:
                pressure = st.number_input("Pression (bar)", min_value=0.0, max_value=100.0, value=4.5)
                rpm = st.number_input("RPM", min_value=0, max_value=10000, value=1500)
                rul = st.number_input("RUL (heures)", min_value=0, max_value=10000, value=500)
            
            submitted = st.form_submit_button("Lancer la prédiction", use_container_width=True)
            
            if submitted:
                with st.spinner("Analyse en cours..."):
                    time.sleep(2)
                    probability = np.random.random()
                    
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=probability * 100,
                        domain={'x': [0, 1], 'y': [0, 1]},
                        title={'text': "Probabilité de panne"},
                        gauge={
                            'axis': {'range': [None, 100]},
                            'bar': {'color': "#3498db"},
                            'steps': [
                                {'range': [0, 30], 'color': "#2ecc71"},
                                {'range': [30, 70], 'color': "#f1c40f"},
                                {'range': [70, 100], 'color': "#e74c3c"}
                            ]
                        }
                    ))
                    
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    if probability > 0.7:
                        st.error(f"⚠️ Risque élevé : {probability*100:.1f}%")
                    elif probability > 0.3:
                        st.warning(f"⚠️ Risque modéré : {probability*100:.1f}%")
                    else:
                        st.success(f"✅ Risque faible : {probability*100:.1f}%")
    
    elif current_page == "📊 Analyses":
        st.subheader("Analyses des données")
        
        # Sélecteur de période
        period = st.selectbox("Période d'analyse", ["7 derniers jours", "30 derniers jours", "3 derniers mois", "Année complète"])
        
        # Graphiques d'analyse
        col1, col2 = st.columns(2)
        
        with col1:
            # Histogramme des températures
            temp_data = np.random.normal(75, 10, 1000)
            fig = px.histogram(temp_data, nbins=30, title="Distribution des températures")
            fig.update_layout(plot_bgcolor='white', paper_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Corrélation
            machines = ['M1', 'M2', 'M3', 'M4']
            corr_data = np.random.rand(4, 4)
            fig = px.imshow(corr_data, 
                          labels=dict(x="Machine", y="Machine", color="Corrélation"),
                          x=machines, y=machines,
                          title="Matrice de corrélation")
            fig.update_layout(plot_bgcolor='white', paper_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)
    
    elif current_page == "📁 Historique":
        st.subheader("Historique des interventions")
        
        # Charger les données
        df_historique = generate_history_data()
        
        # Filtres en haut
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Période**")
            min_date = df_historique['Date'].min().date()
            max_date = df_historique['Date'].max().date()
            date_range = st.date_input(
                "",
                value=(min_date, max_date),
                label_visibility="collapsed",
                key="date_hist"
            )
        
        with col2:
            st.markdown("**Machine**")
            machines_list = ["Toutes"] + sorted(df_historique['Machine'].unique().tolist())
            machine = st.selectbox("", machines_list, label_visibility="collapsed", key="machine_hist")
        
        with col3:
            st.markdown("**Statut**")
            status_list = ["Tous", "✅ Résolu", "⚠️ En cours"]
            status = st.selectbox("", status_list, label_visibility="collapsed", key="status_hist")
        
        # Bouton de filtrage
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            filtrer = st.button("🔍 Filtrer", use_container_width=True)
        
        # Initialiser les filtres dans session state
        if 'filtres_historique' not in st.session_state:
            st.session_state['filtres_historique'] = {
                'date_range': (min_date, max_date),
                'machine': "Toutes",
                'status': "Tous"
            }
        
        # Mettre à jour les filtres quand on clique sur le bouton
        if filtrer:
            st.session_state['filtres_historique'] = {
                'date_range': date_range,
                'machine': machine,
                'status': status
            }
        
        # Appliquer les filtres
        df_filtered = df_historique.copy()
        filtres = st.session_state['filtres_historique']
        
        # Filtre par date
        if len(filtres['date_range']) == 2:
            start_date, end_date = filtres['date_range']
            df_filtered = df_filtered[
                (df_filtered['Date'].dt.date >= start_date) & 
                (df_filtered['Date'].dt.date <= end_date)
            ]
        
        # Filtre par machine
        if filtres['machine'] != "Toutes":
            df_filtered = df_filtered[df_filtered['Machine'] == filtres['machine']]
        
        # Filtre par statut
        if filtres['status'] != "Tous":
            df_filtered = df_filtered[df_filtered['Statut'] == filtres['status']]
        
        # Formatage des probabilités
        df_filtered['Probabilité'] = df_filtered['Probabilité'].apply(lambda x: f"{x:.4f}")
        
        # Affichage du nombre de résultats
        st.markdown(f"**{len(df_filtered)} résultats trouvés**")
        
        # Affichage du tableau
        st.dataframe(
            df_filtered,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Date": st.column_config.DatetimeColumn("Date", format="YYYY-MM-DD HH:mm:ss"),
                "Probabilité": st.column_config.TextColumn("Probabilité"),
            }
        )
        
        # Légende des statuts en bas
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Statut**")
        with col2:
            st.markdown("✅ Résolu  ⚠️ En cours")
        
        # Téléchargement des données filtrées
        if len(df_filtered) > 0:
            csv = df_filtered.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Télécharger les données filtrées (CSV)",
                data=csv,
                file_name=f"historique_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    elif current_page == "⚙️ Paramètres":
        st.subheader("Paramètres du système")
        
        with st.form("settings_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**👤 Informations personnelles**")
                email = st.text_input("Email", value=f"{st.session_state['username']}@company.com")
                company = st.text_input("Entreprise", value="Industrie Maintenance")
                language = st.selectbox("Langue", ["Français", "English", "Español", "Deutsch"])
            
            with col2:
                st.markdown("**🔔 Notifications**")
                email_notif = st.checkbox("Notifications par email", value=True)
                sms_notif = st.checkbox("Notifications SMS", value=False)
                alert_threshold = st.slider("Seuil d'alerte (%)", 0, 100, 70)
            
            submitted = st.form_submit_button("Sauvegarder", use_container_width=True)
            if submitted:
                st.success("✅ Paramètres mis à jour avec succès !")
    
    # Signature dans le dashboard
    st.markdown("""
    <div class="footer">
        Réalisé par <strong>KHAIROUR Ikram</strong> © 2024 - Tous droits réservés
    </div>
    """, unsafe_allow_html=True)

# Point d'entrée
if __name__ == "__main__":
    # Initialisation
    init_db()
    
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    
    # Création d'un compte démo
    create_user("demo", "demo@example.com", "demo123")
    
    # Affichage
    if st.session_state['authenticated']:
        dashboard()
    else:
        login_page()