# Push this folder to GitHub

Unzip `Investment_Planner_repo.zip`, open a terminal in the unzipped folder, then:

```bash
# if the repo on GitHub is still empty
git init -b main
git add .
git commit -m "Goalwright: consumer app, agent console, runnable demo"
git remote add origin https://github.com/aditig2024-lab/Investment_Planner.git
git push -u origin main
```

```bash
# if the repo already has commits (e.g. a README created on GitHub)
git clone https://github.com/aditig2024-lab/Investment_Planner.git
# copy everything from the unzipped folder into the clone (overwrite README.md), then
cd Investment_Planner
git add .
git commit -m "Goalwright: consumer app, agent console, runnable demo"
git push
```

Then, once:
1. **GitHub Pages** — Settings → Pages → Source: *Deploy from a branch* → `main` / `/ (root)` → Save.
   Live in ~1 minute at https://aditig2024-lab.github.io/Investment_Planner/ (app) and …/console.html (console).
2. **Claude artifacts** — open each artifact link in the README → *Share* → *Anyone with the link*.
   (The HTML-preview links in the README work immediately for a public repo, no setup.)
