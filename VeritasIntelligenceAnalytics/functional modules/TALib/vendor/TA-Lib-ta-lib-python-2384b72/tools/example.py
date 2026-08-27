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
import sys
import numpy as np
import pylab

import talib
from talib.abstract import Function

TEST_LEN = int(sys.argv[1]) if len(sys.argv) > 1 else 100
r = np.arange(TEST_LEN)
idata = np.random.random(TEST_LEN)

def func_example():
    odata = talib.MA(idata)
    upper, middle, lower = talib.BBANDS(idata)
    kama = talib.KAMA(idata)
    plot(odata, upper, middle, lower, kama)

def abstract_example():
    sma = Function('sma')
    input_arrays = sma.get_input_arrays()
    for key in input_arrays.keys():
        input_arrays[key] = idata
    sma.set_input_arrays(input_arrays)
    odata = sma(30) # timePeriod=30, specified as an arg

    bbands = Function('bbands', input_arrays)
    bbands.parameters = {
        'timeperiod': 20,
        'nbdevup': 2,
        'nbdevdn': 2
    }
    upper, middle, lower = bbands() # multiple output values unpacked (these will always have the correct order)

    kama = Function('kama').run(input_arrays) # alternative run() calling method.
    plot(odata, upper, middle, lower, kama)

def plot(odata, upper, middle, lower, kama):
    pylab.plot(r, idata, 'b-', label="original")
    pylab.plot(r, odata, 'g-', label="MA")
    pylab.plot(r, upper, 'r-', label="Upper")
    pylab.plot(r, middle, 'r-', label="Middle")
    pylab.plot(r, lower, 'r-', label="Lower")
    pylab.plot(r, kama, 'g', label="KAMA")
    pylab.legend()
    pylab.show()

if __name__ == '__main__':
    print('All functions (sorted by group):')
    groups = talib.get_function_groups()
    for group, functions in sorted(groups.items()):
        print('%s functions: %s' % (group, functions))

    if len(sys.argv) == 1 or sys.argv[1] == 'func':
        print('Using talib.func')
        func_example()
    else:
        print('Using talib.abstract')
        abstract_example()
