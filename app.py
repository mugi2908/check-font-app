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


def analyze_pdf(pdf_bytes, target_font):

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    fonts = []
    sizes = []

    for page in doc:

        blocks = page.get_text("dict")["blocks"]

        for b in blocks:

            if "lines" in b:

                for line in b["lines"]:

                    for span in line["spans"]:

                        fonts.append(normalize_font(span["font"], target_font))
                        sizes.append(round(span["size"],1))

    doc.close()

    font_count = Counter(fonts)
    size_count = Counter(sizes)

    total = sum(font_count.values())

    font_percent = {
        k: round((v/total)*100,2)
        for k,v in font_count.items()
    }

    return font_count, font_percent, size_count


def generate_output(pdf_bytes, target_font):

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    result = fitz.open()

    for page in doc:

        blocks = page.get_text("dict")["blocks"]

        for b in blocks:

            if "lines" in b:

                for line in b["lines"]:

                    for span in line["spans"]:

                        if target_font.lower() not in span["font"].lower():

                            rect = fitz.Rect(span["bbox"])

                            highlight = page.add_highlight_annot(rect)
                            highlight.set_colors(stroke=(1,1,0))
                            highlight.update()

    result.insert_pdf(doc)

    buffer = io.BytesIO()
    result.save(buffer)
    buffer.seek(0)

    doc.close()
    result.close()

    return buffer


st.title("📄 CHECK FONT APP by Mugi")

font_target = st.selectbox(
    "Pilih Font Standar Dokumen",
    ["Times New Roman","Arial","Calibri","Cambria","Georgia"]
)

uploaded = st.file_uploader("Upload PDF", type=["pdf"])


if uploaded is not None:

    st.success("File berhasil diupload!")

    try:

        pdf_bytes = uploaded.read()

        if len(pdf_bytes) == 0:
            st.error("File kosong")
            st.stop()

        font_count, font_percent, size_count = analyze_pdf(pdf_bytes, font_target)

        st.subheader("Distribusi Font (%)")
        st.write(font_percent)

        st.subheader("Distribusi Ukuran Font")
        st.write(size_count)

        labels = list(font_percent.keys())
        values = list(font_percent.values())

        fig, ax = plt.subplots()
        ax.bar(labels, values)
        ax.set_title("Distribusi Font (%)")

        st.pyplot(fig)

        output_pdf = generate_output(pdf_bytes, font_target)

        st.download_button(
            "Download PDF Highlight",
            data=output_pdf,
            file_name="font_analysis.pdf",
            mime="application/pdf"
        )

    except Exception as e:

        st.error(e)