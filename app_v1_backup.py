#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OPTI MQL5 - Interface Web
Application Streamlit pour analyser les optimisations MetaTrader 5
"""

import streamlit as st
import pandas as pd
import numpy as np
import io
import json
from mql5_optimization_analyzer import MQL5OptimizationAnalyzer
import plotly.express as px
import plotly.graph_objects as go

# Configuration de la page
st.set_page_config(
    page_title="OPTI MQL5 - Analyseur d'Optimisations",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

def parse_mt5_xml(file_path):
    """Parse un fichier XML MetaTrader 5 et le convertit en DataFrame"""
    import xml.etree.ElementTree as ET

    # Lire le fichier avec différents encodages
    content = None
    for encoding in ['utf-8', 'utf-16', 'cp1252', 'iso-8859-1', 'windows-1252']:
        try:
            with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                content = f.read()
            break
        except:
            continue

    if content is None:
        # Si tous les encodages échouent, lire en mode binaire et nettoyer
        with open(file_path, 'rb') as f:
            raw_content = f.read()
        content = raw_content.decode('utf-8', errors='ignore')

    # Parser le XML depuis le contenu nettoyé
    root = ET.fromstring(content)

    # Trouver la worksheet
    ns = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}
    worksheet = root.find('.//ss:Worksheet', ns)
    table = worksheet.find('.//ss:Table', ns)
    rows = table.findall('.//ss:Row', ns)

    data = []
    headers = []

    for i, row in enumerate(rows):
        cells = row.findall('.//ss:Cell', ns)
        row_data = []

        for cell in cells:
            data_elem = cell.find('.//ss:Data', ns)
            if data_elem is not None:
                value = data_elem.text
                # Convertir en numérique si possible
                try:
                    if '.' in str(value):
                        value = float(value)
                    else:
                        value = int(value)
                except:
                    pass
                row_data.append(value)
            else:
                row_data.append(None)

        if i == 0:
            headers = row_data
        else:
            data.append(row_data)

    # Créer le DataFrame
    df = pd.DataFrame(data, columns=headers)
    return df

def main():
    # En-tête
    st.markdown('<h1 class="main-header">🚀 OPTI MQL5</h1>', unsafe_allow_html=True)
    st.markdown("### Analyseur d'Optimisations MetaTrader 5")

    st.markdown("---")

    # Sidebar pour les paramètres
    st.sidebar.header("⚙️ Paramètres d'Analyse")

    profit_min = st.sidebar.number_input(
        "Profit minimum (€)",
        min_value=0,
        max_value=50000,
        value=7000,
        step=500,
        help="Seuil minimum de profit pour filtrer les optimisations"
    )

    dd_max = st.sidebar.number_input(
        "Drawdown maximum (%)",
        min_value=0.0,
        max_value=100.0,
        value=7.0,
        step=0.5,
        help="Seuil maximum de drawdown acceptable"
    )

    top_n = st.sidebar.slider(
        "Nombre de meilleures optimisations",
        min_value=5,
        max_value=50,
        value=15,
        help="Combien d'optimisations afficher dans le top"
    )

    # Upload de fichier
    st.header("📁 Uploadez votre fichier d'optimisation")

    uploaded_file = st.file_uploader(
        "Choisissez votre fichier Excel/CSV d'optimisation MetaTrader 5",
        type=['xlsx', 'xls', 'csv', 'xml'],
        help="Formats supportés: Excel (.xlsx, .xls), CSV (.csv), XML (.xml)"
    )

    if uploaded_file is not None:
        try:
            # Affichage des informations du fichier
            file_details = {
                "Nom": uploaded_file.name,
                "Taille": f"{uploaded_file.size:,} bytes",
                "Type": uploaded_file.type
            }

            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"📄 **Fichier:** {file_details['Nom']}")
            with col2:
                st.info(f"💾 **Taille:** {file_details['Taille']}")
            with col3:
                st.info(f"🔧 **Type:** {file_details['Type']}")

            # Bouton d'analyse
            if st.button("🚀 ANALYSER LES OPTIMISATIONS", type="primary"):
                analyze_optimizations(uploaded_file, profit_min, dd_max, top_n)

        except Exception as e:
            st.error(f"[ERREUR] Erreur lors du chargement du fichier: {str(e)}")

    else:
        # Instructions d'utilisation
        st.info("👆 Uploadez votre fichier pour commencer l'analyse")

        with st.expander("ℹ️ Comment exporter depuis MetaTrader 5"):
            st.markdown("""
            **Étapes pour exporter vos optimisations :**
            1. Dans MetaTrader 5, allez dans **Strategy Tester**
            2. Lancez votre optimisation
            3. Dans l'onglet **Optimization Results**, clic droit → **Save**
            4. Sauvegardez au format Excel (.xlsx) ou CSV
            5. Uploadez le fichier ici 👆
            """)

        with st.expander("📊 Que fait l'analyseur ?"):
            st.markdown(f"""
            **L'analyseur va automatiquement :**
            - ✅ Filtrer les optimisations avec profit ≥ {profit_min}€
            - ✅ Exclure celles avec drawdown > {dd_max}%
            - ✅ Analyser chaque variable (RSI, SL, TP, etc.)
            - ✅ Calculer les statistiques détaillées
            - ✅ Classer les {top_n} meilleures configurations
            - ✅ Générer des graphiques interactifs
            """)

def analyze_optimizations(uploaded_file, profit_min, dd_max, top_n):
    """Analyse les optimisations uploadées"""

    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # Étape 1: Chargement
        status_text.text("📂 Chargement du fichier...")
        progress_bar.progress(20)

        # Lecture du fichier
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith('.xml'):
            # Traitement spécial pour les fichiers XML MetaTrader 5
            st.info("🔧 Traitement du fichier XML MetaTrader 5...")

            # Sauvegarder temporairement le fichier uploadé
            with open("temp_file.xml", "wb") as f:
                f.write(uploaded_file.getvalue())

            # Essayer différentes méthodes de lecture
            df = None
            methods_tried = []

            # Méthode 1: pandas avec openpyxl
            try:
                df = pd.read_excel("temp_file.xml", engine='openpyxl')
                methods_tried.append("✅ openpyxl")
            except Exception as e1:
                methods_tried.append(f"❌ openpyxl: {str(e1)[:50]}...")

            # Méthode 2: pandas standard
            if df is None:
                try:
                    df = pd.read_excel("temp_file.xml")
                    methods_tried.append("✅ pandas standard")
                except Exception as e2:
                    methods_tried.append(f"❌ pandas standard: {str(e2)[:50]}...")

            # Méthode 3: parser XML manuel
            if df is None:
                try:
                    df = parse_mt5_xml("temp_file.xml")
                    methods_tried.append("✅ parser XML manuel")
                except Exception as e3:
                    methods_tried.append(f"❌ parser manuel: {str(e3)[:50]}...")

            # Afficher les méthodes essayées
            with st.expander("🔍 Méthodes de lecture testées"):
                for method in methods_tried:
                    st.write(method)

            # Nettoyer le fichier temporaire
            import os
            if os.path.exists("temp_file.xml"):
                os.remove("temp_file.xml")

            if df is None:
                st.error("❌ Impossible de lire le fichier XML. Essayez de l'exporter en format Excel (.xlsx) depuis MetaTrader 5.")
                return
        else:
            df = pd.read_excel(uploaded_file)

        progress_bar.progress(40)

        # Étape 2: Analyse
        status_text.text("🔍 Analyse des données...")

        analyzer = MQL5OptimizationAnalyzer()
        analyzer.data = df

        progress_bar.progress(60)

        # Filtrage
        analyzer.filter_profitable_optimizations(min_profit=profit_min, max_drawdown=dd_max)

        progress_bar.progress(80)

        # Analyse des variables
        analyzer.analyze_variables()
        analyzer.find_best_optimizations(top_n=top_n)

        progress_bar.progress(100)
        status_text.text("✅ Analyse terminée!")

        # Affichage des résultats
        display_results(analyzer, profit_min, dd_max)

    except Exception as e:
        st.error(f"❌ Erreur durant l'analyse: {str(e)}")
        st.exception(e)

def display_results(analyzer, profit_min, dd_max):
    """Affiche les résultats de l'analyse"""

    st.markdown("---")
    st.header("📊 Résultats de l'Analyse")

    # Résumé général
    total_opts = len(analyzer.data) if analyzer.data is not None else 0
    profitable_opts = len(analyzer.filtered_data) if analyzer.filtered_data is not None else 0
    success_rate = (profitable_opts / total_opts * 100) if total_opts > 0 else 0

    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📈 Total Optimisations", f"{total_opts:,}")

    with col2:
        st.metric("✅ Profitables", f"{profitable_opts:,}")

    with col3:
        st.metric("🎯 Taux de Succès", f"{success_rate:.1f}%")

    with col4:
        profit_cols = [col for col in analyzer.data.columns if 'profit' in col.lower() or 'gain' in col.lower()]
        if profit_cols and analyzer.filtered_data is not None and len(analyzer.filtered_data) > 0:
            max_profit = analyzer.filtered_data[profit_cols[0]].max()
            st.metric("💰 Meilleur Profit", f"{max_profit:,.2f}€")

    if profitable_opts == 0:
        st.warning(f"⚠️ Aucune optimisation ne respecte vos critères (profit ≥ {profit_min}€, DD ≤ {dd_max}%)")
        return

    # Graphiques
    st.subheader("📊 Visualisations")

    # Graphique de distribution des profits
    if analyzer.filtered_data is not None:
        profit_cols = [col for col in analyzer.filtered_data.columns if 'profit' in col.lower() or 'gain' in col.lower()]
        if profit_cols:
            fig_hist = px.histogram(
                analyzer.filtered_data,
                x=profit_cols[0],
                title="Distribution des Profits",
                nbins=20,
                color_discrete_sequence=['#1f77b4']
            )
            fig_hist.update_layout(xaxis_title="Profit (€)", yaxis_title="Nombre d'optimisations")
            st.plotly_chart(fig_hist, use_container_width=True)

    # Analyse par variables
    if analyzer.variable_stats:
        st.subheader("🔍 Analyse par Variables")

        # Sélection de variable à analyser
        var_names = list(analyzer.variable_stats.keys())
        selected_var = st.selectbox("Choisissez une variable à analyser:", var_names)

        if selected_var:
            var_stats = analyzer.variable_stats[selected_var]

            # Statistiques de la variable
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"""
                **📊 Statistiques pour {selected_var}:**
                - Valeurs uniques testées: **{var_stats['valeurs_uniques']}**
                - Profit minimum: **{var_stats['profit_min']:.2f}€**
                - Profit maximum: **{var_stats['profit_max']:.2f}€**
                - Profit moyen: **{var_stats['profit_moyen']:.2f}€**
                """)

            with col2:
                # Top 5 des valeurs
                if var_stats['top_valeurs']:
                    st.markdown("**🏆 Top 5 des meilleures valeurs:**")
                    for i, top_val in enumerate(var_stats['top_valeurs'][:5], 1):
                        st.write(f"{i}. **{top_val['valeur']}** → {top_val['profit_moyen']:.2f}€ (×{top_val['occurrences']})")

    # Meilleures optimisations
    st.subheader("🏆 Meilleures Optimisations")

    if analyzer.best_optimizations:
        # Tableau des meilleures optimisations
        best_df = pd.DataFrame(analyzer.best_optimizations)

        # Formatage pour l'affichage
        if 'profit' in best_df.columns:
            best_df['profit'] = best_df['profit'].apply(lambda x: f"{x:,.2f}€")

        st.dataframe(
            best_df,
            use_container_width=True,
            height=400
        )

        # Boutons de téléchargement
        col1, col2 = st.columns(2)

        with col1:
            # Téléchargement CSV
            csv = best_df.to_csv(index=False)
            st.download_button(
                label="📥 Télécharger CSV",
                data=csv,
                file_name="meilleures_optimisations.csv",
                mime="text/csv"
            )

        with col2:
            # Téléchargement JSON
            json_data = {
                'variable_stats': analyzer.variable_stats,
                'best_optimizations': analyzer.best_optimizations,
                'summary': {
                    'total_optimizations': total_opts,
                    'profitable_optimizations': profitable_opts,
                    'success_rate': success_rate
                }
            }
            json_str = json.dumps(json_data, ensure_ascii=False, indent=2, default=str)
            st.download_button(
                label="📥 Télécharger JSON",
                data=json_str,
                file_name="analyse_complete.json",
                mime="application/json"
            )

if __name__ == "__main__":
    main()