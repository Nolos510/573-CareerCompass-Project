from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from careercompass.kaggle_linkedin import (
    DEFAULT_PROCESSED_PATH,
    DEFAULT_RAW_DIR,
    KAGGLE_DATASET_URL,
    write_mvp_postings,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepare the Kaggle LinkedIn job postings dataset for CareerCompass."
    )
    parser.add_argument(
        "source",
        nargs="?",
        default=str(DEFAULT_RAW_DIR),
        help="Path to downloaded Kaggle zip, extracted folder, or postings CSV.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_PROCESSED_PATH),
        help="Output JSON path used by the CareerCompass retriever.",
    )
    parser.add_argument("--limit", type=int, default=2000)
    args = parser.parse_args()

    output = write_mvp_postings(args.source, args.output, limit=args.limit)
    print(f"Prepared LinkedIn postings for CareerCompass: {output}")
    print(f"Source dataset: {KAGGLE_DATASET_URL}")


if __name__ == "__main__":
    main()
