import streamlit as st
import fitz
from collections import Counter
import matplotlib.pyplot as plt
import io
import numpy as np

st.set_page_config(page_title="CHECK FONT APP", page_icon="📄", layout="wide")

# ===============================
# FONT FAMILY ALIAS
# ===============================

FONT_ALIASES = {
    "Times New Roman": [
        "timesnewroman",
        "timesnewromanps",
        "timesnewromanpsmt",
        "timesnewromanps-boldmt",
        "timesnewromanps-italicmt",
        "timesnewromanps-bolditalicmt"
    ],
    "Arial": [
        "arial",
        "arialmt",
        "arial-boldmt",
        "arial-italicmt"
    ],
    "Calibri": [
        "calibri",
        "calibri-bold",
        "calibri-italic"
    ]
}

# ===============================
# CEK FONT FAMILY
# ===============================

def is_same_font_family(font_name, target_font):

    font_name = font_name.lower()

    if target_font not in FONT_ALIASES:
        return target_font.lower() in font_name

    for alias in FONT_ALIASES[target_font]:

        if alias in font_name:
            return True

    return False


# ===============================
# ANALISIS PDF
# ===============================

def analyze_pdf(file_bytes, target_font):

    doc = fitz.open(stream=file_bytes, filetype="pdf")

    font_list = []
    size_list = []
    spacing_list = []

    for page in doc:

        blocks = page.get_text("dict")["blocks"]

        for b in blocks:

            if "lines" in b:

                last_y = None

                for l in b["lines"]:

                    y = l["bbox"][1]

                    if last_y is not None:
                        spacing_list.append(abs(y-last_y))

                    last_y = y

                    for s in l["spans"]:

                        font_raw = s["font"]

                        if is_same_font_family(font_raw, target_font):
                            font = target_font
                        else:
                            font = font_raw

                        font_list.append(font)
                        size_list.append(round(s["size"],1))

    doc.close()

    font_counter = Counter(font_list)
    size_counter = Counter(size_list)

    total = sum(font_counter.values())

    font_percentage = {
        f: round((c/total)*100,2)
        for f,c in font_counter.items()
    }

    spacing_est = round(np.mean(spacing_list),2) if spacing_list else 0

    return font_counter, font_percentage, size_counter, spacing_est


# ===============================
# GRAFIK
# ===============================

def create_chart(font_percentage, target_font):

    labels = list(font_percentage.keys())
    values = list(font_percentage.values())

    colors = []

    for font in labels:

        if font == target_font:
            colors.append("green")
        else:
            colors.append("orange")

    fig, ax = plt.subplots(figsize=(6,4))

    bars = ax.bar(labels, values, color=colors)

    ax.set_title("Distribusi Font dalam Dokumen (%)")
    ax.set_ylabel("Persentase (%)")

    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")

    for bar,val in zip(bars,values):

        ax.text(
            bar.get_x()+bar.get_width()/2,
            bar.get_height(),
            f"{val}%",
            ha="center"
        )

    img = io.BytesIO()

    plt.tight_layout()
    plt.savefig(img, format="png")
    plt.close()

    img.seek(0)

    return img


# ===============================
# HIGHLIGHT PDF
# ===============================

def highlight_pdf(file_bytes, target_font):

    doc = fitz.open(stream=file_bytes, filetype="pdf")

    for page in doc:

        blocks = page.get_text("dict")["blocks"]

        for b in blocks:

            if "lines" in b:

                for l in b["lines"]:

                    for s in l["spans"]:

                        rect = fitz.Rect(s["bbox"])
                        font = s["font"]

                        highlight = page.add_highlight_annot(rect)

                        if is_same_font_family(font, target_font):

                            highlight.set_colors(stroke=(0,1,0))  # hijau

                        else:

                            highlight.set_colors(stroke=(1,0,0))  # merah

                            page.add_text_annot(
                                rect.br,
                                f"Font: {font}"
                            )

                        highlight.update()

    buffer = io.BytesIO()

    doc.save(buffer)

    doc.close()

    buffer.seek(0)

    return buffer


# ===============================
# BUAT PDF HASIL
# ===============================

def build_result_pdf(original_bytes, font_counter, font_percentage, size_counter, spacing, target_font):

    result = fitz.open()

    chart = create_chart(font_percentage, target_font)

    cover = result.new_page()

    rect = cover.rect

    cover.insert_textbox(
        fitz.Rect(0,100,rect.width,200),
        "CHECK FONT APP",
        fontsize=30,
        align=1
    )

    cover.insert_textbox(
        fitz.Rect(0,160,rect.width,220),
        "by Mugi",
        fontsize=18,
        align=1
    )

    summary = result.new_page()

    y = 50

    summary.insert_text((50,y),"Ringkasan Analisis Dokumen",fontsize=16)
    y += 30

    summary.insert_text((50,y),f"Font Standar : {target_font}",fontsize=12)
    y += 30

    summary.insert_text((50,y),"Distribusi Font:",fontsize=13)
    y += 20

    total = sum(font_counter.values())

    for font,count in font_counter.most_common():

        percent = (count/total)*100

        summary.insert_text(
            (70,y),
            f"- {font}: {count} teks ({percent:.2f}%)",
            fontsize=11
        )

        y += 15

    y += 20

    summary.insert_text((50,y),"Distribusi Font Size:",fontsize=13)
    y += 20

    for size,count in size_counter.most_common():

        summary.insert_text(
            (70,y),
            f"- {size} pt : {count} teks",
            fontsize=11
        )

        y += 15

    y += 20

    summary.insert_text(
        (50,y),
        f"Estimasi Line Spacing : {spacing}",
        fontsize=12
    )

    img_rect = fitz.Rect(100, y+40, 500, y+300)

    summary.insert_image(img_rect, stream=chart.getvalue())

    highlighted = highlight_pdf(original_bytes, target_font)

    doc_original = fitz.open(stream=highlighted.read(), filetype="pdf")

    result.insert_pdf(doc_original)

    buffer = io.BytesIO()

    result.save(buffer)

    result.close()
    doc_original.close()

    buffer.seek(0)

    return buffer


# ===============================
# STREAMLIT UI
# ===============================

st.title("📄 CHECK FONT APP by Mugi")

st.write("Aplikasi untuk mendeteksi font, ukuran font, dan spasi dokumen PDF.")

font_target = st.selectbox(
    "Pilih Font Standar Dokumen",
    [
        "Times New Roman",
        "Arial",
        "Calibri"
    ]
)

uploaded = st.file_uploader("Upload file PDF", type="pdf")

if uploaded:

    st.success("File berhasil diupload! Tunggu sebentar...")

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