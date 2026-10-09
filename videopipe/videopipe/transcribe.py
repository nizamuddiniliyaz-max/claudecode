"""WhisperX wrapper. Runs locally. Diarization needs a HF token (model download only)."""
import json
import os
import subprocess
import tempfile
from pathlib import Path

from . import config
from .project import source_file


def extract_audio(video: Path, wav: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(video), "-ac", "1", "-ar", "16000", str(wav)],
        check=True,
    )


def normalize(result: dict, language: str) -> dict:
    """Flatten WhisperX output into the pipeline's transcript schema."""
    words, segments = [], []
    for si, seg in enumerate(result["segments"]):
        segments.append({"id": si, "start": seg["start"], "end": seg["end"],
                         "text": seg["text"].strip(), "speaker": seg.get("speaker")})
        for w in seg.get("words", []):
            if "start" not in w:  # alignment failed for this token (numbers, symbols)
                continue
            words.append({"w": w["word"], "start": w["start"], "end": w["end"],
                          "speaker": w.get("speaker", seg.get("speaker")),
                          "score": round(w.get("score", 0), 3), "seg": si})
    return {"language": language, "words": words, "segments": segments}


def transcribe(proj: Path, model: str = config.WHISPER_MODEL, device: str = "auto",
               diarize: bool = True, min_speakers=None, max_speakers=None) -> Path:
    import whisperx  # lazy: heavy optional dependency

    if device == "auto":
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
    compute = config.WHISPER_COMPUTE if device == "cpu" else "float16"
    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "audio.wav"
        extract_audio(source_file(proj), wav)
        audio = whisperx.load_audio(str(wav))
        m = whisperx.load_model(model, device, compute_type=compute)
        result = m.transcribe(audio, batch_size=config.WHISPER_BATCH)
        del m  # free memory before alignment (8 GB RAM)
        lang = result["language"]
        am, meta = whisperx.load_align_model(language_code=lang, device=device)
        result = whisperx.align(result["segments"], am, meta, audio, device)
        del am
        if diarize:
            token = os.environ.get("HF_TOKEN")
            if not token:
                raise SystemExit("Diarization needs HF_TOKEN (read token, model terms accepted). "
                                 "Re-run with --no-diarize to skip.")
            from whisperx.diarize import DiarizationPipeline
            dia = DiarizationPipeline(use_auth_token=token, device=device)
            result = whisperx.assign_word_speakers(
                dia(audio, min_speakers=min_speakers, max_speakers=max_speakers), result)
    out = Path(proj) / "transcript" / "transcript.json"
    out.write_text(json.dumps(normalize(result, lang), indent=1))
    return out
