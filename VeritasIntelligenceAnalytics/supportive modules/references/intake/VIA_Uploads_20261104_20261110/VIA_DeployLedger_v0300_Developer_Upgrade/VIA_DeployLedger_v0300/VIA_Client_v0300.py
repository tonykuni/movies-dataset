from __future__ import annotations
"""VIA client installer/runtime. Compiled with a dependency-closed verifier.

No authority key generation, product issuance, server database, or build commands.
VIA:ACCEL-BRIDGE: bounded execution / conservative thread budget.
"""
# def PART 1 — parameters
MAX_ARCHIVE_FILES = 100000
MAX_ARCHIVE_BYTES = 16 * 1024 * 1024 * 1024
MAX_ENTRY_BYTES = 1024 * 1024 * 1024
MIN_FREE_BYTES = 1024 * 1024 * 1024
MAX_JSON_BYTES = 8 * 1024 * 1024
DEFAULT_HOME_NAME = "VIA"

import argparse
import contextlib
import getpass
import hashlib
import json
import os
import re
import secrets
import shutil
import stat
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone

import VIA_HybridEdgeCloud_AllInOne_v0200 as runtime
from via_pins import AUTHORITY_PIN, RELEASE_PIN


def read(path):
    return runtime.def_read_json(Path(path), max_bytes=MAX_JSON_BYTES)


def write(path, value):
    return runtime.def_write_json(Path(path), value, overwrite=True)


def relative(value):
    if not isinstance(value, str) or not value or "\\" in value or ":" in value or "\x00" in value:
        raise ValueError("Invalid package path")
    p = PurePosixPath(value)
    if p.is_absolute() or any(x in {"", ".", ".."} for x in value.split("/")):
        raise ValueError("Package path traversal")
    reserved = {"CON", "PRN", "AUX", "NUL", *("COM"+str(i) for i in range(1,10)), *("LPT"+str(i) for i in range(1,10))}
    if any(x.endswith((".", " ")) or x.split(".")[0].upper() in reserved for x in p.parts):
        raise ValueError("Windows reserved filename")
    return value


def under(root, rel):
    root = Path(root).resolve()
    p = root / relative(rel)
    runtime.def_validate_no_link_chain(p)
    if not p.resolve().is_relative_to(root):
        raise ValueError("Path escaped approved root")
    return p


def key(path, pin):
    return runtime.def_load_trusted_public_key(Path(path), pin)


def validate_release(doc):
    if doc.get("schema") != "via.client-release.v3" or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", doc.get("release_id", "")):
        raise ValueError("Invalid release metadata")
    runtime.def_normalize_product_number(doc["product_number"])
    ids = set()
    if not doc.get("units"):
        raise ValueError("Empty release")
    for u in doc["units"]:
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{1,63}", u.get("id", "")) or u["id"] in ids:
            raise ValueError("Duplicate or invalid engine identity")
        ids.add(u["id"])
        relative(u["artifact"])
        if not u["artifact"].endswith(".exe") or not isinstance(u["smoke_args"], list) or not u["smoke_args"] or not all(isinstance(a, str) for a in u["smoke_args"]):
            raise ValueError("Compiled executable / smoke arguments required")
        re.compile(u["success_regex"])
        if type(u["timeout"]) is not int or not 1 <= u["timeout"] <= 3600:
            raise ValueError("Invalid smoke timeout")
    return doc


def verify_package(payload, signed_manifest):
    payload = Path(payload)
    rp = key(payload / "release.pub", RELEASE_PIN)
    key(payload / "authority.pub", AUTHORITY_PIN)
    # Verify metadata is covered by the signature before accepting any commands.
    envelope = read(signed_manifest)
    manifest = runtime.def_verify_signed_payload(envelope, rp, runtime.def_PARAM_RELEASE_KEY_ID, "via.package-tree-envelope.v2.2")
    checked = runtime.def_verify_package_tree_manifest(envelope, rp, payload, manifest["product_number"])
    if not checked.ok:
        raise ValueError("Package integrity failed: " + str(checked.errors))
    doc = validate_release(read(payload / "release.json"))
    if doc["product_number"] != manifest["product_number"] or doc["release_id"] != manifest["release_id"]:
        raise ValueError("Release metadata does not match signed tree")
    return doc


def extract_archive(archive, target):
    """Authenticate the manifest, then extract exactly its file set with limits."""
    target = Path(target)
    if target.exists():
        raise FileExistsError("Extraction target must be new")
    with zipfile.ZipFile(archive) as z:
        infos = z.infolist()
        names = [i.filename for i in infos]
        if not names or len(names) > MAX_ARCHIVE_FILES or len({n.casefold() for n in names}) != len(names):
            raise ValueError("Empty, duplicate or over-limit archive")
        total = 0
        for i in infos:
            relative(i.filename)
            mode = i.external_attr >> 16
            if i.is_dir() or stat.S_ISLNK(mode) or i.file_size > MAX_ENTRY_BYTES or i.flag_bits & 1:
                raise ValueError("Unsupported archive entry")
            total += i.file_size
        if total > MAX_ARCHIVE_BYTES:
            raise ValueError("Archive exceeds uncompressed size limit")
        for small in ("payload/release.pub", "package.signed.json"):
            if z.getinfo(small).file_size > MAX_JSON_BYTES:
                raise ValueError("Oversized signature metadata")
        public_bytes = z.read("payload/release.pub")
        if hashlib.sha256(public_bytes).hexdigest() != RELEASE_PIN:
            raise ValueError("Archive release key does not match compiled pin")
        from cryptography.hazmat.primitives.serialization import load_pem_public_key
        envelope = json.loads(z.read("package.signed.json"), object_pairs_hook=runtime.def_json_object_no_duplicates)
        manifest = runtime.def_verify_signed_payload(envelope, load_pem_public_key(public_bytes), runtime.def_PARAM_RELEASE_KEY_ID, "via.package-tree-envelope.v2.2")
        rows = manifest["files"]
        expected = {"payload/" + relative(r["path"]): r for r in rows}
        if len(expected) != len(rows) or set(names) != set(expected) | {"package.signed.json"}:
            raise ValueError("Archive file set differs from signed manifest")
        for name, row in expected.items():
            if z.getinfo(name).file_size != row["size"]:
                raise ValueError("Archive file size differs from manifest")
        runtime.def_require_free_disk(target.parent, total + MIN_FREE_BYTES)
        target.mkdir(parents=True)
        for info in infos:
            dest = under(target, info.filename)
            dest.parent.mkdir(parents=True, exist_ok=True)
            h, written = hashlib.sha256(), 0
            with z.open(info) as src, dest.open("xb") as dst:
                while chunk := src.read(1024 * 1024):
                    written += len(chunk)
                    if written > info.file_size:
                        raise ValueError("Archive size changed while extracting")
                    h.update(chunk)
                    dst.write(chunk)
            if info.filename in expected and h.hexdigest() != expected[info.filename]["sha256"]:
                raise ValueError("Archive hash mismatch")
    verify_package(target / "payload", target / "package.signed.json")
    return target


# def PART 2 — device-bound activation and licensed entrypoint
def activation(home, number, replace_key=False, secret_reader=None):
    home = Path(home)
    home.mkdir(parents=True, exist_ok=True)
    number = runtime.def_normalize_product_number(number)
    product_state = home / "product.dpapi"
    if replace_key and (home / "current.json").exists():
        raise ValueError("An active installation cannot silently replace its product key")
    if product_state.exists() and not replace_key:
        current = runtime.def_load_product_key_state(product_state)
        if current["product_number"] != number:
            raise ValueError("Installed product differs; use a separate home")
    else:
        secret = (secret_reader or getpass.getpass)("產品 KEY（輸入不回顯）: ")
        if not secret:
            raise ValueError("Product KEY was not entered")
        runtime.def_store_product_key_state(product_state, number, secret, overwrite=replace_key)
        secret = ""
    state = runtime.def_load_product_key_state(product_state)
    device = runtime.def_get_or_create_device_key(home / "device.dpapi")
    req = runtime.def_create_activation_request(device, runtime.def_PARAM_PRODUCT_SKU, "PRO", number, state["master_key"], "pc", runtime.def_load_hardware_hashes())
    write(home / "activation-request.json", req)
    return {"status": "ACTIVATION_PENDING", "request": str(home / "activation-request.json"), "request_valid_seconds": runtime.def_PARAM_REQUEST_MAX_AGE_SECONDS}


def validate_license(home, payload, license_file):
    home, payload = Path(home), Path(payload)
    state = runtime.def_load_product_key_state(home / "product.dpapi")
    device = runtime.def_load_device_private_key(home / "device.dpapi")
    authority = key(payload / "authority.pub", AUTHORITY_PIN)
    check = runtime.def_verify_license(read(license_file), authority, device, runtime.def_PARAM_PRODUCT_SKU, runtime.def_PARAM_ENGINE_VERSION, state["product_number"], state["master_key"], "VIA_ALL_ENGINES", runtime.def_load_hardware_hashes(), state_path=home / "clock.json", update_clock_state=True)
    if not check.ok:
        raise ValueError("License rejected: " + str(check.errors))
    release = read(payload / "release.json")
    if state["product_number"] != release["product_number"]:
        raise ValueError("Product does not match this installation package")
    return state, device, authority


def launch_unit(home, payload, unit, license_file, arguments=None):
    home, payload = Path(home), Path(payload)
    state, device, authority = validate_license(home, payload, license_file)
    rp = key(payload / "release.pub", RELEASE_PIN)
    artifact = under(payload, unit["artifact"])
    mp = under(payload, "Manifests/" + unit["id"] + ".json")
    handshake = runtime.def_create_module_handshake(read(mp), rp, artifact, read(license_file), authority, device, runtime.def_PARAM_PRODUCT_SKU, runtime.def_PARAM_ENGINE_VERSION, state["product_number"], state["master_key"], runtime.def_load_hardware_hashes(), secrets.token_hex(24), state_path=home / "clock.json", execution_mode="CHILD_PROCESS")
    if not handshake.ok:
        raise ValueError("Engine authorization rejected: " + str(handshake.errors))
    # Outputs and temporary data live outside the immutable release tree.
    os.environ["VIA_HOME"] = str(home / "data")
    os.environ["VIA_ASSET_ROOT"] = str(payload / "Assets")
    (home / "data").mkdir(exist_ok=True)
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[name] = str(max(1, min(4, (os.cpu_count() or 2)//2)))
    return runtime.def_launch_guarded_executable(artifact, handshake.data["token"], Path(license_file), mp, payload / "authority.pub", payload / "release.pub", home / "device.dpapi", home / "product.dpapi", home / "replay.jsonl", unit["smoke_args"] if arguments is None else arguments, timeout_seconds=unit["timeout"] if arguments is None else 86400)


def quick_test(home, payload, signed_manifest, license_file):
    release = verify_package(payload, signed_manifest)
    results = []
    for u in release["units"]:
        result = launch_unit(home, payload, u, license_file)
        if not result["ok"] or not re.search(u["success_regex"], result["stdout_tail"] + result["stderr_tail"]):
            raise ValueError("Quick test failed: " + u["id"])
        results.append({"id": u["id"], "status": "PASS", "exit_code": result["exit_code"]})
    verify_package(payload, signed_manifest)
    return {"status": "PASS", "units": results, "release_id": release["release_id"]}


# def PART 3 — transactional side-by-side installation and rollback
def install(home, package, license_file):
    home = Path(home).expanduser().absolute()
    runtime.def_validate_no_link_chain(home)
    home.mkdir(parents=True, exist_ok=True)
    with runtime.def_file_lock(home / "installation"):
        stage = home / "staging" / secrets.token_hex(12)
        stage.parent.mkdir(exist_ok=True)
        before = read(home / "current.json") if (home / "current.json").is_file() else None
        journal = {"status": "PREPARING", "previous": before, "stage": str(stage), "started_at": datetime.now(timezone.utc).isoformat()}
        write(home / "install-journal.json", journal)
        committed = False
        try:
            extract_archive(package, stage)
            payload = stage / "payload"
            release = verify_package(payload, stage / "package.signed.json")
            validate_license(home, payload, license_file)
            size = sum(p.stat().st_size for p in stage.rglob("*") if p.is_file())
            runtime.def_require_free_disk(home, size + MIN_FREE_BYTES)
            check = quick_test(home, payload, stage / "package.signed.json", license_file)
            releases = home / "releases"
            releases.mkdir(exist_ok=True)
            destination = under(releases, release["release_id"])
            if destination.exists():
                existing = verify_package(destination / "payload", destination / "package.signed.json")
                if read(destination / "package.signed.json") != read(stage / "package.signed.json") or existing != release:
                    raise ValueError("Existing release ID has different content")
                # Retain this verified attempt in staging for diagnosis; do not overwrite.
            else:
                os.replace(stage, destination)
            # Keep the license per accepted release; a failed upgrade cannot replace
            # the last-known-good version's license. Pointer is the commit boundary.
            write(destination / "license.json", read(license_file))
            previous = before["release_id"] if before and before["release_id"] != release["release_id"] else (before or {}).get("previous")
            pointer = {"release_id": release["release_id"], "previous": previous, "product_number": release["product_number"], "accepted_at": datetime.now(timezone.utc).isoformat(), "tree_sha256": read(destination / "package.signed.json")["payload"]["tree_sha256"]}
            write(home / "current.json", pointer)
            committed = True
            journal.update(status="ACTIVE", current=pointer, quick_test=check)
            write(home / "install-journal.json", journal)
            return journal
        except Exception as exc:
            if committed:
                return {"status": "ACTIVE_JOURNAL_WARNING", "current": pointer, "quick_test": check, "error": str(exc)}
            journal.update(status="FAILED_PREVIOUS_RETAINED", error=str(exc))
            write(home / "install-journal.json", journal)
            raise


def installed_release(home):
    home = Path(home)
    pointer = read(home / "current.json")
    root = under(home / "releases", pointer["release_id"])
    release = verify_package(root / "payload", root / "package.signed.json")
    if release["release_id"] != pointer["release_id"] or read(root / "package.signed.json")["payload"]["tree_sha256"] != pointer["tree_sha256"]:
        raise ValueError("Active pointer mismatch")
    return root, release


def rollback(home):
    home = Path(home)
    with runtime.def_file_lock(home / "installation"):
        current = read(home / "current.json")
        previous = current.get("previous")
        if not previous:
            raise ValueError("No previous accepted release")
        root = under(home / "releases", previous)
        release = verify_package(root / "payload", root / "package.signed.json")
        test = quick_test(home, root / "payload", root / "package.signed.json", root / "license.json")
        write(home / "current.json", {"release_id": previous, "previous": current["release_id"], "product_number": release["product_number"], "tree_sha256": read(root / "package.signed.json")["payload"]["tree_sha256"], "accepted_at": datetime.now(timezone.utc).isoformat()})
        return {"status": "ROLLED_BACK", "release_id": previous, "quick_test": test}


def wizard(home):
    """Native desktop handoff: no command entry required once a compiled kit exists."""
    import tkinter as tk
    from tkinter import filedialog, messagebox, simpledialog
    app = tk.Tk()
    app.withdraw()
    home = Path(home)
    try:
        if (home / "current.json").is_file() and messagebox.askyesno("VIA", "啟動已安裝的 VIA？\n選擇「否」可安裝新版本。", parent=app):
            with runtime.def_file_lock(home / "installation"):
                root, release = installed_release(home)
                unit = next((u for u in release["units"] if u["id"].startswith("VRN")), release["units"][0])
                return launch_unit(home, root / "payload", unit, root / "license.json", [])
        package = filedialog.askopenfilename(title="選擇 VIA 安裝包", filetypes=[("VIA package", "*.zip")], parent=app)
        if not package:
            return {"status": "CANCELLED"}
        print("[1/4] 驗證安裝包簽章與完整性…", flush=True)
        with tempfile.TemporaryDirectory(prefix="via-package-check-") as temp:
            staged = extract_archive(package, Path(temp) / "verified")
            release = verify_package(staged / "payload", staged / "package.signed.json")
        print("[2/4] 驗證產品號與裝置啟用…", flush=True)
        activation(home, release["product_number"], secret_reader=lambda prompt: simpledialog.askstring("VIA 產品授權", prompt, show="*", parent=app))
        license_file = filedialog.askopenfilename(title="選擇供應商簽發的授權檔；尚未取得可按取消", filetypes=[("License", "*.json")], parent=app)
        if not license_file:
            messagebox.showinfo("VIA 啟用待完成", "裝置啟用請求已建立：\n" + str(home / "activation-request.json") + "\n請在 15 分鐘內由管理端簽發；逾時重新開啟此精靈產生請求。", parent=app)
            return {"status": "ACTIVATION_PENDING", "request": str(home / "activation-request.json")}
        print("[3/4] 安裝並執行全部快速驗收…", flush=True)
        result = install(home, package, license_file)
        print("[4/4] 已啟用。", flush=True)
        if messagebox.askyesno("VIA", "安裝與快速測試完成，立即啟動 VRN？", parent=app):
            with runtime.def_file_lock(home / "installation"):
                root, release = installed_release(home)
                unit = next((u for u in release["units"] if u["id"].startswith("VRN")), release["units"][0])
                launch = launch_unit(home, root / "payload", unit, root / "license.json", [])
                result["launch"] = launch
        return result
    except Exception as exc:
        messagebox.showerror("VIA 安裝未完成", str(exc), parent=app)
        raise
    finally:
        app.destroy()


def main(argv=None):
    p = argparse.ArgumentParser(description="VIA 客戶安裝與授權入口")
    p.add_argument("--home", default=str(Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / DEFAULT_HOME_NAME))
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("wizard")
    q = sub.add_parser("activate"); q.add_argument("--product-number", required=True); q.add_argument("--replace-key", action="store_true")
    q = sub.add_parser("install"); q.add_argument("--package", required=True); q.add_argument("--license", required=True)
    sub.add_parser("test"); sub.add_parser("rollback")
    q = sub.add_parser("run"); q.add_argument("--unit", required=True); q.add_argument("arguments", nargs=argparse.REMAINDER)
    a = p.parse_args(argv)
    try:
        if os.name != "nt":
            raise RuntimeError("Production client requires Windows DPAPI and hardware evidence")
        if a.cmd in {None, "wizard"}: result = wizard(a.home)
        elif a.cmd == "activate": result = activation(a.home, a.product_number, a.replace_key)
        elif a.cmd == "install": result = install(a.home, a.package, a.license)
        elif a.cmd == "rollback": result = rollback(a.home)
        else:
            home = Path(a.home)
            with runtime.def_file_lock(home / "installation"):
                root, release = installed_release(home)
                if a.cmd == "test": result = quick_test(home, root / "payload", root / "package.signed.json", root / "license.json")
                else:
                    unit = next((u for u in release["units"] if u["id"] == a.unit), None)
                    if unit is None: raise ValueError("Unknown engine")
                    arguments = a.arguments[1:] if a.arguments[:1] == ["--"] else a.arguments
                    result = launch_unit(home, root / "payload", unit, root / "license.json", arguments)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok", True) else 3
    except Exception as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "error": str(exc)}, ensure_ascii=False))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
