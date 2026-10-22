"""Build only the public browser app and model into dist/ (no raw datasets)."""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
output = ROOT / 'dist'
artifact = ROOT / 'artifacts' / 'model.json'
model = json.loads(artifact.read_text())
assert model['inference']['players'], 'Train the model before building Pages.'
output.mkdir(exist_ok=True)
for name in ('index.html', 'styles.css', 'app.js', 'model.mjs'):
    shutil.copy2(ROOT / 'web' / name, output / name)
shutil.copy2(artifact, output / 'model.json')
(output / '.nojekyll').touch()
print(f'Built {output} with {len(model["inference"]["players"])} players')
