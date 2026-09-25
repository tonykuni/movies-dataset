#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# VIA_CGE_AdaptiveInterface  v0500  (only-increase add-on to VIA_CentralGovernanceEngine v0400)
# AIR = Adaptive Interface Registry
#   1) Dynamic schema inference by AST (Pydantic BaseModel / dataclass / TypedDict / NamedTuple /
#      typed public functions / explicit VIA_INTERFACE manifest). Modules are NEVER imported
#      (no side effects, no pydantic dependency).
#   2) Plug-and-play registration: blake2s contract fingerprint, semver auto-bump, admission gates.
#   3) Adaptive contract drift: rename detection = NORM (case/separator) > SYN (CGE governance_vocab
#      + builtin seeds) > FUZZY (difflib); AUTO>=0.90 adapter map, ASK>=0.75 review queue.
#      Breaking changes are HELD (old version stays current) until --accept-breaking or confirmation.
#   4) Append-only: registry never removes (MISSING/RELISTED), hash-chained ledger, adapters chain
#      so old payloads replay into the current contract.
# Python CLI default = dry-run; --commit persists.
import argparse, ast, datetime, difflib, hashlib, html, json, os, re, shutil, sys, tempfile, unicodedata

VERSION = "0500"
ENGINE = "VIA_CGE_AdaptiveInterface"
SCHEMA = "VIA_CGE_AIR/1.0"
VIA_INTERFACE = {
    "name": "adapt_payload",
    "inputs": {"iface_id": "str", "payload": "dict", "from_ver": "str"},
    "outputs": {"return": "dict"},
}
OUTF = {
    "registry": "cge_interface_registry.json",
    "ledger": "cge_interface_ledger.jsonl",
    "adapters": "cge_contract_adapters.json",
    "pending": "cge_interface_pending.json",
    "report": "cge_adaptive_report.json",
    "state": "cge_adaptive_state.json",
    "html": "VIA_CGE_Adaptive.html",
    "confirm": "iface_confirmations.jsonl",
}
PRUNE = {".git", "__pycache__", ".venv", "venv", "env", "site-packages", "node_modules", "dist",
         "build", ".mypy_cache", ".pytest_cache", "Lib", "Scripts", "_to_delete", ".idea", ".vscode",
         ".tox", "wheels", "_air_selftest"}
PYD_BASES = {"BaseModel", "BaseSettings", "RootModel", "SQLModel"}
AUTO_T, ASK_T = 0.90, 0.75
MAX_BYTES = 2 * 1024 * 1024
BUILTIN_SYN = {
    "ticker": ["symbol", "stock_id", "stock_code", "sec_id", "證券代號", "股票代號", "代號"],
    "trade_date": ["date", "dt", "as_of", "asof_date", "日期", "交易日期", "資料日期"],
    "close": ["close_price", "closing_price", "收盤價", "px_last"],
    "open": ["open_price", "開盤價"],
    "high": ["high_price", "最高價"],
    "low": ["low_price", "最低價"],
    "volume": ["vol", "trade_volume", "成交量", "成交股數"],
    "turnover": ["trade_value", "amount", "成交金額"],
    "security_name": ["stock_name", "證券名稱", "公司名稱"],
    "market": ["exchange", "市場別", "上市櫃"],
}
TYPING_MAP = {"List": "list", "Dict": "dict", "Tuple": "tuple", "Set": "set",
              "FrozenSet": "frozenset", "Type": "type", "Text": "str", "Sequence": "sequence",
              "Mapping": "mapping"}


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def bhash(s):
    return hashlib.blake2s(s.encode("utf-8"), digest_size=16).hexdigest()


def jdump(o):
    return json.dumps(o, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def read_json(p, default):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return default


def write_text(p, s):
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)
    os.replace(tmp, p)


_QUIET = [False]


def log(msg, force=False):
    if force or not _QUIET[0]:
        print(msg, flush=True)


# ---------------------------------------------------------------- naming / synonyms
def norm(s):
    s = unicodedata.normalize("NFKC", str(s)).lstrip("*")
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)
    s = re.sub(r"[\s\-\./]+", "_", s)
    return s.lower().strip("_")


def load_synonyms(path):
    idx = {}
    for canon, terms in BUILTIN_SYN.items():
        for t in [canon] + terms:
            idx.setdefault(norm(t), canon)
    src = "builtin(%d)" % len(idx)
    if not path or not os.path.isfile(path):
        return idx, src
    data = read_json(path, None)
    added = [0]

    def take(cid, syns):
        items = list(syns.keys()) if isinstance(syns, dict) else list(syns)
        for s in items:
            term, status = None, None
            if isinstance(s, str):
                term = s
            elif isinstance(s, dict):
                term = s.get("text") or s.get("term") or s.get("value") or s.get("synonym")
                status = s.get("status")
            if not isinstance(term, str) or status in ("REJECTED", "QUARANTINE"):
                continue
            k = norm(term)
            if len(k) >= 2 and k not in idx:
                idx[k] = cid
                added[0] += 1
        if norm(cid) not in idx:
            idx[norm(cid)] = cid

    def walk(o, hint=None):
        if isinstance(o, dict):
            cid = o.get("canonical") or o.get("canonical_id") or o.get("id") or o.get("code") or hint
            syns = o.get("synonyms") or o.get("aliases") or o.get("variants")
            if isinstance(cid, str) and isinstance(syns, (list, dict)):
                take(cid, syns)
            for k, v in o.items():
                walk(v, k if isinstance(v, dict) else None)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(data)
    return idx, "%s + %s(+%d)" % (src, os.path.basename(path), added[0])


# ---------------------------------------------------------------- AST schema inference
def _base_name(n):
    if isinstance(n, ast.Name):
        return n.id
    if isinstance(n, ast.Attribute):
        return n.attr
    if isinstance(n, ast.Call):
        return _base_name(n.func)
    return ""


def _members(node):
    if node is None:
        return ["?"]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return _members(node.left) + _members(node.right)
    if isinstance(node, ast.Subscript):
        b = _base_name(node.value)
        sl = node.slice
        if b == "Optional":
            return _members(sl) + ["None"]
        if b == "Union":
            out = []
            for e in (sl.elts if isinstance(sl, ast.Tuple) else [sl]):
                out.extend(_members(e))
            return out
        if b == "Annotated":
            return _members(sl.elts[0] if isinstance(sl, ast.Tuple) else sl)
        if b in ("Required", "NotRequired", "ReadOnly", "Final"):
            return _members(sl)
    if isinstance(node, ast.Constant):
        if node.value is None:
            return ["None"]
        if isinstance(node.value, str):
            try:
                return _members(ast.parse(node.value, mode="eval").body)
            except SyntaxError:
                return [node.value]
    s = ast.unparse(node)
    s = re.sub(r"\btyping\.", "", s)
    for k, v in TYPING_MAP.items():
        s = re.sub(r"\b%s\b" % k, v, s)
    return [s.replace(" ", "")]


def type_str(node):
    return "|".join(sorted(set(_members(node)), key=lambda x: (x == "None", x)))


def type_str_text(s):
    try:
        return type_str(ast.parse(str(s), mode="eval").body)
    except SyntaxError:
        return str(s)


def _is_ellipsis(n):
    return isinstance(n, ast.Constant) and n.value is Ellipsis


def class_fields(cls, kind):
    total = True
    for kw in cls.keywords:
        if kw.arg == "total" and isinstance(kw.value, ast.Constant):
            total = bool(kw.value.value)
    out = []
    for st in cls.body:
        if not (isinstance(st, ast.AnnAssign) and isinstance(st.target, ast.Name)):
            continue
        name = st.target.id
        if name.startswith("_") or name == "model_config":
            continue
        ann = st.annotation
        wrap = _base_name(ann.value) if isinstance(ann, ast.Subscript) else _base_name(ann)
        if wrap == "ClassVar":
            continue
        alias = None
        v = st.value
        required = v is None
        if isinstance(v, ast.Call) and _base_name(v.func) in ("Field", "field"):
            has_default = any(k.arg in ("default", "default_factory") for k in v.keywords)
            if v.args:
                has_default = not _is_ellipsis(v.args[0])
            for k in v.keywords:
                if k.arg == "default" and _is_ellipsis(k.value):
                    has_default = False
                if k.arg in ("alias", "validation_alias") and isinstance(k.value, ast.Constant) \
                        and isinstance(k.value.value, str):
                    alias = k.value.value
            required = not has_default
        if kind == "typeddict":
            required = total
            if wrap == "NotRequired":
                required = False
            if wrap == "Required":
                required = True
        f = {"name": name, "type": type_str(ann), "required": bool(required)}
        if alias:
            f["alias"] = alias
        out.append(f)
    return out


def func_contract(fn):
    a = fn.args
    params = a.posonlyargs + a.args
    defaults = [None] * (len(params) - len(a.defaults)) + list(a.defaults)
    ins = []
    for p, d in zip(params, defaults):
        if p.arg in ("self", "cls"):
            continue
        ins.append({"name": p.arg, "type": type_str(p.annotation), "required": d is None})
    for p, d in zip(a.kwonlyargs, a.kw_defaults):
        ins.append({"name": p.arg, "type": type_str(p.annotation), "required": d is None})
    if a.vararg:
        ins.append({"name": "*" + a.vararg.arg, "type": type_str(a.vararg.annotation), "required": False})
    if a.kwarg:
        ins.append({"name": "**" + a.kwarg.arg, "type": type_str(a.kwarg.annotation), "required": False})
    outs = [{"name": "return", "type": type_str(fn.returns), "required": True}]
    annotated = fn.returns is not None or any(p.annotation is not None for p in params + a.kwonlyargs)
    return ins, outs, annotated


def _decl_fields(spec):
    out = []
    if isinstance(spec, dict):
        for k, v in spec.items():
            if isinstance(v, dict):
                out.append({"name": str(k), "type": type_str_text(v.get("type", "?")),
                            "required": bool(v.get("required", True))})
            else:
                out.append({"name": str(k), "type": type_str_text(v), "required": True})
    elif isinstance(spec, list):
        for v in spec:
            if isinstance(v, dict) and "name" in v:
                out.append({"name": str(v["name"]), "type": type_str_text(v.get("type", "?")),
                            "required": bool(v.get("required", True))})
    return out


def contract_fp(c):
    core = {s: sorted([[f["name"], f["type"], f["required"]] for f in c.get(s, [])]) for s in ("inputs", "outputs")}
    return bhash(jdump(core))


def extract(tree):
    found = []
    classes = {}
    for st in tree.body:
        if isinstance(st, ast.Assign) and any(isinstance(t, ast.Name) and t.id in ("VIA_INTERFACE", "__via_interface__")
                                               for t in st.targets):
            try:
                val = ast.literal_eval(st.value)
            except Exception:
                continue
            for d in (val if isinstance(val, list) else [val]):
                if isinstance(d, dict):
                    found.append({"name": str(d.get("name", "module")), "kind": "declared", "grade": "V",
                                  "contract": {"inputs": _decl_fields(d.get("inputs", {})),
                                               "outputs": _decl_fields(d.get("outputs", {}))}})
        elif isinstance(st, ast.ClassDef):
            bases = {_base_name(b) for b in st.bases}
            decos = {_base_name(d) for d in st.decorator_list}
            kind = None
            parents = [classes[b] for b in bases if b in classes]
            if bases & PYD_BASES:
                kind = "pydantic"
            elif "TypedDict" in bases:
                kind = "typeddict"
            elif "NamedTuple" in bases:
                kind = "namedtuple"
            elif "dataclass" in decos or "define" in decos or "attrs" in decos:
                kind = "dataclass"
            elif parents:
                kind = parents[0]["kind"]
            if not kind:
                continue
            merged = {}
            for p in parents:
                for f in p["contract"]["inputs"]:
                    merged[f["name"]] = f
            for f in class_fields(st, kind):
                merged[f["name"]] = f
            rec = {"name": st.name, "kind": kind, "grade": "M",
                   "contract": {"inputs": list(merged.values()), "outputs": []}}
            classes[st.name] = rec
            if not st.name.startswith("_"):
                found.append(rec)
        elif isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if st.name.startswith("_") or "overload" in {_base_name(d) for d in st.decorator_list}:
                continue
            ins, outs, annotated = func_contract(st)
            if annotated:
                found.append({"name": st.name, "kind": "function", "grade": "M",
                              "contract": {"inputs": ins, "outputs": outs}})
    return found


def scan(roots, max_files):
    found, errors, dups, scanned = {}, [], [], []
    nfiles = 0
    for root in roots:
        root = os.path.abspath(root)
        if not os.path.isdir(root):
            log("  [WARN] scan root not found: %s" % root)
            continue
        scanned.append(root)
        for dp, dns, fns in os.walk(root):
            dns[:] = sorted(d for d in dns if d not in PRUNE and not d.startswith("."))
            for fn in sorted(fns):
                if not fn.endswith(".py"):
                    continue
                p = os.path.join(dp, fn)
                try:
                    if os.path.getsize(p) > MAX_BYTES:
                        continue
                    with open(p, "rb") as fh:
                        raw = fh.read()
                    tree = ast.parse(raw.decode("utf-8-sig", errors="replace"), filename=p)
                except (SyntaxError, ValueError, OSError) as e:
                    errors.append({"file": p, "error": "%s: %s" % (type(e).__name__, str(e)[:160])})
                    continue
                nfiles += 1
                if nfiles % 250 == 0:
                    log("  ... parsed %d files" % nfiles)
                rel = os.path.relpath(p, root).replace("\\", "/")[:-3]
                for it in extract(tree):
                    iid = "%s::%s" % (rel, it["name"])
                    it.update({"id": iid, "file": p, "root": root, "module": rel,
                               "fp": contract_fp(it["contract"])})
                    if iid in found and found[iid]["file"] != p:
                        dups.append({"id": iid, "file": p, "first": found[iid]["file"]})
                    else:
                        found[iid] = it  # same-file redefinition: last definition wins (Python semantics)
                if max_files and nfiles >= max_files:
                    log("  [WARN] max-files %d reached" % max_files)
                    return found, errors, dups, nfiles, scanned
    return found, errors, dups, nfiles, scanned


# ---------------------------------------------------------------- drift / adaptive contracts
def similarity(a, b, syn):
    na, nb = norm(a), norm(b)
    if na == nb:
        return 1.0, "NORM"
    ca, cb = syn.get(na), syn.get(nb)
    if ca and ca == cb:
        return 0.97, "SYN"
    r = difflib.SequenceMatcher(None, na, nb).ratio()
    ta, tb = set(na.split("_")), set(nb.split("_"))
    j = len(ta & tb) / len(ta | tb) if (ta | tb) else 0.0
    return max(r, j * 0.95), "FUZZY"


def _tset(t):
    return set(t.split("|"))


def type_change(side, old, new):
    if old == new:
        return None
    o, n = _tset(old), _tset(new)
    if "?" in o or "?" in n or "Any" in n and side == "inputs":
        return "COMPAT"
    if side == "inputs":
        return "COMPAT" if o <= n else "BREAKING"
    return "COMPAT" if n <= o else "BREAKING"


def diff_contract(old, new, syn):
    changes = []
    for side in ("inputs", "outputs"):
        o = {f["name"]: f for f in old.get(side, [])}
        n = {f["name"]: f for f in new.get(side, [])}
        removed = [k for k in o if k not in n]
        added = [k for k in n if k not in o]
        pairs = []
        for r in removed:
            for a in added:
                sc, via = similarity(r, a, syn)
                if not (_tset(o[r]["type"]) & _tset(n[a]["type"])) and "?" not in (o[r]["type"] + n[a]["type"]):
                    sc *= 0.8
                pairs.append((round(sc, 4), r, a, via))
        pairs.sort(key=lambda x: (-x[0], x[1], x[2]))
        ur, ua = set(), set()
        for sc, r, a, via in pairs:
            if r in ur or a in ua or sc < ASK_T:
                continue
            ur.add(r)
            ua.add(a)
            tier = "AUTO" if sc >= AUTO_T else "ASK"
            sev = "COMPAT" if tier == "AUTO" else "REVIEW"
            if side == "inputs" and n[a]["required"] and not o[r]["required"]:
                sev = "BREAKING"
            changes.append({"side": side, "op": "RENAME", "old": r, "new": a, "score": sc,
                            "tier": tier, "via": via, "severity": sev})
        for r in removed:
            if r not in ur:
                changes.append({"side": side, "op": "REMOVE", "old": r, "severity": "BREAKING"})
        for a in added:
            if a in ua:
                continue
            if side == "inputs" and n[a]["required"]:
                changes.append({"side": side, "op": "ADD_REQUIRED", "new": a, "severity": "BREAKING"})
            else:
                changes.append({"side": side, "op": "ADD_OPTIONAL", "new": a, "severity": "COMPAT"})
        for k in o:
            if k not in n:
                continue
            tc = type_change(side, o[k]["type"], n[k]["type"])
            if tc:
                changes.append({"side": side, "op": "TYPE", "old": k, "from": o[k]["type"],
                                "to": n[k]["type"], "severity": tc})
            if side == "inputs" and o[k]["required"] != n[k]["required"]:
                changes.append({"side": side, "op": "REQUIRED" if n[k]["required"] else "OPTIONALIZED",
                                "old": k, "severity": "BREAKING" if n[k]["required"] else "COMPAT"})
    return changes


def vtuple(v):
    try:
        return tuple(int(x) for x in v.split("."))
    except Exception:
        return (0, 0, 0)


def bump_ver(v, kind):
    a, b, c = vtuple(v)
    if kind == "major":
        return "%d.0.0" % (a + 1)
    if kind == "minor":
        return "%d.%d.0" % (a, b + 1)
    return "%d.%d.%d" % (a, b, c + 1)


def adapt_payload(adapters, iface_id, payload, from_ver):
    chain = adapters.get("interfaces", {}).get(iface_id, {}).get("chain", [])
    out = dict(payload)
    trace = []
    for step in sorted(chain, key=lambda s: (vtuple(s["from"]), vtuple(s["to"]))):
        if vtuple(step["from"]) < vtuple(from_ver):
            continue
        for side in ("inputs", "outputs"):
            for old, new in step.get(side, {}).items():
                if old in out and new not in out:
                    out[new] = out.pop(old)
                    trace.append("%s->%s (%s %s->%s)" % (old, new, step.get("via"), step["from"], step["to"]))
    return out, trace


# ---------------------------------------------------------------- ledger
def ledger_tail(path):
    last = "GENESIS"
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        last = json.loads(line).get("hash", last)
                    except Exception:
                        pass
    return last


def ledger_append(path, events):
    prev = ledger_tail(path)
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        for e in events:
            e = dict(e)
            e["prev"] = prev
            e["hash"] = bhash(prev + jdump({k: v for k, v in e.items() if k != "hash"}))
            prev = e["hash"]
            f.write(jdump(e) + "\n")


def ledger_verify(path):
    if not os.path.isfile(path):
        return True, 0, ""
    prev = "GENESIS"
    n = 0
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except Exception:
                return False, n, "line %d not JSON" % i
            h = e.get("hash")
            if e.get("prev") != prev or bhash(prev + jdump({k: v for k, v in e.items() if k != "hash"})) != h:
                return False, n, "chain break at line %d" % i
            prev = h
            n += 1
    return True, n, ""


# ---------------------------------------------------------------- confirmations
def read_confirmations(path, consumed):
    out = []
    if not path or not os.path.isfile(path):
        return out
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            h = bhash(s)
            if h in consumed:
                continue
            key, dec = None, None
            if s.startswith("==CGE-CONFIRM=="):
                parts = s.split(None, 3)
                if len(parts) == 4 and parts[1] == "AIR":
                    dec, key = parts[2].upper(), parts[3]
            elif s.startswith("{"):
                try:
                    d = json.loads(s)
                    key, dec = d.get("air_key"), str(d.get("decision", "")).upper()
                except Exception:
                    pass
            if key and dec in ("ACCEPT", "REJECT"):
                out.append((h, key, dec))
    return out


# ---------------------------------------------------------------- governance run
def govern(args):
    root = os.path.abspath(args.root)
    os.makedirs(root, exist_ok=True)
    P = {k: os.path.join(root, v) for k, v in OUTF.items()}
    ts = now()
    reg = read_json(P["registry"], None) or {"schema": SCHEMA, "interfaces": {}}
    adapters = read_json(P["adapters"], None) or {"schema": SCHEMA, "interfaces": {}}
    pending = read_json(P["pending"], None) or {"schema": SCHEMA, "items": {}, "consumed": []}
    vocab = args.vocab or os.path.join(root, "governance_vocab.json")
    syn, syn_src = load_synonyms(vocab)
    events, run_changes = [], []
    log("[AIR %s] root=%s  synonyms=%s  mode=%s" % (VERSION, root, syn_src, "COMMIT" if args.commit else "DRY-RUN"))

    # confirmations (auto-eat workdir file + explicit)
    accepted_hold = set()
    consumed = set(pending.get("consumed", []))
    conf = []
    for cp in [P["confirm"]] + ([args.confirm] if args.confirm else []):
        conf += read_confirmations(cp, consumed)
    for h, key, dec in conf:
        consumed.add(h)
        item = pending["items"].get(key)
        if not item or item.get("status") != "OPEN":
            continue
        item["status"] = "ACCEPTED" if dec == "ACCEPT" else "REJECTED"
        item["decided"] = ts
        events.append({"ts": ts, "event": "CONFIRM_" + item["status"], "iface": item["iface"], "key": key})
        if dec == "ACCEPT" and item["type"] == "RENAME_ASK":
            ch = adapters["interfaces"].setdefault(item["iface"], {"chain": []})["chain"]
            ch.append({"from": item["from"], "to": item["to"], item["side"]: {item["old"]: item["new"]},
                       "via": "HUMAN", "grade": "V", "ts": ts})
        if dec == "ACCEPT" and item["type"] == "HELD_BREAKING":
            accepted_hold.add((item["iface"], item["fp"]))
    pending["consumed"] = sorted(consumed)
    if conf:
        log("  confirmations applied: %d" % len(conf))

    roots = args.scan or [root]
    found, errors, dups, nfiles, scanned = scan(roots, args.max_files)
    log("  parsed %d .py files, %d interfaces, %d parse errors" % (nfiles, len(found), len(errors)))

    cnt = {"REGISTER": 0, "VERSION": 0, "HELD": 0, "MISSING": 0, "RELISTED": 0, "UNCHANGED": 0}
    for iid in sorted(found):
        it = found[iid]
        rec = reg["interfaces"].get(iid)
        if rec is None:
            reg["interfaces"][iid] = {
                "id": iid, "kind": it["kind"], "grade": it["grade"], "module": it["module"],
                "file": it["file"], "root": it["root"], "status": "ACTIVE", "drift": "NONE",
                "first_seen": ts, "last_seen": ts,
                "versions": [{"ver": "1.0.0", "fp": it["fp"], "contract": it["contract"], "ts": ts,
                              "bump": "init", "changes": []}]}
            events.append({"ts": ts, "event": "REGISTER", "iface": iid, "ver": "1.0.0", "fp": it["fp"]})
            run_changes.append({"iface": iid, "result": "REGISTER", "ver": "1.0.0", "changes": []})
            cnt["REGISTER"] += 1
            continue
        rec["last_seen"] = ts
        rec["file"] = it["file"]
        if rec["status"] != "ACTIVE":
            rec["status"] = "ACTIVE"
            events.append({"ts": ts, "event": "RELISTED", "iface": iid})
            cnt["RELISTED"] += 1
        cur = rec["versions"][-1]
        if cur["fp"] == it["fp"]:
            rec["drift"] = "NONE"
            cnt["UNCHANGED"] += 1
            continue
        ch = diff_contract(cur["contract"], it["contract"], syn)
        sev = {c["severity"] for c in ch}
        bump = "major" if "BREAKING" in sev else ("minor" if sev else "patch")
        if bump == "major" and not args.accept_breaking and (iid, it["fp"]) not in accepted_hold:
            key = "HOLD|%s|%s" % (iid, it["fp"])
            if key not in pending["items"]:
                pending["items"][key] = {"type": "HELD_BREAKING", "iface": iid, "from": cur["ver"],
                                         "fp": it["fp"], "changes": ch, "status": "OPEN", "ts": ts}
                events.append({"ts": ts, "event": "HELD_BREAKING", "iface": iid, "from": cur["ver"], "fp": it["fp"]})
            rec["drift"] = "HELD"
            run_changes.append({"iface": iid, "result": "HELD", "ver": cur["ver"], "changes": ch})
            cnt["HELD"] += 1
            continue
        newver = bump_ver(cur["ver"], bump)
        rec["versions"].append({"ver": newver, "fp": it["fp"], "contract": it["contract"], "ts": ts,
                                "bump": bump, "changes": ch})
        rec["drift"] = "NONE"
        step = {"from": cur["ver"], "to": newver, "via": "AUTO", "grade": "M", "ts": ts}
        for c in ch:
            if c["op"] == "RENAME" and c["tier"] == "AUTO":
                step.setdefault(c["side"], {})[c["old"]] = c["new"]
            if c["op"] == "RENAME" and c["tier"] == "ASK":
                key = "REN|%s|%s|%s|%s" % (iid, c["side"], c["old"], c["new"])
                if key not in pending["items"]:
                    pending["items"][key] = {"type": "RENAME_ASK", "iface": iid, "side": c["side"],
                                             "old": c["old"], "new": c["new"], "score": c["score"],
                                             "from": cur["ver"], "to": newver, "status": "OPEN", "ts": ts}
        if "inputs" in step or "outputs" in step:
            adapters["interfaces"].setdefault(iid, {"chain": []})["chain"].append(step)
        for k, item in pending["items"].items():
            if item["type"] == "HELD_BREAKING" and item["iface"] == iid and item["status"] == "OPEN":
                item["status"] = "SUPERSEDED" if item["fp"] != it["fp"] else "ACCEPTED"
                item["decided"] = ts
        events.append({"ts": ts, "event": "VERSION", "iface": iid, "from": cur["ver"], "to": newver,
                       "bump": bump, "n_changes": len(ch)})
        run_changes.append({"iface": iid, "result": "VERSION", "ver": newver, "bump": bump, "changes": ch})
        cnt["VERSION"] += 1

    for iid, rec in reg["interfaces"].items():
        if rec.get("root") in scanned and iid not in found and rec["status"] == "ACTIVE":
            rec["status"] = "MISSING"
            rec["missing_since"] = ts
            events.append({"ts": ts, "event": "MISSING", "iface": iid})
            cnt["MISSING"] += 1

    # ---------------- gates
    gates = []

    def gate(code, ok, level, detail):
        gates.append({"gate": code, "result": "PASS" if ok else level, "detail": detail})

    gate("AIR_PARSE", not errors, "WARN", "%d parse errors" % len(errors))
    gate("AIR_ID_UNIQUE", not dups, "WARN", "%d cross-root id collisions (first kept)" % len(dups))
    untyped = [(i, f["name"]) for i, it in found.items() for s in ("inputs", "outputs")
               for f in it["contract"][s] if f["type"] == "?" and not f["name"].startswith("*")]
    gate("AIR_TYPED", not untyped, "WARN", "%d untyped fields" % len(untyped))
    badname = [(i, f["name"]) for i, it in found.items() for f in it["contract"]["inputs"]
               if not re.match(r"^\**[a-z_][a-z0-9_]*$", f["name"]) and norm(f["name"]) not in syn]
    gate("AIR_NAMING", not badname, "WARN", "%d non-snake_case names outside synonym vocab" % len(badname))
    held_open = [k for k, v in pending["items"].items() if v["status"] == "OPEN"]
    gate("AIR_PENDING", not held_open, "WARN", "%d open review items" % len(held_open))
    bad_steps = []
    for iid, a in adapters["interfaces"].items():
        rec = reg["interfaces"].get(iid)
        if not rec:
            bad_steps.append(iid)
            continue
        vers = {v["ver"]: v for v in rec["versions"]}
        for stp in a["chain"]:
            tgt = vers.get(stp["to"])
            for side in ("inputs", "outputs"):
                for _, new in stp.get(side, {}).items():
                    if not tgt or new not in {f["name"] for f in tgt["contract"][side]}:
                        bad_steps.append("%s:%s" % (iid, new))
    gate("AIR_ADAPTER_REPLAY", not bad_steps, "FAIL", "%d adapter targets unresolved" % len(bad_steps))
    ok_chain, n_chain, why = ledger_verify(P["ledger"])
    gate("AIR_LEDGER_CHAIN", ok_chain, "FAIL", "%d entries %s" % (n_chain, why))

    report = {"engine": ENGINE, "version": VERSION, "ts": ts, "mode": "COMMIT" if args.commit else "DRY_RUN",
              "root": root, "scan_roots": scanned, "files_parsed": nfiles, "synonyms": syn_src,
              "counts": cnt, "gates": gates, "changes": run_changes, "parse_errors": errors[:200],
              "duplicates": dups[:200], "untyped": untyped[:200], "naming": badname[:200],
              "interfaces_total": len(reg["interfaces"]),
              "by_kind": {}, "by_status": {}}
    for rec in reg["interfaces"].values():
        report["by_kind"][rec["kind"]] = report["by_kind"].get(rec["kind"], 0) + 1
        report["by_status"][rec["status"]] = report["by_status"].get(rec["status"], 0) + 1

    fail = any(g["result"] == "FAIL" for g in gates)
    if args.commit and not fail:
        write_text(P["registry"], json.dumps(reg, ensure_ascii=False, indent=1))
        write_text(P["adapters"], json.dumps(adapters, ensure_ascii=False, indent=1))
        write_text(P["pending"], json.dumps(pending, ensure_ascii=False, indent=1))
        if events:
            ledger_append(P["ledger"], events)
        ok_chain, n_chain, why = ledger_verify(P["ledger"])
        for g in gates:
            if g["gate"] == "AIR_LEDGER_CHAIN":
                g["result"] = "PASS" if ok_chain else "FAIL"
                g["detail"] = "%d entries %s" % (n_chain, why)
    elif args.commit and fail:
        report["mode"] = "COMMIT_BLOCKED"
        log("  [FAIL] gate failure: commit blocked, nothing persisted")

    state = {"engine": ENGINE, "version": VERSION, "ts": ts, "mode": report["mode"],
             "interfaces": len(reg["interfaces"]), "counts": cnt,
             "gates": {g["gate"]: g["result"] for g in gates}, "outputs": P}
    write_text(P["report"], json.dumps(report, ensure_ascii=False, indent=1))
    write_text(P["state"], json.dumps(state, ensure_ascii=False, indent=1))
    write_text(P["html"], render_html(report, reg, adapters, pending))
    for g in gates:
        log("  %-20s %-5s %s" % (g["gate"], g["result"], g["detail"]))
    log("  counts: %s" % jdump(cnt))
    log("  html: %s" % P["html"])
    return report, reg, adapters, pending


# ---------------------------------------------------------------- HTML
def render_html(rep, reg, adapters, pending):
    e = html.escape
    color = {"PASS": "ok", "WARN": "warn", "FAIL": "bad"}
    grows = "".join('<tr><td>%s</td><td><span class="pill %s">%s</span></td><td>%s</td></tr>' % (
        e(g["gate"]), color[g["result"]], g["result"], e(g["detail"])) for g in rep["gates"])
    crow = []
    for c in rep["changes"]:
        det = "; ".join(
            "%s %s%s%s" % (x["op"], x.get("old", ""), " → " if x.get("old") and x.get("new") else "", x.get("new", ""))
            + (" [%s %.2f]" % (x["via"], x["score"]) if x["op"] == "RENAME" else "")
            + (" %s→%s" % (x["from"], x["to"]) if x["op"] == "TYPE" else "")
            for x in c["changes"]) or "—"
        cls = {"HELD": "warn", "VERSION": "ok", "REGISTER": "info"}.get(c["result"], "")
        crow.append('<tr><td class="id">%s</td><td><span class="pill %s">%s</span></td><td>%s</td><td>%s</td></tr>' % (
            e(c["iface"]), cls, c["result"], e(c["ver"]), e(det)))
    irow = []
    for iid in sorted(reg["interfaces"]):
        r = reg["interfaces"][iid]
        v = r["versions"][-1]
        st = {"ACTIVE": "ok", "MISSING": "bad"}.get(r["status"], "")
        dr = "warn" if r.get("drift") == "HELD" else ""
        irow.append('<tr><td class="id">%s</td><td>%s</td><td>%s</td><td>%s</td><td>%d / %d</td>'
                    '<td><span class="pill %s">%s</span></td><td><span class="pill %s">%s</span></td><td class="fp">%s</td></tr>' % (
                        e(iid), e(r["kind"]), r["grade"], e(v["ver"]), len(v["contract"]["inputs"]),
                        len(v["contract"]["outputs"]), st, r["status"], dr, r.get("drift", "NONE"), v["fp"][:10]))
    prow = []
    for k, it in pending["items"].items():
        if it["status"] != "OPEN":
            continue
        what = ("rename %s → %s (%.2f)" % (it["old"], it["new"], it["score"]) if it["type"] == "RENAME_ASK"
                else "breaking: " + ", ".join("%s %s" % (x["op"], x.get("old") or x.get("new")) for x in it["changes"]
                                              if x["severity"] == "BREAKING"))
        prow.append('<tr data-key="%s"><td class="id">%s</td><td>%s</td><td>%s</td><td class="act">'
                    '<label><input type="radio" name="%s" value="ACCEPT">接受</label>'
                    '<label><input type="radio" name="%s" value="REJECT">拒絕</label>'
                    '<label><input type="radio" name="%s" value="" checked>略過</label></td></tr>' % (
                        e(k), e(it["iface"]), it["type"], e(what), e(k), e(k), e(k)))
    arow = []
    for iid, a in sorted(adapters["interfaces"].items()):
        for s in a["chain"]:
            m = ", ".join("%s→%s" % (o, n) for side in ("inputs", "outputs") for o, n in s.get(side, {}).items())
            arow.append("<tr><td class='id'>%s</td><td>%s → %s</td><td>%s</td><td>%s/%s</td></tr>" % (
                e(iid), e(s["from"]), e(s["to"]), e(m), e(s.get("via", "")), e(s.get("grade", ""))))
    kinds = " ".join("<span class='chip'>%s <b>%d</b></span>" % (e(k), v) for k, v in sorted(rep["by_kind"].items()))
    cnt = rep["counts"]
    empty = "<tr><td colspan='8' class='empty'>%s</td></tr>"
    return """<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>VIA CGE · Adaptive Interface Registry</title>
<style>
:root{--ink:#1B2433;--paper:#F3F5F8;--panel:#FFFFFF;--line:#D5DCE6;--navy:#1F3A5F;--ok:#0F766E;--warn:#A16207;--bad:#B42318;--info:#3056A0;--mute:#5B6778}
@media (prefers-color-scheme:dark){:root{--ink:#E4E9F1;--paper:#0F1722;--panel:#162232;--line:#2A3A50;--navy:#8FB3E8;--mute:#93A1B5}}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.55 "Noto Sans TC","Microsoft JhengHei","Segoe UI",sans-serif}
header{padding:28px 32px 18px;border-bottom:3px solid var(--navy)}h1{margin:0;font-size:26px;letter-spacing:.2px}
header p{margin:6px 0 0;color:var(--mute)}main{padding:20px 32px 48px;max-width:1400px}
.tally{display:flex;flex-wrap:wrap;gap:28px;margin:6px 0 22px}.tally div{border-left:4px solid var(--navy);padding-left:10px}
.tally b{display:block;font-size:28px;line-height:1.1}.tally span{color:var(--mute);font-size:13px}
section{background:var(--panel);border:1px solid var(--line);border-radius:6px;margin:0 0 18px;padding:14px 16px;overflow-x:auto}
h2{font-size:17px;margin:0 0 10px;color:var(--navy)}table{border-collapse:collapse;width:100%%;font-size:13.5px}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);vertical-align:top}th{color:var(--mute);font-weight:600}
td.id{font-family:Consolas,"Cascadia Mono",monospace;font-size:12.5px;word-break:break-all}td.fp{font-family:Consolas,monospace;color:var(--mute)}
.pill{display:inline-block;padding:1px 8px;border-radius:10px;font-size:12px;font-weight:600;border:1px solid currentColor}
.ok{color:var(--ok)}.warn{color:var(--warn)}.bad{color:var(--bad)}.info{color:var(--info)}
.chip{display:inline-block;margin:0 8px 6px 0;padding:2px 10px;border:1px solid var(--line);border-radius:4px}
.act label{margin-right:10px;white-space:nowrap}.empty{color:var(--mute)}
textarea{width:100%%;min-height:90px;font-family:Consolas,monospace;font-size:12.5px;background:var(--paper);color:var(--ink);border:1px solid var(--line)}
button{background:var(--navy);color:var(--panel);border:0;border-radius:4px;padding:6px 14px;margin:8px 8px 0 0;cursor:pointer;font:inherit}
button:focus-visible,input:focus-visible{outline:3px solid var(--warn);outline-offset:2px}
</style></head><body>
<header><h1>介面自適應登記簿 Adaptive Interface Registry</h1>
<p>%s v%s ｜ %s ｜ %s ｜ %d files parsed ｜ synonyms: %s</p></header><main>
<div class="tally"><div><b>%d</b><span>登記介面</span></div><div><b>%d</b><span>本次新登記</span></div>
<div><b>%d</b><span>版本演進</span></div><div><b>%d</b><span>破壞性變更暫扣</span></div>
<div><b>%d</b><span>失蹤 (保留不刪)</span></div><div><b>%d</b><span>未變動</span></div></div>
<section><h2>型別分布</h2>%s</section>
<section><h2>准入閘門</h2><table><tr><th>Gate</th><th>結果</th><th>說明</th></tr>%s</table></section>
<section><h2>待確認 (滑鼠點選後複製 token 存入 iface_confirmations.jsonl)</h2>
<table><tr><th>介面</th><th>類型</th><th>內容</th><th>決定</th></tr>%s</table>
<button type="button" onclick="acceptAll()">全部接受</button><button type="button" onclick="build()">產生 token</button><button type="button" onclick="copyTok()">複製</button>
<textarea id="tok" readonly aria-label="confirmation tokens"></textarea></section>
<section><h2>本次變動</h2><table><tr><th>介面</th><th>結果</th><th>版本</th><th>變更</th></tr>%s</table></section>
<section><h2>合約轉接鏈 (舊版 payload 自動對齊)</h2><table><tr><th>介面</th><th>版本</th><th>欄位映射</th><th>來源/等級</th></tr>%s</table></section>
<section><h2>介面總表</h2><table><tr><th>ID</th><th>型別</th><th>等級</th><th>版本</th><th>入/出</th><th>狀態</th><th>飄移</th><th>指紋</th></tr>%s</table></section>
</main><script>
function rows(){return Array.from(document.querySelectorAll('tr[data-key]'))}
function build(){var out=[];rows().forEach(function(r){var k=r.getAttribute('data-key');var c=r.querySelector('input:checked');if(c&&c.value){out.push('==CGE-CONFIRM== AIR '+c.value+' '+k)}});document.getElementById('tok').value=out.join('\\n')}
function acceptAll(){rows().forEach(function(r){var i=r.querySelector('input[value=ACCEPT]');if(i){i.checked=true}});build()}
function copyTok(){build();var t=document.getElementById('tok');t.select();try{navigator.clipboard.writeText(t.value)}catch(x){document.execCommand('copy')}}
document.addEventListener('change',build);
</script></body></html>""" % (
        e(ENGINE), VERSION, e(rep["ts"]), rep["mode"], rep["files_parsed"], e(rep["synonyms"]),
        rep["interfaces_total"], cnt["REGISTER"], cnt["VERSION"], cnt["HELD"], cnt["MISSING"], cnt["UNCHANGED"],
        kinds or "—", grows, "".join(prow) or empty % "沒有待確認項目",
        "".join(crow) or empty % "本次無變動", "".join(arow) or empty % "尚無轉接鏈",
        "".join(irow) or empty % "尚無登記介面")


# ---------------------------------------------------------------- selftest
FIX_V1 = '''
from pydantic import BaseModel, Field
from dataclasses import dataclass
from typing import Optional, TypedDict, List
class Quote(BaseModel):
    stock_id: str
    trade_date: str
    close_price: float
    volume: int = 0
    note: Optional[str] = Field(None, alias="remark")
class _Hidden(BaseModel):
    x: int
@dataclass
class FlowRow:
    ticker: str
    net_buy: float
class Cfg(TypedDict, total=False):
    window: int
def fetch_quote(stock_id: str, days: int = 5) -> dict:
    return {}
def untyped(a, b):
    return a
VIA_INTERFACE = {"name": "flow_api", "inputs": {"ticker": "str", "window": {"type": "int", "required": False}}, "outputs": {"net": "float"}}
'''
FIX_V2 = FIX_V1.replace("    stock_id: str\n    trade_date: str\n    close_price: float",
                        "    ticker: str\n    trade_date: str\n    closePrice: float") \
    .replace("    note: Optional[str] = Field(None, alias=\"remark\")",
             "    note: Optional[str] = Field(None, alias=\"remark\")\n    market: str = \"TWSE\"") \
    .replace("def fetch_quote(stock_id: str, days: int = 5) -> dict:",
             "def fetch_quote(stock_id: str, days: int = 5, adjust: bool = False) -> dict:") \
    .replace("    net_buy: float", "    net_buy_amt: float")
FIX_V3 = FIX_V2.replace("    trade_date: str\n", "    source: str\n")


def selftest():
    tmp = tempfile.mkdtemp(prefix="air_selftest_")
    src = os.path.join(tmp, "src")
    wd = os.path.join(tmp, "wd")
    os.makedirs(os.path.join(src, "pkg"))
    mod = os.path.join(src, "pkg", "quotes.py")
    results = []

    def check(name, cond, info=""):
        results.append((name, bool(cond), info))
        log("  [%s] %s %s" % ("PASS" if cond else "FAIL", name, info), force=True)

    def run(extra=None):
        ns = argparse.Namespace(root=wd, scan=[src], commit=True, accept_breaking=False, confirm=None,
                                vocab=None, max_files=0)
        for k, v in (extra or {}).items():
            setattr(ns, k, v)
        return govern(ns)

    def write(code):
        with open(mod, "w", encoding="utf-8") as f:
            f.write(code)

    _QUIET[0] = True
    try:
        log("[selftest] v1 register")
        write(FIX_V1)
        rep, reg, ad, pen = run()
        ids = set(reg["interfaces"])
        check("register_count", rep["counts"]["REGISTER"] == 5, str(sorted(ids)))
        q = reg["interfaces"].get("pkg/quotes::Quote", {})
        qf = {f["name"]: f for f in q["versions"][0]["contract"]["inputs"]} if q else {}
        check("pydantic_required", qf.get("stock_id", {}).get("required") is True and qf.get("volume", {}).get("required") is False)
        check("field_alias_optional", qf.get("note", {}).get("alias") == "remark" and qf["note"]["required"] is False
              and qf["note"]["type"] == "str|None")
        check("private_skipped", "pkg/quotes::_Hidden" not in ids)
        check("typeddict_total_false", reg["interfaces"]["pkg/quotes::Cfg"]["versions"][0]["contract"]["inputs"][0]["required"] is False)
        check("declared_grade_V", reg["interfaces"]["pkg/quotes::flow_api"]["grade"] == "V")
        check("untyped_function_skipped", "pkg/quotes::untyped" not in ids)

        log("[selftest] idempotent rerun")
        rep, reg, ad, pen = run()
        check("idempotent", rep["counts"]["REGISTER"] == 0 and rep["counts"]["VERSION"] == 0)

        log("[selftest] v2 adaptive rename")
        write(FIX_V2)
        rep, reg, ad, pen = run()
        qv = reg["interfaces"]["pkg/quotes::Quote"]["versions"]
        check("minor_bump", qv[-1]["ver"] == "1.1.0", qv[-1]["ver"])
        vias = {(c["old"], c["new"]): c["via"] for c in qv[-1]["changes"] if c["op"] == "RENAME"}
        check("syn_rename", vias.get(("stock_id", "ticker")) == "SYN", str(vias))
        check("norm_rename", vias.get(("close_price", "closePrice")) == "NORM")
        check("func_add_optional", reg["interfaces"]["pkg/quotes::fetch_quote"]["versions"][-1]["ver"] == "1.1.0")
        out, trace = adapt_payload(ad, "pkg/quotes::Quote",
                                   {"stock_id": "2330", "trade_date": "2026-09-16", "close_price": 1.0, "volume": 1}, "1.0.0")
        check("adapter_replay", set(out) == {"ticker", "trade_date", "closePrice", "volume"}, "; ".join(trace))
        ask = [k for k, v in pen["items"].items() if v["type"] == "RENAME_ASK" and v["status"] == "OPEN"]
        check("ask_queue", any("net_buy|net_buy_amt" in k for k in ask), str(ask))

        log("[selftest] confirm ASK via token")
        with open(os.path.join(wd, OUTF["confirm"]), "w", encoding="utf-8") as f:
            f.write("==CGE-CONFIRM== AIR ACCEPT %s\n" % ask[0])
        rep, reg, ad, pen = run()
        check("confirm_accept", pen["items"][ask[0]]["status"] == "ACCEPTED" and
              any(s.get("via") == "HUMAN" for s in ad["interfaces"]["pkg/quotes::FlowRow"]["chain"]))
        rep, reg, ad, pen = run()
        check("confirm_idempotent", sum(1 for s in ad["interfaces"]["pkg/quotes::FlowRow"]["chain"] if s.get("via") == "HUMAN") == 1)

        log("[selftest] v3 breaking held")
        write(FIX_V3)
        rep, reg, ad, pen = run()
        check("breaking_held", reg["interfaces"]["pkg/quotes::Quote"]["versions"][-1]["ver"] == "1.1.0"
              and reg["interfaces"]["pkg/quotes::Quote"]["drift"] == "HELD")
        hold = [k for k, v in pen["items"].items() if v["type"] == "HELD_BREAKING" and v["status"] == "OPEN"]
        check("hold_queued", len(hold) == 1, str(hold))
        rep, reg, ad, pen = run({"accept_breaking": True})
        check("major_bump", reg["interfaces"]["pkg/quotes::Quote"]["versions"][-1]["ver"] == "2.0.0")
        check("hold_closed", pen["items"][hold[0]]["status"] == "ACCEPTED")

        log("[selftest] missing never removed")
        os.remove(mod)
        rep, reg, ad, pen = run()
        check("missing_kept", reg["interfaces"]["pkg/quotes::Quote"]["status"] == "MISSING"
              and len(reg["interfaces"]["pkg/quotes::Quote"]["versions"]) == 3)
        write(FIX_V3)
        rep, reg, ad, pen = run()
        check("relisted", reg["interfaces"]["pkg/quotes::Quote"]["status"] == "ACTIVE" and rep["counts"]["RELISTED"] == 5)

        ok, n, why = ledger_verify(os.path.join(wd, OUTF["ledger"]))
        check("ledger_chain", ok and n > 0, "%d entries %s" % (n, why))
        with open(os.path.join(wd, OUTF["ledger"]), "a", encoding="utf-8") as f:
            f.write('{"event":"FORGED","prev":"x","hash":"y"}\n')
        ok2, _, why2 = ledger_verify(os.path.join(wd, OUTF["ledger"]))
        check("ledger_tamper_detected", not ok2, why2)

        log("[selftest] dry-run persists nothing")
        before = os.path.getmtime(os.path.join(wd, OUTF["registry"]))
        write(FIX_V2)
        rep, reg, ad, pen = run({"commit": False})
        check("dry_run", rep["mode"] == "DRY_RUN" and os.path.getmtime(os.path.join(wd, OUTF["registry"])) == before)
    except Exception as ex:
        check("selftest_exception", False, "%s: %s" % (type(ex).__name__, ex))
    finally:
        _QUIET[0] = False
        shutil.rmtree(tmp, ignore_errors=True)
    passed = sum(1 for r in results if r[1])
    log("[selftest] %d/%d PASS" % (passed, len(results)), force=True)
    return passed == len(results)


def main():
    ap = argparse.ArgumentParser(description="VIA CGE v0500 Adaptive Interface Registry")
    ap.add_argument("--root", default=os.getcwd(), help="CGE workdir (outputs + governance_vocab.json)")
    ap.add_argument("--scan", nargs="*", help="roots to scan for .py interfaces (default: --root)")
    ap.add_argument("--commit", action="store_true", help="persist registry/ledger/adapters (default dry-run)")
    ap.add_argument("--accept-breaking", dest="accept_breaking", action="store_true")
    ap.add_argument("--confirm", help="extra confirmations file (==CGE-CONFIRM== AIR ACCEPT|REJECT <key>)")
    ap.add_argument("--vocab", help="governance_vocab.json path (default <root>/governance_vocab.json)")
    ap.add_argument("--max-files", dest="max_files", type=int, default=0)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--adapt", help="interface id to adapt a payload for")
    ap.add_argument("--payload", help="JSON payload for --adapt")
    ap.add_argument("--from-ver", dest="from_ver", default="1.0.0")
    a = ap.parse_args()
    if a.selftest:
        ok = selftest()
        sys.exit(0 if ok else 1)
    if a.adapt:
        ad = read_json(os.path.join(os.path.abspath(a.root), OUTF["adapters"]), {"interfaces": {}})
        out, trace = adapt_payload(ad, a.adapt, json.loads(a.payload or "{}"), a.from_ver)
        print(json.dumps({"payload": out, "trace": trace}, ensure_ascii=False, indent=1))
        return
    rep = govern(a)[0]
    sys.exit(2 if rep["mode"] == "COMMIT_BLOCKED" else 0)


if __name__ == "__main__":
    main()
