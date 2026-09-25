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
from collections.abc import Iterable, Iterator
from typing import Any

from pip._vendor.dependency_groups import DependencyGroupResolver

from pip._internal.exceptions import InstallationError
from pip._internal.utils.compat import tomllib


def parse_dependency_groups(groups: list[tuple[str, str]]) -> list[str]:
    """
    Parse dependency groups data as provided via the CLI, in a `[path:]group` syntax.

    Raises InstallationErrors if anything goes wrong.
    """
    resolvers = _build_resolvers(path for (path, _) in groups)
    return list(_resolve_all_groups(resolvers, groups))


def _resolve_all_groups(
    resolvers: dict[str, DependencyGroupResolver], groups: list[tuple[str, str]]
) -> Iterator[str]:
    """
    Run all resolution, converting any error from `DependencyGroupResolver` into
    an InstallationError.
    """
    for path, groupname in groups:
        resolver = resolvers[path]
        try:
            yield from (str(req) for req in resolver.resolve(groupname))
        except (ValueError, TypeError, LookupError) as e:
            raise InstallationError(
                f"[dependency-groups] resolution failed for '{groupname}' "
                f"from '{path}': {e}"
            ) from e


def _build_resolvers(paths: Iterable[str]) -> dict[str, Any]:
    resolvers = {}
    for path in paths:
        if path in resolvers:
            continue

        pyproject = _load_pyproject(path)
        if "dependency-groups" not in pyproject:
            raise InstallationError(
                f"[dependency-groups] table was missing from '{path}'. "
                "Cannot resolve '--group' option."
            )
        raw_dependency_groups = pyproject["dependency-groups"]
        if not isinstance(raw_dependency_groups, dict):
            raise InstallationError(
                f"[dependency-groups] table was malformed in {path}. "
                "Cannot resolve '--group' option."
            )

        resolvers[path] = DependencyGroupResolver(raw_dependency_groups)
    return resolvers


def _load_pyproject(path: str) -> dict[str, Any]:
    """
    This helper loads a pyproject.toml as TOML.

    It raises an InstallationError if the operation fails.
    """
    try:
        with open(path, "rb") as fp:
            return tomllib.load(fp)
    except FileNotFoundError:
        raise InstallationError(f"{path} not found. Cannot resolve '--group' option.")
    except tomllib.TOMLDecodeError as e:
        raise InstallationError(f"Error parsing {path}: {e}") from e
    except OSError as e:
        raise InstallationError(f"Error reading {path}: {e}") from e
