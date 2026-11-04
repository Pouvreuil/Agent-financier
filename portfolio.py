
import yfinance as yf
import pandas as pd


def analyze_portfolio(positions):
    results = []

    for position in positions:
        ticker = position["ticker"].strip().upper()
        quantity = float(position["quantity"])
        average_price = float(position["average_price"])

        if quantity <= 0 or average_price <= 0:
            continue

        try:
            stock = yf.Ticker(ticker)
            history = stock.history(period="5d")

            if history.empty:
                continue

            current_price = float(history["Close"].dropna().iloc[-1])

            invested = quantity * average_price
            current_value = quantity * current_price
            gain = current_value - invested
            performance = gain / invested * 100

            results.append({
                "Entreprise": ticker,
                "Quantité": quantity,
                "Prix de revient": average_price,
                "Dernier cours": current_price,
                "Montant investi": invested,
                "Valeur actuelle": current_value,
                "Plus-value / moins-value": gain,
                "Performance (%)": performance
            })

        except Exception:
            continue

    df = pd.DataFrame(results)

    if not df.empty:
        total_invested = df["Montant investi"].sum()
        total_value = df["Valeur actuelle"].sum()

        df["Poids du portefeuille (%)"] = (
            df["Valeur actuelle"] / total_value * 100
        )

        summary = {
            "invested": total_invested,
            "value": total_value,
            "gain": total_value - total_invested,
            "performance": (
                (total_value / total_invested - 1) * 100
                if total_invested else 0
            )
        }
    else:
        summary = {
            "invested": 0,
            "value": 0,
            "gain": 0,
            "performance": 0
        }

    return df, summary
