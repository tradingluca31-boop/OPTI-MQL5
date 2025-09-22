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
            print(f"[OK] Fichier charge: {len(self.data)} optimisations trouvees")
            print(f"[INFO] Colonnes disponibles: {list(self.data.columns)}")
            return True
        except Exception as e:
            print(f"[ERREUR] Erreur de chargement: {e}")
            return False

    def filter_profitable_optimizations(self, min_profit: float = 7000, max_drawdown: float = 7.0):
        """Filtre les optimisations selon les critères de profit et drawdown"""
        if self.data is None:
            print("[ERREUR] Aucune donnee chargee")
            return

        # Recherche automatique des colonnes profit et drawdown
        profit_cols = [col for col in self.data.columns if 'profit' in col.lower() or 'gain' in col.lower() or 'resultat' in col.lower()]
        dd_cols = [col for col in self.data.columns if 'drawdown' in col.lower() or 'dd' in col.lower() or 'perte' in col.lower()]

        if not profit_cols:
            print("[WARNING] Colonne profit non trouvee. Colonnes disponibles:")
            print(list(self.data.columns))
            return

        profit_col = profit_cols[0]
        dd_col = dd_cols[0] if dd_cols else None

        print(f"[PROFIT] Utilisation colonne profit: {profit_col}")
        if dd_col:
            print(f"[DD] Utilisation colonne drawdown: {dd_col}")

        # Filtrage
        mask = self.data[profit_col] >= min_profit

        if dd_col:
            # Convertir les pourcentages négatifs en positifs si nécessaire
            dd_values = abs(self.data[dd_col])
            mask = mask & (dd_values <= max_drawdown)

        self.filtered_data = self.data[mask].copy()

        print(f"[OK] {len(self.filtered_data)} optimisations filtrees (profit >= {min_profit} euros, DD <= {max_drawdown}%)")

    def analyze_variables(self):
        """Analyse les variables d'optimisation et calcule les statistiques"""
        if self.filtered_data is None or len(self.filtered_data) == 0:
            print("[ERREUR] Aucune donnee filtree disponible")
            return

        # Recherche des colonnes de variables (exclut les colonnes de résultats)
        result_keywords = ['profit', 'gain', 'drawdown', 'dd', 'trades', 'total', 'net', 'gross', 'balance', 'equity']
        variable_cols = []

        for col in self.filtered_data.columns:
            if not any(keyword in col.lower() for keyword in result_keywords):
                variable_cols.append(col)

        print(f"[INFO] Variables detectees: {variable_cols}")

        # Trouve la colonne profit pour les calculs
        profit_cols = [col for col in self.filtered_data.columns if 'profit' in col.lower() or 'gain' in col.lower() or 'resultat' in col.lower()]
        profit_col = profit_cols[0] if profit_cols else None

        if not profit_col:
            print("[ERREUR] Colonne profit non trouvee pour l'analyse")
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
                print(f"[WARNING] Erreur analyse variable {var_col}: {e}")

    def find_best_optimizations(self, top_n: int = 10):
        """Trouve les meilleures optimisations"""
        if self.filtered_data is None:
            print("[ERREUR] Aucune donnee filtree disponible")
            return

        # Trouve la colonne profit
        profit_cols = [col for col in self.filtered_data.columns if 'profit' in col.lower() or 'gain' in col.lower() or 'resultat' in col.lower()]
        profit_col = profit_cols[0] if profit_cols else None

        if not profit_col:
            print("[ERREUR] Colonne profit non trouvee")
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

    def calculate_advanced_metrics(self):
        """Calcule les métriques avancées de trading"""
        if self.filtered_data is None:
            return

        self.advanced_metrics = {}

        # Colonnes de base
        profit_cols = [col for col in self.filtered_data.columns if 'profit' in col.lower()]
        dd_cols = [col for col in self.filtered_data.columns if 'drawdown' in col.lower() or 'dd' in col.lower()]
        trades_cols = [col for col in self.filtered_data.columns if 'trades' in col.lower()]

        if not profit_cols:
            return

        profit_col = profit_cols[0]
        dd_col = dd_cols[0] if dd_cols else None
        trades_col = trades_cols[0] if trades_cols else None

        profits = self.filtered_data[profit_col]

        # Métriques de base
        total_profit = profits.sum()
        avg_profit = profits.mean()
        max_profit = profits.max()
        min_profit = profits.min()

        # Risk/Reward et autres métriques
        if dd_col:
            drawdowns = abs(self.filtered_data[dd_col])
            max_dd = drawdowns.max()
            avg_dd = drawdowns.mean()

            # Calmar Ratio = Annual Return / Max Drawdown
            calmar_ratio = (avg_profit * 252) / max_dd if max_dd > 0 else 0

            # Recovery Factor = Total Profit / Max Drawdown
            recovery_factor = total_profit / max_dd if max_dd > 0 else 0
        else:
            max_dd = 0
            avg_dd = 0
            calmar_ratio = 0
            recovery_factor = 0

        # Sharpe Ratio approximation
        if len(profits) > 1:
            returns_std = profits.std()
            sharpe_ratio = avg_profit / returns_std if returns_std > 0 else 0
        else:
            sharpe_ratio = 0

        # Win Rate et Profit Factor
        winning_trades = profits[profits > 0]
        losing_trades = profits[profits < 0]

        win_rate = len(winning_trades) / len(profits) * 100 if len(profits) > 0 else 0

        total_wins = winning_trades.sum() if len(winning_trades) > 0 else 0
        total_losses = abs(losing_trades.sum()) if len(losing_trades) > 0 else 1
        profit_factor = total_wins / total_losses if total_losses > 0 else 0

        # Risk/Reward Ratio
        avg_win = winning_trades.mean() if len(winning_trades) > 0 else 0
        avg_loss = abs(losing_trades.mean()) if len(losing_trades) > 0 else 1
        rr_ratio = avg_win / avg_loss if avg_loss > 0 else 0

        self.advanced_metrics = {
            'total_optimizations': len(self.filtered_data),
            'total_profit': total_profit,
            'average_profit': avg_profit,
            'max_profit': max_profit,
            'min_profit': min_profit,
            'max_drawdown': max_dd,
            'average_drawdown': avg_dd,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'risk_reward_ratio': rr_ratio,
            'sharpe_ratio': sharpe_ratio,
            'calmar_ratio': calmar_ratio,
            'recovery_factor': recovery_factor,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'average_win': avg_win,
            'average_loss': avg_loss
        }

    def categorize_variables(self):
        """Classe les variables par catégories"""
        if self.filtered_data is None:
            return {}

        categorized = {
            'signal': [],
            'risk_management': [],
            'timing': [],
            'filter': [],
            'other': []
        }

        # Colonnes de résultats à exclure
        result_keywords = ['profit', 'gain', 'drawdown', 'dd', 'trades', 'total', 'net', 'gross', 'balance', 'equity', 'result', 'pass']

        variable_categories = {
            'signal': ['rsi', 'ma', 'ema', 'sma', 'macd', 'bollinger', 'stoch', 'period'],
            'risk_management': ['sl', 'tp', 'stop', 'take', 'risk', 'position', 'lot'],
            'timing': ['hour', 'time', 'session', 'day', 'week'],
            'filter': ['filter', 'confirm', 'trend', 'volume']
        }

        for col in self.filtered_data.columns:
            if any(keyword in col.lower() for keyword in result_keywords):
                continue

            col_lower = col.lower()
            categorized_flag = False

            for category, keywords in variable_categories.items():
                if any(keyword in col_lower for keyword in keywords):
                    categorized[category].append(col)
                    categorized_flag = True
                    break

            if not categorized_flag:
                categorized['other'].append(col)

        return categorized

    def generate_report(self, output_file: str = "rapport_optimisations_mql5.txt"):
        """Génère un rapport complet"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("         RAPPORT D'ANALYSE DES OPTIMISATIONS MQL5\n")
            f.write("=" * 80 + "\n\n")

            # Résumé général
            f.write("RESUME GENERAL\n")
            f.write("-" * 40 + "\n")
            if self.data is not None:
                f.write(f"• Total optimisations: {len(self.data)}\n")
            if self.filtered_data is not None:
                f.write(f"• Optimisations profitables (>7000 euros, <7% DD): {len(self.filtered_data)}\n")
                if len(self.data) > 0:
                    success_rate = (len(self.filtered_data) / len(self.data)) * 100
                    f.write(f"• Taux de succes: {success_rate:.1f}%\n")
            f.write("\n")

            # Analyse par variables
            f.write("ANALYSE PAR VARIABLES\n")
            f.write("-" * 40 + "\n")
            for var_name, stats in self.variable_stats.items():
                f.write(f"\n[{var_name}]\n")
                f.write(f"   • Valeurs uniques testees: {stats['valeurs_uniques']}\n")
                f.write(f"   • Profit minimum: {stats['profit_min']:.2f} euros\n")
                f.write(f"   • Profit maximum: {stats['profit_max']:.2f} euros\n")
                f.write(f"   • Profit moyen: {stats['profit_moyen']:.2f} euros\n")

                f.write(f"   • Top 5 valeurs:\n")
                for i, top_val in enumerate(stats['top_valeurs'], 1):
                    f.write(f"     {i}. {top_val['valeur']} -> {top_val['profit_moyen']:.2f} euros (x{top_val['occurrences']})\n")

            # Meilleures optimisations
            f.write(f"\nTOP {len(self.best_optimizations)} MEILLEURES OPTIMISATIONS\n")
            f.write("-" * 40 + "\n")
            for i, opt in enumerate(self.best_optimizations, 1):
                f.write(f"\n#{i} - Profit: {opt['profit']:.2f} euros\n")
                for key, value in opt.items():
                    if key != 'profit':
                        f.write(f"   {key}: {value}\n")

        print(f"[OK] Rapport genere: {output_file}")

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

        print(f"[OK] Donnees sauvegardees: {output_file}")


def main():
    """Fonction principale d'exemple d'utilisation"""
    analyzer = MQL5OptimizationAnalyzer()

    # Instructions d'utilisation
    print("[INFO] ANALYSEUR D'OPTIMISATIONS MQL5")
    print("=" * 50)
    print("\n[INFO] UTILISATION:")
    print("1. Placez votre fichier Excel XML dans le meme dossier")
    print("2. Modifiez le nom du fichier ci-dessous")
    print("3. Executez le script")
    print("\n[INFO] EXEMPLE:")

    # Exemple d'utilisation (à adapter)
    fichier_excel = "optimizations.xlsx"  # <- CHANGEZ CE NOM

    if os.path.exists(fichier_excel):
        print(f"[INFO] Chargement de {fichier_excel}...")

        if analyzer.load_excel_xml(fichier_excel):
            print("[INFO] Filtrage des optimisations profitables...")
            analyzer.filter_profitable_optimizations(min_profit=7000, max_drawdown=7.0)

            print("[INFO] Analyse des variables...")
            analyzer.analyze_variables()

            print("[INFO] Recherche des meilleures optimisations...")
            analyzer.find_best_optimizations(top_n=10)

            print("[INFO] Generation du rapport...")
            analyzer.generate_report()
            analyzer.save_json_data()

            print("\n[OK] ANALYSE TERMINEE!")
            print("[INFO] Consultez 'rapport_optimisations_mql5.txt' pour les resultats")
    else:
        print(f"[ERREUR] Fichier '{fichier_excel}' non trouve")
        print("[INFO] Fichiers Excel disponibles dans le dossier:")
        excel_files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.xls', '.xml'))]
        for f in excel_files:
            print(f"   • {f}")


if __name__ == "__main__":
    main()