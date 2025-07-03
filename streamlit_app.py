import streamlit as st
from PIL import Image
import re
import easyocr
import json
import io
import numpy as np

# Créer un lecteur EasyOCR
reader = easyocr.Reader(['fr', 'en'], gpu=False)

# 🔍 Fonction d’extraction de texte
def extract_text_from_image(uploaded_file):
    image = Image.open(uploaded_file).convert("RGB")
    image_np = np.array(image)
    result = reader.readtext(image_np, detail=0, paragraph=False)
    lines = [line.strip() for line in result if line.strip()]
    return lines

# 🧠 Fonction de parsing des lignes OCR
def parse_id_card(lines):
    data = {}
    previous_line = ""

    for i, line in enumerate(lines):
        clean_line = re.sub(r'[^\w\s:/]', '', line).strip()
        line_upper = clean_line.upper()

        if i == 0 and "CARTE" in line_upper and "IDENTITE" in line_upper:
            data["Type Document"] = "CARTE NATIONALE D'IDENTITE BURKINABE"

        if re.fullmatch(r'\d{17}', ''.join(filter(str.isdigit, clean_line))):
            data["Numero_NIP"] = ''.join(filter(str.isdigit, clean_line))

        if line_upper.startswith("NOM"):
            nom = clean_line.split(":", 1)[-1].strip().title()
            data["Nom"] = nom

        if line_upper.startswith("PRÉNOM") or line_upper.startswith("PRENOM") or line_upper.startswith("PRÉNOMS") or line_upper.startswith("PRENOMS"):
            prenom = clean_line.split(":", 1)[-1].strip().title()
            data["Prenom"] = prenom

        if "NÉ" in line_upper or "NE(E)" in line_upper or "NÉ(E)" in line_upper:
            date_match = re.search(r'\d{2}/\d{2}/\d{4}', clean_line)
            if date_match:
                data["Date_naissance"] = date_match.group()
            # Vérifie la ligne suivante pour le lieu
            if i + 1 < len(lines):
                next_line = lines[i+1].strip()
                if not next_line.upper().startswith(("SEXE", "TAILLE", "PROFESSION", "DÉLIVRÉE", "DELIVREE", "EXPIRE", "SIGNALURE")):
                    data["Lieu_naissance"] = next_line.title()

        if "SEXE" in line_upper:
            sexe_match = re.search(r'SEXE\s*:?\s*([MF])', line_upper)
            if sexe_match:
                data["Sexe"] = sexe_match.group(1)

        if "PROFESSION" in line_upper:
            prof = clean_line.split(":", 1)[-1].strip().title()
            data["Profession"] = prof

        if "DÉLIVRÉE LE" in line_upper or "DELIVREE LE" in line_upper:
            date_match = re.search(r'\d{2}/\d{2}/\d{4}', clean_line)
            if date_match:
                data["Date_delivrance"] = date_match.group()

        if "EXPIRE LE" in line_upper:
            date_match = re.search(r'\d{2}/\d{2}/\d{4}', clean_line)
            if date_match:
                data["Date_expiration"] = date_match.group()

        # Si la ligne ressemble à un numéro document isolé
        if re.match(r'[A-Z]\d{8}', clean_line):
            data["Numero_document"] = clean_line

    return data

# 🎯 Interface Streamlit
st.set_page_config(page_title="OCR Carte d'Identité", layout="centered")
st.title("🪪 Lecture d'une Carte d'Identité Burkinabè")
st.markdown("Importez une **photo de carte** pour extraire automatiquement les informations.")

# 📥 Uploader image
uploaded_file = st.file_uploader("📎 Importer ou glisser une image (JPG, PNG)", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Image chargée", use_container_width=True)

    with st.spinner("🔍 Lecture OCR et extraction..."):
        lines = extract_text_from_image(uploaded_file)
        parsed_data = parse_id_card(lines)

    st.success("✅ Extraction réussie !")
    st.subheader("📄 Informations extraites :")
    st.json(parsed_data)

    # 🧾 Affichage brut
    st.subheader("🧾 Texte brut OCR :")
    st.code("\n".join(lines), language="text")

    # 💾 Télécharger JSON
    st.subheader("⬇️ Télécharger les données extraites")
    json_data = json.dumps(parsed_data, indent=4, ensure_ascii=False)
    json_bytes = io.BytesIO(json_data.encode("utf-8"))
    st.download_button(
        label="📥 Télécharger au format JSON",
        data=json_bytes,
        file_name="donnees_identite.json",
        mime="application/json"
    )
