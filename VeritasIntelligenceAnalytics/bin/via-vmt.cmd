@echo off
rem VIA Master Engine: VMT family orchestrator (colocated with its engines; graceful-skip on missing deps)
py "%~dp0..\supportive modules\VMT_SuperBOM\via_master_engine.py" %*
