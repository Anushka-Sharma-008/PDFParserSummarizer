import streamlit as st
import json
import os
from parser import parse_pdf
from summarizer import load_model_from_hf, summarize_parsed_pdf  # updated import

st.set_page_config(
    page_title="PDF Parser & Summarizer",
    layout="wide",
    page_icon="📄"
)

@st.cache_resource
def load_model_cached():
    # Load model directly from Hugging Face and cache for Streamlit Cloud
    return load_model_from_hf()

def main():
    st.title("📄 PDF Parser & Summarizer")
    st.markdown(
        "Upload a PDF, parse its contents (text + tables), and generate a concise AI-powered summary using a Hugging Face model."
    )
    st.markdown("---")

    # File upload
    uploaded_file = st.file_uploader("📂 Upload a PDF", type="pdf")

    if uploaded_file is not None:
        st.success("✅ File uploaded")

        temp_dir = "temp"
        os.makedirs(temp_dir, exist_ok=True)
        temp_file_path = os.path.join(temp_dir, uploaded_file.name)

        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        if st.button("🚀 Parse & Summarize"):
            with st.spinner("🔍 Parsing PDF..."):
                parsed = parse_pdf(temp_file_path)

            if parsed:
                st.success("✅ Parsing complete")

                # Load model & summarize
                with st.spinner("🤖 Loading model & generating summary..."):
                    summarizer, tokenizer = load_model_cached()
                    summary = summarize_parsed_pdf(parsed, summarizer, tokenizer)

                if summary:
                    st.success("✅ Summarizing complete")

                tab1, tab2, tab3 = st.tabs(["📑 JSON Preview", "📝 Summary", "📊 Metadata"])

                with tab1:
                    st.subheader("Extracted JSON")
                    st.json(parsed)

                    json_output = json.dumps(parsed, indent=2)
                    st.download_button(
                        "⬇️ Download Parsed JSON",
                        json_output,
                        file_name="parsed.json",
                        mime="application/json"
                    )

                with tab2:
                    st.subheader("Generated Summary")
                    st.write(summary)
                    st.download_button("⬇️ Download Summary", summary, file_name="summary.txt")

                with tab3:
                    st.subheader("Document Metadata")
                    num_pages = len(parsed.get("pages", []))
                    total_paragraphs = sum(len(p.get("content", [])) for p in parsed.get("pages", []))
                    word_count = sum(
                        len(block.get("text", "").split())
                        for page in parsed.get("pages", [])
                        for block in page.get("content", [])
                        if block.get("type") == "paragraph"
                    )

                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total Pages", num_pages)
                    col2.metric("Paragraphs Extracted", total_paragraphs)
                    col3.metric("Word Count", word_count)

            else:
                st.error("❌ Could not parse PDF.")

        # cleanup
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; padding: 10px; font-size: 14px; color: grey;">
            Developed by <b>Anushka Sharma</b>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()