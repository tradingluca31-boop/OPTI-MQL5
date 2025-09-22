#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OPTI MQL5 V2 - Interface Web Avancée
Application Streamlit pour analyser les optimisations MetaTrader 5
Version 2.0 avec métriques avancées et interface à onglets
"""

import streamlit as st
import pandas as pd
import numpy as np
import io
import json
from mql5_optimization_analyzer import MQL5OptimizationAnalyzer
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configuration de la page
st.set_page_config(
    page_title="OPTI MQL5 V2 - Analyseur Avancé",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé amélioré
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .version-badge {
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.8rem;
        margin-left: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: white;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .category-header {
        background: linear-gradient(90deg, #11998e, #38ef7d);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        font-weight: bold;
    }
    .variable-card {
        background: #f8f9fa;
        border-left: 4px solid #1f77b4;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
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
    # En-tête avec badge version
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown('<h1 class="main-header">🚀 OPTI MQL5</h1>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="version-badge">V2.0 AVANCÉ</div>', unsafe_allow_html=True)

    st.markdown("### Analyseur Avancé d'Optimisations MetaTrader 5")
    st.markdown("---")

    # Sidebar améliorée
    with st.sidebar:
        st.header("⚙️ Configuration Avancée")

        profit_min = st.number_input(
            "💰 Profit minimum (€)",
            min_value=0,
            max_value=100000,
            value=7000,
            step=500,
            help="Seuil minimum de profit pour filtrer les optimisations"
        )

        dd_max = st.number_input(
            "📉 Drawdown maximum (%)",
            min_value=0.0,
            max_value=100.0,
            value=7.0,
            step=0.5,
            help="Seuil maximum de drawdown acceptable"
        )

        top_n = st.slider(
            "🏆 Top optimisations",
            min_value=5,
            max_value=100,
            value=20,
            help="Nombre d'optimisations à afficher dans le top"
        )

        st.markdown("---")
        st.markdown("### 📊 Métriques Avancées")
        show_sharpe = st.checkbox("Sharpe Ratio", value=True)
        show_calmar = st.checkbox("Calmar Ratio", value=True)
        show_recovery = st.checkbox("Recovery Factor", value=True)
        show_rr = st.checkbox("Risk/Reward Ratio", value=True)

    # Upload de fichier
    st.header("📁 Upload de votre fichier d'optimisation")

    uploaded_file = st.file_uploader(
        "Choisissez votre fichier Excel/CSV/XML d'optimisation MetaTrader 5",
        type=['xlsx', 'xls', 'csv', 'xml'],
        help="Formats supportés: Excel (.xlsx, .xls), CSV (.csv), XML (.xml)"
    )

    if uploaded_file is not None:
        try:
            # Affichage des informations du fichier avec style
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"📄 **{uploaded_file.name}**")
            with col2:
                st.info(f"💾 **{uploaded_file.size:,} bytes**")
            with col3:
                st.info(f"🔧 **{uploaded_file.type}**")

            # Bouton d'analyse avec style
            if st.button("🚀 ANALYSER LES OPTIMISATIONS", type="primary", use_container_width=True):
                analyze_optimizations_v2(uploaded_file, profit_min, dd_max, top_n,
                                       show_sharpe, show_calmar, show_recovery, show_rr)

        except Exception as e:
            st.error(f"[ERREUR] Erreur lors du chargement: {str(e)}")

    else:
        # Instructions d'utilisation améliorées
        st.info("👆 Uploadez votre fichier d'optimisation pour commencer l'analyse avancée")

        with st.expander("📖 Guide d'utilisation V2"):
            st.markdown("""
            **🆕 Nouvelles fonctionnalités V2 :**
            - **Métriques avancées** : Sharpe, Calmar, Recovery Factor, R/R
            - **Interface à onglets** organisée par catégories
            - **Analyses détaillées** par type de variable
            - **Visualisations avancées** et graphiques interactifs
            - **Export complet** de toutes les données
            """)

        with st.expander("ℹ️ Export depuis MetaTrader 5"):
            st.markdown("""
            **Étapes pour exporter vos optimisations :**
            1. Dans MetaTrader 5 → **Strategy Tester**
            2. Lancez votre optimisation
            3. Onglet **Optimization Results** → Clic droit → **Save**
            4. Format recommandé : Excel (.xlsx)
            5. Uploadez ici pour l'analyse V2
            """)

def analyze_optimizations_v2(uploaded_file, profit_min, dd_max, top_n,
                            show_sharpe, show_calmar, show_recovery, show_rr):
    """Analyse avancée des optimisations V2"""

    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # Étape 1: Chargement
        status_text.text("📂 Chargement du fichier...")
        progress_bar.progress(20)

        # Lecture du fichier avec gestion XML améliorée
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith('.xml'):
            st.info("🔧 Traitement spécialisé du fichier XML MetaTrader 5...")

            with open("temp_file.xml", "wb") as f:
                f.write(uploaded_file.getvalue())

            try:
                df = pd.read_excel("temp_file.xml", engine='openpyxl')
            except:
                try:
                    df = parse_mt5_xml("temp_file.xml")
                except Exception as e:
                    st.error(f"[ERREUR] Impossible de lire le XML: {e}")
                    return
            finally:
                import os
                if os.path.exists("temp_file.xml"):
                    os.remove("temp_file.xml")
        else:
            df = pd.read_excel(uploaded_file)

        progress_bar.progress(40)

        # Étape 2: Analyse
        status_text.text("🔍 Analyse avancée des données...")

        analyzer = MQL5OptimizationAnalyzer()
        analyzer.data = df
        analyzer.filter_profitable_optimizations(min_profit=profit_min, max_drawdown=dd_max)

        progress_bar.progress(60)

        # Calculs avancés
        analyzer.analyze_variables()

        # Vérification de compatibilité avec Streamlit Cloud
        if hasattr(analyzer, 'calculate_advanced_metrics'):
            analyzer.calculate_advanced_metrics()
        else:
            st.warning("⚠️ Métriques avancées temporairement indisponibles (problème cache Streamlit Cloud)")
            # Création manuelle des métriques de base
            analyzer.advanced_metrics = {
                'total_optimizations': len(analyzer.filtered_data) if analyzer.filtered_data is not None else 0,
                'total_profit': 0,
                'average_profit': 0,
                'max_profit': 0,
                'min_profit': 0,
                'max_drawdown': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'risk_reward_ratio': 0,
                'sharpe_ratio': 0,
                'calmar_ratio': 0,
                'recovery_factor': 0
            }

        analyzer.find_best_optimizations(top_n=top_n)

        progress_bar.progress(80)

        # Catégorisation
        categorized_vars = analyzer.categorize_variables()

        progress_bar.progress(100)
        status_text.text("✅ Analyse V2 terminée!")

        # Affichage des résultats avec onglets
        display_results_v2(analyzer, categorized_vars, profit_min, dd_max,
                          show_sharpe, show_calmar, show_recovery, show_rr)

    except Exception as e:
        st.error(f"[ERREUR] Erreur durant l'analyse V2: {str(e)}")
        st.exception(e)

def display_results_v2(analyzer, categorized_vars, profit_min, dd_max,
                      show_sharpe, show_calmar, show_recovery, show_rr):
    """Affichage des résultats V2 avec onglets"""

    st.markdown("---")
    st.header("📊 Résultats de l'Analyse V2")

    # Onglets principaux
    tab_overview, tab_signals, tab_risk, tab_timing, tab_advanced = st.tabs([
        "📈 Vue d'ensemble",
        "🎯 Variables Signal",
        "💰 Gestion des Risques",
        "⏰ Variables Timing",
        "📊 Analyse Complète"
    ])

    with tab_overview:
        display_overview(analyzer, profit_min, dd_max)

    with tab_signals:
        display_category_analysis(analyzer, categorized_vars['signal'], "Variables de Signal", "🎯")

    with tab_risk:
        display_category_analysis(analyzer, categorized_vars['risk_management'], "Gestion des Risques", "💰")

    with tab_timing:
        display_category_analysis(analyzer, categorized_vars['timing'], "Variables de Timing", "⏰")

    with tab_advanced:
        display_advanced_metrics(analyzer, show_sharpe, show_calmar, show_recovery, show_rr)

def display_overview(analyzer, profit_min, dd_max):
    """Affichage de la vue d'ensemble"""

    total_opts = len(analyzer.data) if analyzer.data is not None else 0
    profitable_opts = len(analyzer.filtered_data) if analyzer.filtered_data is not None else 0
    success_rate = (profitable_opts / total_opts * 100) if total_opts > 0 else 0

    # Métriques principales avec style
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_opts:,}</div>
            <div class="metric-label">Total Optimisations</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{profitable_opts:,}</div>
            <div class="metric-label">Profitables</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{success_rate:.1f}%</div>
            <div class="metric-label">Taux de Succès</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        if analyzer.advanced_metrics:
            max_profit = analyzer.advanced_metrics.get('max_profit', 0)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{max_profit:,.0f}€</div>
                <div class="metric-label">Meilleur Profit</div>
            </div>
            """, unsafe_allow_html=True)

    if profitable_opts == 0:
        st.warning(f"⚠️ Aucune optimisation ne respecte vos critères (profit ≥ {profit_min}€, DD ≤ {dd_max}%)")
        return

    # Graphique de distribution
    if analyzer.filtered_data is not None:
        profit_cols = [col for col in analyzer.filtered_data.columns if 'profit' in col.lower()]
        if profit_cols:
            fig = px.histogram(
                analyzer.filtered_data,
                x=profit_cols[0],
                title="📊 Distribution des Profits",
                nbins=30,
                color_discrete_sequence=['#1f77b4']
            )
            fig.update_layout(
                xaxis_title="Profit (€)",
                yaxis_title="Nombre d'optimisations",
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)

def display_category_analysis(analyzer, variables, category_name, icon):
    """Affichage de l'analyse par catégorie"""

    if not variables:
        st.info(f"Aucune variable {category_name.lower()} détectée dans ce fichier")
        return

    st.markdown(f'<div class="category-header">{icon} {category_name} ({len(variables)} variables)</div>',
                unsafe_allow_html=True)

    for var in variables:
        if var in analyzer.variable_stats:
            stats = analyzer.variable_stats[var]

            with st.expander(f"📊 {var}"):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"""
                    **Statistiques générales :**
                    - Valeurs uniques: {stats['valeurs_uniques']}
                    - Profit min: {stats['profit_min']:.2f}€
                    - Profit max: {stats['profit_max']:.2f}€
                    - Profit moyen: {stats['profit_moyen']:.2f}€
                    """)

                with col2:
                    if stats['top_valeurs']:
                        st.markdown("**🏆 Top 5 valeurs :**")
                        for i, top_val in enumerate(stats['top_valeurs'][:5], 1):
                            # Format d'affichage amélioré : Variable + Valeur
                            var_display = f"{var} {top_val['valeur']}"
                            st.write(f"{i}. **{var_display}** → {top_val['profit_moyen']:.2f}€ (×{top_val['occurrences']})")

                            # Affichage des profits min/moyen/max pour cette valeur spécifique
                            if 'profit_min' in top_val and 'profit_max' in top_val:
                                st.caption(f"   📊 Min: {top_val['profit_min']:.2f}€ | Moyen: {top_val['profit_moyen']:.2f}€ | Max: {top_val['profit_max']:.2f}€")

                            # Affichage du R/R (toujours visible maintenant)
                            if 'rr_ratio' in top_val:
                                rr_info = f"   🎯 R/R Moyen: {top_val['rr_ratio']:.2f}"
                                if 'rr_min' in top_val and 'rr_max' in top_val:
                                    rr_info += f" | Min: {top_val['rr_min']:.2f} | Max: {top_val['rr_max']:.2f}"
                                st.caption(rr_info)
                            else:
                                st.caption("   🎯 R/R: Non calculé")

def display_advanced_metrics(analyzer, show_sharpe, show_calmar, show_recovery, show_rr):
    """Affichage des métriques avancées"""

    if not analyzer.advanced_metrics:
        st.warning("Métriques avancées non disponibles")
        return

    metrics = analyzer.advanced_metrics

    st.markdown('<div class="category-header">📊 Métriques Avancées de Trading</div>', unsafe_allow_html=True)

    # Métriques de performance
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("💰 Profit Total", f"{metrics['total_profit']:,.2f}€")
        st.metric("📈 Win Rate", f"{metrics['win_rate']:.1f}%")

    with col2:
        st.metric("🎯 Profit Factor", f"{metrics['profit_factor']:.2f}")
        if show_rr:
            st.metric("⚖️ Risk/Reward", f"{metrics['risk_reward_ratio']:.2f}")

    with col3:
        if show_sharpe:
            st.metric("📊 Sharpe Ratio", f"{metrics['sharpe_ratio']:.3f}")
        st.metric("📉 Max Drawdown", f"{metrics['max_drawdown']:.2f}%")

    with col4:
        if show_calmar:
            st.metric("📈 Calmar Ratio", f"{metrics['calmar_ratio']:.3f}")
        if show_recovery:
            st.metric("🔄 Recovery Factor", f"{metrics['recovery_factor']:.2f}")

    # Graphiques de distribution des gains/pertes
    if analyzer.filtered_data is not None:
        profit_cols = [col for col in analyzer.filtered_data.columns if 'profit' in col.lower()]
        if profit_cols:
            profits = analyzer.filtered_data[profit_cols[0]]

            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=('Distribution Profits/Pertes', 'Analyse Win/Loss'),
                specs=[[{"secondary_y": False}, {"type": "pie"}]]
            )

            # Histogramme
            fig.add_trace(
                go.Histogram(x=profits, nbinsx=30, name="Distribution", marker_color='lightblue'),
                row=1, col=1
            )

            # Pie chart Win/Loss
            win_count = len(profits[profits > 0])
            loss_count = len(profits[profits <= 0])

            fig.add_trace(
                go.Pie(
                    labels=['Gains', 'Pertes'],
                    values=[win_count, loss_count],
                    marker_colors=['lightgreen', 'lightcoral']
                ),
                row=1, col=2
            )

            fig.update_layout(height=400, showlegend=False, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

    # Tableau des meilleures optimisations
    if analyzer.best_optimizations:
        st.subheader("🏆 Top Optimisations")

        best_df = pd.DataFrame(analyzer.best_optimizations)
        if 'profit' in best_df.columns:
            best_df['profit'] = best_df['profit'].apply(lambda x: f"{x:,.2f}€")

        st.dataframe(best_df, use_container_width=True, height=400)

        # Boutons de téléchargement
        col1, col2 = st.columns(2)
        with col1:
            csv = best_df.to_csv(index=False)
            st.download_button("📥 CSV", csv, "optimisations_v2.csv", "text/csv")

        with col2:
            json_data = {
                'advanced_metrics': analyzer.advanced_metrics,
                'best_optimizations': analyzer.best_optimizations,
                'variable_stats': analyzer.variable_stats
            }
            json_str = json.dumps(json_data, ensure_ascii=False, indent=2, default=str)
            st.download_button("📥 JSON Complet", json_str, "analyse_v2.json", "application/json")

if __name__ == "__main__":
    main()