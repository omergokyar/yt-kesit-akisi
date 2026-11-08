"""Bir bolumdeki sahne/plan kesimlerini bulur.

Kullanim: python scripts/scenes.py <video> <cikti_klasoru>
Cikti: scenes.json ([{start, end}, ...] saniye cinsinden)
"""
import argparse
import json
import sys
from pathlib import Path

from scenedetect import AdaptiveDetector, SceneManager, open_video

sys.stdout.reconfigure(encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video", type=Path)
    ap.add_argument("out", type=Path)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    video = open_video(str(args.video))
    manager = SceneManager()
    manager.add_detector(AdaptiveDetector())
    manager.detect_scenes(video, show_progress=False)
    scenes = [
        {"start": round(a.seconds, 3), "end": round(b.seconds, 3)}
        for a, b in manager.get_scene_list()
    ]
    (args.out / "scenes.json").write_text(json.dumps(scenes, indent=0), encoding="utf-8")
    lengths = [s["end"] - s["start"] for s in scenes]
    print(f"BITTI: {len(scenes)} plan, ortalama {sum(lengths) / len(lengths):.1f} sn")


if __name__ == "__main__":
    main()
