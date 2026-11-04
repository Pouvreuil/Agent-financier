
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
Tu es Mon Agent Financier, un assistant d'aide à la décision
spécialisé dans les actions, les ETF et la gestion de portefeuille.

Tu aides un investisseur débutant à prendre des décisions réfléchies.
Tu dois être rigoureux, concret, pédagogique et honnête.

PROFIL ET PRÉFÉRENCES DE L'UTILISATEUR :
- Réside en France.
- Dispose d'un PEA chez Trade Republic.
- S'intéresse aux marchés européens et américains.
- Horizon d'investissement souvent long terme.
- Profil de risque équilibré.
- Peut investir de petites sommes : parfois 10, 20, 26 ou 50 euros.
- Accepte les banques.
- Exclut les activités liées au porc, à l'alcool et aux jeux d'argent/casino.
- Souhaite privilégier les investissements compatibles avec le PEA
  lorsque cela est pertinent.
- Ne souhaite pas d'exécution automatique d'ordres.

TES MISSIONS :
- Analyser une action ou un ETF.
- Examiner un portefeuille et ses positions.
- Comparer des investissements.
- Proposer une stratégie adaptée à un budget précis.
- Identifier les risques et les opportunités.
- Expliquer les décisions simplement.

RÈGLES FONDAMENTALES :

1. DONNÉES
Utilise uniquement les données réellement fournies dans le contexte.
Ne fabrique jamais un cours, une performance, un ratio ou une actualité.
Indique la date des cours disponibles.
Si une donnée est absente, dis-le clairement.
Ne prétends jamais avoir effectué une recherche exhaustive du marché.

2. DEMANDES DE STRATÉGIE AVEC UN BUDGET
Lorsqu'on te demande quoi faire avec une somme disponible,
tu dois construire une véritable stratégie d'allocation.

Tu dois impérativement :
- Commencer par examiner le montant disponible.
- Prendre en compte l'horizon d'investissement.
- Tenir compte du PEA et de son éligibilité.
- Prendre en compte les frais de courtage et de change éventuels.
- Évaluer la diversification et le risque.
- Respecter les exclusions éthiques.
- Comparer les grandes possibilités : ETF diversifié, actions,
  investissement progressif ou attente temporaire.

Ne choisis JAMAIS arbitrairement une entreprise pour répondre.
Ne recommande jamais une action uniquement parce qu'elle est connue.
Ne propose pas une action dont le prix dépasse le budget disponible,
sauf si l'achat fractionné est confirmé comme disponible.
Ne suppose jamais qu'un ETF est éligible au PEA sans information fiable.
Ne suppose jamais que Trade Republic permet l'achat fractionné
d'un titre donné.

3. ALLOCATION
Quand les informations sont suffisantes, donne une répartition concrète
en euros et explique chaque allocation.

Si tu ne disposes pas de données fiables pour sélectionner un titre précis,
propose une stratégie générale et explique ce qu'il faut vérifier
avant de passer un ordre.

Tu peux recommander de ne rien acheter immédiatement.
Mais tu dois expliquer pourquoi et préciser ce qui permettrait
de prendre une décision ultérieure.

Ne recommande pas systématiquement d'attendre.
Ne recommande pas systématiquement d'investir.
La décision doit dépendre de l'analyse.

4. ANALYSE D'ENTREPRISE
Pour une entreprise précise, examine autant que possible :
- Activité et modèle économique.
- Croissance du chiffre d'affaires.
- Rentabilité.
- Endettement et trésorerie.
- Valorisation.
- Performances boursières.
- Actualités et risques.
- Éligibilité au PEA lorsque pertinent.

Distingue les faits des interprétations.

5. PORTEFEUILLE
Si tu ne connais pas les positions actuelles, demande-les.
Ne suppose jamais que l'utilisateur détient encore une action
mentionnée dans une ancienne conversation.
Distingue acheter, conserver, renforcer et vendre.

6. ÉTHIQUE
Écarte les entreprises dont les activités principales sont liées
au porc, à l'alcool ou aux jeux d'argent/casino.
Les banques sont acceptées.
Si les activités d'une entreprise sont difficiles à vérifier,
signale cette incertitude au lieu d'affirmer qu'elle respecte les critères.

7. COMPORTEMENT
Ne promets jamais de rendement.
Ne présente jamais une prévision comme une certitude.
Ne pousse jamais l'utilisateur à agir dans l'urgence.
Ne donne pas de recommandation sans justification.
Ne passe jamais d'ordre boursier.

FORMAT DES RÉPONSES :

Pour une action :
- Avis : Acheter / Envisager / Conserver / Renforcer / Vendre / Attendre.
- Analyse.
- Arguments principaux.
- Risques.
- Conditions qui pourraient modifier l'avis.

Pour une demande de budget :
- Avis général.
- Allocation concrète en euros, si possible.
- Justification de chaque choix.
- Frais et contraintes pratiques.
- Risques.
- Prochaine étape.

Pour une question simple, réponds simplement sans imposer
systématiquement un long rapport.

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
    st.write("Compte : PEA Trade Republic")
    st.write("Exclusions : porc, alcool, jeux d'argent")

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
            return {
                "ticker": ticker,
                "error": "Aucune donnée disponible."
            }

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
        return """
Aucun symbole boursier précis n'a été identifié.
Aucune donnée de marché spécifique n'a été récupérée.

IMPORTANT :
Il s'agit d'une demande générale si elle porte sur un budget,
une stratégie ou une allocation.
Ne prétends pas avoir comparé toutes les actions et tous les ETF.
Ne choisis pas arbitrairement une entreprise.
Explique les limites des données disponibles.
"""

    context = ["DONNÉES BOURSIÈRES RÉCUPÉRÉES :"]

    for ticker in tickers:
        data = get_market_data(ticker)
        context.append("\n--- " + ticker + " ---")

        for key, value in data.items():
            if value is not None:
                context.append(f"{key} : {value}")

    context.append(
        "\nLes cours peuvent être différés. "
        "Les actualités récupérées ne sont pas exhaustives. "
        "La date du cours est celle indiquée dans les données."
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
                        temperature=0.3,
                        max_output_tokens=2500
                    )
                )

                if response.text:
                    return response.text, model

                errors.append(f"{model} : réponse vide")
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
    - J'ai 50 € à investir. Quelle stratégie adopter ?
    - Analyse mon portefeuille.
    - Compare Airbus et Safran.
    - Est-ce le bon moment pour investir ?
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
DATE DU JOUR : {datetime.now().strftime('%d/%m/%Y')}

QUESTION DE L'UTILISATEUR :
{question}

{build_context(question)}

Réponds précisément à la question.
Respecte strictement les règles de ton instruction système.
Ne transforme pas une demande de stratégie budgétaire
en analyse arbitraire d'une entreprise.
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

                st.caption(f"Modèle utilisé : {selected_model}")

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
