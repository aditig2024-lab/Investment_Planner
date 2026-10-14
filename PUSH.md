# Push, then deploy

## 1. Push (run in PowerShell — short path avoids Windows' 260-character limit)

```powershell
New-Item -ItemType Directory -Force C:\Projects | Out-Null
Expand-Archive -Force .\Investment_Planner_repo.zip C:\Projects\Investment_Planner
cd C:\Projects\Investment_Planner
git init -b main
git add .
git commit -m "Goalwright: Streamlit app, consumer app, agent console, runnable demo"
git remote add origin https://github.com/aditig2024-lab/Investment_Planner.git
git push -u origin main
```

If GitHub already has a commit in the repo:
`git pull origin main --allow-unrelated-histories` (keep this README.md), then `git push -u origin main`.

If you already ran the earlier commands in a folder that already has `.git` and `origin`: just `git add . ; git commit -m "Add Streamlit app" ; git push`.

## 2. Deploy the Streamlit app (one time)

1. https://share.streamlit.io → sign in with GitHub → **Create app** → *Deploy a public app from GitHub*
2. Repository `aditig2024-lab/Investment_Planner` · Branch `main` · Main file path `streamlit_app.py`
3. Choose an app URL (e.g. `goalwright`) → **Deploy**
4. Copy the `https://….streamlit.app` URL into the badge line at the top of README.md's *Live demos* section, commit, push.

## 3. Make the plain-HTML links public too

- GitHub Pages: Settings → Pages → Source *Deploy from a branch* → `main` / `/ (root)` → Save.
- Claude artifacts: open each link in the README → *Share* → *Anyone with the link*.
