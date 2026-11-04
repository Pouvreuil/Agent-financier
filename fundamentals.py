
import yfinance as yf
import pandas as pd


def get_fundamentals(ticker):
    """
    Récupère les principaux indicateurs financiers
    d'une entreprise cotée.
    """

    stock = yf.Ticker(ticker)

    try:
        info = stock.info or {}
        financials = stock.financials
        balance = stock.balance_sheet
        cashflow = stock.cashflow

        def get_value(table, row):
            if table is None or table.empty or row not in table.index:
                return None

            values = table.loc[row].dropna()
            return float(values.iloc[0]) if not values.empty else None

        def safe_info(key):
            value = info.get(key)

            if value is None:
                return None

            try:
                if pd.isna(value):
                    return None
            except (TypeError, ValueError):
                pass

            return value

        # Données financières
        revenue = get_value(financials, "Total Revenue")
        net_income = get_value(financials, "Net Income")
        operating_income = get_value(financials, "Operating Income")

        total_debt = (
            get_value(balance, "Total Debt")
            or safe_info("totalDebt")
        )

        cash = (
            get_value(balance, "Cash And Cash Equivalents")
            or safe_info("totalCash")
        )

        free_cash_flow = (
            get_value(cashflow, "Free Cash Flow")
            or safe_info("freeCashflow")
        )

        # Calcul des marges
        operating_margin = None
        if revenue and operating_income is not None:
            operating_margin = operating_income / revenue * 100

        net_margin = None
        if revenue and net_income is not None:
            net_margin = net_income / revenue * 100

        # Dette / trésorerie
        debt_to_cash = None
        if total_debt is not None and cash is not None and cash > 0:
            debt_to_cash = total_debt / cash

        # Croissance du chiffre d'affaires
        revenue_growth = safe_info("revenueGrowth")

        # Harmonisation des données pour le moteur de notation
        return {
            "name": safe_info("longName") or ticker.upper(),
            "ticker": ticker.upper(),
            "sector": safe_info("sector"),
            "industry": safe_info("industry"),
            "currency": safe_info("currency"),
            "market_cap": safe_info("marketCap"),
            "price": safe_info("currentPrice") or safe_info("regularMarketPrice"),

            "pe_ratio": safe_info("trailingPE"),
            "forward_pe": safe_info("forwardPE"),
            "price_to_book": safe_info("priceToBook"),

            "revenue": revenue,
            "revenue_growth": revenue_growth,

            "net_income": net_income,
            "operating_income": operating_income,
            "operating_margin": operating_margin,
            "net_margin": net_margin,

            "total_debt": total_debt,
            "debt": total_debt,
            "cash": cash,
            "debt_to_cash": debt_to_cash,

            "free_cash_flow": free_cash_flow,

            "return_on_equity": safe_info("returnOnEquity"),
            "dividend_yield": safe_info("dividendYield"),
            "website": safe_info("website"),
            "employees": safe_info("fullTimeEmployees")
        }

    except Exception as error:
        return {
            "error": str(error),
            "ticker": ticker.upper()
        }


def format_number(value, currency=""):
    if value is None:
        return "Non disponible"

    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f} Md {currency}"

    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f} M {currency}"

    return f"{value:,.2f} {currency}"


def analyze_fundamentals(data):
    """
    Produit des observations simples à partir des données.
    """

    if data.get("error"):
        return ["Impossible de réaliser l'analyse : " + data["error"]]

    observations = []

    margin = data.get("operating_margin")

    if margin is not None:
        if margin >= 15:
            observations.append(
                "Marge opérationnelle élevée : bonne rentabilité opérationnelle."
            )
        elif margin >= 5:
            observations.append("Marge opérationnelle intermédiaire.")
        else:
            observations.append(
                "Marge opérationnelle faible : rentabilité à examiner."
            )

    pe = data.get("pe_ratio")

    if pe is not None:
        if pe <= 0:
            observations.append(
                "PER négatif ou nul : bénéfices négatifs ou non exploitables."
            )
        elif pe < 15:
            observations.append(
                "PER relativement faible. Cela ne signifie pas nécessairement "
                "que l'action est sous-évaluée."
            )
        elif pe <= 25:
            observations.append(
                "PER intermédiaire : à comparer avec les entreprises du même secteur."
            )
        else:
            observations.append(
                "PER élevé : les perspectives de croissance doivent justifier cette valorisation."
            )

    debt = data.get("debt_to_cash")

    if debt is not None:
        if debt > 3:
            observations.append(
                "Dette importante par rapport à la trésorerie disponible."
            )
        else:
            observations.append(
                "Rapport dette/trésorerie à examiner avec les flux de trésorerie."
            )

    cashflow = data.get("free_cash_flow")

    if cashflow is not None:
        if cashflow > 0:
            observations.append("Flux de trésorerie disponible positif.")
        else:
            observations.append(
                "Flux de trésorerie disponible négatif : comprendre les raisons."
            )

    if not observations:
        observations.append(
            "Données insuffisantes pour produire des observations pertinentes."
        )

    return observations
