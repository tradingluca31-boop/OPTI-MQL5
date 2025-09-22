# 🚀 OPTI MQL5 - Analyseur d'Optimisations MetaTrader 5

**Analyseur intelligent pour vos résultats d'optimisation MQL5**

Transformez vos fichiers Excel d'optimisation MetaTrader 5 en rapports détaillés avec statistiques avancées et tri automatique des meilleures configurations.

## 🎯 Objectif

Cet outil vous permet d'analyser automatiquement vos résultats d'optimisation MQL5 selon vos critères spécifiques :
- ✅ **Filtrage intelligent** : >7000€ profit + <7% DD maximum
- ✅ **Tri par variables** : RSI, SL, TP, et toutes autres variables
- ✅ **Statistiques détaillées** : Occurrences, profit min/moyen/max
- ✅ **Meilleures optimisations** : Top configurations classées

## 📊 Fonctionnalités

### 🔍 Filtrage Automatique
- Sélectionne uniquement les optimisations avec **profit ≥ 7000€**
- Exclut les configurations avec **drawdown > 7%**
- Détection automatique des colonnes profit/drawdown

### 📈 Analyse par Variables
- **Variables détectées automatiquement** : RSI, SL, TP, Period, etc.
- **Statistiques complètes** par variable :
  - Nombre d'occurrences
  - Profit minimum, maximum, moyen
  - Top 5 des meilleures valeurs
- **Tri intelligent** des configurations gagnantes

### 📋 Rapports Détaillés
- **Rapport texte** : Lisible et structuré
- **Export JSON** : Données brutes pour analyse avancée
- **Résumé exécutif** : Taux de succès, statistiques globales

## 🚀 Installation & Utilisation

### Prérequis
```bash
pip install pandas numpy openpyxl
```

### Utilisation Simple
1. **Placez votre fichier Excel** d'optimisation dans ce dossier
2. **Modifiez** le nom du fichier dans `example_usage.py` ligne 17
3. **Exécutez** :
```bash
python example_usage.py
```

### Utilisation Avancée
```python
from mql5_optimization_analyzer import MQL5OptimizationAnalyzer

# Créer l'analyseur
analyzer = MQL5OptimizationAnalyzer()

# Charger et analyser
analyzer.load_excel_xml("mes_optimisations.xlsx")
analyzer.filter_profitable_optimizations(min_profit=7000, max_drawdown=7.0)
analyzer.analyze_variables()
analyzer.find_best_optimizations(top_n=15)

# Générer les rapports
analyzer.generate_report("rapport_detaille.txt")
analyzer.save_json_data("donnees_completes.json")
```

## 📁 Structure du Projet

```
OPTI-MQL5/
├── README.md                      # Documentation principale
├── mql5_optimization_analyzer.py  # Analyseur principal
├── example_usage.py              # Script d'exemple
└── [votre_fichier.xlsx]          # Vos données d'optimisation
```

## 📊 Exemple de Sortie

```
📊 RÉSUMÉ GÉNÉRAL
----------------------------------------
• Total optimisations: 1000
• Optimisations profitables (>7000€, <7% DD): 45
• Taux de succès: 4.5%

🔍 ANALYSE PAR VARIABLES
----------------------------------------

🎯 RSI_Period
   • Valeurs uniques testées: 20
   • Profit minimum: 7012.50€
   • Profit maximum: 15420.80€
   • Profit moyen: 9850.30€
   • Top 5 valeurs:
     1. 14 → 12450.60€ (×3)
     2. 21 → 11230.40€ (×2)
     3. 18 → 10890.15€ (×4)
     ...

🏆 TOP 15 MEILLEURES OPTIMISATIONS
----------------------------------------
#1 - Profit: 15420.80€
   RSI_Period: 14
   Stop_Loss: 50
   Take_Profit: 150
   ...
```

## ⚙️ Configuration

Personnalisez vos critères dans `example_usage.py` :

```python
profit_minimum = 7000      # € minimum requis
drawdown_maximum = 7.0     # % DD maximum
top_optimisations = 15     # Nombre de meilleures configs
```

## 📋 Format de Fichier Supporté

**Fichiers acceptés :**
- Excel (.xlsx, .xls)
- XML exporté depuis MetaTrader 5

**Colonnes détectées automatiquement :**
- **Profit** : profit, gain, résultat, net, total
- **Drawdown** : drawdown, dd, perte
- **Variables** : Toutes autres colonnes (RSI, SL, TP, etc.)

## 🔧 Résolution de Problèmes

| Problème | Solution |
|----------|----------|
| Fichier non trouvé | Vérifiez le chemin et le nom du fichier |
| Colonnes non détectées | Assurez-vous que l'Excel contient profit/drawdown |
| Erreur de lecture | Sauvegardez votre fichier au format .xlsx |
| Aucune optimisation filtrée | Vérifiez vos critères (7000€, 7% DD) |

## 📞 Support

Pour questions ou améliorations, créez une issue sur ce dépôt GitHub.

---

**Développé pour optimiser l'analyse des stratégies de trading MQL5** 📈

*Transformez vos données d'optimisation en insights actionnables !*