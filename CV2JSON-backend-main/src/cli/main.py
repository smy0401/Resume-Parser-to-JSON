import argparse
import json
import logging
from src.pipeline import run_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="CV Parser CLI")
    parser.add_argument("input_file", help="Path to the input CV file (PDF or DOCX)")
    parser.add_argument("-o", "--output", help="Path to save JSON output", default=None)
    args = parser.parse_args()

    try:
        logger.info(f"📄 Processing: {args.input_file}")
        result = run_pipeline(args.input_file)

        output_json = json.dumps(result, indent=2, ensure_ascii=False)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output_json)
            logger.info(f"✅ JSON saved to {args.output}")
        else:
            print(output_json)

    except Exception as e:
        logger.exception("❌ CLI pipeline failed.")
        print(json.dumps({"error": str(e)}, indent=2))

if __name__ == "__main__":
    main()
