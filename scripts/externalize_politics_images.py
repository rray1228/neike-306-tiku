"""Keep politics text bundles small; retain exact original WebP image bytes."""
import base64
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
assets = root / 'public/politics/reference-pages'
assets.mkdir(parents=True, exist_ok=True)
prefix = 'data:image/webp;base64,'
written = set()


def externalize(value):
    if isinstance(value, str) and value.startswith(prefix):
        image = base64.b64decode(value[len(prefix):], validate=True)
        assert image[:4] == b'RIFF' and image[8:12] == b'WEBP'
        name = hashlib.sha256(image).hexdigest()[:24] + '.webp'
        (assets / name).write_bytes(image)
        written.add(name)
        return '/politics/reference-pages/' + name
    if isinstance(value, dict):
        return {key: externalize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [externalize(item) for item in value]
    return value


for path in sorted((root / 'src/data').glob('politics*.json')):
    data = externalize(json.loads(path.read_text()))
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
print(f'Externalized {len(written)} unique original images.')
