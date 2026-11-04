
import re
from datetime import datetime

import streamlit as st
import yfinance as yf
import pandas as pd
from google import genai
from google.genai import types


# =====================================================
# CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="Mon Agent Financier",
    page_icon="📈",
    layout="centered"
)

MODEL = "gemini-3.8-flash"

SYSTEM_INSTRUCTION = """
Tu es Mon Agent Financier, un assistant spécialisé dans
l'investissement en actions et ETF.

TON OBJECTIF :
Aider l'utilisateur à prendre des décisions d'investissement
éclairées, avec des réponses simples, concrètes et argumentées.

TES MISSIONS :
- Analyser un portefeuille et ses différentes positions.
- Étudier une action et son entreprise.
- Évaluer une opportunité d'investissement.
- Adapter les propositions au budget disponible.
- Examiner les risques et les perspectives.
- Comparer plusieurs entreprises.
- Expliquer les décisions en termes accessibles à un débutant.

PRÉFÉRENCES DE L'UTILISATEUR :
- Marchés européens et américains.
- Investissement à court et long terme.
- Approche équilibrée du risque.
- Exclusions éthiques : porc, alcool et jeux d'argent/casino.
- Les banques sont acceptées.
- Privilégier les investissements accessibles avec de petits montants.
- Tenir compte de l'éligibilité au PEA lorsque c'est pertinent.

RÈGLES IMPÉRATIVES :
1. Utilise les données financières fournies dans le contexte.
2. Ne prétends jamais avoir consulté des informations que tu n'as pas reçues.
3. Distingue les données récentes, anciennes et indisponibles.
4. Ne fabrique jamais un cours, un résultat financier ou une actualité.
5. Si tu n'as pas les positions du portefeuille, demande à l'utilisateur
   de fournir les titres, quantités et prix d'achat.
6. Ne confonds jamais une donnée manquante avec une mauvaise performance.
7. Pour chaque recommandation, explique les raisons et les risques.
8. Ne promets jamais un rendement.
9. Ne donne jamais une certitude sur l'évolution future d'une action.
10. Ne passe jamais d'ordre d'achat ou de vente.

FORMAT DES RÉPONSES :

Commence par une conclusion claire :
- Acheter / Envisager un achat
- Conserver
- Renforcer avec prudence
- Vendre / Envisager une vente
- Attendre

Puis présente :
1. Mon avis.
2. Les raisons principales.
3. Les risques.
4. Ce qui pourrait changer mon avis.

Adapte la longueur à la question. Évite le jargon inutile.
Si les données sont insuffisantes, dis-le clairement.

Tu es un assistant d'aide à la décision, pas un conseiller financier
agréé. L'utilisateur garde toujours le contrôle de ses décisions.
"""


# =====================================================
# STYLE
# =====================================================

st.title("📈 Mon Agent Financier")

st.caption(
    "Ton assistant personnel pour comprendre les marchés "
    "et prendre tes décisions d'investissement."
)

with st.sidebar:

    st.header("⚙️ Mon assistant")

    st.write("**Marchés :** Europe et États-Unis")
    st.write("**Style :** Investissement équilibré")
    st.write("**Budget :** À définir selon tes projets")

    st.divider()

    st.caption(
        "Les analyses sont indicatives. "
        "Aucun ordre boursier n'est exécuté."
    )

    if st.button("Nouvelle conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# =====================================================
# CONNEXION À GEMINI
# =====================================================

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]

    client = genai.Client(api_key=API_KEY)

except Exception:

    st.error(
        "Impossible de trouver la clé API Gemini. "
        "Vérifie les Secrets de ton application Streamlit."
    )

    st.stop()


# =====================================================
# RECONNAISSANCE DE QUELQUES ENTREPRISES
# =====================================================

COMPANY_TICKERS = {
    "airbus": "AIR.PA",
    "apple": "AAPL",
    "microsoft": "MSFT",
    "nvidia": "NVDA",
    "amazon": "AMZN",
    "tesla": "TSLA",
    "lvmh": "MC.PA",
    "totalenergies": "TTE.PA",
    "sanofi": "SAN.PA",
    "bnp paribas": "BNP.PA",
    "loreal": "OR.PA",
    "l'oréal": "OR.PA",
}


# =====================================================
# IDENTIFICATION DES ACTIONS DANS LA QUESTION
# =====================================================

def find_tickers(question):

    candidates = []

    # Recherche de symboles comme AIR.PA, AAPL, MSFT
    matches = re.findall(
        r"\b[A-Z]{1,5}(?:\.[A-Z]{1,3})?\b",
        question
    )

    excluded = {
        "PEA", "ETF", "EUR", "USD", "USA",
        "CAC", "IA", "TVA", "PER", "RSI",
        "ACHAT", "VENTE", "ACTION", "ACTIONS"
    }

    for ticker in matches:

        if ticker not in excluded and ticker not in candidates:
            candidates.append(ticker)

    # Recherche de noms d'entreprises connus
    lower_question = question.lower()

    for company, ticker in COMPANY_TICKERS.items():

        if company in lower_question and ticker not in candidates:
            candidates.append(ticker)

    return candidates[:5]


# =====================================================
# RÉCUPÉRATION DES DONNÉES BOURSIÈRES
# =====================================================

@st.cache_data(ttl=900, show_spinner=False)
def get_market_data(ticker):

    result = {
        "ticker": ticker,
        "error": None
    }

    try:

        stock = yf.Ticker(ticker)

        history = stock.history(period="1y")

        if history.empty:

            result["error"] = "Aucun historique boursier disponible."
            return result

        info = stock.info or {}

        close = history["Close"].dropna()

        current_price = float(close.iloc[-1])

        previous_price = (
            float(close.iloc[-2])
            if len(close) > 1 else None
        )

        variation = None

        if previous_price:
            variation = (
                (current_price / previous_price) - 1
            ) * 100

        def performance(period):

            if len(close) < period:
                return None

            old_price = float(close.iloc[-period])

            if old_price == 0:
                return None

            return round(
                ((current_price / old_price) - 1) * 100,
                2
            )

        # Données principales
        result.update({

            "name": info.get("longName") or info.get("shortName"),

            "sector": info.get("sector"),

            "industry": info.get("industry"),

            "currency": info.get("currency"),

            "price": round(current_price, 3),

            "daily_change": (
                round(variation, 2)
                if variation is not None else None
            ),

            "performance_1_month": performance(22),

            "performance_3_months": performance(66),

            "performance_6_months": performance(126),

            "performance_1_year": performance(252),

            "market_cap": info.get("marketCap"),

            "PER": info.get("trailingPE"),

            "forward_PER": info.get("forwardPE"),

            "profit_margin": info.get("profitMargins"),

            "revenue_growth": info.get("revenueGrowth"),

            "total_debt": info.get("totalDebt"),

            "cash": info.get("totalCash"),

            "dividend_yield": info.get("dividendYield"),

            "fifty_day_average": info.get("fiftyDayAverage"),

            "two_hundred_day_average": info.get("twoHundredDayAverage"),

            "data_date": str(history.index[-1].date())

        })

        # Actualités disponibles chez Yahoo Finance
        try:

            news_items = stock.news or []

            news_list = []

            for item in news_items[:5]:

                content = item.get("content", item)

                title = content.get("title")

                publisher = content.get("publisher")

                if not publisher:

                    provider = content.get("provider", {})
                    publisher = provider.get("displayName")

                if not title:
                    continue

                news_list.append({

                    "title": title,

                    "publisher": publisher or "Source inconnue",

                    "date": content.get("pubDate"),

                    "url": (
                        content.get("canonicalUrl", {}).get("url")
                        or content.get("clickThroughUrl", {}).get("url")
                    )

                })

            result["news"] = news_list

        except Exception:

            result["news"] = []

        return result

    except Exception as e:

        result["error"] = str(e)

        return result


# =====================================================
# CONSTRUCTION DU CONTEXTE FINANCIER
# =====================================================

def build_financial_context(question):

    tickers = find_tickers(question)

    if not tickers:

        return (
            "Aucun symbole boursier précis n'a été identifié dans "
            "la question. Tu ne disposes donc pas de données de marché "
            "récupérées automatiquement pour cette demande. "
            "Ne prétends pas avoir effectué un scan du marché."
        )

    context = []

    context.append(
        "DONNÉES BOURSIÈRES RÉCUPÉRÉES AUTOMATIQUEMENT :"
    )

    for ticker in tickers:

        data = get_market_data(ticker)

        context.append("\n-------------------------")
        context.append(f"SYMBOLE : {ticker}")

        if data.get("error"):

            context.append(
                "Erreur de récupération : " + data["error"]
            )

            continue

        for key, value in data.items():

            if key not in ["news", "error"] and value is not None:

                context.append(f"{key} : {value}")

        news = data.get("news", [])

        context.append("ACTUALITÉS DISPONIBLES :")

        if news:

            for article in news:

                context.append(
                    f"- {article['title']} "
                    f"({article['publisher']}, {article['date']})"
                )

                if article.get("url"):
                    context.append(
                        "Lien : " + article["url"]
                    )

        else:

            context.append(
                "Aucune actualité récupérée."
            )

    context.append(
        "\nIMPORTANT : les données peuvent être différées, "
        "incomplètes ou indisponibles. Vérifie leur date."
    )

    return "\n".join(context)


# =====================================================
# HISTORIQUE DE CONVERSATION
# =====================================================

if "messages" not in st.session_state:

    st.session_state.messages = []


# =====================================================
# AFFICHAGE DE LA CONVERSATION
# =====================================================

if not st.session_state.messages:

    st.info(
        "Bonjour ! Je suis ton assistant financier. "
        "Pose-moi une question sur ton portefeuille, "
        "une action ou un investissement."
    )

    st.markdown("### Quelques exemples")

    st.markdown("""
    - Analyse Airbus et dis-moi si elle est intéressante.
    - J'ai 50 € à investir, que me conseilles-tu ?
    - Analyse mon portefeuille et dis-moi quoi faire.
    - Compare Airbus et Safran.
    - Quels sont les risques de mon investissement ?
    """)


for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])


# =====================================================
# ENVOI D'UNE QUESTION
# =====================================================

question = st.chat_input(
    "Pose ta question à ton agent financier..."
)


if question:

    st.session_state.messages.append({

        "role": "user",

        "content": question

    })

    with st.chat_message("user"):

        st.markdown(question)

    with st.chat_message("assistant"):

        with st.spinner(
            "J'analyse ta demande et les données disponibles..."
        ):

            try:

                financial_context = build_financial_context(question)

                current_date = datetime.now().strftime("%d/%m/%Y")

                complete_context = f"""
DATE DU JOUR : {current_date}

QUESTION DE L'UTILISATEUR :
{question}

{financial_context}

Réponds maintenant à la question de l'utilisateur.
Sois précis, honnête et concret.
"""

                history = []

                for message in st.session_state.messages[:-1]:

                    role = (
                        "user"
                        if message["role"] == "user"
                        else "model"
                    )

                    history.append(
                        types.Content(
                            role=role,
                            parts=[
                                types.Part.from_text(
                                    text=message["content"]
                                )
                            ]
                        )
                    )

                history.append(
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(
                                text=complete_context
                            )
                        ]
                    )
                )

                response = client.models.generate_content(

                    model=MODEL,

                    contents=history,

                    config=types.GenerateContentConfig(

                        system_instruction=SYSTEM_INSTRUCTION,

                        temperature=0.4,

                        max_output_tokens=2500

                    )

                )

                answer = response.text

                if not answer:

                    answer = (
                        "Je n'ai pas réussi à produire une réponse. "
                        "Essaie de reformuler ta question."
                    )

                st.markdown(answer)

                st.session_state.messages.append({

                    "role": "assistant",

                    "content": answer

                })

            except Exception as e:

                st.error(
                    "Une erreur est survenue pendant l'analyse."
                )

                st.code(str(e))
