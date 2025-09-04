import streamlit as st
import fitz
from collections import Counter
import matplotlib.pyplot as plt
import io

# Daftar alias font Times New Roman
ALIAS_TIMES = [
    "times new roman",
    "timesnewromanps",
    "timesnewromanpsmt",
    "timesnewromanps-boldmt",
    "timesnewromanps-italicmt",
    "timesnewromanps-bolditalicmt"
]

def normalisasi_font(font_name):
    """Samakan nama font agar variasi Times New Roman dianggap satu"""
    fname = font_name.lower()
    for alias in ALIAS_TIMES:
        if alias in fname:
            return "Times New Roman"
    return font_name

def highlight_with_cover(file_bytes):
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    semua_font = []

    # kumpulkan semua font
    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            if "lines" in b:
                for l in b["lines"]:
                    for s in l["spans"]:
                        semua_font.append(normalisasi_font(s["font"]))

    counter = Counter(semua_font)
    total = sum(counter.values())

    # === Chart distribusi font ===
    labels = list(counter.keys())
    sizes = [counter[f] for f in labels]
    persentase = [round((x/total)*100, 2) for x in sizes]

    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(labels, persentase, color="skyblue")
    ax.set_title("Distribusi Font dalam Dokumen (%)")
    ax.set_ylabel("Persentase (%)")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")

    for bar, p in zip(bars, persentase):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                f"{p}%", ha="center", va="bottom", fontsize=8)

    chart_path = "chart.png"
    plt.tight_layout()
    plt.savefig(chart_path, bbox_inches="tight")
    plt.close()

    # === Buat dokumen hasil ===
    result = fitz.open()

    # --- Cover ---
    cover = result.new_page()
    rect = cover.rect
    cover.insert_textbox(
        fitz.Rect(0, 100, rect.width, 200),
        "CHECK FONT APP",
        fontsize=30,
        fontname="helv",
        align=1,
        color=(0, 0, 1)
    )
    cover.insert_textbox(
        fitz.Rect(0, 160, rect.width, 220),
        "by Mugi",
        fontsize=18,
        fontname="helv",
        align=1,
        color=(0.2, 0.2, 0.2)
    )

    cover.insert_textbox(
        fitz.Rect(100, 300, rect.width-100, rect.height-200),
        "Aplikasi otomatis untuk mendeteksi dan menandai font dalam dokumen.\n"
        "Hasil analisis disajikan dengan ringkasan, grafik distribusi, dan highlight teks.",
        fontsize=14,
        fontname="helv",
        align=1,
        color=(0, 0, 0)
    )

    cover.draw_rect(
        fitz.Rect(50, rect.height-150, rect.width-50, rect.height-100),
        color=(0.2, 0.5, 0.9),
        fill=(0.2, 0.5, 0.9)
    )

    # --- Ringkasan ---
    summary = result.new_page()
    text = "📊 Ringkasan Analisis Font\n\n"
    for font, count in counter.most_common():
        persen = (count / total) * 100
        text += f"- {font}: {count} teks ({persen:.2f}%)\n"

    if len(counter) == 1 and "Times New Roman" in counter:
        text += "\n✅ Semua teks sudah menggunakan Times New Roman"
    else:
        text += "\n⚠️ Dokumen masih mengandung font selain Times New Roman"

    summary.insert_text((50, 50), text, fontsize=12)
    rect_chart = fitz.Rect(50, 200, 500, 500)
    summary.insert_image(rect_chart, filename=chart_path)

    # --- Highlight font salah ---
    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            if "lines" in b:
                for l in b["lines"]:
                    for s in l["spans"]:
                        font = normalisasi_font(s["font"])
                        teks = s["text"].strip()
                        if teks and font != "Times New Roman":
                            rect = fitz.Rect(s["bbox"])
                            highlight = page.add_highlight_annot(rect)
                            highlight.set_colors(stroke=(1, 1, 0))  # kuning
                            highlight.update()
                            page.add_text_annot(rect.br, f"Font: {font}")

    result.insert_pdf(doc)

    # simpan ke memory buffer
    output = io.BytesIO()
    result.save(output)
    result.close()
    doc.close()
    output.seek(0)
    return output

# ===================== Streamlit UI =====================
st.title("📄 CHECK FONT APP by Mugi")
st.write("Aplikasi untuk mendeteksi font pada dokumen PDF.")

uploaded = st.file_uploader("Upload file PDF", type="pdf")

if uploaded:
    st.success("File berhasil diupload! Tunggu sebentar...")
    highlighted_pdf = highlight_with_cover(uploaded.read())
    st.download_button(
        "📥 Download hasil analisis PDF",
        data=highlighted_pdf,
        file_name="Hasil_Cek_Font.pdf",
        mime="application/pdf"
    )
