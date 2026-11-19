#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Thin tail. The matrix is still v0100. This file only puts the accelerator import in the syntax tree."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def load_accel():
    import VIA_SuperAccel_Module as via_accel
    return via_accel


def prior():
    path = Path(__file__).with_name("VDF_MDL026_InputApiMatrix_v0100.py")
    spec = importlib.util.spec_from_file_location("vdf_matrix_v0100", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(argv=None) -> int:
    return prior().main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
