
import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from fundamentals import get_fundamentals, analyze_fundamentals, format_number
from datetime import datetime
from comparison import compare_companies, compare_observations

st.set_page_config(
    page_title="Mon Agent Financier",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Mon Agent Financier")
st.caption("Assistant personnel d'analyse des marchés financiers")

st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Choisir une rubrique",
["Tableau de bord", "Analyse d'une action", "Analyse fondamentale", "Comparateur", "Actualités", "Mon portefeuille"]
)


def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1/period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


if page == "Tableau de bord":
    st.header("Bienvenue sur ton espace financier")
    st.write("Surveille les marchés et analyse tes investissements.")

    col1, col2, col3 = st.columns(3)
    col1.metric("Marchés suivis", "Europe et USA")
    col2.metric("Budget mensuel", "0 €")
    col3.metric("Statut", "En construction")

    st.info("Ton assistant financier évolue progressivement.")

elif page == "Analyse d'une action":
    st.header("🔎 Analyse technique")

    ticker = st.text_input(
        "Symbole boursier",
        placeholder="Exemple : AIR.PA ou AAPL"
    )

    if st.button("Lancer l'analyse"):
        if ticker:
            with st.spinner("Analyse des données financières..."):
                try:
                    stock = yf.Ticker(ticker)
                    history = stock.history(period="1y")

                    if history.empty or len(history) < 50:
                        st.error("Données insuffisantes pour cette analyse.")
                    else:
                        close = history["Close"]
                        volume = history["Volume"]

                        history["MM50"] = close.rolling(50).mean()
                        history["MM200"] = close.rolling(200).mean()
                        history["RSI"] = calculate_rsi(close)

                        current = close.iloc[-1]
                        previous = close.iloc[-2]
                        variation = ((current / previous) - 1) * 100

                        one_month = ((current / close.iloc[-22]) - 1) * 100
                        three_months = ((current / close.iloc[-66]) - 1) * 100
                        six_months = ((current / close.iloc[-126]) - 1) * 100

                        volatility = close.pct_change().std() * np.sqrt(252) * 100
                        rsi = history["RSI"].iloc[-1]

                        st.subheader(f"Analyse de {ticker.upper()}")

                        c1, c2, c3 = st.columns(3)
                        c1.metric("Dernier cours", f"{current:.2f}")
                        c2.metric("Variation du jour", f"{variation:.2f}%")
                        c3.metric("RSI (14)", f"{rsi:.1f}")

                        st.subheader("Performances historiques")
                        c1, c2, c3 = st.columns(3)
                        c1.metric("1 mois", f"{one_month:.2f}%")
                        c2.metric("3 mois", f"{three_months:.2f}%")
                        c3.metric("6 mois", f"{six_months:.2f}%")

                        st.subheader("Évolution du cours et moyennes mobiles")
                        st.line_chart(history[["Close", "MM50", "MM200"]])

                        st.subheader("Volume des échanges")
                        st.bar_chart(volume)

                        st.subheader("Volatilité annualisée")
                        st.metric("Volatilité estimée", f"{volatility:.2f}%")

                        st.subheader("Interprétation des indicateurs")

                        if rsi >= 70:
                            st.warning("RSI élevé : situation de surachat possible.")
                        elif rsi <= 30:
                            st.warning("RSI faible : situation de survente possible.")
                        else:
                            st.info("RSI dans une zone intermédiaire.")

                        if current > history["MM50"].iloc[-1]:
                            st.write("Le cours est au-dessus de sa moyenne mobile 50 jours.")
                        else:
                            st.write("Le cours est sous sa moyenne mobile 50 jours.")

                        if len(history) >= 200:
                            if current > history["MM200"].iloc[-1]:
                                st.write("Le cours est au-dessus de sa moyenne mobile 200 jours.")
                            else:
                                st.write("Le cours est sous sa moyenne mobile 200 jours.")

                        st.caption(
                            "Données indicatives issues de Yahoo Finance. "
                            "Les indicateurs techniques ne prédisent pas les performances futures."
                        )

                except Exception as e:
                    st.error(f"Erreur pendant l'analyse : {e}")
        else:
            st.warning("Entre un symbole boursier.")

elif page == "Analyse fondamentale":
    st.header("🏢 Analyse fondamentale d'une entreprise")

    ticker_fund = st.text_input(
        "Symbole de l'entreprise",
        placeholder="Exemple : AIR.PA, MC.PA ou MSFT"
    )

    if st.button("Analyser les fondamentaux"):
        if ticker_fund:
            with st.spinner("Récupération des données financières..."):
                data = get_fundamentals(ticker_fund)

                if data.get("error"):
                    st.error(data["error"])
                else:
                    st.subheader(data["name"])

                    st.write(
                        f"Secteur : {data.get('sector') or 'Non disponible'}"
                    )
                    st.write(
                        f"Industrie : {data.get('industry') or 'Non disponible'}"
                    )

                    currency = data.get("currency") or ""

                    st.subheader("Valorisation")
                    c1, c2, c3 = st.columns(3)
                    c1.metric(
                        "Capitalisation",
                        format_number(data.get("market_cap"), currency)
                    )
                    c2.metric(
                        "PER",
                        f"{data['pe_ratio']:.2f}" if data.get("pe_ratio") is not None else "N/D"
                    )
                    c3.metric(
                        "PER prévisionnel",
                        f"{data['forward_pe']:.2f}" if data.get("forward_pe") is not None else "N/D"
                    )

                    st.subheader("Rentabilité")
                    c1, c2 = st.columns(2)
                    c1.metric(
                        "Marge opérationnelle",
                        f"{data['operating_margin']:.2f}%" if data.get("operating_margin") is not None else "N/D"
                    )
                    c2.metric(
                        "Marge nette",
                        f"{data['net_margin']:.2f}%" if data.get("net_margin") is not None else "N/D"
                    )

                    st.subheader("Santé financière")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Chiffre d'affaires", format_number(data.get("revenue"), currency))
                    c2.metric("Résultat net", format_number(data.get("net_income"), currency))
                    c3.metric("Dette totale", format_number(data.get("total_debt"), currency))

                    st.write(
                        "Trésorerie :",
                        format_number(data.get("cash"), currency)
                    )
                    st.write(
                        "Flux de trésorerie disponible :",
                        format_number(data.get("free_cash_flow"), currency)
                    )

                    st.subheader("Observations de l'analyste")
                    for observation in analyze_fundamentals(data):
                        st.write("• " + observation)

                    st.caption(
                        "Données indicatives issues de Yahoo Finance. "
                        "Les informations peuvent être incomplètes ou différées. "
                        "Cette analyse ne constitue pas un conseil financier."
                    )
        else:
            st.warning("Entre un symbole boursier.")

elif page == "Comparateur":
    st.header("⚖️ Comparateur d'entreprises")
    st.write("Compare jusqu'à trois entreprises cotées.")

    tickers_input = st.text_input(
        "Symboles boursiers séparés par des virgules",
        value="AIR.PA, BA, LMT",
        help="Exemple : AIR.PA, MC.PA, MSFT"
    )

    if st.button("Comparer les entreprises"):
        tickers = list(dict.fromkeys(
            ticker.strip().upper()
            for ticker in tickers_input.split(",")
            if ticker.strip()
        ))

        if len(tickers) < 2:
            st.warning("Entre au moins deux entreprises.")
        elif len(tickers) > 3:
            st.warning("Trois entreprises maximum pour le moment.")
        else:
            with st.spinner("Comparaison financière en cours..."):
                comparison = compare_companies(tickers)

                st.subheader("Résultats comparatifs")
                st.dataframe(
                    comparison,
                    use_container_width=True,
                    hide_index=True
                )

                st.subheader("Observations")
                for observation in compare_observations(comparison):
                    st.write("• " + observation)

                st.caption(
                    "Les données peuvent être incomplètes ou différées. "
                    "Les entreprises de secteurs différents ne sont pas "
                    "nécessairement comparables directement."
                )

elif page == "Actualités":
    st.header("📰 Actualités financières")
    st.info("La veille économique et l'analyse des actualités seront ajoutées prochainement.")

elif page == "Mon portefeuille":
    st.header("💼 Mon portefeuille")
    st.info("Le suivi détaillé de tes investissements sera ajouté prochainement.")

st.divider()
st.caption(f"Agent financier personnel — {datetime.now().strftime('%d/%m/%Y')}")
