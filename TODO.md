# SafeScan — Pre-deployment Checklist

## Local smoke test
- [x] `pip install -r requirements.txt` succeeds in fresh venv
- [ ] `streamlit run frontend/app.py` opens on `http://localhost:8501` without import errors
- [ ] Sidebar shows the API-key input and Privacy notes
- [ ] Without a key: hero shows the yellow warning banner, all Run/Extract buttons are disabled
- [ ] With a key pasted: warning disappears, buttons enable

## Functional checks
- [ ] **Label Scan**: upload a photo → extraction returns a comma-separated list with a product_type
- [ ] Extracted text is editable in the textarea
- [ ] Each analyzer tab: **Load from label scan** populates the input
- [ ] Each analyzer tab: **Load sample** populates the input with the bundled example
- [ ] Each analyzer tab: **Run analysis** returns a valid response with banner + per-ingredient findings
- [ ] HIGH and MEDIUM ingredient cards auto-expand; LOW and MINIMAL stay collapsed
- [ ] Running the same analyzer twice shows non-zero `cache_read_tokens` on the second call

## Security & secrets
- [ ] `.env` is in `.gitignore` (already configured)
- [ ] `.env` is not in the git history: `git log --all -- .env` returns empty
- [ ] `.env.example` contains a placeholder, never a real key
- [ ] Any API key that has appeared in screenshots, screen-shares, chat history, or commits has been **revoked** at console.anthropic.com
- [ ] No `.streamlit/secrets.toml` checked in

## GitHub
- [ ] Repository initialized (`git init`) at the project root
- [ ] Initial commit excludes `venv/`, `.env`, `__pycache__/`, `sample image.jpg` (optional — decide whether to include)
- [ ] Remote set: `git remote add origin git@github.com:<you>/<repo>.git`
- [ ] First push: `git push -u origin main`
- [ ] README renders cleanly on the repo page

## Streamlit Community Cloud deploy
- [ ] Signed in to [share.streamlit.io](https://share.streamlit.io) with the same GitHub account
- [ ] **New app** → repo selected → main file `frontend/app.py`
- [ ] Python version set to 3.11+
- [ ] **Secrets left empty** — this is what makes the demo BYOK
- [ ] App deploys successfully (check build log for missing imports)
- [ ] Live URL works: `https://<app-name>.streamlit.app`
- [ ] Sidebar BYOK flow works end-to-end on the deployed instance
