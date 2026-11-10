# Demo site

Static click-through demos, published to GitHub Pages by `.github/workflows/pages.yml`.
Only this `site/` folder is deployed.

Live: https://sneha-beepbeep.github.io/CRA-compliance/

```
site/
  index.html                  landing page, one card per product
  assets/css/site.css         shared styles (light/dark, phone-first)
  assets/js/stepper.js        reusable Next/Back stepper
  demos/_template/            copy this to start a new demo
  demos/cra-compliance/       CRA and AI Act Security Tracker walkthrough
```

## Add a demo

1. Copy `demos/_template/` to `demos/<product-slug>/`.
2. Write 5-7 `<section class="step" data-title="…">` blocks: problem, input, result, what it means.
3. Use synthetic data only. No API keys or tokens. Pre-record any LLM output into a JSON or JS file.
4. Keep the banner: `Demo with sample data, not legal advice.` (the deploy fails without it).
5. Add a card to `index.html`.

Stepper hooks: `canLeave[n]` returns `true` or a message to block Next; `onEnter[n]` renders a step. Steps are deep-linkable as `#step-n`.

## Preview locally

```sh
python3 -m http.server -d site 8080
```

Then open http://localhost:8080/.

## Publish (one-time setup)

1. Merge this branch into `main`.
2. On GitHub: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
   Or from a terminal: `gh api -X POST repos/sneha-beepbeep/CRA-compliance/pages -f build_type=workflow`
3. Run the workflow once: **Actions → pages → Run workflow** (or `gh workflow run pages.yml`).
   After that it redeploys on every push to `main` that touches `site/`.
4. Check https://sneha-beepbeep.github.io/CRA-compliance/ and the demo at `/demos/cra-compliance/`.

## Link the demo from GitHub

- **About → Website:** on the repo home page, click the gear next to **About**, paste
  `https://sneha-beepbeep.github.io/CRA-compliance/demos/cra-compliance/`, tick nothing else, save.
  Or: `gh repo edit sneha-beepbeep/CRA-compliance --homepage https://sneha-beepbeep.github.io/CRA-compliance/demos/cra-compliance/`
- **README:** add near the top:
  `**[Try the click-through demo →](https://sneha-beepbeep.github.io/CRA-compliance/demos/cra-compliance/)** (sample data, not legal advice)`
- **Other products:** each product repo links to its own card's demo URL the same way, and gets a card in `index.html`.
