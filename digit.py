import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
from io import BytesIO
import base64

# Configuration de la page
st.set_page_config(
    page_title="Gestion Fiches Digitalisation Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé amélioré
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    .kpi-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        border-left: 4px solid;
        transition: transform 0.2s, box-shadow 0.2s;
        height: 100%;
    }
    
    .kpi-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.15);
    }
    
    .evolution-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-left: 0.5rem;
    }
    
    .evolution-positive {
        background: #d1fae5;
        color: #065f46;
    }
    
    .evolution-negative {
        background: #fee2e2;
        color: #991b1b;
    }
    
    .evolution-neutral {
        background: #e0e7ff;
        color: #3730a3;
    }
    
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
    }
    
    .status-termine {
        background: #d1fae5;
        color: #065f46;
    }
    
    .status-encours {
        background: #fef3c7;
        color: #92400e;
    }
    
    .status-attente {
        background: #e0e7ff;
        color: #3730a3;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s;
        border: none;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# Fichiers de sauvegarde
SAVE_FILE = "fiches_data.json"
RAPPORTS_FILE = "rapports_historique.json"

# Configuration des sous-systèmes
SOUS_SYSTEMES_CONFIG = {
    'Voie ferrée': {'responsable_defaut': 'MOUSSE', 'couleur': '#3b82f6'},
    'Catenaire': {'responsable_defaut': 'Ange', 'couleur': '#10b981'},
    'Courant fort': {'responsable_defaut': 'Hamed Samagaci', 'couleur': '#f59e0b'},
    'Courant faible': {'responsable_defaut': 'Non assigné', 'couleur': '#ef4444'}
}

LISTE_RESPONSABLES = [
    'MOUSSE', 'Ange', 'Hamed Samagaci', 'Responsable qualité', 'Non assigné', 'Autre'
]

# Initialisation
def init_session_state():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'fiches' not in st.session_state:
        st.session_state.fiches = []
    if 'objectifs' not in st.session_state:
        st.session_state.objectifs = {
            'Voie ferrée': 0,
            'Catenaire': 5,
            'Courant fort': 0,
            'Courant faible': 0
        }
    if 'rapports_historique' not in st.session_state:
        st.session_state.rapports_historique = []
    if 'fiche_a_modifier' not in st.session_state:
        st.session_state.fiche_a_modifier = None
    load_data()

def load_data():
    """Charge les données depuis les fichiers JSON"""
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                st.session_state.fiches = data.get('fiches', [])
                st.session_state.objectifs = data.get('objectifs', st.session_state.objectifs)
        except:
            pass
    
    if os.path.exists(RAPPORTS_FILE):
        try:
            with open(RAPPORTS_FILE, 'r', encoding='utf-8') as f:
                st.session_state.rapports_historique = json.load(f)
        except:
            st.session_state.rapports_historique = []

def save_data():
    """Sauvegarde les données dans les fichiers JSON"""
    data = {
        'fiches': st.session_state.fiches,
        'objectifs': st.session_state.objectifs
    }
    with open(SAVE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_rapports():
    """Sauvegarde l'historique des rapports"""
    with open(RAPPORTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(st.session_state.rapports_historique, f, ensure_ascii=False, indent=2)

def generer_snapshot():
    """Génère un snapshot de l'état actuel pour comparaison"""
    stats = calculer_stats()
    
    snapshot = {
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_fiches': len(st.session_state.fiches),
        'fiches_terminees': len([f for f in st.session_state.fiches if f['statut'] == 'Terminé']),
        'fiches_en_cours': len([f for f in st.session_state.fiches if f['statut'] == 'En cours']),
        'fiches_en_attente': len([f for f in st.session_state.fiches if f['statut'] == 'En attente']),
        'sous_systemes': {}
    }
    
    for ss, data in stats.items():
        snapshot['sous_systemes'][ss] = {
            'objectif': data['objectif'],
            'termine': data['termine'],
            'en_cours': data['en_cours'],
            'taux_avancement': data['taux_avancement']
        }
    
    return snapshot

def calculer_evolution(snapshot_actuel, snapshot_precedent):
    """Calcule l'évolution entre deux snapshots"""
    if not snapshot_precedent:
        return None
    
    evolution = {
        'total_fiches': snapshot_actuel['total_fiches'] - snapshot_precedent['total_fiches'],
        'fiches_terminees': snapshot_actuel['fiches_terminees'] - snapshot_precedent['fiches_terminees'],
        'fiches_en_cours': snapshot_actuel['fiches_en_cours'] - snapshot_precedent['fiches_en_cours'],
        'fiches_en_attente': snapshot_actuel['fiches_en_attente'] - snapshot_precedent['fiches_en_attente'],
        'jours_ecoules': (datetime.strptime(snapshot_actuel['date'], '%Y-%m-%d %H:%M:%S') - 
                         datetime.strptime(snapshot_precedent['date'], '%Y-%m-%d %H:%M:%S')).days,
        'sous_systemes': {}
    }
    
    for ss in snapshot_actuel['sous_systemes']:
        if ss in snapshot_precedent['sous_systemes']:
            evolution['sous_systemes'][ss] = {
                'termine': snapshot_actuel['sous_systemes'][ss]['termine'] - 
                          snapshot_precedent['sous_systemes'][ss]['termine'],
                'taux_avancement': snapshot_actuel['sous_systemes'][ss]['taux_avancement'] - 
                                  snapshot_precedent['sous_systemes'][ss]['taux_avancement']
            }
    
    return evolution

def get_evolution_badge(valeur, prefix=""):
    """Retourne un badge d'évolution coloré"""
    if valeur > 0:
        return f'<span class="evolution-badge evolution-positive">▲ {prefix}{valeur}</span>'
    elif valeur < 0:
        return f'<span class="evolution-badge evolution-negative">▼ {prefix}{abs(valeur)}</span>'
    else:
        return f'<span class="evolution-badge evolution-neutral">— {prefix}{valeur}</span>'

def page_login():
    """Page de connexion"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        st.markdown("""
        <div style='text-align: center; margin-bottom: 2rem;'>
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        width: 100px; height: 100px; margin: 0 auto; border-radius: 50%;
                        display: flex; align-items: center; justify-content: center;
                        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);'>
                <span style='font-size: 3rem;'>📊</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<h1 style='text-align: center; color: #1f2937;'>Gestion des Fiches Pro</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #6b7280; margin-bottom: 2rem;'>Système de digitalisation et suivi avancé</p>", unsafe_allow_html=True)
        
        with st.container():
            username = st.text_input("👤 Nom d'utilisateur", placeholder="yves niamke")
            password = st.text_input("🔒 Mot de passe", type="password", placeholder="••••••••")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("🚀 Se connecter", use_container_width=True, type="primary"):
                if username == "yves niamke" and password == "papachoco":
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("❌ Identifiants incorrects")
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #9ca3af; font-size: 0.85rem;'>© 2024 Système de Gestion Pro - Tous droits réservés</p>", unsafe_allow_html=True)

def calculer_stats():
    """Calcule les statistiques par sous-système"""
    stats = {}
    
    for ss in SOUS_SYSTEMES_CONFIG.keys():
        fiches_ss = [f for f in st.session_state.fiches if f['sous_systeme'] == ss]
        objectif = st.session_state.objectifs[ss]
        termine = len([f for f in fiches_ss if f['statut'] == 'Terminé'])
        en_cours = len(fiches_ss)
        
        stats[ss] = {
            'objectif': objectif,
            'termine': termine,
            'en_cours': en_cours,
            'taux_avancement': round((termine / objectif * 100), 1) if objectif > 0 else 0,
            'taux_realisation': round((termine / en_cours * 100), 1) if en_cours > 0 else 0,
            'couleur': SOUS_SYSTEMES_CONFIG[ss]['couleur']
        }
    
    return stats

def get_status_badge(statut):
    """Retourne un badge HTML coloré selon le statut"""
    class_map = {
        'Terminé': 'status-termine',
        'En cours': 'status-encours',
        'En attente': 'status-attente'
    }
    return f'<span class="status-badge {class_map.get(statut, "status-encours")}">{statut}</span>'

def afficher_dashboard_evolution():
    """Affiche le dashboard avec les KPIs d'évolution"""
    st.markdown("### 📈 Tableau de Bord avec Évolution")
    
    # Générer le snapshot actuel
    snapshot_actuel = generer_snapshot()
    
    # Récupérer le dernier rapport (snapshot précédent)
    snapshot_precedent = None
    if st.session_state.rapports_historique:
        snapshot_precedent = st.session_state.rapports_historique[-1]
    
    # Calculer l'évolution
    evolution = calculer_evolution(snapshot_actuel, snapshot_precedent)
    
    # Afficher les KPIs globaux avec évolution
    st.markdown("#### 🎯 Indicateurs Globaux")
    cols = st.columns(4)
    
    kpis = [
        {
            'titre': 'Total Fiches',
            'valeur': snapshot_actuel['total_fiches'],
            'evolution': evolution['total_fiches'] if evolution else 0,
            'couleur': '#3b82f6',
            'icon': '📋'
        },
        {
            'titre': 'Terminées',
            'valeur': snapshot_actuel['fiches_terminees'],
            'evolution': evolution['fiches_terminees'] if evolution else 0,
            'couleur': '#10b981',
            'icon': '✅'
        },
        {
            'titre': 'En Cours',
            'valeur': snapshot_actuel['fiches_en_cours'],
            'evolution': evolution['fiches_en_cours'] if evolution else 0,
            'couleur': '#f59e0b',
            'icon': '🔄'
        },
        {
            'titre': 'En Attente',
            'valeur': snapshot_actuel['fiches_en_attente'],
            'evolution': evolution['fiches_en_attente'] if evolution else 0,
            'couleur': '#ef4444',
            'icon': '⏸️'
        }
    ]
    
    for idx, kpi in enumerate(kpis):
        with cols[idx]:
            evolution_badge = get_evolution_badge(kpi['evolution'])
            
            st.markdown(f"""
            <div class="kpi-card" style="border-left-color: {kpi['couleur']};">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">{kpi['icon']}</div>
                <h4 style="margin: 0; color: #6b7280; font-size: 0.9rem; font-weight: 500;">{kpi['titre']}</h4>
                <h2 style="margin: 0.5rem 0; font-size: 2.5rem; font-weight: 700; color: {kpi['couleur']};">{kpi['valeur']}</h2>
                <div style="margin-top: 0.5rem;">{evolution_badge}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # KPIs par sous-système avec évolution
    st.markdown("#### 🔧 Performance par Sous-système")
    stats = calculer_stats()
    cols = st.columns(4)
    
    for idx, (ss, data) in enumerate(stats.items()):
        with cols[idx]:
            progression = (data['termine'] / data['objectif'] * 100) if data['objectif'] > 0 else 0
            
            evolution_ss = ""
            if evolution and ss in evolution['sous_systemes']:
                ev_termine = evolution['sous_systemes'][ss]['termine']
                ev_taux = evolution['sous_systemes'][ss]['taux_avancement']
                evolution_ss = f"{get_evolution_badge(ev_termine)} {get_evolution_badge(ev_taux, prefix='')}"
            
            st.markdown(f"""
            <div class="kpi-card" style="border-left-color: {data['couleur']};">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
                    <h4 style="margin: 0; color: {data['couleur']}; font-size: 0.95rem; font-weight: 600;">{ss}</h4>
                    <span style="background: {data['couleur']}15; color: {data['couleur']}; 
                                 padding: 0.25rem 0.5rem; border-radius: 6px; font-size: 0.75rem; font-weight: 600;">
                        {data['taux_avancement']}%
                    </span>
                </div>
                <h2 style="margin: 0 0 0.5rem 0; font-size: 2rem; font-weight: 700; color: #1f2937;">
                    {data['termine']}<span style="font-size: 1.2rem; color: #9ca3af;"> / {data['objectif']}</span>
                </h2>
                <div style="background: #f3f4f6; height: 8px; border-radius: 4px; overflow: hidden; margin-bottom: 0.75rem;">
                    <div style="background: {data['couleur']}; height: 100%; width: {min(progression, 100)}%; 
                                border-radius: 4px; transition: width 0.3s;"></div>
                </div>
                <p style="margin: 0 0 0.5rem 0; color: #6b7280; font-size: 0.85rem;">
                    📋 {data['en_cours']} fiche(s) digitalisée(s)
                </p>
                <div style="margin-top: 0.5rem;">{evolution_ss}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Afficher la période de comparaison
    if evolution and snapshot_precedent:
        jours = evolution['jours_ecoules']
        date_precedente = datetime.strptime(snapshot_precedent['date'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
        st.info(f"📊 Évolution depuis le dernier rapport du {date_precedente} ({jours} jour(s))")

def generer_graphiques_avances():
    """Génère des graphiques avancés pour les rapports"""
    stats = calculer_stats()
    
    # Graphique 1: Comparaison Objectif vs Réalisé avec évolution
    st.markdown("### 📊 Analyse Graphique Avancée")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Objectifs vs Réalisations")
        
        df_bar = pd.DataFrame({
            'Sous-système': list(stats.keys()),
            'Objectif': [data['objectif'] for data in stats.values()],
            'Terminées': [data['termine'] for data in stats.values()],
            'Restantes': [max(0, data['objectif'] - data['termine']) for data in stats.values()],
            'En cours': [data['en_cours'] - data['termine'] for data in stats.values()]
        })
        
        fig_bar = go.Figure()
        
        fig_bar.add_trace(go.Bar(
            name='Objectif',
            x=df_bar['Sous-système'],
            y=df_bar['Objectif'],
            marker_color='#3b82f6',
            text=df_bar['Objectif'],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Objectif: %{y}<extra></extra>'
        ))
        
        fig_bar.add_trace(go.Bar(
            name='Terminées',
            x=df_bar['Sous-système'],
            y=df_bar['Terminées'],
            marker_color='#10b981',
            text=df_bar['Terminées'],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Terminées: %{y}<extra></extra>'
        ))
        
        fig_bar.update_layout(
            barmode='group',
            height=400,
            xaxis_title="",
            yaxis_title="Nombre de fiches",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode='x unified',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col2:
        st.markdown("#### Répartition des Statuts")
        
        statuts = {
            'Terminé': len([f for f in st.session_state.fiches if f['statut'] == 'Terminé']),
            'En cours': len([f for f in st.session_state.fiches if f['statut'] == 'En cours']),
            'En attente': len([f for f in st.session_state.fiches if f['statut'] == 'En attente'])
        }
        
        fig_pie = go.Figure(data=[go.Pie(
            labels=list(statuts.keys()),
            values=list(statuts.values()),
            hole=0.5,
            marker_colors=['#10b981', '#f59e0b', '#ef4444'],
            textinfo='label+percent+value',
            textfont_size=12,
            hovertemplate='<b>%{label}</b><br>%{value} fiches<br>%{percent}<extra></extra>'
        )])
        
        fig_pie.update_layout(
            height=400,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
            annotations=[dict(text=f'{sum(statuts.values())}<br>Fiches', x=0.5, y=0.5, font_size=20, showarrow=False)]
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # Graphique 3: Taux d'avancement par sous-système (Gauge)
    st.markdown("#### 🎯 Taux d'Avancement par Sous-système")
    cols = st.columns(4)
    
    for idx, (ss, data) in enumerate(stats.items()):
        with cols[idx]:
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=data['taux_avancement'],
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': ss, 'font': {'size': 14}},
                delta={'reference': 100, 'suffix': '%'},
                gauge={
                    'axis': {'range': [None, 100], 'tickwidth': 1},
                    'bar': {'color': data['couleur']},
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "gray",
                    'steps': [
                        {'range': [0, 50], 'color': '#fee2e2'},
                        {'range': [50, 80], 'color': '#fef3c7'},
                        {'range': [80, 100], 'color': '#d1fae5'}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            
            fig_gauge.update_layout(
                height=250,
                margin=dict(l=20, r=20, t=50, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                font={'size': 12}
            )
            
            st.plotly_chart(fig_gauge, use_container_width=True)
    
    # Graphique 4: Timeline des fiches (si données disponibles)
    if st.session_state.fiches:
        st.markdown("#### 📅 Timeline des Fiches Digitalisées")
        
        df_timeline = pd.DataFrame(st.session_state.fiches)
        df_timeline['date_reception'] = pd.to_datetime(df_timeline['date_reception'])
        df_timeline['mois'] = df_timeline['date_reception'].dt.to_period('M').astype(str)
        
        timeline_data = df_timeline.groupby(['mois', 'sous_systeme']).size().reset_index(name='count')
        
        fig_timeline = px.line(
            timeline_data,
            x='mois',
            y='count',
            color='sous_systeme',
            markers=True,
            title="Évolution du nombre de fiches par mois",
            color_discrete_map={ss: SOUS_SYSTEMES_CONFIG[ss]['couleur'] for ss in SOUS_SYSTEMES_CONFIG.keys()}
        )
        
        fig_timeline.update_layout(
            height=350,
            xaxis_title="Mois",
            yaxis_title="Nombre de fiches",
            hovermode='x unified',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig_timeline, use_container_width=True)
    
    # Graphique 5: Vélocité et tendances
    if len(st.session_state.rapports_historique) > 1:
        st.markdown("#### 📈 Tendances et Vélocité")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Graphique d'évolution du nombre de fiches terminées
            dates = [r['date'] for r in st.session_state.rapports_historique]
            terminees = [r['fiches_terminees'] for r in st.session_state.rapports_historique]
            
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                x=dates,
                y=terminees,
                mode='lines+markers',
                name='Fiches terminées',
                line=dict(color='#10b981', width=3),
                marker=dict(size=8),
                fill='tozeroy',
                fillcolor='rgba(16, 185, 129, 0.1)'
            ))
            
            fig_trend.update_layout(
                title="Évolution des Fiches Terminées",
                xaxis_title="Date",
                yaxis_title="Nombre de fiches",
                height=300,
                hovermode='x unified',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            st.plotly_chart(fig_trend, use_container_width=True)
        
        with col2:
            # Calcul de la vélocité
            velocites = []
            for i in range(1, len(st.session_state.rapports_historique)):
                delta_fiches = (st.session_state.rapports_historique[i]['fiches_terminees'] - 
                              st.session_state.rapports_historique[i-1]['fiches_terminees'])
                date1 = datetime.strptime(st.session_state.rapports_historique[i-1]['date'], '%Y-%m-%d %H:%M:%S')
                date2 = datetime.strptime(st.session_state.rapports_historique[i]['date'], '%Y-%m-%d %H:%M:%S')
                jours = (date2 - date1).days
                velocite = (delta_fiches / jours * 7) if jours > 0 else 0
                velocites.append({
                    'date': st.session_state.rapports_historique[i]['date'],
                    'velocite': round(velocite, 2)
                })
            
            if velocites:
                fig_velocite = go.Figure()
                fig_velocite.add_trace(go.Bar(
                    x=[v['date'] for v in velocites],
                    y=[v['velocite'] for v in velocites],
                    marker_color='#3b82f6',
                    text=[v['velocite'] for v in velocites],
                    textposition='outside',
                    hovertemplate='<b>%{x}</b><br>Vélocité: %{y} fiches/semaine<extra></extra>'
                ))
                
                fig_velocite.update_layout(
                    title="Vélocité (Fiches/Semaine)",
                    xaxis_title="Période",
                    yaxis_title="Fiches par semaine",
                    height=300,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                
                st.plotly_chart(fig_velocite, use_container_width=True)

def generer_rapport_hebdomadaire():
    """Génère un rapport hebdomadaire avec comparaison"""
    st.markdown("### 📋 Générer un Nouveau Rapport Hebdomadaire")
    
    # Vérifier s'il y a déjà un rapport cette semaine
    aujourd_hui = datetime.now()
    dernier_rapport = None
    
    if st.session_state.rapports_historique:
        dernier_rapport_date = datetime.strptime(
            st.session_state.rapports_historique[-1]['date'], 
            '%Y-%m-%d %H:%M:%S'
        )
        jours_depuis = (aujourd_hui - dernier_rapport_date).days
        
        st.info(f"📅 Dernier rapport généré il y a {jours_depuis} jour(s) - {dernier_rapport_date.strftime('%d/%m/%Y %H:%M')}")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        titre_rapport = st.text_input("📝 Titre du rapport", value=f"Rapport Hebdomadaire - S{aujourd_hui.isocalendar()[1]} {aujourd_hui.year}")
    
    with col2:
        commentaire_rapport = st.text_area("💬 Commentaires / Observations", placeholder="Ajoutez des remarques sur la période...")
    
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📊 Générer le Rapport", type="primary", use_container_width=True):
            # Créer le snapshot
            snapshot = generer_snapshot()
            snapshot['titre'] = titre_rapport
            snapshot['commentaire'] = commentaire_rapport
            
            # Ajouter à l'historique
            st.session_state.rapports_historique.append(snapshot)
            save_rapports()
            
            st.success("✅ Rapport généré avec succès !")
            st.balloons()
            st.rerun()

def afficher_historique_rapports():
    """Affiche l'historique des rapports"""
    if not st.session_state.rapports_historique:
        st.info("📭 Aucun rapport généré pour le moment. Créez votre premier rapport ci-dessus.")
        return
    
    st.markdown("### 📚 Historique des Rapports")
    
    # Tableau récapitulatif
    rapports_data = []
    for i, rapport in enumerate(reversed(st.session_state.rapports_historique)):
        date_rapport = datetime.strptime(rapport['date'], '%Y-%m-%d %H:%M:%S')
        
        # Calculer l'évolution si possible
        evolution_txt = "-"
        if i < len(st.session_state.rapports_historique) - 1:
            idx_actuel = len(st.session_state.rapports_historique) - 1 - i
            idx_precedent = idx_actuel - 1
            delta = (st.session_state.rapports_historique[idx_actuel]['fiches_terminees'] - 
                    st.session_state.rapports_historique[idx_precedent]['fiches_terminees'])
            evolution_txt = f"+{delta}" if delta >= 0 else str(delta)
        
        rapports_data.append({
            'Date': date_rapport.strftime('%d/%m/%Y %H:%M'),
            'Titre': rapport.get('titre', f"Rapport du {date_rapport.strftime('%d/%m/%Y')}"),
            'Total Fiches': rapport['total_fiches'],
            'Terminées': rapport['fiches_terminees'],
            'Taux Global': f"{round(rapport['fiches_terminees']/rapport['total_fiches']*100, 1)}%" if rapport['total_fiches'] > 0 else "0%",
            'Évolution': evolution_txt
        })
    
    df_rapports = pd.DataFrame(rapports_data)
    st.dataframe(df_rapports, use_container_width=True, hide_index=True)
    
    # Détails des rapports
    st.markdown("#### 🔍 Détails des Rapports")
    
    for i, rapport in enumerate(reversed(st.session_state.rapports_historique)):
        date_rapport = datetime.strptime(rapport['date'], '%Y-%m-%d %H:%M:%S')
        titre = rapport.get('titre', f"Rapport du {date_rapport.strftime('%d/%m/%Y')}")
        
        with st.expander(f"📄 {titre} - {date_rapport.strftime('%d/%m/%Y %H:%M')}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("**📊 Résumé Global**")
                col_a, col_b, col_c, col_d = st.columns(4)
                with col_a:
                    st.metric("Total", rapport['total_fiches'])
                with col_b:
                    st.metric("Terminées", rapport['fiches_terminees'])
                with col_c:
                    st.metric("En Cours", rapport['fiches_en_cours'])
                with col_d:
                    st.metric("En Attente", rapport['fiches_en_attente'])
                
                st.markdown("**🔧 Détails par Sous-système**")
                for ss, data in rapport['sous_systemes'].items():
                    st.write(f"**{ss}:** {data['termine']}/{data['objectif']} ({data['taux_avancement']}%)")
            
            with col2:
                if rapport.get('commentaire'):
                    st.markdown("**💬 Commentaires**")
                    st.info(rapport['commentaire'])
                
                # Bouton de suppression
                if st.button(f"🗑️ Supprimer ce rapport", key=f"del_rapport_{i}"):
                    idx_to_remove = len(st.session_state.rapports_historique) - 1 - i
                    st.session_state.rapports_historique.pop(idx_to_remove)
                    save_rapports()
                    st.rerun()

def exporter_excel_pro():
    """Export Excel professionnel avec tous les onglets"""
    if not st.session_state.fiches:
        st.warning("⚠️ Aucune fiche à exporter")
        return
    
    # Préparer toutes les données
    df_fiches = pd.DataFrame(st.session_state.fiches)
    stats = calculer_stats()
    
    output_file = f"rapport_pro_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Onglet 1: Dashboard
        dashboard_data = pd.DataFrame([
            {'Indicateur': 'Date du rapport', 'Valeur': datetime.now().strftime('%d/%m/%Y %H:%M')},
            {'Indicateur': 'Total fiches', 'Valeur': len(st.session_state.fiches)},
            {'Indicateur': 'Fiches terminées', 'Valeur': len([f for f in st.session_state.fiches if f['statut'] == 'Terminé'])},
            {'Indicateur': 'Fiches en cours', 'Valeur': len([f for f in st.session_state.fiches if f['statut'] == 'En cours'])},
            {'Indicateur': 'Fiches en attente', 'Valeur': len([f for f in st.session_state.fiches if f['statut'] == 'En attente'])},
        ])
        dashboard_data.to_excel(writer, sheet_name='Dashboard', index=False)
        
        # Onglet 2: Fiches
        df_fiches.to_excel(writer, sheet_name='Toutes les fiches', index=False)
        
        # Onglet 3: Stats par sous-système
        stats_ss = pd.DataFrame([
            {
                'Sous-système': ss,
                'Objectif': data['objectif'],
                'Terminées': data['termine'],
                'En cours': data['en_cours'],
                'Restantes': max(0, data['objectif'] - data['termine']),
                'Taux avancement (%)': data['taux_avancement']
            }
            for ss, data in stats.items()
        ])
        stats_ss.to_excel(writer, sheet_name='Stats sous-systèmes', index=False)
        
        # Onglet 4: Historique des rapports
        if st.session_state.rapports_historique:
            rapports_hist = pd.DataFrame([
                {
                    'Date': r['date'],
                    'Total': r['total_fiches'],
                    'Terminées': r['fiches_terminees'],
                    'En cours': r['fiches_en_cours']
                }
                for r in st.session_state.rapports_historique
            ])
            rapports_hist.to_excel(writer, sheet_name='Historique rapports', index=False)
    
    st.success(f"✅ Export Excel professionnel créé : {output_file}")
    
    with open(output_file, 'rb') as f:
        st.download_button(
            label="📥 Télécharger le Rapport Excel",
            data=f,
            file_name=output_file,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )

def generer_rapport_pdf_pro():
    """Génère un rapport PDF professionnel avec graphiques et traçabilité complète"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch, cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        from reportlab.pdfgen import canvas
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')
    except ImportError:
        st.error("❌ Bibliothèques manquantes. Installez: pip install reportlab matplotlib")
        st.code("pip install reportlab matplotlib", language="bash")
        return
    
    if not st.session_state.fiches:
        st.warning("⚠️ Aucune fiche à exporter")
        return
    
    # Créer le PDF
    pdf_file = f"rapport_complet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    doc = SimpleDocTemplate(pdf_file, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Styles personnalisés
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.grey,
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#764ba2'),
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    )
    
    # === PAGE 1: PAGE DE GARDE ===
    elements.append(Spacer(1, 2*inch))
    elements.append(Paragraph("📊 RAPPORT PROFESSIONNEL", title_style))
    elements.append(Paragraph("Gestion des Fiches de Digitalisation", subtitle_style))
    elements.append(Spacer(1, 0.5*inch))
    
    info_table_data = [
        ['Date du rapport:', datetime.now().strftime('%d/%m/%Y à %H:%M')],
        ['Généré par:', 'Yves Niamke'],
        ['Période:', f"Du {min([f['date_reception'] for f in st.session_state.fiches])} au {datetime.now().strftime('%Y-%m-%d')}"],
        ['Total de fiches:', str(len(st.session_state.fiches))],
    ]
    
    info_table = Table(info_table_data, colWidths=[4*cm, 10*cm])
    info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(info_table)
    elements.append(PageBreak())
    
    # === PAGE 2: RÉSUMÉ EXÉCUTIF ===
    elements.append(Paragraph("RÉSUMÉ EXÉCUTIF", heading_style))
    
    stats = calculer_stats()
    total_fiches = len(st.session_state.fiches)
    total_terminees = len([f for f in st.session_state.fiches if f['statut'] == 'Terminé'])
    total_en_cours = len([f for f in st.session_state.fiches if f['statut'] == 'En cours'])
    total_en_attente = len([f for f in st.session_state.fiches if f['statut'] == 'En attente'])
    
    # Tableau résumé
    resume_data = [
        ['INDICATEUR', 'VALEUR', 'POURCENTAGE'],
        ['Total des fiches', str(total_fiches), '100%'],
        ['Fiches terminées', str(total_terminees), f"{round(total_terminees/total_fiches*100, 1)}%"],
        ['Fiches en cours', str(total_en_cours), f"{round(total_en_cours/total_fiches*100, 1)}%"],
        ['Fiches en attente', str(total_en_attente), f"{round(total_en_attente/total_fiches*100, 1)}%"],
    ]
    
    resume_table = Table(resume_data, colWidths=[8*cm, 4*cm, 4*cm])
    resume_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ]))
    
    elements.append(resume_table)
    elements.append(Spacer(1, 0.5*inch))
    
    # === STATISTIQUES PAR SOUS-SYSTÈME ===
    elements.append(Paragraph("PERFORMANCE PAR SOUS-SYSTÈME", heading_style))
    
    ss_data = [['SOUS-SYSTÈME', 'OBJECTIF', 'TERMINÉES', 'EN COURS', 'RESTANTES', 'AVANCEMENT']]
    for ss, data in stats.items():
        restantes = max(0, data['objectif'] - data['termine'])
        ss_data.append([
            ss,
            str(data['objectif']),
            str(data['termine']),
            str(data['en_cours']),
            str(restantes),
            f"{data['taux_avancement']}%"
        ])
    
    ss_table = Table(ss_data, colWidths=[4*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm])
    ss_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ]))
    
    elements.append(ss_table)
    elements.append(PageBreak())
    
    # === PAGE 3: GRAPHIQUES ===
    elements.append(Paragraph("ANALYSES GRAPHIQUES", heading_style))
    
    # Graphique 1: Répartition par statut (Pie Chart)
    fig1, ax1 = plt.subplots(figsize=(8, 6))
    statuts_values = [total_terminees, total_en_cours, total_en_attente]
    statuts_labels = ['Terminées', 'En cours', 'En attente']
    colors_pie = ['#10b981', '#f59e0b', '#ef4444']
    
    ax1.pie(statuts_values, labels=statuts_labels, autopct='%1.1f%%', colors=colors_pie, startangle=90)
    ax1.set_title('Répartition des Fiches par Statut', fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    pie_img = "temp_pie.png"
    plt.savefig(pie_img, dpi=150, bbox_inches='tight')
    plt.close()
    
    elements.append(Image(pie_img, width=14*cm, height=10*cm))
    elements.append(Spacer(1, 0.3*inch))
    
    # Graphique 2: Objectifs vs Terminées (Bar Chart)
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    sous_systemes = list(stats.keys())
    objectifs = [stats[ss]['objectif'] for ss in sous_systemes]
    terminees = [stats[ss]['termine'] for ss in sous_systemes]
    
    x = range(len(sous_systemes))
    width = 0.35
    
    ax2.bar([i - width/2 for i in x], objectifs, width, label='Objectif', color='#3b82f6')
    ax2.bar([i + width/2 for i in x], terminees, width, label='Terminées', color='#10b981')
    
    ax2.set_xlabel('Sous-systèmes', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Nombre de fiches', fontsize=12, fontweight='bold')
    ax2.set_title('Objectifs vs Réalisations par Sous-système', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(sous_systemes, rotation=15, ha='right')
    ax2.legend()
    ax2.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    
    bar_img = "temp_bar.png"
    plt.savefig(bar_img, dpi=150, bbox_inches='tight')
    plt.close()
    
    elements.append(PageBreak())
    elements.append(Paragraph("OBJECTIFS VS RÉALISATIONS", heading_style))
    elements.append(Image(bar_img, width=16*cm, height=10*cm))
    elements.append(Spacer(1, 0.3*inch))
    
    # === PAGE 4: TRAÇABILITÉ - HISTORIQUE DES RAPPORTS ===
    if st.session_state.rapports_historique:
        elements.append(PageBreak())
        elements.append(Paragraph("TRAÇABILITÉ - HISTORIQUE DES RAPPORTS", heading_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Tableau de l'historique
        hist_data = [['DATE', 'TOTAL', 'TERMINÉES', 'EN COURS', 'ATTENTE', 'TAUX']]
        for rapport in st.session_state.rapports_historique:
            date_r = datetime.strptime(rapport['date'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')
            taux = f"{round(rapport['fiches_terminees']/rapport['total_fiches']*100, 1)}%" if rapport['total_fiches'] > 0 else "0%"
            hist_data.append([
                date_r,
                str(rapport['total_fiches']),
                str(rapport['fiches_terminees']),
                str(rapport['fiches_en_cours']),
                str(rapport['fiches_en_attente']),
                taux
            ])
        
        hist_table = Table(hist_data, colWidths=[4*cm, 2*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2*cm])
        hist_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        elements.append(hist_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Graphique d'évolution
        if len(st.session_state.rapports_historique) > 1:
            fig3, ax3 = plt.subplots(figsize=(12, 6))
            dates = [datetime.strptime(r['date'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m') for r in st.session_state.rapports_historique]
            terminees_hist = [r['fiches_terminees'] for r in st.session_state.rapports_historique]
            total_hist = [r['total_fiches'] for r in st.session_state.rapports_historique]
            
            ax3.plot(dates, terminees_hist, marker='o', linewidth=2, markersize=8, label='Fiches terminées', color='#10b981')
            ax3.plot(dates, total_hist, marker='s', linewidth=2, markersize=8, label='Total fiches', color='#3b82f6')
            
            ax3.set_xlabel('Date des rapports', fontsize=12, fontweight='bold')
            ax3.set_ylabel('Nombre de fiches', fontsize=12, fontweight='bold')
            ax3.set_title('Évolution des Fiches dans le Temps', fontsize=14, fontweight='bold')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            evol_img = "temp_evolution.png"
            plt.savefig(evol_img, dpi=150, bbox_inches='tight')
            plt.close()
            
            elements.append(Image(evol_img, width=16*cm, height=10*cm))
    
    # === PAGE 5: LISTE DÉTAILLÉE DES FICHES ===
    elements.append(PageBreak())
    elements.append(Paragraph("LISTE DÉTAILLÉE DES FICHES", heading_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Tableau des fiches
    fiches_data = [['ID', 'NOM', 'SOUS-SYSTÈME', 'RESPONSABLE', 'STATUT', 'AVANCEMENT']]
    for fiche in st.session_state.fiches[:50]:  # Limiter à 50 pour éviter un PDF trop long
        fiches_data.append([
            str(fiche['id']),
            fiche.get('nom_fiche', 'N/A')[:30],
            fiche['sous_systeme'][:15],
            fiche.get('responsable_qualite', 'N/A')[:20],
            fiche['statut'],
            f"{fiche['avancement']}%"
        ])
    
    fiches_table = Table(fiches_data, colWidths=[1.5*cm, 5*cm, 3*cm, 3.5*cm, 2.5*cm, 2*cm])
    fiches_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#764ba2')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ]))
    
    elements.append(fiches_table)
    
    if len(st.session_state.fiches) > 50:
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph(f"<i>Note: Seules les 50 premières fiches sont affichées. Total: {len(st.session_state.fiches)} fiches.</i>", styles['Normal']))
    
    # === FOOTER ===
    elements.append(PageBreak())
    elements.append(Spacer(1, 3*inch))
    elements.append(Paragraph("FIN DU RAPPORT", title_style))
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph(f"Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", subtitle_style))
    elements.append(Paragraph("© 2024 Système de Gestion des Fiches Pro - Tous droits réservés", subtitle_style))
    
    # Construire le PDF
    doc.build(elements)
    
    # Nettoyer les fichiers temporaires
    for temp_file in [pie_img, bar_img]:
        try:
            os.remove(temp_file)
        except:
            pass
    
    if st.session_state.rapports_historique and len(st.session_state.rapports_historique) > 1:
        try:
            os.remove(evol_img)
        except:
            pass
    
    st.success(f"✅ Rapport PDF professionnel généré : {pdf_file}")
    
    with open(pdf_file, 'rb') as f:
        st.download_button(
            label="📄 Télécharger le Rapport PDF",
            data=f,
            file_name=pdf_file,
            mime="application/pdf",
            type="primary"
        )

def page_principale():
    """Page principale améliorée"""
    
    # Header
    st.markdown(f"""
    <div class="main-header">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h1 style="margin: 0; font-size: 2rem; font-weight: 700;">📊 Gestion des Fiches - Version Pro</h1>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Bienvenue, Yves Niamke • {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Bouton déconnexion
    col_h1, col_h2 = st.columns([6, 1])
    with col_h2:
        if st.button("🚪 Déconnexion", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🎯 Objectifs par Sous-système")
        st.markdown("<br>", unsafe_allow_html=True)
        
        for ss, config in SOUS_SYSTEMES_CONFIG.items():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{ss}**")
            with col2:
                new_obj = st.number_input(
                    "obj",
                    min_value=0,
                    value=st.session_state.objectifs[ss],
                    step=1,
                    key=f"obj_{ss}",
                    label_visibility="collapsed"
                )
                if new_obj != st.session_state.objectifs[ss]:
                    st.session_state.objectifs[ss] = new_obj
                    save_data()
        
        st.markdown("---")
        st.markdown("### 📁 Actions Rapides")
        
        if st.button("➕ Ajouter une fiche", use_container_width=True, type="primary"):
            st.session_state.show_add_form = True
        
        if st.button("📥 Exporter Excel Pro", use_container_width=True):
            exporter_excel_pro()
        
        if st.button("📄 Générer Rapport PDF", use_container_width=True):
            generer_rapport_pdf_pro()
        
        st.markdown("---")
        st.markdown("### 📊 Vue Rapide")
        total_fiches = len(st.session_state.fiches)
        total_terminees = len([f for f in st.session_state.fiches if f['statut'] == 'Terminé'])
        st.metric("Total fiches", total_fiches)
        st.metric("Terminées", total_terminees)
        if total_fiches > 0:
            st.metric("Taux", f"{round(total_terminees/total_fiches*100, 1)}%")
    
    # Onglets principaux
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📋 Gestion des Fiches", "📈 Rapports Hebdomadaires", "📚 Historique"])
    
    with tab1:
        afficher_dashboard_evolution()
        st.markdown("---")
        generer_graphiques_avances()
    
    with tab2:
        # Formulaire d'ajout
        if st.session_state.get('show_add_form', False):
            st.markdown("### ➕ Ajouter une Nouvelle Fiche")
            
            with st.form("form_add", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    nom_fiche = st.text_input("📝 Nom de la fiche *")
                    date_reception = st.date_input("📅 Date de réception", datetime.now())
                    sous_systeme = st.selectbox("🔧 Sous-système *", list(SOUS_SYSTEMES_CONFIG.keys()))
                
                with col2:
                    responsable_defaut = SOUS_SYSTEMES_CONFIG[sous_systeme]['responsable_defaut']
                    index_defaut = LISTE_RESPONSABLES.index(responsable_defaut) if responsable_defaut in LISTE_RESPONSABLES else 0
                    
                    responsable_qualite = st.selectbox("👨‍💼 Responsable qualité *", LISTE_RESPONSABLES, index=index_defaut)
                    date_echeance = st.date_input("⏰ Date d'échéance", datetime.now() + timedelta(days=30))
                    statut = st.selectbox("📊 Statut", ["En cours", "Terminé", "En attente"])
                
                commentaire = st.text_area("💬 Commentaire")
                
                col_btn1, col_btn2 = st.columns([1, 5])
                with col_btn1:
                    submitted = st.form_submit_button("✅ Ajouter", type="primary")
                    if submitted and nom_fiche:
                        nouvelle_fiche = {
                            'id': len(st.session_state.fiches) + 1,
                            'nom_fiche': nom_fiche,
                            'date_reception': date_reception.strftime('%Y-%m-%d'),
                            'date_echeance': date_echeance.strftime('%Y-%m-%d'),
                            'sous_systeme': sous_systeme,
                            'responsable_qualite': responsable_qualite,
                            'statut': statut,
                            'avancement': 100 if statut == 'Terminé' else 0,
                            'commentaire': commentaire
                        }
                        st.session_state.fiches.append(nouvelle_fiche)
                        save_data()
                        st.session_state.show_add_form = False
                        st.success("✅ Fiche ajoutée !")
                        st.rerun()
                
                with col_btn2:
                    if st.form_submit_button("❌ Annuler"):
                        st.session_state.show_add_form = False
                        st.rerun()
            
            st.markdown("---")
        
        # Formulaire de modification
        if st.session_state.get('fiche_a_modifier') is not None:
            fiche_mod = None
            for f in st.session_state.fiches:
                if f['id'] == st.session_state.fiche_a_modifier:
                    fiche_mod = f
                    break
            
            if fiche_mod:
                st.markdown(f"### ✏️ Modifier la Fiche #{fiche_mod['id']}")
                
                with st.form("form_modifier"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        nom_fiche_mod = st.text_input("📝 Nom de la fiche *", value=fiche_mod.get('nom_fiche', ''))
                        date_reception_mod = st.date_input("📅 Date de réception", 
                                                           datetime.strptime(fiche_mod['date_reception'], '%Y-%m-%d'))
                        sous_systeme_mod = st.selectbox("🔧 Sous-système *", 
                                                        list(SOUS_SYSTEMES_CONFIG.keys()),
                                                        index=list(SOUS_SYSTEMES_CONFIG.keys()).index(fiche_mod['sous_systeme']))
                    
                    with col2:
                        responsable_mod = st.selectbox(
                            "👨‍💼 Responsable qualité *", 
                            LISTE_RESPONSABLES,
                            index=LISTE_RESPONSABLES.index(fiche_mod.get('responsable_qualite', LISTE_RESPONSABLES[0]))
                        )
                        
                        date_echeance_mod = st.date_input("⏰ Date d'échéance", 
                                                          datetime.strptime(fiche_mod['date_echeance'], '%Y-%m-%d'))
                        statut_mod = st.selectbox("📊 Statut", ["En cours", "Terminé", "En attente"],
                                                 index=["En cours", "Terminé", "En attente"].index(fiche_mod['statut']))
                    
                    avancement_mod = st.slider("📈 Avancement (%)", 0, 100, fiche_mod['avancement'])
                    commentaire_mod = st.text_area("💬 Commentaire", value=fiche_mod.get('commentaire', ''))
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 4])
                    with col_btn1:
                        save_modif = st.form_submit_button("💾 Sauvegarder", type="primary")
                    with col_btn2:
                        cancel_modif = st.form_submit_button("❌ Annuler")
                    
                    if save_modif:
                        # Mettre à jour la fiche
                        for f in st.session_state.fiches:
                            if f['id'] == fiche_mod['id']:
                                f['nom_fiche'] = nom_fiche_mod
                                f['date_reception'] = date_reception_mod.strftime('%Y-%m-%d')
                                f['date_echeance'] = date_echeance_mod.strftime('%Y-%m-%d')
                                f['sous_systeme'] = sous_systeme_mod
                                f['responsable_qualite'] = responsable_mod
                                f['statut'] = statut_mod
                                f['avancement'] = avancement_mod
                                f['commentaire'] = commentaire_mod
                                break
                        
                        save_data()
                        st.session_state.fiche_a_modifier = None
                        st.success("✅ Fiche modifiée avec succès !")
                        st.rerun()
                    
                    if cancel_modif:
                        st.session_state.fiche_a_modifier = None
                        st.rerun()
                
                st.markdown("---")
        
        # Filtres avancés pour la liste des fiches
        st.markdown("### 🔍 Filtres de Recherche")
        
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])
        
        with col1:
            recherche = st.text_input("🔎 Rechercher", placeholder="Nom, ID, responsable...", key="recherche_fiches")
        with col2:
            filtre_ss = st.selectbox("🔧 Sous-système", ["Tous"] + list(SOUS_SYSTEMES_CONFIG.keys()), key="filtre_ss")
        with col3:
            filtre_statut = st.selectbox("📊 Statut", ["Tous", "En cours", "Terminé", "En attente"], key="filtre_statut")
        with col4:
            filtre_responsable = st.selectbox("👨‍💼 Responsable", ["Tous"] + LISTE_RESPONSABLES, key="filtre_resp")
        with col5:
            tri_par = st.selectbox("🔀 Trier par", ["ID ↓", "ID ↑", "Date récep. ↓", "Date récep. ↑", "Échéance ↓", "Échéance ↑"], key="tri")
        
        col_date1, col_date2, col_date3 = st.columns([2, 2, 6])
        with col_date1:
            date_debut = st.date_input("📅 Date début", datetime.now() - timedelta(days=90), key="date_debut")
        with col_date2:
            date_fin = st.date_input("📅 Date fin", datetime.now(), key="date_fin")
        
        st.markdown("---")
        
        # Filtrer les fiches
        fiches_filtrees = st.session_state.fiches.copy()
        
        # Filtre par recherche
        if recherche:
            recherche_lower = recherche.lower()
            fiches_filtrees = [
                f for f in fiches_filtrees 
                if recherche_lower in f.get('nom_fiche', '').lower() 
                or recherche_lower in str(f['id']).lower()
                or recherche_lower in f.get('responsable_qualite', '').lower()
                or recherche_lower in f.get('commentaire', '').lower()
            ]
        
        # Filtre par sous-système
        if filtre_ss != "Tous":
            fiches_filtrees = [f for f in fiches_filtrees if f['sous_systeme'] == filtre_ss]
        
        # Filtre par statut
        if filtre_statut != "Tous":
            fiches_filtrees = [f for f in fiches_filtrees if f['statut'] == filtre_statut]
        
        # Filtre par responsable
        if filtre_responsable != "Tous":
            fiches_filtrees = [f for f in fiches_filtrees if f.get('responsable_qualite') == filtre_responsable]
        
        # Filtre par dates
        fiches_filtrees = [
            f for f in fiches_filtrees 
            if date_debut.strftime('%Y-%m-%d') <= f['date_reception'] <= date_fin.strftime('%Y-%m-%d')
        ]
        
        # Tri
        if tri_par == "ID ↓":
            fiches_filtrees.sort(key=lambda x: x['id'], reverse=True)
        elif tri_par == "ID ↑":
            fiches_filtrees.sort(key=lambda x: x['id'])
        elif tri_par == "Date récep. ↓":
            fiches_filtrees.sort(key=lambda x: x['date_reception'], reverse=True)
        elif tri_par == "Date récep. ↑":
            fiches_filtrees.sort(key=lambda x: x['date_reception'])
        elif tri_par == "Échéance ↓":
            fiches_filtrees.sort(key=lambda x: x['date_echeance'], reverse=True)
        elif tri_par == "Échéance ↑":
            fiches_filtrees.sort(key=lambda x: x['date_echeance'])
        
        # Affichage des résultats
        st.markdown(f"### 📋 Résultats de la Recherche")
        st.markdown(f"**{len(fiches_filtrees)} fiche(s) trouvée(s)** sur {len(st.session_state.fiches)} total")
        st.markdown("<br>", unsafe_allow_html=True)
        
        if fiches_filtrees:
            for fiche in fiches_filtrees:
                couleur_ss = SOUS_SYSTEMES_CONFIG[fiche['sous_systeme']]['couleur']
                nom_affichage = fiche.get('nom_fiche', f"Fiche #{fiche['id']}")
                status_html = get_status_badge(fiche['statut'])
                
                with st.expander(f"📄 **{nom_affichage}** - {fiche['sous_systeme']}", expanded=False):
                    st.markdown(status_html, unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    col1, col2, col3 = st.columns([2, 2, 3])
                    
                    with col1:
                        st.markdown("**📝 Informations**")
                        st.write(f"**ID:** #{fiche['id']}")
                        st.write(f"**Nom:** {fiche.get('nom_fiche', 'N/A')}")
                        st.write(f"**Sous-système:** {fiche['sous_systeme']}")
                    
                    with col2:
                        st.markdown("**📅 Dates**")
                        st.write(f"**Réception:** {fiche['date_reception']}")
                        st.write(f"**Échéance:** {fiche['date_echeance']}")
                        
                        # Calcul du délai
                        date_ech = datetime.strptime(fiche['date_echeance'], '%Y-%m-%d')
                        jours_restants = (date_ech - datetime.now()).days
                        if jours_restants < 0:
                            st.error(f"⚠️ En retard de {abs(jours_restants)} jour(s)")
                        elif jours_restants < 7:
                            st.warning(f"⏰ {jours_restants} jour(s) restant(s)")
                        else:
                            st.info(f"✅ {jours_restants} jour(s) restant(s)")
                    
                    with col3:
                        st.markdown("**👨‍💼 Responsable & Avancement**")
                        st.write(f"**Responsable qualité:** {fiche.get('responsable_qualite', 'N/A')}")
                        
                        nouvel_avancement = st.slider(
                            "Avancement (%)",
                            0, 100,
                            fiche['avancement'],
                            key=f"slider_{fiche['id']}"
                        )
                        
                        if nouvel_avancement != fiche['avancement']:
                            for f in st.session_state.fiches:
                                if f['id'] == fiche['id']:
                                    f['avancement'] = nouvel_avancement
                                    f['statut'] = 'Terminé' if nouvel_avancement == 100 else 'En cours'
                                    break
                            save_data()
                            st.rerun()
                    
                    if fiche.get('commentaire'):
                        st.markdown("**💬 Commentaire**")
                        st.info(fiche['commentaire'])
                    
                    col_action1, col_action2, col_action3 = st.columns([1, 1, 4])
                    with col_action1:
                        if st.button(f"✏️ Modifier", key=f"edit_{fiche['id']}", type="primary"):
                            st.session_state.fiche_a_modifier = fiche['id']
                            st.rerun()
                    with col_action2:
                        if st.button(f"🗑️ Supprimer", key=f"del_{fiche['id']}", type="secondary"):
                            st.session_state.fiches = [f for f in st.session_state.fiches if f['id'] != fiche['id']]
                            save_data()
                            st.success("Fiche supprimée !")
                            st.rerun()
        else:
            st.warning("📭 Aucune fiche ne correspond aux critères de recherche")
    
    with tab3:
        generer_rapport_hebdomadaire()
    
    with tab4:
        afficher_historique_rapports()

# Point d'entrée
def main():
    init_session_state()
    
    if not st.session_state.authenticated:
        page_login()
    else:
        page_principale()                                                                                                                                                                                                                   

if __name__ == "__main__":
    main()