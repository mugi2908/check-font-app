import streamlit as st
import fitz
from collections import Counter
import matplotlib.pyplot as plt
import io

st.set_page_config(page_title="CHECK FONT APP", page_icon="📄", layout="wide")

def normalize_font(font_name, target):
    name = font_name.lower()
    if target.lower() in name:
        return target
    return font_name


def analyze_pdf(file_bytes, target_font):

    doc = fitz.open(stream=file_bytes, filetype="pdf")

    fonts = []
    sizes = []
    spacing = []

    for page in doc:
        blocks = page.get_text("dict")["blocks"]

        for b in blocks:
            if "lines" in b:

                y_pos = []

                for line in b["lines"]:
                    y_pos.append(line["bbox"][1])

                    for span in line["spans"]:
                        fonts.append(normalize_font(span["font"], target_font))
                        sizes.append(round(span["size"],1))

                if len(y_pos) > 1:
                    for i in range(len(y_pos)-1):
                        spacing.append(abs(y_pos[i+1] - y_pos[i]))

    doc.close()

    font_count = Counter(fonts)
    size_count = Counter(sizes)

    total = sum(font_count.values())

    font_percent = {k: round((v/total)*100,2) for k,v in font_count.items()}

    if spacing:
        avg = sum(spacing)/len(spacing)

        if avg < 15:
            spacing_label = "Single (1.0)"
        elif avg < 22:
            spacing_label = "1.5 Spacing"
        else:
            spacing_label = "Double (2.0)"
    else:
        spacing_label = "Tidak terdeteksi"

    return font_count, font_percent, size_count, spacing_label


def generate_pdf(file_bytes, target_font, font_count, size_count, spacing_label):

    doc = fitz.open(stream=file_bytes, filetype="pdf")
    result = fitz.open()

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

    summary = result.new_page()

    text = "RINGKASAN ANALISIS\n\n"
    text += f"Font Standar : {target_font}\n\n"

    text += "Distribusi Font\n"
    for f,c in font_count.items():
        text += f"{f} : {c}\n"

    text += "\nDistribusi Ukuran Font\n"
    for s,c in size_count.items():
        text += f"{s} pt : {c}\n"

    text += f"\nEstimasi Spasi : {spacing_label}"

    summary.insert_text((50,50), text, fontsize=12)

    for page in doc:

        blocks = page.get_text("dict")["blocks"]

        for b in blocks:
            if "lines" in b:

                for l in b["lines"]:
                    for s in l["spans"]:

                        if target_font.lower() not in s["font"].lower():

                            rect = fitz.Rect(s["bbox"])

                            highlight = page.add_highlight_annot(rect)
                            highlight.set_colors(stroke=(1,1,0))
                            highlight.update()

    result.insert_pdf(doc)

    output = io.BytesIO()
    result.save(output)
    output.seek(0)

    doc.close()
    result.close()

    return output


st.title("📄 CHECK FONT APP by Mugi")
st.write("Aplikasi untuk mendeteksi font, ukuran font, dan spasi dokumen PDF.")

font_target = st.selectbox(
    "Pilih Font Standar Dokumen",
    ["Times New Roman","Arial","Calibri","Cambria","Georgia"]
)

uploaded = st.file_uploader("Upload file PDF", type=["pdf"])

if uploaded:

    st.success("File berhasil diupload!")

    try:

        file_bytes = uploaded.getvalue()

        if file_bytes is None or len(file_bytes) == 0:
            st.error("File kosong atau tidak valid")
            st.stop()

        font_count, font_percent, size_count, spacing_label = analyze_pdf(
            file_bytes,
            font_target
        )

        st.subheader("Distribusi Font (%)")
        st.write(font_percent)

        st.subheader("Distribusi Ukuran Font")
        st.write(size_count)

        st.subheader("Estimasi Spasi")
        st.write(spacing_label)

        labels = list(font_percent.keys())
        values = list(font_percent.values())

        fig, ax = plt.subplots()
        ax.bar(labels, values)
        ax.set_title("Distribusi Font (%)")
        st.pyplot(fig)

        output_pdf = generate_pdf(
            file_bytes,
            font_target,
            font_count,
            size_count,
            spacing_label
        )

        st.download_button(
            "Download Hasil Analisis PDF",
            data=output_pdf,
            file_name="hasil_check_font.pdf",
            mime="application/pdf"
        )

    except Exception as e:

        st.error(f"Error: {e}")