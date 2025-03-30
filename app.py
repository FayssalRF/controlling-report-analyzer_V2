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

    note_lower = note.lower()
    for pattern in patterns:
        if fuzz.partial_ratio(pattern.lower(), note_lower) > 75:
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

    with st.sidebar:
    st.markdown("""
    <style>
    .sidebar-title {
        font-size: 20px;
        font-weight: bold;
        margin-bottom: 15px;
    }
    div[class^='stRadio'] > label > div[data-testid='stMarkdownContainer'] {
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    div[class^='stRadio'] input[type='radio'] {
        display: none !important;
        appearance: none;
        -webkit-appearance: none;
        -moz-appearance: none;
        margin: 0;
        padding: 0;
        height: 0;
        width: 0;
        opacity: 0;
    }
    div[class^='stRadio'] input[type='radio'] + div {
        border: 1px solid #ccc;
        border-radius: 6px;
        padding: 10px;
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

    st.markdown('<div class="sidebar-title">📂 Navigation</div>', unsafe_allow_html=True)
    menu = st.radio("", ["📊 Analyse", "🛠️ Forbedre Mønstre", "📈 Statistik"], key="menu_radio")

    patterns = load_patterns()

    if 'feedback_rows' not in st.session_state:
        st.session_state.feedback_rows = []

    if menu == "📊 Analyse":
        uploaded_file = st.file_uploader("Upload din Controlling Report (Excel)", type="xlsx")

        if uploaded_file:
            df = pd.read_excel(uploaded_file)
            if 'SupportNote' in df.columns:
                df['Keywords'] = df['SupportNote'].apply(lambda x: classify_note(x, patterns))
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

    elif menu == "🛠️ Forbedre Mønstre":
        if 'last_df' in st.session_state:
            df = st.session_state['last_df']
            vis_cols = ["SessionId", "Date", "Slug", "CustomerId", "CustomerName", "DurationDifference", "SupportNote", "Keywords"]
            st.write("### Marker en række som fejlklassificeret")
            edited_df = st.data_editor(df[vis_cols], num_rows="dynamic", use_container_width=True, key="edit")

            index = st.number_input("Indtast række-ID for fejlklassificering", min_value=0, max_value=len(df)-1, step=1)
            if df.shape[0] > 0:
                if st.button("Markér som forkert"):
                st.session_state.feedback_rows.append(df.iloc[index])
                st.success("Række markeret som forkert.")

            if st.button("Forbedre Mønstre baseret på fejl"):
                explanations = []
                new_patterns = []
                for row in st.session_state.feedback_rows:
                    note = row['SupportNote']
                    explanations.append(f"Tidligere support note: '{note}' blev klassificeret som 'Nej'.")
                    new_patterns.extend([word for word in str(note).split() if len(word) > 4])
                if new_patterns:
                    patterns = list(set(patterns + new_patterns))
                    save_patterns(patterns)
                    st.success("Mønstergenkendelsen er blevet forbedret!")
                    st.write("### Forklaringer på forbedring:")
                    for e in explanations:
                        st.markdown(f"- {e}")
        else:
            st.info("Upload og analysér først en fil i fanen 'Analyse'.")

    elif menu == "📈 Statistik":
        if 'last_df' in st.session_state:
            df = st.session_state['last_df']
            total_notes = df['SupportNote'].notna().sum()
            tagged_yes = df[df['Keywords'] == 'Ja'].shape[0]

            st.metric("Rækker med Support Notes", total_notes)
            st.metric("Klassificeret som 'Ja'", tagged_yes)
        else:
            st.info("Ingen analyseret data tilgængelig endnu.")

if __name__ == '__main__':
    main()
