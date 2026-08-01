# 🎬 Movies dataset template

## VIA · 一鍵全包 One PowerShell to handle all

Paste this whole block into **any** Windows PowerShell window (works from a
bare machine — installs git / PowerShell 7 if missing, clones or updates the
repo, then runs the master script `VIA.ps1`, whose default `StartAll` chains
Sync → QA → AutoPlot Workbench → three-round panoramic Launch):

```powershell
$R = "$HOME\Downloads\movies-dataset"
$B = 'claude/via-system-integration-completion-k2lf85'
if (-not (Get-Command git  -ErrorAction SilentlyContinue)) { winget install --id Git.Git -e --accept-source-agreements --accept-package-agreements }
if (-not (Get-Command pwsh -ErrorAction SilentlyContinue)) { winget install --id Microsoft.PowerShell -e --accept-source-agreements --accept-package-agreements }
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
if (Test-Path "$R\.git") { git -C $R fetch origin $B; git -C $R checkout $B; git -C $R pull origin $B }
else { git clone --branch $B https://github.com/tonykuni/movies-dataset.git $R }
pwsh -NoProfile -ExecutionPolicy Bypass -File "$R\VIA.ps1"
```

Day-to-day (repo already present) it reduces to:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File "$HOME\Downloads\movies-dataset\VIA.ps1"
```

See the header of [`VIA.ps1`](VIA.ps1) for all actions
(`StartAll` / `Sync` / `Install` / `QA` / `UI` / `Plot` / `Launch` / `Promote`).

A simple Streamlit app showing movie data from [The Movie Database (TMDB)](https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata). 

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://movies-dataset-template.streamlit.app/)

### How to run it on your own machine

1. Install the requirements

   ```
   $ pip install -r requirements.txt
   ```

2. Run the app

   ```
   $ streamlit run streamlit_app.py
   ```
