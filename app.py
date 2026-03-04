import streamlit as st
import fitz
from collections import Counter
import matplotlib.pyplot as plt
import io
import numpy as np

st.set_page_config(page_title="CHECK FONT APP", page_icon="📄", layout="wide")

# ==============================
# NORMALISASI FONT
# ==============================

def normalize_font(font_name, target_font):

    fname = font_name.lower()

    if target_font.lower() in fname:
        return target_font

    return font_name


# ==============================
# ANALISIS PDF
# ==============================

def analyze_pdf(file_bytes, target_font):

    doc = fitz.open(stream=file_bytes, filetype="pdf")

    font_list = []
    size_list = []
    line_spacing = []

    for page in doc:

        blocks = page.get_text("dict")["blocks"]

        for b in blocks:

            if "lines" in b:

                last_y = None

                for l in b["lines"]:

                    y = l["bbox"][1]

                    if last_y is not None:
                        line_spacing.append(abs(y - last_y))

                    last_y = y

                    for s in l["spans"]:

                        font = normalize_font(s["font"], target_font)

                        font_list.append(font)
                        size_list.append(round(s["size"],1))

    font_counter = Counter(font_list)
    size_counter = Counter(size_list)

    total = sum(font_counter.values())

    font_percentage = {
        f: round((c/total)*100,2)
        for f,c in font_counter.items()
    }

    spacing_estimate = round(np.mean(line_spacing),2) if line_spacing else 0

    return font_counter, font_percentage, size_counter, spacing_estimate


# ==============================
# BUAT GRAFIK
# ==============================

def create_chart(font_percentage):

    labels = list(font_percentage.keys())
    values = list(font_percentage.values())

    fig, ax = plt.subplots(figsize=(6,4))

    bars = ax.bar(labels, values, color="skyblue")

    ax.set_title("Distribusi Font dalam Dokumen (%)")
    ax.set_ylabel("Persentase (%)")
    ax.set_xticklabels(labels, rotation=45, ha="right")

    for bar,val in zip(bars,values):
        ax.text(
            bar.get_x() + bar.get_width()/2,
            bar.get_height(),
            f"{val}%",
            ha="center"
        )

    chart = io.BytesIO()
    plt.tight_layout()
    plt.savefig(chart, format="png")
    plt.close()

    chart.seek(0)

    return chart


# ==============================
# HIGHLIGHT PDF
# ==============================

def highlight_pdf(file_bytes, target_font):

    doc = fitz.open(stream=file_bytes, filetype="pdf")

    for page in doc:

        blocks = page.get_text("dict")["blocks"]

        for b in blocks:

            if "lines" in b:

                for l in b["lines"]:

                    for s in l["spans"]:

                        font = s["font"]

                        if target_font.lower() not in font.lower():

                            rect = fitz.Rect(s["bbox"])

                            highlight = page.add_highlight_annot(rect)
                            highlight.set_colors(stroke=(1,1,0))
                            highlight.update()

                            page.add_text_annot(rect.br, f"Font: {font}")

    buffer = io.BytesIO()
    doc.save(buffer)
    doc.close()

    buffer.seek(0)

    return buffer


# ==============================
# BUAT PDF HASIL ANALISIS
# ==============================

def build_result_pdf(original_bytes, font_counter, font_percentage, size_counter, spacing, target_font):

    result = fitz.open()

    chart = create_chart(font_percentage)

    # ======================
    # COVER
    # ======================

    cover = result.new_page()

    rect = cover.rect

    cover.insert_textbox(
        fitz.Rect(0,100,rect.width,200),
        "CHECK FONT APP",
        fontsize=32,
        align=1
    )

    cover.insert_textbox(
        fitz.Rect(0,160,rect.width,220),
        "by Mugi",
        fontsize=18,
        align=1
    )

    cover.insert_textbox(
        fitz.Rect(100,300,rect.width-100,rect.height-200),
        "Aplikasi untuk mendeteksi font, ukuran font, dan spasi dalam dokumen PDF.",
        fontsize=14,
        align=1
    )


    # ======================
    # RINGKASAN ANALISIS
    # ======================

    summary = result.new_page()

    text = "Ringkasan Analisis Dokumen\n\n"

    text += f"Font Standar: {target_font}\n\n"

    text += "Distribusi Font:\n"

    total = sum(font_counter.values())

    for f,c in font_counter.most_common():

        percent = (c/total)*100

        text += f"- {f}: {c} teks ({percent:.2f}%)\n"

    text += "\nDistribusi Font Size:\n"

    for size,count in size_counter.most_common():

        text += f"- {size} pt : {count} teks\n"

    text += f"\nEstimasi Line Spacing: {spacing}\n"

    if len(font_counter)==1 and target_font in font_counter:
        text += "\nSemua teks menggunakan font standar"
    else:
        text += "\nDokumen masih mengandung font selain font standar"

    summary.insert_text((50,50), text, fontsize=12)

    img_rect = fitz.Rect(50,250,500,500)

    summary.insert_image(img_rect, stream=chart.getvalue())


    # ======================
    # DOKUMEN DENGAN HIGHLIGHT
    # ======================

    highlighted = highlight_pdf(original_bytes, target_font)

    doc_original = fitz.open(stream=highlighted.read(), filetype="pdf")

    result.insert_pdf(doc_original)

    buffer = io.BytesIO()

    result.save(buffer)

    result.close()
    doc_original.close()

    buffer.seek(0)

    return buffer


# ==============================
# STREAMLIT UI
# ==============================

st.title("📄 CHECK FONT APP by Mugi")

st.write("Aplikasi untuk mendeteksi font, ukuran font, dan spasi pada dokumen PDF.")

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

    st.success("File berhasil diupload! Sedang dianalisis...")

    file_bytes = uploaded.read()

    font_counter, font_percentage, size_counter, spacing = analyze_pdf(file_bytes, font_target)

    st.subheader("Distribusi Font (%)")

    st.write(font_percentage)

    st.subheader("Distribusi Font Size")

    st.write(size_counter)

    st.subheader("Estimasi Line Spacing")

    st.write(spacing)

    result_pdf = build_result_pdf(
        file_bytes,
        font_counter,
        font_percentage,
        size_counter,
        spacing,
        font_target
    )

    st.download_button(
        "📥 Download hasil analisis PDF",
        data=result_pdf,
        file_name="Hasil_Cek_Font.pdf",
        mime="application/pdf"
    )