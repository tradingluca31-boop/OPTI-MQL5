#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exemple d'utilisation de l'analyseur d'optimisations MQL5
"""

from mql5_optimization_analyzer import MQL5OptimizationAnalyzer
import os

def analyze_my_optimizations():
    """Exemple d'analyse d'optimisations MQL5"""

    # Créer l'analyseur
    analyzer = MQL5OptimizationAnalyzer()

    # 🔧 CONFIGURATION - Modifiez ces paramètres selon vos besoins
    fichier_excel = "mon_fichier_optimisations.xlsx"  # ← Votre fichier Excel
    profit_minimum = 7000  # € minimum
    drawdown_maximum = 7.0  # % maximum
    top_optimisations = 15  # Nombre de meilleures optimisations à afficher

    print("🚀 DÉMARRAGE DE L'ANALYSE")
    print("=" * 50)

    # Vérifier si le fichier existe
    if not os.path.exists(fichier_excel):
        print(f"❌ Fichier '{fichier_excel}' non trouvé!")
        print("\n📁 Fichiers Excel disponibles:")
        excel_files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.xls', '.xml'))]
        if excel_files:
            for f in excel_files:
                print(f"   • {f}")
            print(f"\n💡 Modifiez 'fichier_excel' dans ce script avec un des fichiers ci-dessus")
        else:
            print("   Aucun fichier Excel trouvé dans ce dossier")
        return False

    # 1. Charger les données
    print(f"📂 Chargement de {fichier_excel}...")
    if not analyzer.load_excel_xml(fichier_excel):
        print("❌ Impossible de charger le fichier")
        return False

    # 2. Filtrer les optimisations profitables
    print(f"🔍 Filtrage: profit ≥ {profit_minimum}€ et DD ≤ {drawdown_maximum}%...")
    analyzer.filter_profitable_optimizations(
        min_profit=profit_minimum,
        max_drawdown=drawdown_maximum
    )

    # 3. Analyser les variables
    print("📊 Analyse des variables d'optimisation...")
    analyzer.analyze_variables()

    # 4. Trouver les meilleures optimisations
    print(f"🏆 Recherche du top {top_optimisations}...")
    analyzer.find_best_optimizations(top_n=top_optimisations)

    # 5. Générer les rapports
    print("📄 Génération des rapports...")
    analyzer.generate_report("mon_rapport_optimisations.txt")
    analyzer.save_json_data("mes_donnees_optimisations.json")

    print("\n✅ ANALYSE TERMINÉE!")
    print("📖 Consultez 'mon_rapport_optimisations.txt' pour les résultats détaillés")
    print("💾 Données brutes sauvegardées dans 'mes_donnees_optimisations.json'")

    return True

def quick_stats():
    """Affichage rapide de statistiques"""
    analyzer = MQL5OptimizationAnalyzer()

    # Remplacez par votre fichier
    fichier = "mon_fichier_optimisations.xlsx"

    if analyzer.load_excel_xml(fichier):
        total = len(analyzer.data)
        analyzer.filter_profitable_optimizations()
        profitable = len(analyzer.filtered_data) if analyzer.filtered_data is not None else 0

        print(f"📊 STATISTIQUES RAPIDES")
        print(f"   Total optimisations: {total}")
        print(f"   Optimisations profitables: {profitable}")
        if total > 0:
            print(f"   Taux de réussite: {(profitable/total)*100:.1f}%")

if __name__ == "__main__":
    # Lancer l'analyse complète
    analyze_my_optimizations()

    # Optionnel: affichage rapide des stats
    # quick_stats()