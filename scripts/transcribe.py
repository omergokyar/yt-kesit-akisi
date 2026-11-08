"""Bir bolumun Farsca dokumunu cikarir (yerel GPU, faster-whisper).

Kullanim: python scripts/transcribe.py <video> <cikti_klasoru> [--model large-v3]
Cikti: transcript.json (kelime zamanli), transcript.fa.srt, transcript.compact.txt
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

import torch  # CUDA DLL'leri icin faster_whisper'dan once yuklenmeli

os.environ["PATH"] = str(Path(torch.__file__).parent / "lib") + os.pathsep + os.environ["PATH"]

from faster_whisper import WhisperModel  # noqa: E402

from zaman import duzelt  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")


def srt_time(seconds: float) -> str:
    ms = round(seconds * 1000)
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--model", default="large-v3")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    model = WhisperModel(args.model, device="cuda", compute_type="float16")
    started = time.time()
    segments, info = model.transcribe(
        str(args.video),
        language="fa",
        beam_size=5,
        word_timestamps=True,
        condition_on_previous_text=False,  # tekrar/halusinasyon dongulerini azaltir
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
    )

    result = []
    for seg in segments:
        result.append(
            {
                "start": round(seg.start, 2),
                "end": round(seg.end, 2),
                "text": seg.text.strip(),
                "avg_logprob": round(seg.avg_logprob, 3),
                "no_speech_prob": round(seg.no_speech_prob, 3),
                "words": [
                    {"start": round(w.start, 2), "end": round(w.end, 2), "word": w.word, "p": round(w.probability, 3)}
                    for w in (seg.words or [])
                ],
            }
        )
        print(f"{seg.end / info.duration:6.1%}  {srt_time(seg.start)[:8]}", flush=True)

    print(f"zaman duzeltmesi: {duzelt(result)} segment", flush=True)
    (args.out / "transcript.compact.txt").write_text(
        "\n".join(f"{int(s['start']) // 60:02}:{int(s['start']) % 60:02} {s['text']}" for s in result), encoding="utf-8"
    )
    meta = {"model": args.model, "duration": info.duration, "source": args.video.name, "elapsed_s": round(time.time() - started)}
    (args.out / "transcript.json").write_text(
        json.dumps({"meta": meta, "segments": result}, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    srt = "\n".join(
        f"{i}\n{srt_time(s['start'])} --> {srt_time(s['end'])}\n{s['text']}\n" for i, s in enumerate(result, 1)
    )
    (args.out / "transcript.fa.srt").write_text(srt, encoding="utf-8")
    print(f"BITTI: {len(result)} segment, {meta['elapsed_s']} sn")


if __name__ == "__main__":
    main()
