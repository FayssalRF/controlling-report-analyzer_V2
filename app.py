import streamlit as st
import pandas as pd
import json
from fuzzywuzzy import fuzz

# Load patterns
PATTERNS_FILE = 'patterns.json'


@st.cache_data
def load_patterns():
    try:
        with open(PATTERNS_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return [
            'trafik', 'traffic', 'problemer med adgang', 'ikke adgang', 'forsinkelse',
            'blomsterbutikken åbnede senere', 'forsinket lager', 'forkert adresse',
            'ingen adgang', 'problemer med porten', 'alarm', 'besværlig leveringsadresse',
            'hospital', 'skole', 'center', 'gågade', 'manglende parkering'
        ]


def save_patterns(patterns):
    with open(PATTERNS_FILE, 'w') as file:
        json.dump(patterns, file)


def classify_note(note, patterns):
    if pd.isna(note):
        return "Nej"
    for pattern in patterns:
        if fuzz.partial_ratio(pattern.lower(), note.lower()) > 75:
            return "Ja"
    return "Nej"


def main():
    st.title("Controlling Report Analyzer")

    patterns = load_patterns()

    uploaded_file = st.file_uploader("Upload din Controlling Report (Excel)", type="xlsx")

    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        if 'SupportNote' in df.columns:
            df['Keywords'] = df['SupportNote'].apply(lambda x: classify_note(x, patterns))
            st.write("### Resultater")
            st.dataframe(df)

            if st.button("Download Resultater"):
                result_file = df.to_excel('Analyseret_Resultat.xlsx', index=False)
                st.write("Resultater gemt som Analyseret_Resultat.xlsx")

            if st.button("Forbedre Mønstre"):
                new_patterns = []
                for index, row in df.iterrows():
                    if row['Keywords'] == 'Nej':
                        new_patterns.extend([word for word in str(row['SupportNote']).split() if len(word) > 4])
                patterns = list(set(patterns + new_patterns))
                save_patterns(patterns)
                st.success("Mønstergenkendelsen er blevet forbedret!")

        else:
            st.error("Den uploadede fil mangler kolonnen 'SupportNote'.")


if __name__ == '__main__':
    main()
