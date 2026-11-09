"""Render the first frame of every level of the ARC-AGI-3 public games and
extract simple visual features for annotating which levels add new elements.

Loads each game the way the official arc_agi toolkit does (exec of the game
source, class named from the game id), jumps to each level with set_level(),
and takes the frames returned by a level RESET. Writes:
  frames/<game>.png      one row per game, every level side by side
  features.json          per-level features (colors, object shapes, novelty)

Usage: python -I render_levels.py <environment_files dir> <output dir>
"""

import glob
import hashlib
import importlib.util
import json
import os
import sys
from collections import Counter, deque

import numpy as np
from PIL import Image, ImageDraw

os.environ["ONLY_RESET_LEVELS"] = "true"  # RESET restarts the current level

from arcengine import ActionInput, ARCBaseGame, GameAction  # noqa: E402

# arc_agi/rendering.py COLOR_MAP
PALETTE = [
    "#FFFFFF", "#CCCCCC", "#999999", "#666666", "#333333", "#000000",
    "#E53AA3", "#FF7BCC", "#F93C31", "#1E93FF", "#88D8F1", "#FFDC00",
    "#FF851B", "#921231", "#4FCC30", "#A356D6",
]
PALETTE_RGB = np.array([[int(c[i:i + 2], 16) for i in (1, 3, 5)] for c in PALETTE], dtype=np.uint8)
SMALL_OBJECT_AREA = 64  # components up to this many cells count as objects
SCALE, GAP, LABEL_H = 4, 8, 14


def load_game(meta_path):
    meta = json.load(open(meta_path))
    game_id = meta["game_id"]
    first_four = game_id[:4]
    class_name = first_four[0].upper() + first_four[1:]
    src_dir = os.path.dirname(meta_path)
    game_file = os.path.join(src_dir, f"{class_name.lower()}.py")
    spec = importlib.util.spec_from_loader(f"arc_agi_3.{game_id}", loader=None)
    module = importlib.util.module_from_spec(spec)
    exec(open(game_file, encoding="utf-8").read(), module.__dict__)
    cls = getattr(module, class_name)
    assert issubclass(cls, ARCBaseGame)
    return meta, cls()


def components(frame, background):
    """4-connected components of each non-background color."""
    h, w = frame.shape
    seen = np.zeros_like(frame, dtype=bool)
    out = []
    for y in range(h):
        for x in range(w):
            c = frame[y, x]
            if seen[y, x] or c == background:
                continue
            cells, q = [], deque([(y, x)])
            seen[y, x] = True
            while q:
                cy, cx = q.popleft()
                cells.append((cy, cx))
                for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                    if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] and frame[ny, nx] == c:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            ys, xs = zip(*cells)
            y0, x0 = min(ys), min(xs)
            mask = np.zeros((max(ys) - y0 + 1, max(xs) - x0 + 1), dtype=np.uint8)
            mask[np.array(ys) - y0, np.array(xs) - x0] = 1
            shape = hashlib.sha1(mask.tobytes() + bytes(mask.shape)).hexdigest()[:10]
            out.append({"color": int(c), "area": len(cells), "shape": shape})
    return out


def features(frame):
    counts = Counter(frame.flatten().tolist())
    background = max(counts, key=counts.get)
    comps = components(frame, background)
    small = [c for c in comps if c["area"] <= SMALL_OBJECT_AREA]
    return {
        "background": int(background),
        "colors": sorted(int(c) for c in counts),
        "object_types": sorted({f'{c["color"]}:{c["shape"]}' for c in small}),
        "object_shapes": sorted({c["shape"] for c in small}),
        "region_colors": sorted({c["color"] for c in comps if c["area"] > SMALL_OBJECT_AREA}),
        "n_components": len(comps),
    }


def level_frames(game, index):
    game.set_level(index)
    data = game.perform_action(ActionInput(id=GameAction.RESET), raw=True)
    return [np.asarray(f) for f in data.frame]


def tile(game_id, frames, baselines):
    cell = 64 * SCALE
    img = Image.new("RGB", (len(frames) * (cell + GAP), cell + LABEL_H), "white")
    draw = ImageDraw.Draw(img)
    for i, f in enumerate(frames):
        x = i * (cell + GAP)
        draw.text((x + 2, 1), f"{game_id[:4]} L{i + 1}  human={baselines[i]}", fill="black")
        if f is None:
            draw.text((x + 4, LABEL_H + 4), "render failed", fill="red")
            continue
        rgb = PALETTE_RGB[np.clip(f, 0, 15)]
        img.paste(Image.fromarray(rgb).resize((cell, cell), Image.NEAREST), (x, LABEL_H))
    return img


def main(env_dir, out_dir):
    os.makedirs(os.path.join(out_dir, "frames"), exist_ok=True)
    games = []
    for meta_path in sorted(glob.glob(os.path.join(env_dir, "*", "*", "metadata.json"))):
        meta, game = load_game(meta_path)
        baselines = meta["baseline_actions"]
        n = len(game._levels)
        record = {"game_id": meta["game_id"], "tags": meta.get("tags"), "n_levels": n,
                  "baseline_actions": baselines, "available_actions": list(game._available_actions),
                  "levels": []}
        seen_colors, seen_types, seen_shapes, seen_regions = set(), set(), set(), set()
        last_frames = []
        for i in range(n):
            entry = {"level": i + 1, "human_baseline": baselines[i] if i < len(baselines) else None}
            try:
                frames = level_frames(game, i)
                f = frames[-1]
                feat = features(f)
                entry.update(feat)
                entry["frames_on_reset"] = len(frames)
                if i > 0:
                    entry["new_colors"] = sorted(set(feat["colors"]) - seen_colors)
                    entry["new_object_types"] = len(set(feat["object_types"]) - seen_types)
                    entry["new_object_shapes"] = len(set(feat["object_shapes"]) - seen_shapes)
                    entry["new_region_colors"] = sorted(set(feat["region_colors"]) - seen_regions)
                seen_colors |= set(feat["colors"])
                seen_types |= set(feat["object_types"])
                seen_shapes |= set(feat["object_shapes"])
                seen_regions |= set(feat["region_colors"])
                last_frames.append(f)
            except Exception as e:  # keep going; record the failure
                entry["error"] = f"{type(e).__name__}: {e}"[:300]
                last_frames.append(None)
            record["levels"].append(entry)
        tile(meta["game_id"], last_frames, baselines).save(
            os.path.join(out_dir, "frames", f'{meta["game_id"][:4]}.png'))
        games.append(record)
        errs = sum(1 for e in record["levels"] if "error" in e)
        print(f'{meta["game_id"]:16} levels={n} render_errors={errs}')
    json.dump(games, open(os.path.join(out_dir, "features.json"), "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
