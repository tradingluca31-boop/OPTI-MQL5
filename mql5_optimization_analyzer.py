#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyseur d'Optimisations MQL5
Analyse les résultats d'optimisation MetaTrader 5 depuis des fichiers Excel XML
"""

import pandas as pd
import numpy as np
from collections import defaultdict
import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple
import os
import json

class MQL5OptimizationAnalyzer:
    def __init__(self):
        self.data = None
        self.filtered_data = None
        self.variable_stats = {}
        self.best_optimizations = []

    def load_excel_xml(self, file_path: str):
        """Charge les données depuis un fichier Excel XML"""
        try:
            # Tentative de lecture directe avec pandas
            self.data = pd.read_excel(file_path)
            print(f"✅ Fichier chargé: {len(self.data)} optimisations trouvées")
            print(f"📊 Colonnes disponibles: {list(self.data.columns)}")
            return True
        except Exception as e:
            print(f"❌ Erreur de chargement: {e}")
            return False

    def filter_profitable_optimizations(self, min_profit: float = 7000, max_drawdown: float = 7.0):
        """Filtre les optimisations selon les critères de profit et drawdown"""
        if self.data is None:
            print("❌ Aucune donnée chargée")
            return

        # Recherche automatique des colonnes profit et drawdown
        profit_cols = [col for col in self.data.columns if 'profit' in col.lower() or 'gain' in col.lower() or 'résultat' in col.lower()]
        dd_cols = [col for col in self.data.columns if 'drawdown' in col.lower() or 'dd' in col.lower() or 'perte' in col.lower()]

        if not profit_cols:
            print("⚠️ Colonne profit non trouvée. Colonnes disponibles:")
            print(list(self.data.columns))
            return

        profit_col = profit_cols[0]
        dd_col = dd_cols[0] if dd_cols else None

        print(f"📈 Utilisation colonne profit: {profit_col}")
        if dd_col:
            print(f"📉 Utilisation colonne drawdown: {dd_col}")

        # Filtrage
        mask = self.data[profit_col] >= min_profit

        if dd_col:
            # Convertir les pourcentages négatifs en positifs si nécessaire
            dd_values = abs(self.data[dd_col])
            mask = mask & (dd_values <= max_drawdown)

        self.filtered_data = self.data[mask].copy()

        print(f"✅ {len(self.filtered_data)} optimisations filtrées (profit ≥ {min_profit}€, DD ≤ {max_drawdown}%)")

    def analyze_variables(self):
        """Analyse les variables d'optimisation et calcule les statistiques"""
        if self.filtered_data is None or len(self.filtered_data) == 0:
            print("❌ Aucune donnée filtrée disponible")
            return

        # Recherche des colonnes de variables (exclut les colonnes de résultats)
        result_keywords = ['profit', 'gain', 'drawdown', 'dd', 'trades', 'total', 'net', 'gross', 'balance', 'equity']
        variable_cols = []

        for col in self.filtered_data.columns:
            if not any(keyword in col.lower() for keyword in result_keywords):
                variable_cols.append(col)

        print(f"🔍 Variables détectées: {variable_cols}")

        # Trouve la colonne profit pour les calculs
        profit_cols = [col for col in self.filtered_data.columns if 'profit' in col.lower() or 'gain' in col.lower() or 'résultat' in col.lower()]
        profit_col = profit_cols[0] if profit_cols else None

        if not profit_col:
            print("❌ Colonne profit non trouvée pour l'analyse")
            return

        # Analyse chaque variable
        for var_col in variable_cols:
            try:
                # Nettoie les données (enlève les NaN, convertit en numérique si possible)
                clean_data = self.filtered_data[[var_col, profit_col]].dropna()

                if len(clean_data) == 0:
                    continue

                # Groupe par valeur de variable
                grouped = clean_data.groupby(var_col)[profit_col]

                self.variable_stats[var_col] = {
                    'occurrences': len(grouped),
                    'valeurs_uniques': clean_data[var_col].nunique(),
                    'profit_min': grouped.min().min(),
                    'profit_max': grouped.max().max(),
                    'profit_moyen': clean_data[profit_col].mean(),
                    'top_valeurs': []
                }

                # Top 5 des meilleures valeurs pour cette variable
                top_values = grouped.mean().nlargest(5)
                for value, avg_profit in top_values.items():
                    count = grouped.get_group(value).count()
                    self.variable_stats[var_col]['top_valeurs'].append({
                        'valeur': value,
                        'profit_moyen': avg_profit,
                        'occurrences': count,
                        'profit_total': grouped.get_group(value).sum()
                    })

            except Exception as e:
                print(f"⚠️ Erreur analyse variable {var_col}: {e}")

    def find_best_optimizations(self, top_n: int = 10):
        """Trouve les meilleures optimisations"""
        if self.filtered_data is None:
            print("❌ Aucune donnée filtrée disponible")
            return

        # Trouve la colonne profit
        profit_cols = [col for col in self.filtered_data.columns if 'profit' in col.lower() or 'gain' in col.lower() or 'résultat' in col.lower()]
        profit_col = profit_cols[0] if profit_cols else None

        if not profit_col:
            print("❌ Colonne profit non trouvée")
            return

        # Trie par profit décroissant
        best = self.filtered_data.nlargest(top_n, profit_col)

        self.best_optimizations = []
        for idx, row in best.iterrows():
            opt = {'profit': row[profit_col]}

            # Ajoute toutes les variables
            for col in self.filtered_data.columns:
                if col != profit_col:
                    opt[col] = row[col]

            self.best_optimizations.append(opt)

    def generate_report(self, output_file: str = "rapport_optimisations_mql5.txt"):
        """Génère un rapport complet"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("         RAPPORT D'ANALYSE DES OPTIMISATIONS MQL5\n")
            f.write("=" * 80 + "\n\n")

            # Résumé général
            f.write("📊 RÉSUMÉ GÉNÉRAL\n")
            f.write("-" * 40 + "\n")
            if self.data is not None:
                f.write(f"• Total optimisations: {len(self.data)}\n")
            if self.filtered_data is not None:
                f.write(f"• Optimisations profitables (>7000€, <7% DD): {len(self.filtered_data)}\n")
                if len(self.data) > 0:
                    success_rate = (len(self.filtered_data) / len(self.data)) * 100
                    f.write(f"• Taux de succès: {success_rate:.1f}%\n")
            f.write("\n")

            # Analyse par variables
            f.write("🔍 ANALYSE PAR VARIABLES\n")
            f.write("-" * 40 + "\n")
            for var_name, stats in self.variable_stats.items():
                f.write(f"\n🎯 {var_name}\n")
                f.write(f"   • Valeurs uniques testées: {stats['valeurs_uniques']}\n")
                f.write(f"   • Profit minimum: {stats['profit_min']:.2f}€\n")
                f.write(f"   • Profit maximum: {stats['profit_max']:.2f}€\n")
                f.write(f"   • Profit moyen: {stats['profit_moyen']:.2f}€\n")

                f.write(f"   • Top 5 valeurs:\n")
                for i, top_val in enumerate(stats['top_valeurs'], 1):
                    f.write(f"     {i}. {top_val['valeur']} → {top_val['profit_moyen']:.2f}€ (×{top_val['occurrences']})\n")

            # Meilleures optimisations
            f.write(f"\n🏆 TOP {len(self.best_optimizations)} MEILLEURES OPTIMISATIONS\n")
            f.write("-" * 40 + "\n")
            for i, opt in enumerate(self.best_optimizations, 1):
                f.write(f"\n#{i} - Profit: {opt['profit']:.2f}€\n")
                for key, value in opt.items():
                    if key != 'profit':
                        f.write(f"   {key}: {value}\n")

        print(f"📄 Rapport généré: {output_file}")

    def save_json_data(self, output_file: str = "optimisations_data.json"):
        """Sauvegarde les données en JSON pour usage ultérieur"""
        data_export = {
            'variable_stats': self.variable_stats,
            'best_optimizations': self.best_optimizations,
            'summary': {
                'total_optimizations': len(self.data) if self.data is not None else 0,
                'profitable_optimizations': len(self.filtered_data) if self.filtered_data is not None else 0
            }
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data_export, f, ensure_ascii=False, indent=2, default=str)

        print(f"💾 Données sauvegardées: {output_file}")


def main():
    """Fonction principale d'exemple d'utilisation"""
    analyzer = MQL5OptimizationAnalyzer()

    # Instructions d'utilisation
    print("🚀 ANALYSEUR D'OPTIMISATIONS MQL5")
    print("=" * 50)
    print("\n📋 UTILISATION:")
    print("1. Placez votre fichier Excel XML dans le même dossier")
    print("2. Modifiez le nom du fichier ci-dessous")
    print("3. Exécutez le script")
    print("\n💡 EXEMPLE:")

    # Exemple d'utilisation (à adapter)
    fichier_excel = "optimizations.xlsx"  # ← CHANGEZ CE NOM

    if os.path.exists(fichier_excel):
        print(f"📁 Chargement de {fichier_excel}...")

        if analyzer.load_excel_xml(fichier_excel):
            print("🔄 Filtrage des optimisations profitables...")
            analyzer.filter_profitable_optimizations(min_profit=7000, max_drawdown=7.0)

            print("📊 Analyse des variables...")
            analyzer.analyze_variables()

            print("🏆 Recherche des meilleures optimisations...")
            analyzer.find_best_optimizations(top_n=10)

            print("📄 Génération du rapport...")
            analyzer.generate_report()
            analyzer.save_json_data()

            print("\n✅ ANALYSE TERMINÉE!")
            print("📖 Consultez 'rapport_optimisations_mql5.txt' pour les résultats")
    else:
        print(f"❌ Fichier '{fichier_excel}' non trouvé")
        print("📁 Fichiers Excel disponibles dans le dossier:")
        excel_files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.xls', '.xml'))]
        for f in excel_files:
            print(f"   • {f}")


if __name__ == "__main__":
    main()