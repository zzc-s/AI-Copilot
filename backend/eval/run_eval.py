import json
from pathlib import Path

from app.services.jd_parser import parse_jd
from app.services.resume_matcher import match_resume_to_jd


def keyword_recall(expected: list[str], predicted: list[str]) -> float:
    if not expected:
        return 1.0
    hit = len([k for k in expected if k in predicted])
    return hit / len(expected)


def main() -> None:
    dataset_path = Path(__file__).with_name("sample_eval_set.json")
    data = json.loads(dataset_path.read_text(encoding="utf-8"))
    rows = []
    for item in data:
        parsed = parse_jd(item["jd_text"], "unknown")
        score, _, _ = match_resume_to_jd(item["resume_text"], parsed)
        recall = keyword_recall(item["expected_keywords"], parsed.get("keywords", []))
        rows.append({"name": item["name"], "match_score": score, "keyword_recall": round(recall, 3)})

    avg_match = round(sum(r["match_score"] for r in rows) / len(rows), 2)
    avg_recall = round(sum(r["keyword_recall"] for r in rows) / len(rows), 3)
    result = {"cases": rows, "summary": {"avg_match_score": avg_match, "avg_keyword_recall": avg_recall}}
    out_path = Path(__file__).with_name("last_eval_report.json")
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
