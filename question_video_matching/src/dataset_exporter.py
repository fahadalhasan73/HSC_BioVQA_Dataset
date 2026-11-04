from typing import Any, Dict, List


def build_joined_view(questions, segments, pairs, accepted_statuses=("matched",)):
    q_by_id = {x.get("question_id"): x for x in questions if x.get("question_id")}
    s_by_id = {x.get("segment_id"): x for x in segments if x.get("segment_id")}
    accepted = set(accepted_statuses)

    out: List[Dict[str, Any]] = []
    for pair in pairs:
        if pair.get("status") not in accepted:
            continue
        question = q_by_id.get(pair.get("question_id"))
        segment = s_by_id.get(pair.get("segment_id"))
        if question and segment:
            out.append({"pair": pair, "question": question, "segment": segment})
    return out
