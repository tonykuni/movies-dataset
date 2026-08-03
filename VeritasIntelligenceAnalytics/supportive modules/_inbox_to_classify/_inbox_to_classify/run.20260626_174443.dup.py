import json, sys, pathlib, datetime

def main():
    cfg_path = sys.argv[1] if len(sys.argv) > 1 else "engine.config.json"
    data = {}
    try:
        data = json.loads(pathlib.Path(cfg_path).read_text(encoding="utf-8"))
    except Exception as exc:
        print(json.dumps({"status":"FAIL_CONFIG_READ","engine":"def_CoerceBool","error":str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps({"status":"OK_DRY_RUN","engine":"def_CoerceBool","mode":data.get("mode","dry_run"),"timestamp":datetime.datetime.now().isoformat()}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
