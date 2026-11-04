import argparse
import json
import logging
from pathlib import Path

from .config_loader import load_config
from .video_loader import validate_video, video_manifest
from .metadata_extractor import extract_metadata
from .audio_extractor import extract_audio
from .asr_transcriber import transcribe_audio
from .transcript_normalizer import normalize_asr_segments
from .microchunk_builder import build_microchunks
from .taxonomy_loader import TaxonomyIndex
from .llm_client import LLMClient
from .curriculum_tagger import CurriculumTagger
from .semantic_encoder import adjacent_similarities
from .scene_detector import detect_scenes
from .frame_sampler import sample_frames
from .boundary_detector import build_boundaries
from .segment_merger import merge_chunks
from .segment_validator import validate_segment
from .keyframe_extractor import extract_segment_keyframes
from .segment_store import SegmentStore
from .utils import atomic_write_json, utc_now_iso


AGENT_ROOT = Path(__file__).resolve().parents[1]


def resolve(path_value):
    path = Path(path_value)

    if path.is_absolute():
        return path

    return (AGENT_ROOT / path).resolve()


def main():
    # ---------------------------------------------------------
    # CLI arguments
    # ---------------------------------------------------------
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--video",
        required=True,
    )

    parser.add_argument(
        "--config",
        default=str(
            AGENT_ROOT
            / "config"
            / "segmentation_config.yaml"
        ),
    )

    parser.add_argument(
        "--force",
        action="store_true",
    )

    parser.add_argument(
        "--skip-curriculum",
        action="store_true",
    )

    args = parser.parse_args()

    # ---------------------------------------------------------
    # Load configuration
    # ---------------------------------------------------------
    cfg = load_config(
        args.config
    )

    # ---------------------------------------------------------
    # Logging
    # ---------------------------------------------------------
    log_path = resolve(
        cfg["paths"]["log_file"]
    )

    log_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(message)s"
        ),
        handlers=[
            logging.FileHandler(
                log_path,
                encoding="utf-8",
            ),
            logging.StreamHandler(),
        ],
    )

    logger = logging.getLogger(
        __name__
    )

    # ---------------------------------------------------------
    # Validate video
    # ---------------------------------------------------------
    video = validate_video(
        args.video,
        cfg["video"]["accepted_extensions"],
    )

    manifest = video_manifest(
        video
    )

    video_id = manifest[
        "video_id"
    ]

    workspace = (
        resolve(
            cfg["paths"][
                "processed_video_dir"
            ]
        )
        / video_id
    )

    # ---------------------------------------------------------
    # Workspace directories
    # ---------------------------------------------------------
    dirs = {
        name: workspace / name
        for name in [
            "metadata",
            "audio",
            "transcript",
            "microchunks",
            "curriculum_tags",
            "scenes",
            "frames",
            "embeddings",
            "boundaries",
            "segments",
            "keyframes",
        ]
    }

    for directory in dirs.values():
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    # ---------------------------------------------------------
    # Metadata
    # ---------------------------------------------------------
    metadata = extract_metadata(
        video
    )

    atomic_write_json(
        dirs["metadata"]
        / "metadata.json",
        {
            **manifest,
            **metadata,
        },
    )

    # ---------------------------------------------------------
    # Audio extraction
    # ---------------------------------------------------------
    audio_path = (
        dirs["audio"]
        / "audio.wav"
    )

    if (
        args.force
        or not audio_path.exists()
    ):
        logger.info(
            "Extracting audio"
        )

        extract_audio(
            video,
            audio_path,
            cfg["video"][
                "audio_sample_rate"
            ],
            cfg["video"][
                "audio_channels"
            ],
        )
    else:
        logger.info(
            "Using existing audio: %s",
            audio_path,
        )

    # ---------------------------------------------------------
    # Transcript
    # ---------------------------------------------------------
    transcript_path = (
        dirs["transcript"]
        / "transcript.json"
    )

    if (
        transcript_path.exists()
        and not args.force
    ):
        logger.info(
            "Loading existing transcript: %s",
            transcript_path,
        )

        with transcript_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            transcript = json.load(
                file
            )

    else:
        logger.info(
            "Running ASR transcription"
        )

        transcript = transcribe_audio(
            audio_path,
            cfg["asr"],
        )

        transcript[
            "segments"
        ] = normalize_asr_segments(
            transcript["segments"]
        )

        atomic_write_json(
            transcript_path,
            transcript,
        )

        logger.info(
            "Transcript saved: %s",
            transcript_path,
        )

    # ---------------------------------------------------------
    # Build / load microchunks
    # ---------------------------------------------------------
    microchunks_path = (
        dirs["microchunks"]
        / "microchunks.json"
    )

    if (
        microchunks_path.exists()
        and not args.force
    ):
        logger.info(
            "Loading existing microchunks: %s",
            microchunks_path,
        )

        with microchunks_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            chunks = json.load(
                file
            )

    else:
        logger.info(
            "Building microchunks"
        )

        chunks = build_microchunks(
            transcript["segments"],
            cfg["microchunks"][
                "target_duration_seconds"
            ],
            cfg["microchunks"][
                "max_duration_seconds"
            ],
            cfg["microchunks"][
                "min_text_characters"
            ],
        )

        # Save BEFORE Gemini.
        atomic_write_json(
            microchunks_path,
            chunks,
        )

        logger.info(
            "Saved %s microchunks",
            len(chunks),
        )

    # ---------------------------------------------------------
    # Taxonomy
    # ---------------------------------------------------------
    taxonomy = (
        TaxonomyIndex.from_file(
            resolve(
                cfg["paths"][
                    "taxonomy_file"
                ]
            )
        )
    )

    # ---------------------------------------------------------
    # Curriculum tagging with checkpoint/resume
    # ---------------------------------------------------------
    tags_path = (
        dirs["curriculum_tags"]
        / "chunk_tags.json"
    )

    curriculum_enabled = (
        cfg[
            "curriculum_tagger"
        ].get(
            "enabled",
            True,
        )
        and not args.skip_curriculum
    )

    if curriculum_enabled:
        llm = LLMClient(
            cfg[
                "curriculum_tagger"
            ]
        )

        tagger = CurriculumTagger(
            taxonomy,
            llm,
            resolve(
                cfg["paths"][
                    "prompts_dir"
                ]
            )
            / "chunk_curriculum_tagger.txt",
            cfg[
                "curriculum_tagger"
            ],
        )

        existing_by_id = {}

        # -----------------------------------------------------
        # Resume previous curriculum mappings
        # -----------------------------------------------------
        if (
            tags_path.exists()
            and not args.force
        ):
            try:
                with tags_path.open(
                    "r",
                    encoding="utf-8",
                ) as file:
                    saved_tags = json.load(
                        file
                    )

                for saved_chunk in (
                    saved_tags.get(
                        "chunks",
                        [],
                    )
                ):
                    chunk_id = (
                        saved_chunk.get(
                            "chunk_id"
                        )
                    )

                    mapping = (
                        saved_chunk.get(
                            "curriculum_mapping"
                        )
                    )

                    if (
                        chunk_id
                        and mapping
                    ):
                        existing_by_id[
                            chunk_id
                        ] = mapping

                logger.info(
                    "Loaded %s saved "
                    "curriculum tags",
                    len(
                        existing_by_id
                    ),
                )

            except Exception as exc:
                logger.warning(
                    "Could not load "
                    "curriculum checkpoint: %s",
                    exc,
                )

        # -----------------------------------------------------
        # Tag each microchunk
        # -----------------------------------------------------
        for index, chunk in enumerate(
            chunks,
            start=1,
        ):
            chunk_id = chunk[
                "chunk_id"
            ]

            # Reuse completed tag.
            if (
                chunk_id
                in existing_by_id
            ):
                chunk[
                    "curriculum_mapping"
                ] = existing_by_id[
                    chunk_id
                ]

                logger.info(
                    "Skipping already tagged "
                    "%s/%s %s",
                    index,
                    len(chunks),
                    chunk_id,
                )

                continue

            logger.info(
                "Tagging %s/%s %s",
                index,
                len(chunks),
                chunk_id,
            )

            try:
                chunk[
                    "curriculum_mapping"
                ] = tagger.tag(
                    chunk[
                        "transcript"
                    ]
                )

            except Exception:
                # Save all completed work
                # before exiting.
                atomic_write_json(
                    tags_path,
                    {
                        "video_id":
                            video_id,
                        "chunks":
                            chunks,
                    },
                )

                logger.exception(
                    "Curriculum tagging "
                    "failed at %s. "
                    "Progress saved.",
                    chunk_id,
                )

                raise

            # -------------------------------------------------
            # Checkpoint after every successful Gemini call
            # -------------------------------------------------
            atomic_write_json(
                tags_path,
                {
                    "video_id":
                        video_id,
                    "chunks":
                        chunks,
                },
            )

            logger.info(
                "Checkpoint saved "
                "after %s",
                chunk_id,
            )

    else:
        logger.info(
            "Curriculum tagging skipped"
        )

        atomic_write_json(
            tags_path,
            {
                "video_id":
                    video_id,
                "chunks":
                    chunks,
            },
        )

    # =========================================================
    # IMPORTANT:
    # Everything below runs whether curriculum is enabled
    # or skipped.
    # =========================================================

    # ---------------------------------------------------------
    # Scene detection
    # ---------------------------------------------------------
    if cfg["visual"].get(
        "scene_detection_enabled"
    ):
        scenes = detect_scenes(
            video,
            cfg["visual"][
                "scene_sample_interval_seconds"
            ],
            cfg["visual"][
                "scene_threshold"
            ],
        )
    else:
        scenes = []

    atomic_write_json(
        dirs["scenes"]
        / "scenes.json",
        scenes,
    )

    # ---------------------------------------------------------
    # Frame sampling
    # ---------------------------------------------------------
    if cfg["visual"].get(
        "frame_sampling_enabled"
    ):
        frames = sample_frames(
            video,
            dirs["frames"],
            cfg["visual"][
                "frame_interval_seconds"
            ],
        )

        atomic_write_json(
            dirs["frames"]
            / "frames.json",
            frames,
        )

    # ---------------------------------------------------------
    # Semantic similarities
    # ---------------------------------------------------------
    if cfg["semantic"].get(
        "enabled"
    ):
        similarities = (
            adjacent_similarities(
                chunks
            )
        )
    else:
        similarities = [
            1.0
        ] * max(
            0,
            len(chunks) - 1,
        )

    atomic_write_json(
        dirs["embeddings"]
        / "adjacent_similarity.json",
        similarities,
    )

    # ---------------------------------------------------------
    # Boundary detection
    # ---------------------------------------------------------
    boundaries = build_boundaries(
        chunks,
        cfg[
            "boundary_detection"
        ],
        similarities,
        scenes,
    )

    atomic_write_json(
        dirs["boundaries"]
        / "boundaries.json",
        boundaries,
    )

    # ---------------------------------------------------------
    # Segment merging
    # ---------------------------------------------------------
    segments = merge_chunks(
        video_id,
        chunks,
        boundaries,
        cfg["merging"][
            "max_final_segment_seconds"
        ],
    )

    # ---------------------------------------------------------
    # Segment validation
    # ---------------------------------------------------------
    for segment in segments:
        validate_segment(
            segment,
            taxonomy,
        )

    # ---------------------------------------------------------
    # Optional keyframes
    # ---------------------------------------------------------
    if cfg["visual"].get(
        "keyframe_extraction_enabled"
    ):
        keyframes = (
            extract_segment_keyframes(
                video,
                segments,
                dirs["keyframes"],
            )
        )

        atomic_write_json(
            dirs["keyframes"]
            / "keyframes.json",
            keyframes,
        )

    # ---------------------------------------------------------
    # Per-video segments.json
    # ---------------------------------------------------------
    per_video_output = {
        "video_id":
            video_id,

        "taxonomy_version":
            taxonomy.content_version,

        "generated_at":
            utc_now_iso(),

        "segments":
            segments,
    }

    atomic_write_json(
        dirs["segments"]
        / "segments.json",
        per_video_output,
    )

    # ---------------------------------------------------------
    # Master segment registry
    # ---------------------------------------------------------
    store = SegmentStore(
        resolve(
            cfg["paths"][
                "segment_store"
            ]
        ),
        resolve(
            cfg["paths"][
                "segment_backup_dir"
            ]
        ),
    )

    store.upsert_video(
        {
            **manifest,
            **metadata,
            "processed_at":
                utc_now_iso(),
            "workspace":
                str(workspace),
        },
        segments,
    )

    store.save(
        cfg["storage"].get(
            "create_backup_before_write",
            True,
        )
    )

    # ---------------------------------------------------------
    # Final summary
    # ---------------------------------------------------------
    print(
        f"\nVideo ID: {video_id}\n"
        f"ASR segments: "
        f"{len(transcript['segments'])}\n"
        f"Microchunks: "
        f"{len(chunks)}\n"
        f"Final segments: "
        f"{len(segments)}\n"
        f"Workspace: "
        f"{workspace}"
    )


if __name__ == "__main__":
    main()