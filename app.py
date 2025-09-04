import streamlit as st
import fitz  # PyMuPDF
import matplotlib.pyplot as plt
import pandas as pd
import io

# -------------------------------
# Fungsi analisis PDF
# -------------------------------
def analyze_pdf(file_path, target_font="Times New Roman"):
    doc = fitz.open(file_path)
    font_usage = {}

    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        font_name = span["font"]
                        font_usage[font_name] = font_usage.get(font_name, 0) + 1

    return font_usage


# -------------------------------
# Streamlit App
# -------------------------------
st.title("📑 CHECK FONT APP by Mugi")
st.markdown("Aplikasi untuk mendeteksi font pada dokumen PDF.")

# Upload file
uploaded_file = st.file_uploader("Upload file PDF", type=["pdf"])

if uploaded_file:
    # Simpan file sementara
    with open("uploaded.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Analisis font
    font_count = analyze_pdf("uploaded.pdf")
    total = sum(font_count.values())

    # Tabel hasil
    df = pd.DataFrame(list(font_count.items()), columns=["Font", "Jumlah"])
    df["Persentase (%)"] = (df["Jumlah"] / total * 100).round(2)
    st.subheader("📊 Ringkasan Font")
    st.dataframe(df)

    # Grafik batang
    fig, ax = plt.subplots()
    ax.bar(df["Font"], df["Persentase (%)"])
    ax.set_ylabel("Persentase (%)")
    ax.set_xlabel("Font")
    ax.set_title("Distribusi Font dalam Dokumen")
    plt.xticks(rotation=45, ha="right")
    st.pyplot(fig)

    # Keterangan
    st.success("Analisis selesai ✅. File berhasil diproses.")
