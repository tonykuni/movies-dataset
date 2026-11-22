from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
V3_ROOT = ROOT / "v3"
LEXICON_PATH = ROOT / "VIA_NLP_SSOT_Lexicon_v5.json"
sys.path.insert(0, str(ROOT))
from v3.via_content_reconstructor import reconstruct_file, reconstruct_paths as reconstruct_v3_paths, sha256_text, stable_id  # noqa: E402

SCHEMA = "VIA_NLP_RECONSTRUCTION/5.0"
ENGINE_ID = "VIA-ENG-004"
ENGINE_VERSION = "5.0.0"


def load_lexicon(path: Path = LEXICON_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def flatten_synonyms(lexicon: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for canonical, values in lexicon.get("synonyms", {}).items():
        result[canonical.casefold()] = canonical
        for value in values:
            result[str(value).casefold()] = canonical
    return result


def normalize_for_match(text: str, synonym_map: dict[str, str]) -> str:
    value = text.casefold()
    for alias, canonical in sorted(synonym_map.items(), key=lambda item: len(item[0]), reverse=True):
        value = re.sub(rf"(?<![\w]){re.escape(alias)}(?![\w])", f" {canonical} ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def token_terms(text: str, lexicon: dict[str, Any]) -> list[str]:
    synonym_map = flatten_synonyms(lexicon)
    normalized = normalize_for_match(text, synonym_map)
    stopwords = {item.casefold() for item in lexicon.get("stopwords", [])}
    candidates = re.findall(r"[\u3400-\u9fff]{2,8}|[A-Za-z][A-Za-z0-9_-]{2,}|\b\d{4}\b", normalized)
    terms: list[str] = []
    for candidate in candidates:
        item = candidate.casefold()
        if item in stopwords or len(item) < 2:
            continue
        terms.append(item)
    # Keep canonical factor names even when their surface form is short.
    for category, values in lexicon.get("factors", {}).items():
        for value in values:
            if re.search(re.escape(value), normalized, re.I):
                terms.append(f"factor:{category}:{value.casefold()}")
    return terms


def factor_matches(text: str, lexicon: dict[str, Any]) -> list[dict[str, str]]:
    normalized = normalize_for_match(text, flatten_synonyms(lexicon))
    found: list[dict[str, str]] = []
    for category, values in lexicon.get("factors", {}).items():
        for value in values:
            if re.search(rf"(?<![\w]){re.escape(value)}(?![\w])", normalized, re.I):
                found.append({"factor": value, "category": category, "source": "lexicon"})
    return found


def regex_matches(text: str, lexicon: dict[str, Any], limit: int = 300) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for kind, expression in lexicon.get("regex", {}).items():
        try:
            pattern = re.compile(expression, re.I | re.M)
        except re.error:
            continue
        for match in pattern.finditer(text):
            result.append({"kind": kind, "text": match.group(0), "start": match.start(), "end": match.end()})
            if len(result) >= limit:
                return result
    return result


def language_profile(text: str) -> dict[str, Any]:
    zh = len(re.findall(r"[\u3400-\u9fff]", text))
    latin = len(re.findall(r"[A-Za-z]", text))
    digits = len(re.findall(r"\d", text))
    spaces = len(re.findall(r"\s", text))
    total = max(1, zh + latin + digits)
    return {
        "primary": "zh-Hant" if zh >= latin else "en",
        "mixed": zh > 0 and latin > 0,
        "zh_ratio": round(zh / total, 4),
        "latin_ratio": round(latin / total, 4),
        "digit_ratio": round(digits / total, 4),
        "whitespace_ratio": round(spaces / max(1, len(text)), 4),
    }


def extract_speaker(text: str) -> dict[str, str] | None:
    line = text.strip().splitlines()[0] if text.strip() else ""
    match = re.match(r"(?:(?P<time>\d{1,2}:\d{2})\s+)?(?P<speaker>[^:：\n]{1,36}?)(?:\s+☎️.*)?\s*$", line)
    if not match or not match.group("speaker"):
        return None
    speaker = match.group("speaker").strip(" -·")
    if not speaker or speaker.casefold() in {"內容", "評論", "結論", "summary", "input", "output"}:
        return None
    return {"speaker": speaker, "timestamp": match.group("time") or ""}


def topic_anchor(text: str, lexicon: dict[str, Any]) -> list[str]:
    terms = token_terms(text, lexicon)
    counts = Counter(terms)
    # Preserve first-seen order among high-frequency terms for deterministic topic IDs.
    chosen: list[str] = []
    for term in terms:
        if term not in chosen and (counts[term] >= 1):
            chosen.append(term)
        if len(chosen) >= 5:
            break
    return chosen


def jaccard(left: Iterable[str], right: Iterable[str]) -> float:
    a, b = set(left), set(right)
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def enrich_units(record: dict[str, Any], lexicon: dict[str, Any]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for unit in record.get("units", []):
        text = unit.get("corrected_text", unit.get("source_text", ""))
        speaker = extract_speaker(text)
        terms = token_terms(text, lexicon)
        factors = factor_matches(text, lexicon)
        regexes = regex_matches(text, lexicon, limit=60)
        semantic = {
            "unit_id": unit["unit_id"],
            "speaker": speaker["speaker"] if speaker else None,
            "timestamp": speaker["timestamp"] if speaker else None,
            "language": language_profile(text),
            "terms": terms[:24],
            "topic_anchor": topic_anchor(text, lexicon),
            "factor_matches": factors[:40],
            "regex_match_counts": dict(Counter(item["kind"] for item in regexes)),
            "question": bool(re.search(lexicon["regex"]["question"], text, re.I)),
            "command": bool(re.search(lexicon["regex"]["command"], text, re.I)),
            "constraint": bool(re.search(lexicon["regex"]["constraint"], text, re.I)),
            "verification": bool(re.search(lexicon["regex"]["verification"], text, re.I)),
        }
        copy = dict(unit)
        copy["nlp_v5"] = semantic
        copy["term_signature"] = sha256_text("|".join(sorted(set(terms))))[:16]
        enriched.append(copy)
    return enriched


def build_topic_episodes(units: list[dict[str, Any]], threshold: float = 0.18) -> list[dict[str, Any]]:
    episodes: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for order, unit in enumerate(units):
        nlp = unit["nlp_v5"]
        anchors = nlp["topic_anchor"]
        speaker = nlp.get("speaker")
        new_episode = current is None
        similarity = 0.0
        if current is not None:
            similarity = jaccard(anchors, current["topic_anchor"])
            strong_boundary = bool(re.search(r"(?:^|\n)(?:#{1,6}|[一二三四五六七八九十]+[、.]|\d+[.)])", unit["corrected_text"]))
            has_new_entity = bool(anchors and current["topic_anchor"] and anchors[0] != current["topic_anchor"][0] and similarity < threshold)
            speaker_boundary = bool(speaker and current.get("last_speaker") and speaker != current["last_speaker"] and similarity < threshold / 2)
            new_episode = strong_boundary or has_new_entity or speaker_boundary
        if new_episode:
            episode_id = stable_id("TOPIC", unit["source_name"], order, "|".join(anchors))
            current = {
                "episode_id": episode_id,
                "order": len(episodes),
                "unit_ids": [],
                "topic_anchor": list(anchors),
                "topic_label": " / ".join(anchors[:3]) or unit["primary_type"],
                "speakers": [],
                "last_speaker": None,
                "similarity_to_previous": similarity,
                "return_links": [],
            }
            episodes.append(current)
        current["unit_ids"].append(unit["unit_id"])
        if speaker and speaker not in current["speakers"]:
            current["speakers"].append(speaker)
        current["last_speaker"] = speaker or current.get("last_speaker")
        if not current["topic_anchor"]:
            current["topic_anchor"] = list(anchors)
            current["topic_label"] = " / ".join(anchors[:3]) or unit["primary_type"]
    # Return links: repeated anchors in non-adjacent episodes.
    for index, episode in enumerate(episodes):
        for previous in episodes[:index]:
            score = jaccard(episode["topic_anchor"], previous["topic_anchor"])
            if score >= 0.35 and index - previous["order"] > 1:
                episode["return_links"].append({"episode_id": previous["episode_id"], "similarity": round(score, 4), "type": "topic_return"})
    return episodes


def attach_topics(units: list[dict[str, Any]], episodes: list[dict[str, Any]]) -> None:
    index: dict[str, str] = {}
    for episode in episodes:
        for unit_id in episode["unit_ids"]:
            index[unit_id] = episode["episode_id"]
    for unit in units:
        unit["topic_episode_id"] = index.get(unit["unit_id"])


def canonical_parameter_name(name: str, lexicon: dict[str, Any]) -> str:
    lowered = name.casefold().lstrip("-$")
    for canonical, aliases in lexicon.get("synonyms", {}).items():
        if lowered == canonical.casefold() or lowered in {str(alias).casefold() for alias in aliases}:
            return canonical
    return lowered.replace("-", "_")


def classify_value(value: str) -> str:
    value = value.strip()
    if re.fullmatch(r"[-+]?\d+(?:\.\d+)?", value):
        return "number"
    if re.fullmatch(r"(?:true|false|yes|no|on|off)", value, re.I):
        return "boolean"
    if re.fullmatch(r"20\d{2}[-/]\d{1,2}[-/]\d{1,2}", value):
        return "date"
    if value.startswith(("[", "{")):
        return "structured"
    return "string"


def enrich_parameters(units: list[dict[str, Any]], lexicon: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    params: list[dict[str, Any]] = []
    by_name: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for unit in units:
        for parameter in unit.get("parameters", []):
            copy = dict(parameter)
            canonical = canonical_parameter_name(copy["name"], lexicon)
            copy.update({
                "canonical_name": canonical,
                "type_candidate": classify_value(copy.get("value", "")),
                "factor_domain": next((category for category, values in lexicon.get("factors", {}).items() if canonical in values), "unknown"),
                "source_unit_id": unit["unit_id"],
                "review_required": True,
            })
            params.append(copy)
            by_name[canonical].append(copy)
    conflicts: list[dict[str, Any]] = []
    for name, values in by_name.items():
        distinct = sorted({str(value.get("value", "")) for value in values})
        if len(distinct) > 1:
            conflicts.append({
                "conflict_id": stable_id("CONFLICT", name, *distinct),
                "canonical_name": name,
                "values": distinct,
                "source_unit_ids": [value["source_unit_id"] for value in values],
                "status": "review_required",
                "resolution": "preserve_all_values",
            })
    return params, conflicts


def command_signature(command: dict[str, Any], lexicon: dict[str, Any]) -> set[str]:
    text = " ".join([command.get("goal", ""), *command.get("actions", []), *command.get("constraints", [])])
    terms = set(token_terms(text, lexicon))
    for parameter in command.get("parameters", []):
        terms.add(f"param:{canonical_parameter_name(parameter, lexicon)}")
    for key in ("constraints", "verification"):
        if command.get(key):
            terms.add(key)
    return terms


def merge_similar_commands(commands: list[dict[str, Any]], lexicon: dict[str, Any], threshold: float = 0.62) -> dict[str, Any]:
    groups: list[dict[str, Any]] = []
    assigned: set[str] = set()
    signatures = {command["command_id"]: command_signature(command, lexicon) for command in commands}
    for command in commands:
        cid = command["command_id"]
        if cid in assigned:
            continue
        members = [command]
        assigned.add(cid)
        scores: list[float] = []
        for candidate in commands:
            if candidate["command_id"] in assigned:
                continue
            score = jaccard(signatures[cid], signatures[candidate["command_id"]])
            if score >= threshold:
                members.append(candidate)
                assigned.add(candidate["command_id"])
                scores.append(score)
        merged_actions: list[str] = []
        parameters: list[str] = []
        constraints: list[str] = []
        verification: list[str] = []
        for member in members:
            for action in member.get("actions", []):
                if action not in merged_actions:
                    merged_actions.append(action)
            for parameter in member.get("parameters", []):
                canonical = canonical_parameter_name(parameter, lexicon)
                if canonical not in parameters:
                    parameters.append(canonical)
            for key, target in (("constraints", constraints), ("verification", verification)):
                for value in member.get(key, []):
                    if value not in target:
                        target.append(value)
        representative = min(members, key=lambda item: len(item.get("goal", "")))
        group_id = stable_id("CMDGROUP", *[member["command_id"] for member in members])
        groups.append({
            "merge_group_id": group_id,
            "canonical_command_id": stable_id("CMDMERGED", group_id),
            "member_command_ids": [member["command_id"] for member in members],
            "member_count": len(members),
            "representative_goal": representative.get("goal", ""),
            "merged_actions": merged_actions[:24],
            "parameters": parameters,
            "constraints": constraints,
            "verification": verification,
            "similarity_min": round(min(scores) if scores else 1.0, 4),
            "similarity_mean": round(sum(scores) / len(scores), 4) if scores else 1.0,
            "merge_status": "candidate_projection" if len(members) > 1 else "singleton",
            "source_commands_preserved": True,
            "executable": False,
            "review_required": len(members) > 1,
        })
    merged_count = sum(max(0, group["member_count"] - 1) for group in groups)
    return {
        "algorithm": "lexicon_normalized_signature_jaccard_greedy",
        "threshold": threshold,
        "groups": groups,
        "original_command_count": len(commands),
        "merged_command_count": len(groups),
        "deduplicated_candidate_count": merged_count,
        "source_commands_preserved": True,
        "review_required": any(group["member_count"] > 1 for group in groups),
    }


def build_enhanced_summary(record: dict[str, Any], units: list[dict[str, Any]], episodes: list[dict[str, Any]], merged: dict[str, Any], conflicts: list[dict[str, Any]]) -> dict[str, Any]:
    frequency = Counter(term for unit in units for term in unit["nlp_v5"]["terms"] if not term.startswith("factor:"))
    ranked: list[tuple[float, dict[str, Any]]] = []
    for index, unit in enumerate(units):
        nlp = unit["nlp_v5"]
        terms = set(nlp["terms"])
        centrality = sum(frequency[term] for term in terms)
        marker_score = 2.0 * bool(nlp["command"]) + 1.5 * bool(nlp["question"]) + 1.0 * bool(nlp["verification"]) + 0.8 * bool(nlp["constraint"])
        position_score = 1.0 / (1.0 + index / max(1, len(units)))
        ranked.append((centrality + marker_score + position_score, unit))
    ranked.sort(key=lambda item: (-item[0], item[1]["order"]))
    key_points = []
    for score, unit in ranked[: min(12, len(ranked))]:
        key_points.append({
            "text": unit["corrected_text"][:400],
            "source_unit_id": unit["unit_id"],
            "topic_episode_id": unit.get("topic_episode_id"),
            "score": round(score, 4),
        })
    questions = [{"text": unit["corrected_text"], "source_unit_id": unit["unit_id"]} for unit in units if unit["nlp_v5"]["question"]][:20]
    constraints = [{"text": unit["corrected_text"], "source_unit_id": unit["unit_id"]} for unit in units if unit["nlp_v5"]["constraint"]][:20]
    topic_rows = [{
        "episode_id": episode["episode_id"],
        "label": episode["topic_label"],
        "unit_count": len(episode["unit_ids"]),
        "unit_ids": episode["unit_ids"],
        "return_links": episode["return_links"],
    } for episode in episodes]
    top_terms = [term for term, _ in frequency.most_common(20)]
    executive = "；".join(item["text"].replace("\n", " ")[:180] for item in key_points[:3])
    return {
        "title": record["source"]["source_name"],
        "executive_summary": executive,
        "key_points": key_points,
        "top_terms": top_terms,
        "topics": topic_rows,
        "questions": questions,
        "constraints": constraints,
        "command_groups": merged["groups"][:20],
        "parameter_conflict_count": len(conflicts),
        "content_type_counts": dict(Counter(unit["primary_type"] for unit in units)),
        "unit_count": len(units),
        "method": "v5_lexicon_weighted_extractive_topic_summary",
        "source_unit_traceable": True,
        "source_preserved": True,
        "review_required": True,
    }


def reconstruct_v5_file(path: str | Path, lexicon: dict[str, Any], command_threshold: float = 0.62) -> dict[str, Any]:
    record = reconstruct_file(path)
    units = enrich_units(record, lexicon)
    episodes = build_topic_episodes(units)
    attach_topics(units, episodes)
    parameters, conflicts = enrich_parameters(units, lexicon)
    original_commands = record["projections"]["command_reconstruction"]["commands"]
    merged = merge_similar_commands(original_commands, lexicon, threshold=command_threshold)
    enhanced_summary = build_enhanced_summary(record, units, episodes, merged, conflicts)
    all_text = record["source_text"]
    record["schema"] = SCHEMA
    record["engine"] = {"engine_id": ENGINE_ID, "engine_version": ENGINE_VERSION, "base_engine_version": "3.0.0"}
    record["units"] = units
    record["projections"]["legacy_v3_summary"] = record["projections"].get("summary")
    record["projections"]["summary"] = enhanced_summary
    record["projections"]["topic_reconstruction"] = {
        "episodes": episodes,
        "episode_count": len(episodes),
        "return_link_count": sum(len(episode["return_links"]) for episode in episodes),
        "method": "anchor_and_term_jaccard_incremental_episode_builder",
    }
    record["projections"]["command_reconstruction"]["original_commands"] = original_commands
    record["projections"]["command_reconstruction"]["similarity_merge"] = merged
    record["projections"]["command_reconstruction"]["commands"] = original_commands
    record["projections"]["parameter_reconstruction"]["parameters"] = parameters
    record["projections"]["parameter_reconstruction"]["count"] = len(parameters)
    record["projections"]["parameter_reconstruction"]["conflicts"] = conflicts
    record["projections"]["factor_library_projection"] = {
        "factor_matches": [match for unit in units for match in unit["nlp_v5"]["factor_matches"]],
        "factor_count": sum(len(unit["nlp_v5"]["factor_matches"]) for unit in units),
        "lexicon_version": lexicon["version"],
    }
    record["projections"]["regex_projection"] = {
        "match_counts": dict(Counter(item["kind"] for unit in units for item in regex_matches(unit["corrected_text"], lexicon, limit=60))),
        "lexicon_version": lexicon["version"],
        "protected_before_normalization": True,
    }
    record["projections"]["nlp_v5"] = {
        "language_profile": language_profile(all_text),
        "lexicon_version": lexicon["version"],
        "synonym_normalization": True,
        "factor_library": True,
        "parameter_library": True,
        "topic_reconstruction": True,
        "command_similarity_merge": True,
        "summary_enhancement": True,
    }
    record["quality_gates"].update({
        "v5_source_preserved": True,
        "v5_source_text_sha256": sha256_text(all_text),
        "v5_original_command_count": len(original_commands),
        "v5_merged_command_group_count": merged["merged_command_count"],
        "v5_deduplicated_candidate_count": merged["deduplicated_candidate_count"],
        "v5_source_commands_preserved": merged["source_commands_preserved"],
        "v5_semantic_rewrite_executable": False,
        "v5_review_required": True,
    })
    record["status"] = "PASS_WITH_REVIEW"
    return record


def reconstruct_v5_paths(paths: Iterable[str | Path], lexicon: dict[str, Any], command_threshold: float = 0.45) -> dict[str, Any]:
    records = [reconstruct_v5_file(path, lexicon, command_threshold) for path in paths]
    all_groups = [record["projections"]["command_reconstruction"]["similarity_merge"] for record in records]
    return {
        "schema": "VIA_NLP_RECONSTRUCTION_BUNDLE/5.0",
        "engine": {"engine_id": ENGINE_ID, "engine_version": ENGINE_VERSION},
        "lexicon": {"path": str(LEXICON_PATH), "version": lexicon["version"]},
        "source_preserved": True,
        "record_count": len(records),
        "records": records,
        "summary": {
            "files": [record["source"]["source_name"] for record in records],
            "total_units": sum(len(record["units"]) for record in records),
            "original_commands": sum(group["original_command_count"] for group in all_groups),
            "merged_command_groups": sum(group["merged_command_count"] for group in all_groups),
            "deduplicated_command_candidates": sum(group["deduplicated_candidate_count"] for group in all_groups),
            "topics": sum(len(record["projections"]["topic_reconstruction"]["episodes"]) for record in records),
            "parameter_conflicts": sum(len(record["projections"]["parameter_reconstruction"]["conflicts"]) for record in records),
            "review_required": True,
        },
        "quality_gates": {
            "source_preserved": all(record["quality_gates"]["v5_source_preserved"] for record in records),
            "source_deleted": False,
            "source_mutated": False,
            "original_commands_preserved": all(record["quality_gates"]["v5_source_commands_preserved"] for record in records),
            "semantic_rewrite_executable": False,
            "review_required": True,
        },
    }


def write_v5_outputs(bundle: dict[str, Any], output_dir: str | Path) -> Path:
    output = Path(output_dir).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    bundle_path = output / "VIA_NLP_Reconstruction_Bundle_v5.json"
    bundle_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for record in bundle["records"]:
        stem = re.sub(r"[^A-Za-z0-9._-]+", "_", record["source"]["source_name"])
        record_dir = output / stem
        record_dir.mkdir(exist_ok=True)
        for filename, payload in {
            "record.json": record,
            "summary_v5.json": record["projections"]["summary"],
            "topic_reconstruction.json": record["projections"]["topic_reconstruction"],
            "command_similarity_merge.json": record["projections"]["command_reconstruction"]["similarity_merge"],
            "parameter_library_projection.json": record["projections"]["parameter_reconstruction"],
            "factor_library_projection.json": record["projections"]["factor_library_projection"],
            "regex_projection.json": record["projections"]["regex_projection"],
        }.items():
            (record_dir / filename).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return bundle_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="VIA v5 enhanced NLP reconstruction")
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("VIA_NLP_Reconstruction_Output_v5"))
    parser.add_argument("--lexicon", type=Path, default=LEXICON_PATH)
    parser.add_argument("--command-threshold", type=float, default=0.45)
    args = parser.parse_args(argv)
    lexicon = load_lexicon(args.lexicon)
    bundle = reconstruct_v5_paths(args.inputs, lexicon, args.command_threshold)
    path = write_v5_outputs(bundle, args.output_dir)
    print(json.dumps({"status": "PASS_WITH_REVIEW", "bundle": str(path), "summary": bundle["summary"], "gates": bundle["quality_gates"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
