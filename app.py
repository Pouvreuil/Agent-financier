
import re
import time
from datetime import datetime

import streamlit as st
import yfinance as yf
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

MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.7-flash",
    "gemini-3.8-flash"
]

SYSTEM_INSTRUCTION = """
Tu es Mon Agent Financier, un assistant spécialisé dans
l'investissement en actions et ETF.

Tu aides l'utilisateur à prendre des décisions éclairées.

TES MISSIONS :
- Analyser un portefeuille.
- Étudier une action et son entreprise.
- Évaluer une opportunité d'investissement.
- Adapter les propositions au budget disponible.
- Examiner les risques et les perspectives.
- Comparer plusieurs entreprises.
- Expliquer tes conclusions simplement.

PRÉFÉRENCES :
- Marchés européens et américains.
- Investissement à court et long terme.
- Approche équilibrée du risque.
- Exclusions éthiques : porc, alcool et jeux d'argent/casino.
- Les banques sont acceptées.
- Tenir compte de l'éligibilité au PEA lorsque pertinent.

RÈGLES :
1. Utilise les données financières fournies.
2. Ne prétends jamais avoir consulté une information absente.
3. Distingue les données récentes, anciennes et indisponibles.
4. Ne fabrique jamais de cours ou d'actualité.
5. Si tu ne connais pas le portefeuille, demande les positions.
6. Ne confonds pas donnée manquante et mauvaise performance.
7. Explique les raisons et les risques de tes recommandations.
8. Ne promets jamais de rendement.
9. Ne prétends jamais connaître l'évolution future d'une action.
10. Ne passe jamais d'ordre d'achat ou de vente.

FORMAT :
Commence par un avis clair :
- Acheter / envisager un achat
- Conserver
- Renforcer avec prudence
- Vendre / envisager une vente
- Attendre

Présente ensuite :
1. Mon avis.
2. Les raisons principales.
3. Les risques.
4. Ce qui pourrait changer mon avis.

Sois concret, honnête et accessible à un débutant.

Tu es un assistant d'aide à la décision, pas un conseiller financier agréé.
L'utilisateur conserve toujours le contrôle de ses décisions.
"""


# =====================================================
# INTERFACE
# =====================================================

st.title("📈 Mon Agent Financier")

st.caption(
    "Ton assistant personnel pour comprendre les marchés "
    "et prendre tes décisions d'investissement."
)

with st.sidebar:

    st.header("Mon assistant")

    st.write("Marchés : Europe et États-Unis")
    st.write("Profil : équilibré")
    st.write("Budget : selon tes projets")

    st.divider()

    if st.button("Nouvelle conversation"):
        st.session_state.messages = []
        st.rerun()

    st.caption("Aucun ordre boursier n'est exécuté.")


# =====================================================
# CONNEXION GEMINI
# =====================================================

try:
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)

except Exception:
    st.error(
        "Clé API introuvable. Vérifie les Secrets de Streamlit."
    )
    st.stop()


# =====================================================
# ENTREPRISES CONNUES
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
    "safran": "SAF.PA",
    "spineguard": "ALSGD.PA",
    "haffner": "ALHAF.PA",
    "valbiotis": "ALVAL.PA"
}


def find_tickers(question):

    candidates = []

    matches = re.findall(
        r"\b[A-Z]{1,5}(?:\.[A-Z]{1,3})?\b",
        question
    )

    excluded = {
        "PEA", "ETF", "EUR", "USD", "USA",
        "CAC", "IA", "TVA", "PER", "RSI"
    }

    for ticker in matches:

        if ticker not in excluded and ticker not in candidates:
            candidates.append(ticker)

    lower_question = question.lower()

    for company, ticker in COMPANY_TICKERS.items():

        if company in lower_question and ticker not in candidates:
            candidates.append(ticker)

    return candidates[:5]


# =====================================================
# DONNÉES BOURSIÈRES
# =====================================================

@st.cache_data(ttl=900, show_spinner=False)
def get_market_data(ticker):

    try:

        stock = yf.Ticker(ticker)
        history = stock.history(period="1y")

        if history.empty:
            return {"ticker": ticker, "error": "Aucune donnée disponible."}

        info = stock.info or {}
        close = history["Close"].dropna()

        current = float(close.iloc[-1])

        def performance(days):

            if len(close) <= days:
                return None

            old = float(close.iloc[-days - 1])

            if old == 0:
                return None

            return round((current / old - 1) * 100, 2)

        result = {
            "ticker": ticker,
            "name": info.get("longName") or info.get("shortName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "currency": info.get("currency"),
            "price": round(current, 3),
            "date": str(history.index[-1].date()),
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
            "news": []
        }

        try:

            for item in (stock.news or [])[:5]:

                content = item.get("content", item)

                title = content.get("title")

                if title:

                    provider = content.get("provider", {})

                    result["news"].append({
                        "title": title,
                        "publisher": provider.get(
                            "displayName", "Source inconnue"
                        ),
                        "date": content.get("pubDate"),
                        "url": content.get(
                            "canonicalUrl", {}
                        ).get("url")
                    })

        except Exception:
            pass

        return result

    except Exception as error:

        return {
            "ticker": ticker,
            "error": str(error)
        }


# =====================================================
# CONTEXTE FINANCIER
# =====================================================

def build_context(question):

    tickers = find_tickers(question)

    if not tickers:

        return (
            "Aucun symbole boursier identifié. "
            "Aucune donnée de marché spécifique n'a été récupérée. "
            "Ne prétends pas avoir effectué une analyse de marché exhaustive."
        )

    context = ["DONNÉES BOURSIÈRES :"]

    for ticker in tickers:

        data = get_market_data(ticker)

        context.append("\n--- " + ticker + " ---")

        for key, value in data.items():

            if value is not None:
                context.append(f"{key} : {value}")

    context.append(
        "\nLes cours peuvent être différés. "
        "Les actualités récupérées ne sont pas exhaustives."
    )

    return "\n".join(context)


# =====================================================
# APPEL DES MODÈLES AVEC SECOURS AUTOMATIQUE
# =====================================================

def ask_gemini(history, context):

    errors = []

    for model in MODELS:

        for attempt in range(2):

            try:

                response = client.models.generate_content(
                    model=model,
                    contents=history + [
                        types.Content(
                            role="user",
                            parts=[
                                types.Part.from_text(text=context)
                            ]
                        )
                    ],
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        temperature=0.4,
                        max_output_tokens=2500
                    )
                )

                if response.text:
                    return response.text, model

                errors.append(
                    f"{model} : réponse vide"
                )

                break

            except Exception as error:

                error_text = str(error)

                errors.append(
                    f"{model}, essai {attempt + 1} : {error_text}"
                )

                temporary_error = (
                    "503" in error_text
                    or "429" in error_text
                    or "UNAVAILABLE" in error_text
                    or "RESOURCE_EXHAUSTED" in error_text
                )

                if temporary_error and attempt == 0:

                    time.sleep(3)
                    continue

                break

    raise RuntimeError(
        "Tous les modèles sont momentanément indisponibles.\n\n"
        + "\n".join(errors[-4:])
    )


# =====================================================
# CONVERSATION
# =====================================================

if "messages" not in st.session_state:
    st.session_state.messages = []


if not st.session_state.messages:

    st.info(
        "Bonjour ! Pose-moi une question sur ton portefeuille, "
        "une action ou un investissement."
    )

    st.markdown("""
    **Exemples :**
    - Analyse Airbus et dis-moi si je dois conserver.
    - J'ai 50 € à investir. Que me conseilles-tu ?
    - Analyse mon portefeuille.
    - Compare Airbus et Safran.
    """)


for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


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

        with st.spinner("Ton agent analyse ta demande..."):

            try:

                context = f"""
DATE : {datetime.now().strftime('%d/%m/%Y')}

QUESTION :
{question}

{build_context(question)}

Réponds à la question en tenant compte de toutes les informations
disponibles. Si les données sont insuffisantes, explique-le.
"""

                history = []

                previous_messages = st.session_state.messages[:-1]

                for message in previous_messages:

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

                answer, selected_model = ask_gemini(
                    history,
                    context
                )

                st.markdown(answer)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer
                })

                st.caption(
                    f"Modèle utilisé : {selected_model}"
                )

            except Exception as error:

                st.error(
                    "Je n'ai pas réussi à obtenir une réponse "
                    "des modèles IA pour le moment."
                )

                st.warning(
                    "Cela peut être dû à une surcharge temporaire "
                    "ou à une limite d'utilisation de l'API."
                )

                with st.expander("Détails techniques"):

                    st.code(str(error))
