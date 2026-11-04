
import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime

st.set_page_config(
    page_title="Mon Agent Financier",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Mon Agent Financier")
st.caption("Ton assistant personnel d'analyse des marchés financiers")

st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Choisir une rubrique",
    ["Tableau de bord", "Analyse d'une action", "Actualités", "Mon portefeuille"]
)

if page == "Tableau de bord":
    st.header("Bienvenue sur ton espace financier")

    st.write(
        "Ton agent personnel t'aidera à suivre les marchés, "
        "analyser les entreprises et comprendre ton portefeuille."
    )

    st.info("🚧 Projet en construction : les fonctionnalités arriveront progressivement.")

    col1, col2, col3 = st.columns(3)
    col1.metric("Marchés suivis", "Europe et USA")
    col2.metric("Budget mensuel", "0 €")
    col3.metric("Statut", "En construction")

elif page == "Analyse d'une action":
    st.header("🔎 Analyser une action")

    ticker = st.text_input(
        "Symbole boursier",
        placeholder="Exemple : AIR.PA, MC.PA ou AAPL"
    )

    if st.button("Lancer l'analyse"):
        if ticker:
            with st.spinner("Récupération des données..."):
                try:
                    stock = yf.Ticker(ticker)
                    history = stock.history(period="6mo")

                    if history.empty:
                        st.error("Aucune donnée trouvée. Vérifie le symbole.")
                    else:
                        st.subheader(ticker.upper())
                        st.line_chart(history["Close"])
                        st.write("Dernières données disponibles :")
                        st.dataframe(history.tail())
                except Exception as e:
                    st.error(f"Erreur : {e}")
        else:
            st.warning("Entre un symbole boursier.")

elif page == "Actualités":
    st.header("📰 Actualités financières")
    st.info("La récupération et l'analyse des actualités seront ajoutées prochainement.")

elif page == "Mon portefeuille":
    st.header("💼 Mon portefeuille")
    st.info("Nous ajouterons ici tes investissements et le suivi de tes performances.")

st.divider()
st.caption(f"Agent financier personnel — {datetime.now().strftime('%d/%m/%Y')}")
