# CMI Test-Set Showcase

This directory contains:

- `cmi-pref-test.jsonl`: test split metadata from `cmi-pref`
- `comparison_metadata_test.jsonl`: test split metadata from `cmi-pref-pseudo`
- `assets/`: only the audio files used by the showcase page
- `index.html`, `styles.css`, `app.js`: static site files
- `generate_showcase_data.py`: rebuilds `data/samples.json`

## Serve locally

```bash
python3 -m http.server 8000
```

Then open `http://localhost:8000`.

## Anonymous hosting

If you push this directory to a public GitHub repository, an anonymous mirror can be
shared in the same format as:

`https://anonymous.4open.science/w/<repo-name>-<suffix>/`

The site is fully static, so no build step is required.
