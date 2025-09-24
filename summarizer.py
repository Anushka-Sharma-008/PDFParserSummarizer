from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline

# Hugging Face model ID
MODEL_NAME = "sshleifer/distilbart-cnn-12-6"
MAX_INPUT_TOKENS = 1024  # distilBART token limit

def load_model_from_hf():
    """
    Load the summarization model and tokenizer directly from Hugging Face.
    Works in Streamlit Cloud without uploading local folders.
    """
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    summarizer = pipeline(
        "summarization",
        model=model,
        tokenizer=tokenizer,
        device=-1  # CPU, change to 0 if GPU is available
    )
    return summarizer, tokenizer

def summarize_text(text, summarizer, tokenizer, min_len=50, max_len_cap=500):
    """
    Summarize long text intelligently:
    - One-shot if under MAX_INPUT_TOKENS
    - Chunked otherwise
    """
    tokens = tokenizer.encode(text, truncation=False)
    num_tokens = len(tokens)

    if num_tokens <= MAX_INPUT_TOKENS:
        # Single-pass summarization
        max_len = min(max_len_cap, max(min_len, int(len(text.split()) * 0.2)))
        summary = summarizer(
            text,
            max_length=max_len,
            min_length=min_len,
            do_sample=False,
            truncation=True
        )
        return summary[0]["summary_text"]
    else:
        # Split into chunks
        chunks = []
        for i in range(0, num_tokens, MAX_INPUT_TOKENS):
            chunk_tokens = tokens[i:i + MAX_INPUT_TOKENS]
            chunk_text = tokenizer.decode(chunk_tokens, skip_special_tokens=True)
            summary = summarizer(
                chunk_text,
                max_length=min(max_len_cap, 150),
                min_length=50,
                do_sample=False,
                truncation=True
            )
            chunks.append(summary[0]["summary_text"])

        # Meta-summary of all chunks
        combined_text = " ".join(chunks)
        final_summary = summarizer(
            combined_text,
            max_length=max_len_cap,
            min_length=min_len,
            do_sample=False,
            truncation=True
        )
        return final_summary[0]["summary_text"]

def summarize_parsed_pdf(parsed_json, summarizer, tokenizer):
    """
    Convert parsed PDF JSON into text and summarize.
    Extracts paragraphs and table snippets.
    """
    parts = []
    for page in parsed_json.get("pages", []):
        for block in page.get("content", []):
            if block.get("type") == "paragraph":
                parts.append(block.get("text"))
            elif block.get("type") == "table":
                table = block.get("table_data", [])
                rows = [" | ".join([str(cell) for cell in r]) for r in table[:2]] if table else []
                if rows:
                    parts.append("Table snippet: " + " ; ".join(rows))

    doc_text = "\n".join(parts)
    return summarize_text(doc_text, summarizer, tokenizer)