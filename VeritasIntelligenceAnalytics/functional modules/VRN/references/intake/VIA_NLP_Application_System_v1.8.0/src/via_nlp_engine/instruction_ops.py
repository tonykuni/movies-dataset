"""Evidence-first reconstruction of fragmented instructions and shell commands."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from .bilingual_ops import ROLE_LABELS, bilingual_label, build_glossary, detect_language


ORDER_MARKER_RE = re.compile(
    r"(?:首先|第一步|先|接著|其次|然後|再來|最後|完成後|before|first|next|then|after|finally)", re.I
)
PREREQUISITE_RE = re.compile(r"(?:前置條件|事前|需要先|必須先|先安裝|prerequisite|before|requires?\s+first)", re.I)
VERIFICATION_RE = re.compile(r"(?:驗證|確認|檢查|測試|應看到|預期|verify|validate|check|confirm|test|expect)", re.I)
PROHIBITION_RE = re.compile(r"(?:禁止|不得|不可|不要|避免|嚴禁|must\s+not|do\s+not|never|forbid)", re.I)
REQUIREMENT_RE = re.compile(r"(?:必須|需要|應該|務必|請|要求|must|shall|should|need\s+to|required?)", re.I)
DECISION_RE = re.compile(r"(?:決定|採用|改為|更新為|以.+為準|decid(?:e|ed)|adopt|use\s+.+instead)", re.I)
ACTION_RE = re.compile(r"(?:執行|建立|新增|修改|更新|安裝|啟動|停止|匯出|匯入|重建|run|create|add|update|install|start|stop|export|import|build)", re.I)
COMMAND_START_RE = re.compile(
    r"^\s*(?:pwsh|powershell|python|python3|py|pip|pip3|git|docker|npm|npx|pnpm|yarn|curl|wget|"
    r"dotnet|java|node|pytest|uvicorn|conda|poetry|Invoke-[A-Za-z]|Get-[A-Za-z]|Set-[A-Za-z]|"
    r"New-[A-Za-z]|Start-[A-Za-z]|Stop-[A-Za-z]|Test-[A-Za-z]|Remove-[A-Za-z]|\.\\|\.\/|[A-Za-z]:\\)",
    re.I,
)
COMMENT_RE = re.compile(r"^\s*(?:#|//|REM\s)", re.I)
CONTROL_RE = re.compile(r"^\s*(?:function\b|def\b|class\b|param\s*\(|if\b|for\b|while\b|try\b|catch\b|finally\b|\{|\})", re.I)
CONTINUATION = {"powershell": "`", "bash": "\\", "cmd": "^"}


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def _instruction_type(text: str) -> str | None:
    if PROHIBITION_RE.search(text):
        return "prohibition"
    if PREREQUISITE_RE.search(text):
        return "prerequisite"
    if VERIFICATION_RE.search(text):
        return "verification"
    if DECISION_RE.search(text):
        return "decision"
    if REQUIREMENT_RE.search(text):
        return "requirement"
    if ORDER_MARKER_RE.search(text) and ACTION_RE.search(text):
        return "action"
    return None


def _command_shell(language: str, line: str) -> str:
    selected = language.casefold()
    if selected in {"powershell", "bash"}:
        return selected
    if selected in {"bat", "batch", "cmd"}:
        return "cmd"
    lowered = line.lstrip().casefold()
    if lowered.startswith(("invoke-", "get-", "set-", "new-", "start-", "stop-", "test-", "remove-", "pwsh", "powershell")):
        return "powershell"
    if lowered.startswith(("#!/bin", "./", "bash ", "sh ")):
        return "bash"
    if lowered.startswith(("python", "python3", "py ", "pip", "pytest")):
        return "python_cli"
    return "generic_cli"


class InstructionReconstructor:
    """Rebuild a reviewable procedure; it never executes or activates commands."""

    def build(
        self,
        segments: list[dict[str, Any]],
        refinement_ledger: list[dict[str, Any]],
        code_blocks: list[dict[str, Any]],
        source_text: str,
    ) -> dict[str, Any]:
        glossary = build_glossary(source_text)
        segment_order = {item["segment_id"]: index for index, item in enumerate(segments, start=1)}
        segment_map = {item["segment_id"]: item for item in segments}
        instructions = self._natural_instructions(refinement_ledger, segment_map, segment_order, glossary)
        commands = self._command_units(code_blocks, segment_order, glossary)
        ordered_items = sorted(
            [
                {"step_id": item["instruction_id"], "kind": "instruction", **self._step_projection(item)}
                for item in instructions
            ]
            + [
                {"step_id": item["command_id"], "kind": "command", **self._step_projection(item)}
                for item in commands
            ],
            key=lambda item: (item["source_order"], item["source_suborder"], item["step_id"]),
        )
        dependencies = self._dependencies(ordered_items)
        procedures = self._procedures(ordered_items, dependencies)
        incomplete_commands = [item["command_id"] for item in commands if not item["completeness"]["continuation_balanced"]]
        ambiguous_instructions = [
            item["instruction_id"] for item in instructions if item["confidence"] < 0.75
        ]
        return {
            "schema": "VIA_INSTRUCTION_RECONSTRUCTION/1.0",
            "languages": ["zh", "en"],
            "instructions": instructions,
            "command_units": commands,
            "procedures": procedures,
            "dependencies": dependencies,
            "review_queue": {
                "incomplete_command_ids": incomplete_commands,
                "ambiguous_instruction_ids": ambiguous_instructions,
                "all_command_ids": [item["command_id"] for item in commands],
                "reason": "all reconstructed commands require human review before any execution",
                "reason_bilingual": {
                    "zh": "所有重建命令在執行前都需要人工審查",
                    "en": "All reconstructed commands require human review before execution",
                },
            },
            "statistics": {
                "instruction_count": len(instructions),
                "command_count": len(commands),
                "command_occurrence_count": sum(len(item["occurrences"]) for item in commands),
                "procedure_count": len(procedures),
                "incomplete_commands": len(incomplete_commands),
                "source_segments_referenced": len(
                    {segment_id for item in instructions + commands for segment_id in item["source_segments"]}
                ),
            },
            "quality_gates": {
                "source_traceability": "pass" if all(item["source_segments"] for item in instructions + commands) else "fail",
                "command_execution_authorized": False,
                "automatic_canonical_write": False,
                "incomplete_command_fail_closed": True,
                "unknown_translation_policy": "preserve_source_and_mark_needs_translation",
            },
        }

    @staticmethod
    def _step_projection(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "source_order": item["source_order"],
            "source_suborder": item["source_suborder"],
            "source_segments": item["source_segments"],
            "type": item.get("instruction_type", "command"),
        }

    def _natural_instructions(
        self,
        refinement_ledger: list[dict[str, Any]],
        segment_map: dict[str, dict[str, Any]],
        segment_order: dict[str, int],
        glossary: dict[str, str],
    ) -> list[dict[str, Any]]:
        found: dict[str, dict[str, Any]] = {}
        for refined in refinement_ledger:
            segment_id = str(refined["segment_id"])
            candidates = refined.get("semantic_units") or [refined.get("optimized_text", "")]
            for suborder, candidate in enumerate(candidates, start=1):
                text = str(candidate).strip()
                selected_type = _instruction_type(text)
                if not text or not selected_type:
                    continue
                identity = _sha256_text(f"{selected_type}\0{_normalize(text)}")
                occurrence = {
                    "source_segment": segment_id,
                    "source_order": segment_order[segment_id],
                    "source_suborder": suborder,
                    "source_sha256": segment_map[segment_id].get("sha256"),
                }
                if identity not in found:
                    confidence = 0.96 if selected_type in {"prohibition", "prerequisite", "verification"} else 0.86
                    found[identity] = {
                        "instruction_id": f"INS-{identity[:16].upper()}",
                        "instruction_type": selected_type,
                        "type_label": ROLE_LABELS[selected_type],
                        "text": text,
                        "text_sha256": _sha256_text(text),
                        "bilingual_text": bilingual_label(text, glossary),
                        "source_language": detect_language(text),
                        "source_segments": [segment_id],
                        "occurrences": [occurrence],
                        "source_order": occurrence["source_order"],
                        "source_suborder": suborder,
                        "confidence": confidence,
                        "status": "recorded_requires_review",
                        "is_derivative": True,
                    }
                else:
                    item = found[identity]
                    item["occurrences"].append(occurrence)
                    if segment_id not in item["source_segments"]:
                        item["source_segments"].append(segment_id)
        return sorted(found.values(), key=lambda item: (item["source_order"], item["source_suborder"], item["instruction_id"]))

    def _command_units(
        self,
        code_blocks: list[dict[str, Any]],
        segment_order: dict[str, int],
        glossary: dict[str, str],
    ) -> list[dict[str, Any]]:
        output_by_identity: dict[str, dict[str, Any]] = {}
        for block in code_blocks:
            language = str(block.get("language", "text")).casefold()
            if language not in {"powershell", "bash", "bat", "batch", "cmd", "text", "unknown"}:
                continue
            lines = str(block.get("code", "")).splitlines()
            index = 0
            suborder = 0
            while index < len(lines):
                line = lines[index]
                if not COMMAND_START_RE.search(line) or COMMENT_RE.search(line) or CONTROL_RE.search(line):
                    index += 1
                    continue
                suborder += 1
                shell = _command_shell(language, line)
                marker = CONTINUATION.get(shell)
                verbatim = [line]
                while marker and verbatim[-1].rstrip().endswith(marker) and index + 1 < len(lines):
                    index += 1
                    verbatim.append(lines[index])
                balanced = not bool(marker and verbatim[-1].rstrip().endswith(marker))
                reconstructed = " ".join(
                    part.rstrip().removesuffix(marker).rstrip() if marker else part.strip()
                    for part in verbatim
                ).strip()
                source_segments = list(block.get("source_segments") or [])
                first_segment = source_segments[0] if source_segments else ""
                source_position = segment_order.get(first_segment, int(block.get("source_span", {}).get("start", 0)) + 1)
                identity = _sha256_text(f"{shell}\0{_normalize(reconstructed)}")
                occurrence = {
                    "source_code_id": block.get("code_id"),
                    "source_segments": source_segments,
                    "source_order": source_position,
                    "source_suborder": suborder,
                    "verbatim_sha256": _sha256_text("\n".join(verbatim)),
                }
                if identity not in output_by_identity:
                    output_by_identity[identity] = {
                        "command_id": f"CMD-{identity[:16].upper()}",
                        "instruction_type": "command",
                        "type_label": ROLE_LABELS["command"],
                        "shell": shell,
                        "verbatim_lines": verbatim,
                        "verbatim_sha256": _sha256_text("\n".join(verbatim)),
                        "reconstructed_command": reconstructed,
                        "bilingual_purpose": bilingual_label(reconstructed, glossary),
                        "source_language": detect_language(reconstructed),
                        "source_segments": source_segments,
                        "source_code_id": block.get("code_id"),
                        "source_code_ids": [block.get("code_id")],
                        "occurrences": [occurrence],
                        "source_order": source_position,
                        "source_suborder": suborder,
                        "completeness": {
                            "continuation_balanced": balanced,
                            "line_count": len(verbatim),
                            "reconstruction_method": "continuation_marker_join_only",
                            "semantic_completion_attempted": False,
                        },
                        "risk": {
                            "destructive_hint": bool(re.search(r"(?:Remove-Item|rm\s+-rf|DROP\s+TABLE|del\s+/)", reconstructed, re.I)),
                            "network_hint": bool(re.search(r"(?:Invoke-WebRequest|curl\b|wget\b|requests\.)", reconstructed, re.I)),
                        },
                        "confidence": 0.98 if balanced else 0.45,
                        "status": "review_required_never_executed",
                        "execution_authorized": False,
                    }
                else:
                    item = output_by_identity[identity]
                    item["occurrences"].append(occurrence)
                    if block.get("code_id") not in item["source_code_ids"]:
                        item["source_code_ids"].append(block.get("code_id"))
                    for segment_id in source_segments:
                        if segment_id not in item["source_segments"]:
                            item["source_segments"].append(segment_id)
                index += 1
        return sorted(output_by_identity.values(), key=lambda item: (item["source_order"], item["source_suborder"], item["command_id"]))

    @staticmethod
    def _dependencies(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
        dependencies: list[dict[str, Any]] = []
        previous: dict[str, Any] | None = None
        latest_prerequisite: str | None = None
        latest_action: str | None = None
        for step in steps:
            if previous:
                dependencies.append(
                    {
                        "from": previous["step_id"],
                        "to": step["step_id"],
                        "relation": "follows_in_source",
                        "inferred": False,
                        "applied_as_execution_order": False,
                    }
                )
            if step["type"] == "prerequisite":
                latest_prerequisite = step["step_id"]
            elif latest_prerequisite and step["type"] in {"action", "command", "requirement"}:
                dependencies.append(
                    {
                        "from": latest_prerequisite,
                        "to": step["step_id"],
                        "relation": "requires",
                        "inferred": True,
                        "confidence": 0.72,
                        "review_required": True,
                    }
                )
            if step["type"] in {"action", "command"}:
                latest_action = step["step_id"]
            elif step["type"] == "verification" and latest_action:
                dependencies.append(
                    {
                        "from": step["step_id"],
                        "to": latest_action,
                        "relation": "verifies",
                        "inferred": True,
                        "confidence": 0.8,
                        "review_required": True,
                    }
                )
            previous = step
        return dependencies

    @staticmethod
    def _procedures(steps: list[dict[str, Any]], dependencies: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not steps:
            return []
        digest = _sha256_text("\0".join(item["step_id"] for item in steps))
        return [
            {
                "procedure_id": f"PROC-{digest[:16].upper()}",
                "title": {"zh": "依來源逐步重建程序", "en": "Source-Ordered Reconstructed Procedure"},
                "step_ids": [item["step_id"] for item in steps],
                "dependency_count": len(dependencies),
                "ordering_basis": "source_order_with_reviewable_dependency_proposals",
                "execution_authorized": False,
                "canonical_status": "proposal_requires_human_approval",
            }
        ]
