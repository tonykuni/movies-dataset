@echo off
rem VIA 統一輪動引擎(回測+自演化+證偽):py via_pipeline --demo;誠實前提=需同伴檔 rotation_engine.py(本批未含,待補)+numpy/pandas
py "%~dp0..\supportive modules\VIA_Pipeline\via_pipeline.py" --demo %*
