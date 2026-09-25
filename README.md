# 🎬 Movies dataset template

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

## VIA HTML UI

The repository also contains the tested, local-only VIA standardized HTML UI package in [`VIA_HTML_UI/`](./VIA_HTML_UI/). Open [`VIA_HTML_UI/ui/VIA-Complete-System.html`](./VIA_HTML_UI/ui/VIA-Complete-System.html) directly from `file://` to access the central management UI and SYNCHRONIZER. The package includes the cross-device E2E runner, cross-page synchronization test, offline smoke test, and complete-system quality gate documented in [`VIA_HTML_UI/REPOSITORY-INTEGRATION.md`](./VIA_HTML_UI/REPOSITORY-INTEGRATION.md).
