"""Private stages of SUP_MDL743; the public entry is VCGC layout."""
# [VIA:ACCEL-BRIDGE] Share the hub's canonical bridge; no install or network consent.
try:
    import VIA_SuperAccel_Module as VIA_ACCEL
except ImportError:
    VIA_ACCEL = None
