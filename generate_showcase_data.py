import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SAMPLES_PATH = ROOT / "data" / "samples.json"
RESULTS_PATH = ROOT / "cmi_results.jsonl"

DERIVED_DATASET_IDS = {
    "cmi-pref-prediction-agree",
    "cmi-pref-prediction-disagree",
}
SAMPLES_PER_SECTION = 3
FEEDBACK_TRANSLATIONS_BY_PROMPT_ID = {
    52237: (
        "I prefer B because it matches the prompt style better, with steadier drums "
        "and a stronger groove."
    ),
    92647: (
        "Instruction following: neither model includes meaningful lyrics, but model A "
        "matches the style very well. Music quality: model B is heavily distorted, "
        "while model A's accompaniment is clearly more pleasant."
    ),
    92985: (
        "A has a more distinctive melody and a stronger central theme. Its structure is "
        "more coherent, with clearer section changes. The groove is stable, without odd "
        "jitter. The instrumentation is richer without feeling cluttered, with better "
        "layering and separation. The sound quality is clearer and the dynamics feel "
        "more natural. The vocals are clearer and the diction is more natural. Overall, "
        "A feels more complete. B has slightly clearer vocals, but its melody does not "
        "fit the theme and its rhythm is not very stable."
    ),
    93175: (
        "A matches the prompt style well, though it only generates the lyrics correctly "
        "for the final chorus. B is overly avant-garde, and its lyrics are mostly "
        "gibberish. A lacks clear sectional structure, but B has essentially no "
        "structure at all and feels completely erratic."
    ),
    116598: (
        "B better captures the horror and slow, plodding qualities in the prompt, and "
        "its rhythm is clearer and more musical."
    ),
    134402: (
        "B is mostly a mechanical recitation of the lyrics, while A has much better "
        "texture, melody, and rhythm, with a much more coherent structure."
    ),
}


def load_jsonl(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def load_showcase_payload():
    with SAMPLES_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def normalize_media_path(path: str) -> str:
    if not path:
        return ""

    path = path.strip()
    asset_path = ROOT / "assets" / path
    if asset_path.exists():
        return path

    source_candidates = [ROOT / path]
    if path.startswith("cmi-pref/"):
        source_candidates.append(ROOT / path.replace("cmi-pref/", "cmi_pref/", 1))

    for source_path in source_candidates:
        if source_path.exists():
            asset_path.parent.mkdir(parents=True, exist_ok=True)
            if source_path.resolve() != asset_path.resolve():
                shutil.copy2(source_path, asset_path)
            return path

    return path


def trim_text(value: str, limit: int) -> str:
    value = (value or "").strip()
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "…"


def format_title(prompt: str) -> str:
    words = (prompt or "").strip().split()
    if not words:
        return "Untitled sample"
    return " ".join(words[:6])


def translate_feedback(feedback: str, prompt_id):
    translated = FEEDBACK_TRANSLATIONS_BY_PROMPT_ID.get(prompt_id)
    if translated:
        return translated
    return feedback


def parse_row(row):
    predicted_musicality = row.get("predicted_preference-musicality") or row.get(
        "predicted_preference"
    )
    predicted_alignment = row.get("predicted_preference-alignment")
    human_musicality = row.get("preference-musicality")
    human_alignment = row.get("preference-alignment")

    musicality_match = bool(
        human_musicality and predicted_musicality and human_musicality == predicted_musicality
    )
    alignment_match = bool(
        human_alignment and predicted_alignment and human_alignment == predicted_alignment
    )

    return {
        "row": row,
        "predictions": {
            "musicality": predicted_musicality,
            "alignment": predicted_alignment,
        },
        "preferences": {
            "musicality": human_musicality,
            "alignment": human_alignment,
        },
        "agreement": {
            "musicality": musicality_match,
            "alignment": alignment_match,
            "overall": "agree" if musicality_match and alignment_match else "disagree",
        },
        "confidence_sum": float(row.get("confidence_preference-musicality") or 0.0)
        + float(row.get("confidence_preference-alignment") or 0.0),
        "has_feedback": bool((row.get("feedback") or "").strip()),
        "has_reference": bool((row.get("ref-audio-path") or "").strip()),
    }


def build_sample(entry, dataset_id: str, index: int):
    row = entry["row"]
    agreement = entry["agreement"]

    return {
        "dataset": dataset_id,
        "slug": f"{dataset_id}-{index + 1:02d}",
        "title": format_title(row.get("prompt", "")),
        "prompt": row.get("prompt", ""),
        "lyrics_excerpt": trim_text(row.get("lyrics", ""), 900),
        "feedback_excerpt": trim_text(
            translate_feedback(row.get("feedback", ""), row.get("prompt id")),
            420,
        ),
        "models": {
            "a": row.get("model_a", "model_a"),
            "b": row.get("model_b", "model_b"),
        },
        "preferences": entry["preferences"],
        "predictions": entry["predictions"],
        "prediction_scores": {
            "musicality_a": row.get("predicted_musicality"),
            "musicality_b": row.get("predicted_musicality_b"),
            "alignment_a": row.get("predicted_text-music alignment"),
            "alignment_b": row.get("predicted_text-music alignment_b"),
        },
        "agreement": agreement,
        "scores": {
            "music_conf": row.get("confidence_preference-musicality"),
            "align_conf": row.get("confidence_preference-alignment"),
        },
        "assets": {
            "a": normalize_media_path(row.get("audio-path", "")),
            "b": normalize_media_path(row.get("audio2", "")),
            "ref": normalize_media_path(row.get("ref-audio-path", "")),
        },
    }


def sort_entries(entries):
    return sorted(
        entries,
        key=lambda entry: (
            -int(entry["has_feedback"]),
            -entry["confidence_sum"],
            -int(entry["has_reference"]),
            entry["row"].get("prompt id", 0),
        ),
    )


def build_derived_datasets(rows):
    parsed = [parse_row(row) for row in rows]

    agreeing = sort_entries(
        [
            entry
            for entry in parsed
            if entry["agreement"]["musicality"] and entry["agreement"]["alignment"]
        ]
    )[:SAMPLES_PER_SECTION]

    disagreeing = sort_entries(
        [
            entry
            for entry in parsed
            if not entry["agreement"]["musicality"] and not entry["agreement"]["alignment"]
        ]
    )[:SAMPLES_PER_SECTION]

    return [
        {
            "id": "cmi-pref-prediction-agree",
            "label": "Prediction Matches Human Labels",
            "description": "",
            "samples": [
                build_sample(entry, "cmi-pref-prediction-agree", index)
                for index, entry in enumerate(agreeing)
            ],
        },
        {
            "id": "cmi-pref-prediction-disagree",
            "label": "Prediction Disagrees With Human Labels",
            "description": "",
            "samples": [
                build_sample(entry, "cmi-pref-prediction-disagree", index)
                for index, entry in enumerate(disagreeing)
            ],
        },
    ]


def main():
    payload = load_showcase_payload()
    base_datasets = [
        dataset
        for dataset in payload.get("datasets", [])
        if dataset.get("id") not in DERIVED_DATASET_IDS
    ]
    derived_datasets = build_derived_datasets(list(load_jsonl(RESULTS_PATH)))
    payload["datasets"] = [*base_datasets, *derived_datasets]

    with SAMPLES_PATH.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


if __name__ == "__main__":
    main()
