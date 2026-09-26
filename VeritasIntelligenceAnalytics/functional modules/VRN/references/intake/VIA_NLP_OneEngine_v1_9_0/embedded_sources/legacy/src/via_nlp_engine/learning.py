"""Governed feedback loop and out-of-core text classifier evolution."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import sqlite3
import threading
import time
import warnings
from collections import Counter
from pathlib import Path
from typing import Any

from .schemas import FeedbackRecord


SKLEARN_AVAILABLE = importlib.util.find_spec("sklearn") is not None
JOBLIB_AVAILABLE = importlib.util.find_spec("joblib") is not None


def _macro_f1(y_true: list[str], y_pred: list[str], labels: list[str]) -> float:
    scores: list[float] = []
    for label in labels:
        tp = sum(t == label and p == label for t, p in zip(y_true, y_pred))
        fp = sum(t != label and p == label for t, p in zip(y_true, y_pred))
        fn = sum(t == label and p != label for t, p in zip(y_true, y_pred))
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        score = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        scores.append(score)
    return sum(scores) / len(scores) if scores else 0.0


def _balanced_accuracy(y_true: list[str], y_pred: list[str], labels: list[str]) -> float:
    recalls = []
    for label in labels:
        actual = sum(value == label for value in y_true)
        if actual:
            recalls.append(sum(true == label and predicted == label for true, predicted in zip(y_true, y_pred)) / actual)
    return sum(recalls) / len(recalls) if recalls else 0.0


def _per_class_metrics(y_true: list[str], y_pred: list[str], labels: list[str]) -> dict[str, dict[str, float | int]]:
    output: dict[str, dict[str, float | int]] = {}
    for label in labels:
        true_positive = sum(true == label and predicted == label for true, predicted in zip(y_true, y_pred))
        false_positive = sum(true != label and predicted == label for true, predicted in zip(y_true, y_pred))
        false_negative = sum(true == label and predicted != label for true, predicted in zip(y_true, y_pred))
        precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
        recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        output[label] = {
            "support": sum(true == label for true in y_true),
            "precision": round(precision, 6),
            "recall": round(recall, 6),
            "f1": round(f1, 6),
        }
    return output


def _normalized_example(text: str) -> str:
    return " ".join(text.lower().split())


class FeedbackStore:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(str(path), check_same_thread=False, timeout=30)
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT NOT NULL,
                task TEXT NOT NULL,
                text TEXT NOT NULL,
                predicted_label TEXT,
                corrected_label TEXT,
                corrected_text TEXT,
                accepted INTEGER NOT NULL,
                note TEXT,
                created REAL NOT NULL
            )
            """
        )
        self._connection.commit()
        self._lock = threading.RLock()

    def add(self, record: FeedbackRecord) -> int:
        with self._lock:
            cursor = self._connection.execute(
                """
                INSERT INTO feedback(request_id, task, text, predicted_label, corrected_label, corrected_text, accepted, note, created)
                VALUES(?,?,?,?,?,?,?,?,?)
                """,
                (
                    record.request_id,
                    record.task,
                    record.text,
                    record.predicted_label,
                    record.corrected_label,
                    record.corrected_text,
                    int(record.accepted),
                    record.note,
                    time.time(),
                ),
            )
            self._connection.commit()
            return int(cursor.lastrowid)

    def labeled_examples(self) -> list[tuple[str, str]]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT text, corrected_label FROM feedback WHERE accepted=1 AND corrected_label IS NOT NULL ORDER BY id"
            ).fetchall()
        return [(str(text), str(label)) for text, label in rows]

    def count(self) -> int:
        with self._lock:
            return int(self._connection.execute("SELECT COUNT(*) FROM feedback").fetchone()[0])

    def close(self) -> None:
        with self._lock:
            self._connection.close()


class GovernedClassifier:
    """HashingVectorizer + SGDClassifier with guarded candidate promotion."""

    def __init__(self, model_dir: Path, config: dict[str, Any], feedback: FeedbackStore) -> None:
        self.model_dir = model_dir.resolve()
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.config = config
        self.feedback = feedback
        self._bundle: dict[str, Any] | None = None
        self._lock = threading.RLock()
        self.active_path = self.model_dir / "classifier_active.joblib"
        self.manifest_path = self.model_dir / "classifier_active.manifest.json"

    def _new_bundle(self, backend: str = "linear_sgd") -> dict[str, Any]:
        if not (SKLEARN_AVAILABLE and JOBLIB_AVAILABLE):
            raise RuntimeError("Install the 'ml' extra to enable machine learning")
        from sklearn.feature_extraction.text import HashingVectorizer

        if backend == "tiny_neural_cpu":
            from sklearn.neural_network import MLPClassifier

            vectorizer = HashingVectorizer(
                n_features=int(self.config.get("neural_n_features", 2048)),
                alternate_sign=False,
                analyzer="char_wb",
                ngram_range=(2, 5),
                norm="l2",
                dtype="float32",
            )
            classifier = MLPClassifier(
                hidden_layer_sizes=tuple(int(value) for value in self.config.get("neural_hidden_layers", [128, 32])),
                activation="relu",
                solver="adam",
                batch_size="auto",
                learning_rate_init=0.001,
                max_iter=int(self.config.get("neural_max_iter", 80)),
                early_stopping=False,
                random_state=int(self.config["random_state"]),
            )
        else:
            from sklearn.linear_model import SGDClassifier

            vectorizer = HashingVectorizer(
                n_features=int(self.config["n_features"]),
                alternate_sign=False,
                analyzer="char_wb",
                ngram_range=(2, 5),
                dtype="float32",
            )
            classifier = SGDClassifier(
                loss="log_loss",
                alpha=1e-5,
                random_state=int(self.config["random_state"]),
                average=True,
            )
        return {
            "vectorizer": vectorizer,
            "classifier": classifier,
            "classes": list(self.config["classes"]),
            "backend": backend,
        }

    @staticmethod
    def _transform(bundle: dict[str, Any], texts: list[str]) -> Any:
        features = bundle["vectorizer"].transform(texts)
        return features.toarray() if bundle.get("backend") == "tiny_neural_cpu" else features

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    def _load_verified(self) -> dict[str, Any] | None:
        if not self.active_path.exists() or not self.manifest_path.exists():
            return None
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        if self._sha256(self.active_path) != manifest.get("sha256"):
            raise RuntimeError("Active ML model failed its integrity check")
        import joblib

        return joblib.load(self.active_path)

    def predict(self, text: str) -> dict[str, Any] | None:
        if not self.config["enabled"] or not SKLEARN_AVAILABLE:
            return None
        with self._lock:
            if self._bundle is None:
                self._bundle = self._load_verified()
            if self._bundle is None:
                return None
            features = self._transform(self._bundle, [text])
            label = str(self._bundle["classifier"].predict(features)[0])
            probabilities = self._bundle["classifier"].predict_proba(features)[0]
            best = float(max(probabilities))
            return {"label": label, "confidence": round(best, 4), "backend": self._bundle.get("backend", "linear_sgd")}

    def evolve(self, promote: bool | None = None) -> dict[str, Any]:
        raw_examples = self.feedback.labeled_examples()
        minimum = int(self.config["candidate_min_samples"])
        if len(raw_examples) < minimum:
            return {"status": "insufficient_data", "samples": len(raw_examples), "required": minimum, "promoted": False}
        labels = list(self.config["classes"])
        unknown = sorted({label for _, label in raw_examples}.difference(labels))
        if unknown:
            return {"status": "rejected", "reason": f"Unknown labels: {unknown}", "promoted": False}
        if len({label for _, label in raw_examples}) < 2:
            return {"status": "rejected", "reason": "At least two labels are required", "promoted": False}

        label_by_text: dict[str, set[str]] = {}
        deduplicated: dict[tuple[str, str], tuple[str, str]] = {}
        for text, label in raw_examples:
            normalized = _normalized_example(text)
            label_by_text.setdefault(normalized, set()).add(label)
            deduplicated[(normalized, label)] = (text, label)
        conflicts = [
            {"text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(), "labels": sorted(values)}
            for text, values in label_by_text.items()
            if len(values) > 1
        ]
        if conflicts:
            return {
                "status": "rejected",
                "reason": "Conflicting labels exist for identical normalized text",
                "conflicts": conflicts[:100],
                "promoted": False,
            }
        examples = list(deduplicated.values())
        duplicate_ratio = 1.0 - len(examples) / max(1, len(raw_examples))
        if duplicate_ratio > float(self.config.get("max_duplicate_ratio", 0.35)):
            return {
                "status": "rejected",
                "reason": "Duplicate ratio exceeds the configured quality gate",
                "duplicate_ratio": round(duplicate_ratio, 6),
                "promoted": False,
            }
        if len(examples) < minimum:
            return {
                "status": "insufficient_unique_data",
                "samples": len(raw_examples),
                "unique_samples": len(examples),
                "required": minimum,
                "promoted": False,
            }

        train: list[tuple[str, str]] = []
        validation: list[tuple[str, str]] = []
        fraction = float(self.config["validation_fraction"])
        grouped: dict[str, list[tuple[str, str]]] = {label: [] for label in labels}
        for item in examples:
            grouped[item[1]].append(item)
        for label in labels:
            items = sorted(grouped[label], key=lambda item: hashlib.sha256(item[0].encode("utf-8")).hexdigest())
            if len(items) <= 1:
                train.extend(items)
                continue
            validation_count = min(len(items) - 1, max(1, math.ceil(len(items) * fraction)))
            validation.extend(items[:validation_count])
            train.extend(items[validation_count:])
        if len({label for _, label in train}) < 2:
            return {"status": "rejected", "reason": "Training split lacks label diversity", "promoted": False}
        if not validation:
            return {"status": "rejected", "reason": "Validation split is empty", "promoted": False}

        train_texts = [text for text, _ in train]
        y_train = [label for _, label in train]
        validation_texts = [text for text, _ in validation]
        y_valid = [label for _, label in validation]

        candidates: list[dict[str, Any]] = []
        linear_bundle = self._new_bundle("linear_sgd")
        batch_size = max(1, int(self.config.get("training_batch_size", 64)))
        epochs = max(1, int(self.config.get("linear_epochs", 2)))
        first_update = True
        for _ in range(epochs):
            for start in range(0, len(train_texts), batch_size):
                end = start + batch_size
                batch_features = self._transform(linear_bundle, train_texts[start:end])
                batch_labels = y_train[start:end]
                if first_update:
                    linear_bundle["classifier"].partial_fit(batch_features, batch_labels, classes=labels)
                    first_update = False
                else:
                    linear_bundle["classifier"].partial_fit(batch_features, batch_labels)
        linear_predicted = [
            str(value)
            for value in linear_bundle["classifier"].predict(self._transform(linear_bundle, validation_texts))
        ]
        candidates.append(self._candidate_report("linear_sgd", linear_bundle, y_valid, linear_predicted, labels))

        if bool(self.config.get("neural_challenger_enabled", False)) and len(examples) >= int(self.config.get("neural_min_samples", 200)):
            from sklearn.exceptions import ConvergenceWarning

            neural_bundle = self._new_bundle("tiny_neural_cpu")
            with warnings.catch_warnings(record=True) as captured:
                warnings.simplefilter("always", ConvergenceWarning)
                neural_bundle["classifier"].fit(self._transform(neural_bundle, train_texts), y_train)
            neural_predicted = [
                str(value)
                for value in neural_bundle["classifier"].predict(self._transform(neural_bundle, validation_texts))
            ]
            neural_report = self._candidate_report("tiny_neural_cpu", neural_bundle, y_valid, neural_predicted, labels)
            neural_report["converged"] = not any(isinstance(item.message, ConvergenceWarning) for item in captured)
            neural_report["iterations"] = int(neural_bundle["classifier"].n_iter_)
            candidates.append(neural_report)

        eligible_candidates = [
            item for item in candidates if item["backend"] != "tiny_neural_cpu" or bool(item.get("converged", False))
        ]
        selected = max(eligible_candidates, key=lambda item: (item["macro_f1"], item["balanced_accuracy"], item["backend"] == "linear_sgd"))
        bundle = selected.pop("bundle")
        candidate_f1 = float(selected["macro_f1"])

        baseline_f1: float | None = None
        current = self._load_verified()
        if current:
            baseline_pred = [str(value) for value in current["classifier"].predict(self._transform(current, validation_texts))]
            baseline_f1 = _macro_f1(y_valid, baseline_pred, labels)

        passes_absolute = candidate_f1 >= float(self.config["min_macro_f1"])
        passes_regression = baseline_f1 is None or candidate_f1 >= baseline_f1 - float(self.config["max_regression"])
        approved = passes_absolute and passes_regression
        candidate_path = self.model_dir / f"classifier_candidate_{time.time_ns()}.joblib"
        import joblib

        joblib.dump(bundle, candidate_path, compress=3)
        report = {
            "status": "candidate_ready" if approved else "rejected",
            "samples": len(raw_examples),
            "unique_samples": len(examples),
            "duplicate_ratio": round(duplicate_ratio, 6),
            "train_samples": len(train),
            "validation_samples": len(validation),
            "candidate_macro_f1": round(candidate_f1, 6),
            "candidate_balanced_accuracy": selected["balanced_accuracy"],
            "candidate_per_class": selected["per_class"],
            "selected_backend": selected["backend"],
            "challengers": [
                {key: value for key, value in item.items() if key != "bundle"}
                for item in candidates
            ],
            "class_distribution": dict(Counter(label for _, label in examples)),
            "baseline_macro_f1": round(baseline_f1, 6) if baseline_f1 is not None else None,
            "quality_gate_passed": approved,
            "candidate_sha256": self._sha256(candidate_path),
            "promoted": False,
        }
        should_promote = bool(self.config["auto_promote"] if promote is None else promote)
        if approved and should_promote:
            os.replace(candidate_path, self.active_path)
            manifest = {**report, "sha256": self._sha256(self.active_path), "promoted_at": time.time()}
            temp = self.manifest_path.with_suffix(".tmp")
            temp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(temp, self.manifest_path)
            with self._lock:
                self._bundle = bundle
            report["promoted"] = True
            report["status"] = "promoted"
        self._prune_candidates()
        return report

    @staticmethod
    def _candidate_report(
        backend: str,
        bundle: dict[str, Any],
        y_true: list[str],
        y_predicted: list[str],
        labels: list[str],
    ) -> dict[str, Any]:
        return {
            "backend": backend,
            "macro_f1": round(_macro_f1(y_true, y_predicted, labels), 6),
            "balanced_accuracy": round(_balanced_accuracy(y_true, y_predicted, labels), 6),
            "per_class": _per_class_metrics(y_true, y_predicted, labels),
            "bundle": bundle,
        }

    def _prune_candidates(self) -> None:
        retention = max(1, int(self.config.get("candidate_retention", 5)))
        candidates = sorted(self.model_dir.glob("classifier_candidate_*.joblib"), key=lambda path: path.stat().st_mtime, reverse=True)
        for path in candidates[retention:]:
            path.unlink(missing_ok=True)

    def status(self) -> dict[str, Any]:
        return {
            "enabled": bool(self.config["enabled"]),
            "backend_available": SKLEARN_AVAILABLE and JOBLIB_AVAILABLE,
            "active_model": self.active_path.exists(),
            "feedback_records": self.feedback.count(),
            "auto_promote": bool(self.config["auto_promote"]),
            "auto_evolve_every_feedback": int(self.config.get("auto_evolve_every_feedback", 0)),
            "neural_challenger_enabled": bool(self.config.get("neural_challenger_enabled", False)),
            "neural_min_samples": int(self.config.get("neural_min_samples", 200)),
        }

    def fingerprint(self) -> str:
        if not self.active_path.exists() or not self.manifest_path.exists():
            return "rules_only"
        try:
            manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            return str(manifest.get("sha256") or self._sha256(self.active_path))
        except (OSError, json.JSONDecodeError):
            return "active_model_unverified"
