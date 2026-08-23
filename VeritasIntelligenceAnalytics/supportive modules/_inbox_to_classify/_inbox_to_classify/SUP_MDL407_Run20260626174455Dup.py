# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import json, sys, pathlib, datetime

def main():
    cfg_path = sys.argv[1] if len(sys.argv) > 1 else "engine.config.json"
    data = {}
    try:
        data = json.loads(pathlib.Path(cfg_path).read_text(encoding="utf-8"))
    except Exception as exc:
        print(json.dumps({"status":"FAIL_CONFIG_READ","engine":"def_GetVIAUltimateEngineForgeArtifacts","error":str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps({"status":"OK_DRY_RUN","engine":"def_GetVIAUltimateEngineForgeArtifacts","mode":data.get("mode","dry_run"),"timestamp":datetime.datetime.now().isoformat()}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
