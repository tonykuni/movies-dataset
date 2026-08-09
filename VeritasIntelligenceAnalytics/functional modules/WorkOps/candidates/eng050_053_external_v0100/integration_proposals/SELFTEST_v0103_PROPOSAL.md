# selftest v0103 proposal

Add one isolated stage after existing GapFill stage:

1. Build fixture WOP with THR, DEC, MLS.
2. ENG-051 candidate generation creates DEC/MLS candidates but no CMT automatically.
3. Explicit candidate accept issues CMT-0001.
4. ENG-050 register contains DEC/MLS/CMT/THR.
5. ENG-052 clean fixture has no ERROR.
6. Inject closed-WOP/open-MLS contradiction and assert ENG-052 FAIL.
7. ENG-053 produces explainable progress + health with penalties.
8. Fulfill CMT requires evidence; missing evidence must fail.

This stage must run in a temporary sandbox only.
