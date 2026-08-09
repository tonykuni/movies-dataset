"""vtr_py 確定性層測試。

用 stdlib unittest（環境無 pytest，且確定性層本來就該零相依）：

    python3 -m unittest discover -s engine -t engine -v

測試分四類，對應 01_PYTHON_ENGINE_SPEC.md §9：
  單元 · 屬性（不變式）· 對抗（誘使引擎改壞專名）· 回歸
"""

from __future__ import annotations

import copy
import unittest
from dataclasses import replace

from vtr_py.context import Config, Context
from vtr_py.document import (
    ContractError, Document, Patch, Segment, apply_patches,
)
from vtr_py.gate import ConfidenceGate
from vtr_py.pipeline import (
    InvariantViolation, Pipeline, StageResult, check_invariants,
    preprocessing_pipeline,
)
from vtr_py.protect import check_sentinels, find_candidates, mask, unmask
from vtr_py.stages import LangDetectStage, NormalizeStage, ProtectStage, UnprotectStage
from vtr_py.stages.s1_lang_detect import classify, merge_short_runs, raw_runs
from vtr_py.versioning.replay import ReplayMismatch, replay_to

FIXED_CLOCK = lambda: "2026-08-04T00:00:00Z"  # noqa: E731


def ctx(**overrides) -> Context:
    # 深拷貝：淺拷貝會讓巢狀 dict 共用，一個測試的覆寫會污染其他測試。
    data = copy.deepcopy(Config().data)
    for k, v in overrides.items():
        head, _, tail = k.partition(".")
        node = data.setdefault(head, {})
        node[tail] = v
    return Context(config=Config(data), clock=FIXED_CLOCK)


def doc_of(*texts: str, doc_id: str = "T-0001") -> Document:
    return Document(
        doc_id=doc_id,
        meta={"source": "asr", "primary_lang": "mixed"},
        segments=tuple(Segment(id=f"s{i:05d}", lang="mixed", text=t)
                       for i, t in enumerate(texts)),
    )


def run(doc: Document, *stages, **cfg) -> Document:
    return Pipeline(stages=stages).run(doc, ctx(**cfg))


# --------------------------------------------------------------------------- #
# 1. 資料契約
# --------------------------------------------------------------------------- #

class TestDocument(unittest.TestCase):
    def test_roundtrip_json(self):
        d = doc_of("你好 world", "第二句")
        again = Document.from_json(d.to_json())
        self.assertEqual(again.doc_id, d.doc_id)
        self.assertEqual([s.text for s in again.segments],
                         [s.text for s in d.segments])
        self.assertEqual(again.content_hash, d.content_hash)

    def test_content_hash_tracks_text_only(self):
        d = doc_of("同樣的文字")
        tagged = replace(d, meta={**d.meta, "meeting_title": "改了 meta"})
        self.assertEqual(d.content_hash, tagged.content_hash,
                         "meta 不應影響 content_hash")

    def test_rejects_wrong_schema_version(self):
        payload = doc_of("x").to_dict()
        payload["schema_version"] = "vtr-document/0.9"
        with self.assertRaises(ContractError):
            Document.from_dict(payload)

    def test_apply_patches_rejects_overlap(self):
        seg = Segment(id="s00000", lang="zh", text="abcdef")
        p1 = Patch("p1", "NORMALIZE", "s00000", (0, 3), "abc", "X",
                   "VTR.NORMALIZE.nfkc", "deterministic", 1.0, "auto")
        p2 = Patch("p2", "NORMALIZE", "s00000", (2, 5), "cde", "Y",
                   "VTR.NORMALIZE.nfkc", "deterministic", 1.0, "auto")
        with self.assertRaises(ContractError):
            apply_patches(seg, [p1, p2])

    def test_apply_patches_rejects_stale_before(self):
        seg = Segment(id="s00000", lang="zh", text="abcdef")
        bad = Patch("p1", "NORMALIZE", "s00000", (0, 3), "zzz", "X",
                    "VTR.NORMALIZE.nfkc", "deterministic", 1.0, "auto")
        with self.assertRaises(ContractError):
            apply_patches(seg, [bad])


# --------------------------------------------------------------------------- #
# 2. 信心度閘門
# --------------------------------------------------------------------------- #

class TestConfig(unittest.TestCase):
    def test_default_config_is_not_shared_between_instances(self):
        """回歸：預設設定若是淺拷貝，巢狀 dict 會被所有 Config 共用。

        症狀極難反推：某個測試把 pipeline.strict 打開，之後**所有**測試都變
        strict。library 層必須自己深拷貝，不能依賴呼叫端小心。
        """
        a, b = Config(), Config()
        a.data["pipeline"]["strict"] = True
        self.assertFalse(b.data["pipeline"]["strict"],
                         "另一個 Config 實例不應被污染")
        from vtr_py.context import DEFAULT_CONFIG
        self.assertFalse(DEFAULT_CONFIG["pipeline"]["strict"],
                         "全域預設值不應被污染")


class TestGate(unittest.TestCase):
    def test_bands(self):
        g = ConfidenceGate()
        self.assertEqual(g.decide(0.99), "auto")
        self.assertEqual(g.decide(0.70), "review")
        self.assertEqual(g.decide(0.10), "reject")

    def test_llm_can_never_auto_apply(self):
        """架構 §3 的核心保證：LLM 單獨判斷永遠進人工複核。"""
        g = ConfidenceGate()
        self.assertEqual(g.decide(1.0, "llm_arbiter"), "review")
        self.assertEqual(g.decide(1.0, "model"), "auto")

    def test_rejects_ceiling_that_would_let_llm_through(self):
        with self.assertRaises(ValueError):
            ConfidenceGate(auto_threshold=0.85, llm_only_ceiling=0.90)


# --------------------------------------------------------------------------- #
# 3. 步驟 1：語言偵測
# --------------------------------------------------------------------------- #

class TestLangDetect(unittest.TestCase):
    def test_classify(self):
        self.assertEqual(classify("你"), "cjk")
        self.assertEqual(classify("a"), "latin")
        self.assertEqual(classify("7"), "digit")
        self.assertEqual(classify("，"), "punct")

    def test_mixed_sentence_keeps_english_as_embedded(self):
        """『看一下 dashboard 的 KPI』—— 整句偵測器會判成單一語言並吃掉另一邊。

        token 比為 4:2，未達 0.7 門檻，因此誠實的標籤是 mixed 而非 zh。
        真正要保證的是下面那條：英文詞被標為 embedded，不會進英文文法修復。
        """
        out = run(doc_of("看一下 dashboard 的 KPI"), LangDetectStage())
        seg = out.segments[0]
        self.assertEqual(seg.lang, "mixed")
        embedded = [r for r in seg.runs if r.role == "embedded"]
        self.assertTrue(embedded, "英文詞必須標為 embedded，才不會進英文文法修復")
        self.assertIn("dashboard", "".join(r.slice_of(seg.text) for r in embedded))

    def test_chinese_dominant_sentence_is_zh(self):
        out = run(doc_of("我們下週要把這份報告的結論整理給客戶 review"),
                  LangDetectStage())
        self.assertEqual(out.segments[0].lang, "zh")

    def test_pure_english(self):
        out = run(doc_of("Please review the promotion gate before Friday."),
                  LangDetectStage())
        self.assertEqual(out.segments[0].lang, "en")

    def test_balanced_sentence_is_mixed(self):
        out = run(doc_of("VeritasAutoPlot 的 visual lock 規範"), LangDetectStage())
        self.assertEqual(out.segments[0].lang, "mixed")

    def test_short_runs_merge(self):
        runs = merge_short_runs(raw_runs("VIA的KPI"), min_cjk=2, min_latin=3)
        self.assertLess(len(runs), len(raw_runs("VIA的KPI")))

    def test_lang_detect_emits_no_patches(self):
        out = run(doc_of("測試"), LangDetectStage())
        self.assertEqual(out.revisions[-1].patches_applied, ())


# --------------------------------------------------------------------------- #
# 4. 步驟 2：正規化
# --------------------------------------------------------------------------- #

class TestNormalize(unittest.TestCase):
    def test_does_not_destroy_cjk_punctuation(self):
        """整串 NFKC 會把 ，？！ 拉成 ASCII。這是本步驟最重要的一條護欄。"""
        out = run(doc_of("我們決定，下週交付！對嗎？"),
                  LangDetectStage(), NormalizeStage())
        text = out.segments[0].text
        self.assertIn("，", text)
        self.assertIn("！", text)
        self.assertIn("？", text)
        self.assertNotIn(",", text)

    def test_halfwidth_punct_becomes_fullwidth_in_cjk(self):
        out = run(doc_of("我們決定, 下週交付!"), LangDetectStage(), NormalizeStage())
        self.assertIn("，", out.segments[0].text)
        self.assertIn("！", out.segments[0].text)

    def test_english_punctuation_untouched(self):
        out = run(doc_of("We ship on Friday, then review."),
                  LangDetectStage(), NormalizeStage())
        self.assertEqual(out.segments[0].text, "We ship on Friday, then review.")

    def test_fullwidth_alnum_to_halfwidth(self):
        out = run(doc_of("版本ＶＩＡ０１６２"), LangDetectStage(), NormalizeStage())
        self.assertIn("VIA0162", out.segments[0].text)

    def test_decimal_and_time_not_converted(self):
        out = run(doc_of("透明度是0.75，會議在14:30開始"),
                  LangDetectStage(), NormalizeStage())
        text = out.segments[0].text
        self.assertIn("0.75", text)
        self.assertIn("14:30", text)

    def test_whitespace_between_cjk_removed(self):
        out = run(doc_of("我們  決定 交付"), LangDetectStage(), NormalizeStage())
        self.assertEqual(out.segments[0].text, "我們決定交付")

    def test_cjk_latin_boundary_gets_single_space(self):
        out = run(doc_of("看一下dashboard的資料"), LangDetectStage(), NormalizeStage())
        self.assertEqual(out.segments[0].text, "看一下 dashboard 的資料")

    def test_filler_is_proposed_not_applied(self):
        """語助詞必須進 review 佇列，文字不得被自動改動。"""
        out = run(doc_of("嗯嗯，我們決定交付"), LangDetectStage(), NormalizeStage())
        self.assertIn("嗯", out.segments[0].text)
        queued = [p for p in out.review_queue
                  if p.rule_id == "VTR.NORMALIZE.filler_mark"]
        self.assertTrue(queued, "語助詞應產生 review 級刪除建議")
        self.assertEqual(queued[0].decision, "review")

    def test_demonstrative_not_flagged_as_filler(self):
        """「那個料號」是指示代詞，不是語助詞 —— 誤刪會改變語意。"""
        out = run(doc_of("那個料號要確認"), LangDetectStage(), NormalizeStage())
        queued = [p for p in out.review_queue
                  if p.rule_id == "VTR.NORMALIZE.filler_mark"]
        self.assertEqual(queued, [])

    def test_opencc_absence_is_recorded_not_silent(self):
        out = run(doc_of("測試"), NormalizeStage())
        metrics = out.revisions[-1].metrics
        self.assertIn("opencc_available", metrics)
        if not metrics["opencc_available"]:
            self.assertTrue(metrics.get("degraded"),
                            "降級必須出現在 metrics，不得靜默跳過")

    def test_injected_converter_produces_patches(self):
        """簡繁轉換走 difflib hunk 路徑；以注入轉換器驗證，不需安裝 opencc。"""
        stage = NormalizeStage(converter=lambda s: s.replace("软件", "軟體"))
        out = run(doc_of("这个软件很好"), stage)
        self.assertIn("軟體", out.segments[0].text)
        rules = {p.rule_id for r in out.revisions for p in r.patches_applied}
        self.assertIn("VTR.NORMALIZE.opencc_s2twp", rules)

    def test_patches_are_disjoint(self):
        out = run(doc_of("嗯，  看一下dashboard的ＫＰＩ!"),
                  LangDetectStage(), NormalizeStage())
        spans = sorted(p.span for r in out.revisions for p in r.patches_applied)
        for (a_start, a_end), (b_start, _) in zip(spans, spans[1:]):
            self.assertLessEqual(a_end, b_start, "同一 Stage 的 patch 不得重疊")

    def test_idempotent(self):
        once = run(doc_of("我們決定, 下週交付ＫＰＩ"),
                   LangDetectStage(), NormalizeStage())
        twice = run(doc_of(once.segments[0].text),
                    LangDetectStage(), NormalizeStage())
        self.assertEqual(once.segments[0].text, twice.segments[0].text)


# --------------------------------------------------------------------------- #
# 5. P0 遮罩
# --------------------------------------------------------------------------- #

class TestProtect(unittest.TestCase):
    def test_finds_part_numbers_and_camelcase(self):
        text = "請確認 VIA-0162B 與 VeritasAutoPlot 的狀態"
        kinds = ["part_number", "code_ident", "url", "email",
                 "timestamp", "number_unit"]
        found = {c.kind for c in find_candidates(text, kinds)}
        self.assertIn("part_number", found)
        self.assertIn("code_ident", found)

    def test_mask_unmask_roundtrip(self):
        """屬性測試：unprotect(protect(x)) == x。"""
        original = "請在 14:30 前把 VIA-0162B 的圖表寄到 tony@example.com"
        d = doc_of(original)
        masked = run(d, ProtectStage())
        self.assertNotEqual(masked.segments[0].text, original)
        restored = Pipeline(stages=(UnprotectStage(),)).run(masked, ctx())
        self.assertEqual(restored.segments[0].text, original)

    def test_unknown_part_number_flagged_not_guessed(self):
        out = run(doc_of("料號 A7X-2201 要複查"), ProtectStage())
        self.assertIn("unresolved_entity", out.segments[0].flags)

    def test_sentinel_integrity_detects_tampering(self):
        masked = run(doc_of("版本 v0162B 已鎖定"), ProtectStage())
        seg = masked.segments[0]
        broken = replace(seg, text=seg.text.replace("⟦P0001⟧", "v0162 B"))
        violations = check_sentinels([broken])
        self.assertTrue(violations)
        self.assertIn("⟦P0001⟧", violations[0].missing)


# --------------------------------------------------------------------------- #
# 6. Pipeline 不變式
# --------------------------------------------------------------------------- #

class _BadStage:
    """故意違反不變式的 Stage，用來證明檢查不是空轉。"""

    name = "NORMALIZE"

    def __init__(self, mode: str) -> None:
        self.mode = mode

    def apply(self, doc, context):
        seg = doc.segments[0]
        if self.mode == "drop_segment":
            return StageResult(doc=replace(doc, segments=doc.segments[1:]))
        if self.mode == "break_sentinel":
            broken = replace(seg, text=seg.text.replace("⟦P0001⟧", "壞掉"))
            return StageResult(doc=replace(doc, segments=(broken,) + doc.segments[1:]))
        if self.mode == "unknown_rule":
            p = Patch("p000-0001", "NORMALIZE", seg.id, (0, 1), seg.text[0], "X",
                      "VTR.NORMALIZE.not_registered", "deterministic", 1.0, "auto")
            return StageResult(doc=doc, patches=(p,))
        if self.mode == "bad_span":
            p = Patch("p000-0001", "NORMALIZE", seg.id, (0, 999), "亂", "X",
                      "VTR.NORMALIZE.nfkc", "deterministic", 1.0, "auto")
            return StageResult(doc=doc, patches=(p,))
        raise AssertionError(self.mode)


class TestInvariants(unittest.TestCase):
    def test_segment_count_change_is_caught(self):
        d = doc_of("第一句", "第二句")
        problems = check_invariants(
            d, _BadStage("drop_segment").apply(d, ctx()), "NORMALIZE")
        self.assertTrue(any("segment 數量" in p for p in problems))

    def test_sentinel_damage_is_caught(self):
        masked = run(doc_of("版本 v0162B 已鎖定"), ProtectStage())
        problems = check_invariants(
            masked, _BadStage("break_sentinel").apply(masked, ctx()), "NORMALIZE")
        self.assertTrue(any("sentinel" in p for p in problems))

    def test_unregistered_rule_is_caught(self):
        d = doc_of("測試")
        problems = check_invariants(
            d, _BadStage("unknown_rule").apply(d, ctx()), "NORMALIZE")
        self.assertTrue(any("未註冊" in p for p in problems))

    def test_bad_span_is_caught(self):
        d = doc_of("測試")
        problems = check_invariants(
            d, _BadStage("bad_span").apply(d, ctx()), "NORMALIZE")
        self.assertTrue(any("span" in p for p in problems))

    def test_violation_rolls_back_whole_stage(self):
        """違反不變式時整個 Stage 的 patch 都不套用，且 revision 留下紀錄。"""
        masked = run(doc_of("版本 v0162B 已鎖定"), ProtectStage())
        before_text = masked.segments[0].text
        after = Pipeline(stages=(_BadStage("break_sentinel"),)).run(masked, ctx())
        self.assertEqual(after.segments[0].text, before_text, "內容必須完全不動")
        self.assertTrue(after.revisions[-1].metrics.get("stage_rolled_back"))

    def test_strict_mode_raises(self):
        masked = run(doc_of("版本 v0162B 已鎖定"), ProtectStage())
        with self.assertRaises(InvariantViolation):
            Pipeline(stages=(_BadStage("break_sentinel"),)).run(
                masked, ctx(**{"pipeline.strict": True}))


# --------------------------------------------------------------------------- #
# 7. 對抗測試：誘使引擎改壞專名
# --------------------------------------------------------------------------- #

class TestAdversarial(unittest.TestCase):
    CASES = (
        "料號 A7X-2201 的透明度是 0.75",
        "VeritasAutoPlot 在 v0162B 已鎖定, 請看 https://example.com/spec",
        "請於 14:30 前回覆 tony@example.com，KPI 是 95%",
        "看一下dashboard的ＫＰＩ, 嗯，那個 VIA-0162B 要確認",
    )

    def test_protected_content_survives_full_preprocessing(self):
        """遮罩區的內容在還原後必須逐字不變 —— 這是引擎的頭號安全性質。"""
        for raw in self.CASES:
            with self.subTest(raw=raw):
                out = preprocessing_pipeline().run(doc_of(raw), ctx())
                restored = Pipeline(stages=(UnprotectStage(),)).run(out, ctx())
                text = restored.segments[0].text
                for prot in out.segments[0].protections:
                    self.assertIn(prot.surface, text,
                                  f"{prot.surface!r} 在還原後遺失或被改動")

    def test_no_stage_was_rolled_back(self):
        for raw in self.CASES:
            with self.subTest(raw=raw):
                out = preprocessing_pipeline().run(doc_of(raw), ctx())
                rolled = [r.stage for r in out.revisions
                          if r.metrics.get("stage_rolled_back")]
                self.assertEqual(rolled, [], f"不應有 Stage 被回退：{rolled}")


# --------------------------------------------------------------------------- #
# 8. Diff & Versioning
# --------------------------------------------------------------------------- #

class TestReplay(unittest.TestCase):
    def test_replay_to_latest_reproduces_document(self):
        out = preprocessing_pipeline().run(
            doc_of("我們決定, 下週交付 VIA-0162B"), ctx())
        again = replay_to(out, out.rev)
        self.assertEqual(again.content_hash, out.content_hash)
        self.assertEqual([s.text for s in again.segments],
                         [s.text for s in out.segments])

    def test_replay_to_earlier_rev_matches_recorded_hash(self):
        out = preprocessing_pipeline().run(
            doc_of("我們決定, 下週交付 VIA-0162B"), ctx())
        target = out.revisions[1]
        rolled = replay_to(out, target.rev)
        self.assertEqual(rolled.content_hash, target.content_hash)
        self.assertEqual(rolled.rev, target.rev)

    def test_replay_reconstructs_original_input_exactly(self):
        """回歸：反向重播曾多加一個累積位移，導致同一 segment 的第二筆之後全部錯位。

        單筆 patch 的 segment 不會暴露這個 bug —— 必須是「一句話裡多個遮罩」
        才會現形，這正是真實會議紀錄的常態。
        """
        raw = "VeritasAutoPlot 在 v0162B 已鎖定, 請在 14:30 前回覆 tony@example.com"
        out = preprocessing_pipeline().run(doc_of(raw), ctx())
        self.assertGreaterEqual(len(out.segments[0].protections), 4,
                                "本測試需要多筆遮罩才有意義")
        back = replay_to(out, 0)
        self.assertEqual(back.segments[0].text, raw)

    def test_content_hash_ignores_derived_annotations(self):
        """回歸：lang 是衍生標註，不得算進 content_hash。

        LANG_DETECT 只改標註、不產生 patch。若標註進了雜湊，patch 重播就
        永遠重建不出當初記錄的雜湊值，整條 Diff & Versioning 失效。
        """
        d = doc_of("Please confirm the promotion gate before Friday.")
        annotated = run(d, LangDetectStage())
        self.assertEqual(d.segments[0].lang, "mixed")
        self.assertEqual(annotated.segments[0].lang, "en")   # 標註確實變了
        self.assertEqual(d.content_hash, annotated.content_hash)  # 雜湊不受影響

    def test_replayed_annotations_are_recomputed(self):
        """重播後的標註必須與當下文字一致，而不是沿用舊值。"""
        out = preprocessing_pipeline().run(
            doc_of("我們決定, 下週交付 VIA-0162B"), ctx())
        back = replay_to(out, 0)
        self.assertTrue(back.segments[0].runs, "重播後應重算 run")

    def test_tampered_hash_is_detected(self):
        out = preprocessing_pipeline().run(doc_of("測試 VIA-0162B"), ctx())
        tampered = replace(
            out,
            revisions=out.revisions[:-1] + (
                replace(out.revisions[-1], content_hash="0" * 64),),
        )
        with self.assertRaises(ReplayMismatch):
            replay_to(tampered, tampered.rev)


# --------------------------------------------------------------------------- #
# 9. 端到端
# --------------------------------------------------------------------------- #

class TestEndToEnd(unittest.TestCase):
    def test_preprocessing_pipeline_shape(self):
        out = preprocessing_pipeline().run(
            doc_of("嗯，看一下dashboard的ＫＰＩ, VIA-0162B 要在 14:30 前確認"), ctx())
        self.assertEqual([r.stage for r in out.revisions],
                         ["LANG_DETECT", "NORMALIZE", "PROTECT", "LANG_DETECT"])
        self.assertEqual(out.rev, 3)
        self.assertTrue(out.segments[0].runs, "最後一步必須重算 run 座標")
        self.assertTrue(out.review_queue, "語助詞應留在待裁決佇列")

    def test_every_applied_patch_is_explainable(self):
        out = preprocessing_pipeline().run(
            doc_of("嗯，看一下dashboard的ＫＰＩ, VIA-0162B"), ctx())
        for rev in out.revisions:
            for p in rev.patches_applied:
                self.assertTrue(p.rule_id, "每筆改動都要有 rule_id")
                self.assertTrue(p.evidence, "每筆改動都要有可讀的 evidence")
                self.assertIn(p.decision, ("auto",))


if __name__ == "__main__":
    unittest.main(verbosity=2)
