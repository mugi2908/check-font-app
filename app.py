import streamlit as st
import fitz
from collections import Counter
import matplotlib.pyplot as plt
import io

# =========================
# Normalisasi Font
# =========================
def normalisasi_font(font_name, font_target):
    fname = font_name.lower()
    if font_target.lower() in fname:
        return font_target
    return font_name


# =========================
# Analisis PDF
# =========================
def analyze_pdf(file_bytes, font_target):

    doc = fitz.open(stream=file_bytes, filetype="pdf")

    semua_font = []
    semua_size = []
    line_spacing_list = []

    for page in doc:

        blocks = page.get_text("dict")["blocks"]

        for b in blocks:

            if "lines" in b:

                y_positions = []

                for l in b["lines"]:

                    y_positions.append(l["bbox"][1])

                    for s in l["spans"]:

                        font = normalisasi_font(s["font"], font_target)

                        semua_font.append(font)

                        size = round(s["size"], 1)
                        semua_size.append(size)

                # estimasi line spacing
                if len(y_positions) > 1:

                    for i in range(len(y_positions) - 1):

                        spacing = abs(y_positions[i+1] - y_positions[i])
                        line_spacing_list.append(spacing)

    # =====================
    # Statistik
    # =====================

    font_counter = Counter(semua_font)
    size_counter = Counter(semua_size)

    total_font = sum(font_counter.values())

    font_percentage = {
        k: round((v / total_font) * 100, 2)
        for k, v in font_counter.items()
    }

    # estimasi spasi
    if len(line_spacing_list) > 0:

        avg_spacing = sum(line_spacing_list) / len(line_spacing_list)

        if avg_spacing < 15:
            spacing_label = "Single (1.0)"
        elif avg_spacing < 22:
            spacing_label = "1.5 Spacing"
        else:
            spacing_label = "Double (2.0)"

    else:
        spacing_label = "Tidak terdeteksi"

    return font_counter, font_percentage, size_counter, spacing_label, doc


# =========================
# Generate Output PDF
# =========================
def generate_output_pdf(doc, font_target, font_counter, size_counter, spacing_label):

    result = fitz.open()

    # Cover
    cover = result.new_page()
    rect = cover.rect

    cover.insert_textbox(
        fitz.Rect(0,100,rect.width,200),
        "CHECK FONT APP",
        fontsize=30,
        align=1,
        fontname="helv"
    )

    cover.insert_textbox(
        fitz.Rect(0,150,rect.width,230),
        "by Mugi",
        fontsize=18,
        align=1
    )

    cover.insert_textbox(
        fitz.Rect(100,300,rect.width-100,rect.height-200),
        "Aplikasi untuk mendeteksi font, ukuran font, dan spasi dokumen.",
        fontsize=14,
        align=1
    )

    # Summary
    summary = result.new_page()

    text = "📊 RINGKASAN ANALISIS\n\n"

    text += f"Font Standar : {font_target}\n\n"

    text += "Distribusi Font:\n"

    for f, c in font_counter.items():

        text += f"{f} : {c}\n"

    text += "\nDistribusi Ukuran Font:\n"

    for s, c in size_counter.items():

        text += f"{s} pt : {c}\n"

    text += f"\nEstimasi Spasi : {spacing_label}\n"

    summary.insert_text((50,50), text, fontsize=12)

    # highlight font salah
    for page in doc:

        blocks = page.get_text("dict")["blocks"]

        for b in blocks:

            if "lines" in b:

                for l in b["lines"]:

                    for s in l["spans"]:

                        font = s["font"]

                        if font_target.lower() not in font.lower():

                            rect = fitz.Rect(s["bbox"])

                            highlight = page.add_highlight_annot(rect)
                            highlight.set_colors(stroke=(1,1,0))
                            highlight.update()

    result.insert_pdf(doc)

    output = io.BytesIO()

    result.save(output)

    result.close()
    doc.close()

    output.seek(0)

    return output


# =========================
# STREAMLIT UI
# =========================

st.title("📄 CHECK FONT APP by Mugi")

st.write("Aplikasi untuk menganalisis font, ukuran font, dan spasi dokumen PDF.")

# pilih font utama
font_target = st.selectbox(
    "Pilih Font Standar Dokumen",
    [
        "Times New Roman",
        "Arial",
        "Calibri",
        "Cambria",
        "Georgia"
    ]
)

uploaded = st.file_uploader("Upload file PDF", type="pdf")

if uploaded:

    st.success("File berhasil diupload!")

    font_counter, font_percentage, size_counter, spacing_label, doc = analyze_pdf(
        uploaded.read(),
        font_target
    )

    st.subheader("Distribusi Font")

    st.write(font_percentage)

    st.subheader("Distribusi Ukuran Font")

    st.write(size_counter)

    st.subheader("Estimasi Spasi")

    st.write(spacing_label)

    # grafik
    labels = list(font_percentage.keys())
    values = list(font_percentage.values())

    fig, ax = plt.subplots()

    ax.bar(labels, values)

    ax.set_title("Distribusi Font (%)")
    ax.set_ylabel("Persentase")

    st.pyplot(fig)

    output_pdf = generate_output_pdf(
        doc,
        font_target,
        font_counter,
        size_counter,
        spacing_label
    )

    st.download_button(
        "Download Hasil Analisis PDF",
        data=output_pdf,
        file_name="Hasil_Check_Font.pdf",
        mime="application/pdf"
    )