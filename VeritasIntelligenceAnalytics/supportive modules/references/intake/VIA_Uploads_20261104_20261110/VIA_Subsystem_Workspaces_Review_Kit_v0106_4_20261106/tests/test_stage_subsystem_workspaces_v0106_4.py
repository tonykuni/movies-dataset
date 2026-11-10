import hashlib
import importlib.util
import io
import json
from pathlib import Path
import stat
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('stage_v0106.4', ROOT / 'scripts/stage_subsystem_workspaces_v0106_4.py')
assert spec and spec.loader
stage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stage)


def archive(name='public/governance.html', flags=None, mismatch=False, extra=False, symlink=False):
    body = b'candidate only'
    m = {'version': 'v0106.4', 'policy': 'EXISTING_PLUS_NEW_ATLAS_AND_LOCAL_TOOLS', 'release_ready': False,
         'production_deployment': False, 'formal_registration': False, 'existing_engine_modified': False,
         'contracts_activated': False, 'file_count': 1, 'files': {name: {'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()}}}
    m.update(flags or {})
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w') as z:
        info = zipfile.ZipInfo(name)
        if symlink:
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
        z.writestr(info, body)
        z.writestr('manifest.json', json.dumps(m))
        z.writestr('SHA256SUMS', ('0' * 64 if mismatch else m['files'][name]['sha256']) + '  ' + name + '\n')
        if extra:
            z.writestr('extra.py', 'raise RuntimeError()')
    return out.getvalue()


class StageTests(unittest.TestCase):
    def test_valid_archive(self):
        raw = archive()
        self.assertEqual(stage.verify_blob(raw, stage.sha(raw))['file_count'], 1)

    def test_external_sha_required(self):
        with self.assertRaises(ValueError):
            stage.verify_blob(archive(), '0' * 64)

    def test_windows_paths_rejected(self):
        for name in ['/bad', '../bad', 'a/../bad', 'C:/bad', 'a\\b', 'a/name:ads', 'NUL.txt', 'COM0.txt', 'a/LPT9', 'a/space ', 'a/dot.', 'a//b', 'a/x?y']:
            with self.subTest(name=name), self.assertRaises(ValueError):
                raw = archive(name)
                stage.verify_blob(raw, stage.sha(raw))

    def test_symlink_member_rejected(self):
        raw = archive(symlink=True)
        with self.assertRaises(ValueError):
            stage.verify_blob(raw, stage.sha(raw))

    def test_missing_or_true_policy_flags_rejected(self):
        for fields in [{'formal_registration': True}, {'production_deployment': True}, {'version': 'v0104.1'}, {'release_ready': None}, {'policy': 'REPLACE_EXISTING'}]:
            raw = archive(flags=fields)
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                stage.verify_blob(raw, stage.sha(raw))

    def test_extra_member_rejected(self):
        raw = archive(extra=True)
        with self.assertRaises(ValueError):
            stage.verify_blob(raw, stage.sha(raw))

    def test_member_sums_mismatch_rejected(self):
        raw = archive(mismatch=True)
        with self.assertRaises(ValueError):
            stage.verify_blob(raw, stage.sha(raw))

    def test_duplicate_json_and_nonfinite_rejected(self):
        for raw in ['{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}']:
            with self.assertRaises(ValueError):
                stage.strict(raw)

    def test_corrupt_crc_rejected(self):
        raw = bytearray(archive())
        raw[raw.find(b'candidate only')] = ord('X')
        with self.assertRaises(ValueError):
            stage.verify_blob(bytes(raw), stage.sha(bytes(raw)))

    def test_missing_root_is_not_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'kit.zip'
            raw = archive()
            p.write_bytes(raw)
            root = Path(tmp) / 'missing'
            with self.assertRaises(FileNotFoundError):
                stage.stage(p, stage.sha(raw), root)
            self.assertFalse(root.exists())

    def test_stage_is_additive_and_no_engine_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'existing_vcgc.py').write_text('immutable')
            p = root / 'kit.zip'
            raw = archive()
            p.write_bytes(raw)
            one = stage.stage(p, stage.sha(raw), root)
            two = stage.stage(p, stage.sha(raw), root)
            self.assertEqual((root / 'existing_vcgc.py').read_text(), 'immutable')
            self.assertNotEqual(one['target'], two['target'])
            self.assertEqual(one['commands_executed'], 0)
            self.assertEqual((Path(one['target']) / 'public/governance.html').read_bytes(), b'candidate only')

    def test_source_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'kit.zip'
            p.write_bytes(archive())
            link = Path(tmp) / 'linked.zip'
            link.symlink_to(p)
            with self.assertRaises(ValueError):
                stage.verify(link, stage.sha(p.read_bytes()))


if __name__ == '__main__':
    unittest.main()
