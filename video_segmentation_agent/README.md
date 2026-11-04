# Video Segmentation Agent v0.1

End-to-end baseline: video → FFmpeg audio → faster-whisper Bangla ASR → timestamped transcript → microchunks → one-call-per-chunk constrained taxonomy tagging → optional visual/semantic cues → boundary scoring → merged coherent segments → per-video outputs + master `segments.json`.

All intermediate artifacts are stored under `data/videos/processed/<video_id>/` for auditability.

The visual and semantic modules are implemented but disabled by default in v0.1 so the baseline can be evaluated before adding more cues.
