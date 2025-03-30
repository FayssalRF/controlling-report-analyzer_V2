import streamlit as st
import pandas as pd
import json
from fuzzywuzzy import fuzz
from io import BytesIO

st.set_page_config(page_title="Controlling Report Analyzer", layout="wide")

PATTERNS_FILE = 'patterns.json'

@st.cache_data
def load_patterns():
    try:
        with open(PATTERNS_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return [
            # Liste over præcise sætninger – ikke enkeltord
            'trafikprop på motorvejen', 'langsom trafik i området', 'vejen lukket af politi',
            'forsinket afhentning på lager', 'butikken åbnede senere end planlagt',
            'tilføjet ekstra stop efter aftale', 'stop fjernet fra ruten', 'ændret rute grundet ændring',
            'modtager ikke hjemme ved levering', 'ingen svar ved opkald', 'kunden tog ikke telefonen',
            'forkert husnummer angivet', 'adressen findes ikke i systemet', 'kunne ikke komme ind i bygningen',
            'porten var låst', 'ingen adgang til butikken', 'kunden var vred', 'modtager nægtede at modtage',
            'levering til hospital', 'levering i gågade', 'ingen parkering tilgængelig'
        ]

def save_patterns(patterns):
    with open(PATTERNS_FILE, 'w') as file:
        json.dump(patterns, file)

def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Resultat')
    return output.getvalue()

def main():
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
                df['MatchedKeywords'] = df['SupportNote'].apply(
                    lambda note: ', '.join([
                        p for p in patterns
                        if fuzz.token_set_ratio(p.lower(), note.lower()) > 85 and len(p.split()) > 1
                    ])
                )
                df['Keywords'] = df['MatchedKeywords'].apply(lambda matches: "Ja" if matches else "Nej")

                vis_cols = ["SessionId", "Date", "CustomerId", "CustomerName", "SupportNote", "Keywords", "MatchedKeywords"]
                df = df[[col for col in vis_cols if col in df.columns]]

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
            matched_keywords = df['MatchedKeywords']
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
