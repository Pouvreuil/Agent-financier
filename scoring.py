
import pandas as pd


def safe_number(value):
    """Convertit une valeur en nombre exploitable."""
    try:
        number = float(value)
        if pd.isna(number):
            return None
        return number
    except (TypeError, ValueError):
        return None


def score_fundamentals(data):
    """
    Évalue une entreprise sur 100 points.
    Les données absentes ne sont pas considérées comme positives.
    """

    scores = {}
    details = {}
    missing = []

    def add_score(category, points, maximum, explanation):
        scores[category] = points
        details[category] = {
            "score": points,
            "maximum": maximum,
            "explanation": explanation
        }

    # 1. Rentabilité : 25 points
    profit = safe_number(data.get("net_income"))
    operating_margin = safe_number(data.get("operating_margin"))

    points = 0
    explanations = []

    if profit is not None:
        if profit > 0:
            points += 15
            explanations.append("Bénéfice net positif")
        else:
            explanations.append("Entreprise déficitaire")
    else:
        missing.append("Bénéfice net")

    if operating_margin is not None:
        if operating_margin > 0.15:
            points += 10
            explanations.append("Marge opérationnelle élevée")
        elif operating_margin > 0:
            points += 6
            explanations.append("Marge opérationnelle positive")
        else:
            explanations.append("Marge opérationnelle négative")
    else:
        missing.append("Marge opérationnelle")

    add_score("Rentabilité", points, 25, "; ".join(explanations))

    # 2. Endettement : 20 points
    debt = safe_number(data.get("debt"))
    cash = safe_number(data.get("cash"))

    points = 0
    explanation = ""

    if debt is not None and cash is not None:
        if debt == 0:
            points = 20
        elif cash >= debt:
            points = 18
        elif debt <= cash * 2:
            points = 12
        elif debt <= cash * 5:
            points = 6

        explanation = "Dette et trésorerie analysées"
    else:
        missing.append("Dette ou trésorerie")
        explanation = "Données insuffisantes"

    add_score("Endettement", points, 20, explanation)

    # 3. Croissance du chiffre d'affaires : 20 points
    revenue_growth = safe_number(data.get("revenue_growth"))

    points = 0
    if revenue_growth is not None:
        if revenue_growth > 0.15:
            points = 20
        elif revenue_growth > 0.05:
            points = 15
        elif revenue_growth > 0:
            points = 10
        else:
            points = 0
    else:
        missing.append("Croissance du chiffre d'affaires")

    add_score(
        "Croissance",
        points,
        20,
        "Croissance du chiffre d'affaires"
        if revenue_growth is not None else "Donnée indisponible"
    )

    # 4. Flux de trésorerie disponible : 15 points
    free_cash_flow = safe_number(data.get("free_cash_flow"))

    points = 0
    if free_cash_flow is not None:
        if free_cash_flow > 0:
            points = 15
        elif free_cash_flow == 0:
            points = 7
    else:
        missing.append("Free Cash Flow")

    add_score(
        "Trésorerie disponible",
        points,
        15,
        "Free Cash Flow positif"
        if free_cash_flow is not None and free_cash_flow > 0
        else "Free Cash Flow faible, négatif ou indisponible"
    )

    # 5. Valorisation : 20 points
    pe_ratio = safe_number(data.get("pe_ratio"))

    points = 0
    if pe_ratio is not None:
        if 0 < pe_ratio <= 15:
            points = 20
        elif pe_ratio <= 20 and pe_ratio > 0:
            points = 16
        elif pe_ratio <= 30 and pe_ratio > 0:
            points = 10
        elif pe_ratio > 30:
            points = 4
    else:
        missing.append("PER")

    add_score(
        "Valorisation",
        points,
        20,
        f"PER : {pe_ratio:.2f}" if pe_ratio is not None
        else "PER indisponible"
    )

    total = sum(scores.values())

    # Fiabilité des données : part des catégories renseignées
    reliability = (5 - len(set(missing))) / 5 * 100

    # On évite une conclusion trop affirmative si les données manquent
    if reliability < 60:
        verdict = "Données insuffisantes"
    elif total >= 75:
        verdict = "Fondamentaux intéressants"
    elif total >= 55:
        verdict = "Fondamentaux intermédiaires"
    else:
        verdict = "Fondamentaux fragiles"

    return {
        "total_score": total,
        "maximum_score": 100,
        "reliability": reliability,
        "verdict": verdict,
        "categories": details,
        "missing_data": missing
    }
