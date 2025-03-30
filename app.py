import streamlit as st
import pandas as pd
import json
from fuzzywuzzy import fuzz
from io import BytesIO

PATTERNS_FILE = 'patterns.json'

@st.cache_data
def load_patterns():
    try:
        with open(PATTERNS_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return [
            # Trafikproblemer
            'trafik', 'trafikale problemer', 'kø på vejen', 'langsom trafik', 'vejarbejde', 'vejen lukket',
            'lukkede veje', 'trafikprop', 'roadwork', 'road closed', 'heavy traffic', 'traffic jam', 'detour',
            # Ventetid ved afhentning
            'forsinket lager', 'lageret ikke klar', 'afsender ikke klar', 'blomsterbutikken åbnede senere',
            'butikken ikke åben', 'waiting at location', 'sender delayed', 'florist not ready', 'pickup delay', 'no one at pickup',
            # Ekstra stop / ændringer
            'tilføjet ekstra stop', 'ændret rækkefølge', 'stop fjernet', 'ændret rute', 'stop omrokeret',
            'ekstra leverance', 'changed route', 'extra stop', 'stop removed',
            # Modtager ikke til stede
            'ingen svarer', 'modtager ikke hjemme', 'kunden ikke hjemme', 'kunden tager ikke telefon',
            'receiver not present', 'no answer', 'not home', 'unanswered call', 'kunde ikke kontaktbar',
            # Forkert adresse
            'forkert vejnavn', 'forkert husnummer', 'forkert postnummer', 'kunne ikke finde adressen',
            'ikke på adressen', 'adressen findes ikke', 'wrong address', 'wrong street', 'not found', 'location mismatch',
            # Ingen adgang til leveringssted
            'porten lukket', 'ingen adgang', 'adgang nægtet', 'adgang kræver nøgle', 'adgang via alarm',
            'kunne ikke komme ind', 'no access', 'locked gate', 'restricted area', 'entrance blocked',
            # Udfordringer med kunden
            'kunden sur', 'kunden klager', 'afsender afviser', 'modtager uenig', 'problem med kunde',
            'receiver refused', 'sender issue', 'customer complaint',
            # Besværlig leveringsadresse
            'hospital', 'skole', 'center', 'gågade', 'etageejendom', 'manglende parkering',
            'svært at finde', 'busy location', 'pedestrian zone', 'no parking', 'delivery challenge'
        ]

def save_patterns(patterns):
    with open(PATTERNS_FILE, 'w') as file:
        json.dump(patterns, file)

def classify_note(note, patterns):
    if pd.isna(note):
        return "Nej"

    note_lower = note.lower()
    for pattern in patterns:
        score = fuzz.token_set_ratio(pattern.lower(), note_lower)
        if score > 85:
            return "Ja"
    return "Nej"

    

def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Resultat')
    processed_data = output.getvalue()
    return processed_data

def main():
    st.set_page_config(page_title="Controlling Report Analyzer", layout="wide")
    st.title("Controlling Report Analyzer")

    st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
    }
    div[class^='stRadio'] > label > div[data-testid='stMarkdownContainer'] {
        display: flex;
        gap: 10px;
        justify-content: center;
    }
    div[class^='stRadio'] input[type='radio'] {
        display: none;
    }
    div[class^='stRadio'] input[type='radio'] + div {
        border: 1px solid #ccc;
        border-radius: 6px;
        padding: 10px 20px;
        cursor: pointer;
        background-color: #f0f2f6;
        transition: background-color 0.2s ease;
    }
    div[class^='stRadio'] input[type='radio']:checked + div {
        background-color: #4285F4;
        color: white;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

menu = st.radio("Vælg funktion:", ["📊 Analyse", "📈 Statistik"], horizontal=True, key="menu_radio")

patterns = load_patterns()

if menu == "📊 Analyse":
        uploaded_file = st.file_uploader("Upload din Controlling Report (Excel)", type="xlsx")

        if uploaded_file:
            df = pd.read_excel(uploaded_file)
            if 'SupportNote' in df.columns:
                df = df[df['SupportNote'].notna()].copy()
                df['MatchedKeywords'] = df['SupportNote'].apply(lambda note: ', '.join([p for p in patterns if fuzz.token_set_ratio(p.lower(), note.lower()) > 85]))
                df['Keywords'] = df['MatchedKeywords'].apply(lambda matches: "Ja" if matches else "Nej")
                st.write("### Resultater")
                st.dataframe(df)

                excel_data = convert_df_to_excel(df)
                st.download_button(
                    label="Download Resultater som Excel",
                    data=excel_data,
                    file_name="Analyseret_Resultat.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                st.session_state['last_df'] = df
            else:
                st.error("Den uploadede fil mangler kolonnen 'SupportNote'.")

        elif menu == "📈 Statistik":
        if 'last_df' in st.session_state:
            df = st.session_state['last_df']
            total_notes = df['SupportNote'].notna().sum()
            tagged_yes = df[df['Keywords'] == 'Ja'].shape[0]

            st.metric("Rækker med Support Notes", total_notes)
            st.metric("Klassificeret som 'Ja'", tagged_yes)
            matched_keywords = st.session_state['last_df']['MatchedKeywords']
            matched_terms = set()
            for entry in matched_keywords:
                matched_terms.update([term.strip() for term in str(entry).split(',') if term.strip()])
            if matched_terms:
                st.write("### Brugte nøgleord i matches:")
                for word in sorted(matched_terms):
                    st.markdown(f"- {word}")
        else:
            st.info("Ingen analyseret data tilgængelig endnu.")

if __name__ == '__main__':
    main()
