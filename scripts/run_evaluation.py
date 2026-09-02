"""Run evaluation on all change requests and report metrics."""

from src.data_loader import load_data
from src.orchestrator import analyze_change, evaluate_at_k, get_ground_truth


def main():
    data = load_data()

    print("=" * 90)
    print("EVALUATION RESULTS")
    print("=" * 90)

    for cr in ["CR-001", "CR-002", "CR-003", "CR-004", "CR-005"]:
        gt = get_ground_truth(data, cr)
        result = analyze_change(cr, skip_llm=True)
        ids = result.ranked_candidates["id"].tolist()

        print(f"\n{cr} (requirement: {result.requirement_id})")
        print(f"  Ground truth count: {len(gt)}")
        print(f"  Candidates found: {len(ids)}")

        for k in [5, 10, 15, 20]:
            m = evaluate_at_k(ids, gt, k)
            print(
                f"  @{k:2d}: "
                f"P={m['precision']:.3f}  "
                f"R={m['recall']:.3f}  "
                f"F1={m['f1']:.3f}"
            )


if __name__ == "__main__":
    main()
