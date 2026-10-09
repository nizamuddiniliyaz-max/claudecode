"""Defaults. Weights follow the brief and are adjustable, not proven predictors."""

WEIGHTS = {
    "audience_match": 0.25,
    "answer_completeness": 0.25,
    "hook_clarity": 0.20,
    "standalone": 0.15,
    "specificity": 0.15,
}

# 8 GB RAM laptop defaults: small model, int8, no parallel steps.
WHISPER_MODEL = "small"
WHISPER_COMPUTE = "int8"
WHISPER_BATCH = 4

LLM_MODEL = "claude-sonnet-5-5"
CHUNK_SECONDS = 600  # transcript window sent to the LLM
CHUNK_OVERLAP = 60

FILLERS = {"um", "uh", "umm", "uhh", "er", "erm", "ah", "hmm"}
FILLER_PHRASES = [("you", "know"), ("i", "mean"), ("kind", "of"), ("sort", "of")]
MIN_PAUSE = 1.2  # seconds of dead air worth flagging
CLIP_MIN, CLIP_MAX = 20.0, 100.0
