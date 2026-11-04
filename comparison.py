
import pandas as pd
from fundamentals import get_fundamentals


def compare_companies(tickers):
    """
    Compare plusieurs entreprises à partir
    de leurs données financières disponibles.
    """

    results = []

    for ticker in tickers:
        data = get_fundamentals(ticker)

        if data.get("error"):
            results.append({
                "Entreprise": ticker.upper(),
                "Erreur": data["error"]
            })
            continue

        results.append({
            "Entreprise": data.get("name"),
            "Symbole": data.get("ticker"),
            "Secteur": data.get("sector"),
            "Capitalisation": data.get("market_cap"),
            "PER": data.get("pe_ratio"),
            "PER prévisionnel": data.get("forward_pe"),
            "Marge opérationnelle (%)": data.get("operating_margin"),
            "Marge nette (%)": data.get("net_margin"),
            "Chiffre d'affaires": data.get("revenue"),
            "Résultat net": data.get("net_income"),
            "Dette": data.get("total_debt"),
            "Trésorerie": data.get("cash"),
            "Flux de trésorerie": data.get("free_cash_flow")
        })

    return pd.DataFrame(results)


def compare_observations(df):
    """
    Produit quelques observations comparatives.
    Les valeurs manquantes ne sont pas considérées comme nulles.
    """

    observations = []

    if df.empty:
        return ["Aucune entreprise à comparer."]

    if "Erreur" in df.columns:
        errors = df[df["Erreur"].notna()]
        for _, row in errors.iterrows():
            observations.append(
                f"Données indisponibles pour {row['Entreprise']}."
            )

    valid = df[df["PER"].notna()] if "PER" in df.columns else pd.DataFrame()

    if not valid.empty:
        positive = valid[valid["PER"] > 0]

        if not positive.empty:
            cheapest = positive.loc[positive["PER"].idxmin()]
            observations.append(
                f"{cheapest['Entreprise']} présente le PER positif le plus faible."
            )

    if "Marge opérationnelle (%)" in df.columns:
        margins = df[df["Marge opérationnelle (%)"].notna()]

        if not margins.empty:
            best = margins.loc[
                margins["Marge opérationnelle (%)"].idxmax()
            ]
            observations.append(
                f"{best['Entreprise']} présente la marge opérationnelle la plus élevée."
            )

    if not observations:
        observations.append(
            "Données insuffisantes pour établir une comparaison pertinente."
        )

    observations.append(
        "Une valorisation faible ou une marge élevée ne suffit pas "
        "à déterminer quelle entreprise constitue le meilleur investissement."
    )

    return observations
