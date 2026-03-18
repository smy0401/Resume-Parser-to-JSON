from pathlib import Path
import json

def run_on_all_pdfs(pdf_dir: Path, out_dir: Path):
    """
    Run the CV-to-JSON pipeline on all PDFs inside `pdf_dir` and
    save structured JSON results in `out_dir`.
    """
    from src.pipeline import run_pipeline  # import your main function here
    pdf_dir = Path(pdf_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for pdf_file in pdf_dir.glob("*.pdf"):
        print(f"Processing: {pdf_file.name}")
        try:
            result = run_pipeline(str(pdf_file))
            output_path = out_dir / f"{pdf_file.stem}.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"Saved: {output_path}")
        except Exception as e:
            print(f"Error processing {pdf_file.name}: {e}")
