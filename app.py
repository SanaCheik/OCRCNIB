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

    if len(lines) > 0:
        first_line = re.sub(r'[^\w\s]', '', lines[0])
        if "CARTE" in first_line.upper() and "IDENTITE" in first_line.upper():
            data["Type Document"] = "CARTE NATIONALE D'IDENTITE BURKINABE"

    if len(lines) > 1:
        second_line = lines[1]
        chiffres = ''.join(filter(str.isdigit, second_line))
        if len(chiffres) == 17:
            data["Numero_NIP"] = chiffres

    if len(lines) > 2:
        third_line = re.sub(r'[^\w\s]', '', lines[2]).strip()
        third_line = re.sub(r'^\s*NOMS?\s*', '', third_line, flags=re.IGNORECASE)
        data["Nom"] = third_line.strip().title()

    if len(lines) > 3:
        fourth_line = re.sub(r'[^\w\s]', '', lines[3]).strip()
        fourth_line = re.sub(r'^\s*PR[ÉE]NOMS?\s*', '', fourth_line, flags=re.IGNORECASE)
        data["Prenom"] = fourth_line.strip().title()

    for line in lines:
        line_upper = line.upper()

        if "NÉ" in line_upper or "NE(E)" in line_upper or "NE LE" in line_upper:
            date_lieu = re.findall(r'(\d{2}/\d{2}/\d{4}).*?([A-Z ]+)', line_upper)
            if date_lieu:
                data["Date_naissance"] = date_lieu[0][0]
                data["Lieu_naissance"] = date_lieu[0][1].strip().title()

        if "SEXE" in line_upper:
            sexe_match = re.search(r'SEXE:?\s*([MF])', line_upper)
            taille_match = re.search(r'TAILLE:?\s*([\d]+ ?cm)', line_upper)
            if sexe_match:
                data["Sexe"] = sexe_match.group(1)
            if taille_match:
                data["Taille"] = taille_match.group(1).replace(" ", "")

        if "PROFESSION" in line_upper:
            data["Profession"] = line.split(":")[-1].strip().title()

        if "DÉLIVRÉE LE" in line_upper or "DELIVREE LE" in line_upper:
            date_del = re.search(r'(\d{2}/\d{2}/\d{4})', line_upper)
            if date_del:
                data["Date_delivrance"] = date_del.group(1)

        if "EXPIRE LE" in line_upper:
            match = re.search(r'(\d{2}/\d{2}/\d{4}).*?([A-Z0-9]{5,})', line_upper)
            if match:
                data["Date_expiration"] = match.group(1)
                data["Numero_document"] = match.group(2)

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
