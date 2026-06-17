# Graph Report - .  (2026-06-14)

## Corpus Check
- 68 files · ~42,388 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 792 nodes · 2063 edges · 30 communities (26 shown, 4 thin omitted)
- Extraction: 68% EXTRACTED · 32% INFERRED · 0% AMBIGUOUS · INFERRED: 654 edges (avg confidence: 0.55)
- Token cost: 138,942 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Pixel Redaction & Config|Pixel Redaction & Config]]
- [[_COMMUNITY_Audit Log Subsystem|Audit Log Subsystem]]
- [[_COMMUNITY_Synthetic PHI Test Fixtures|Synthetic PHI Test Fixtures]]
- [[_COMMUNITY_De-id Pipeline Orchestration (cross-repo)|De-id Pipeline Orchestration (cross-repo)]]
- [[_COMMUNITY_Pixel Write-back|Pixel Write-back]]
- [[_COMMUNITY_Post-hoc Verification|Post-hoc Verification]]
- [[_COMMUNITY_3D-Render Pruning Gap (cross-repo)|3D-Render Pruning Gap (cross-repo)]]
- [[_COMMUNITY_Audit Log Data Model|Audit Log Data Model]]
- [[_COMMUNITY_Header Anonymization Rules|Header Anonymization Rules]]
- [[_COMMUNITY_Frame Contract & View Classifier (cross-repo)|Frame Contract & View Classifier (cross-repo)]]
- [[_COMMUNITY_Anonymization Tests|Anonymization Tests]]
- [[_COMMUNITY_Config Loading & Tests|Config Loading & Tests]]
- [[_COMMUNITY_Date-Offset Tests|Date-Offset Tests]]
- [[_COMMUNITY_OCR Residual-Text Audit|OCR Residual-Text Audit]]
- [[_COMMUNITY_CLI Entry Point|CLI Entry Point]]
- [[_COMMUNITY_Private Tag Policy|Private Tag Policy]]
- [[_COMMUNITY_Pixel Blackout Processors|Pixel Blackout Processors]]
- [[_COMMUNITY_Pseudonym Linkage Tests|Pseudonym Linkage Tests]]
- [[_COMMUNITY_Banner Measurement Tool|Banner Measurement Tool]]
- [[_COMMUNITY_Design Rationale & Docs|Design Rationale & Docs]]
- [[_COMMUNITY_Pixel Processor Protocol|Pixel Processor Protocol]]
- [[_COMMUNITY_Uncompressed Write-back|Uncompressed Write-back]]
- [[_COMMUNITY_Package Init (dicom_deid)|Package Init (dicom_deid)]]

## God Nodes (most connected - your core abstractions)
1. `FixedRegionBlackoutProcessor` - 55 edges
2. `FractionalRegion` - 54 edges
3. `CompositePixelProcessor` - 49 edges
4. `OCRAuditProcessor` - 49 edges
5. `NoOpPixelProcessor` - 48 edges
6. `PixelProcessor` - 43 edges
7. `DynamicBannerBlackoutProcessor` - 42 edges
8. `ConfigError` - 35 edges
9. `PixelResult` - 35 edges
10. `AuditLog` - 33 edges

## Surprising Connections (you probably didn't know these)
- `read_video()` --references--> `opencv-python-headless==4.5.5.64`  [INFERRED]
  src/data.py → requirements.txt
- `DynamicBannerBlackoutProcessor` --conceptually_related_to--> `banner_blackout mode auto (margin/fallback)`  [INFERRED]
  src/dicom_deid/pixel/blackout.py → configs/default.yaml
- `DynamicBannerBlackoutProcessor` --references--> `SequenceOfUltrasoundRegions (0018,6011)`  [EXTRACTED]
  src/dicom_deid/pixel/blackout.py → README.md
- `Pydantic config schema (extra=forbid)` --references--> `configs/default.yaml (baseline production config)`  [EXTRACTED]
  src/dicom_deid/config.py → configs/default.yaml
- `anonymize.py TAG_RULES (PS 3.15 rule table)` --conceptually_related_to--> `ps3_15 options (retain longitudinal/device/characteristics)`  [INFERRED]
  src/dicom_deid/header/anonymize.py → configs/default.yaml

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **prune() ordered exclusion checks** — prune__prune, prune__is_3d, prune__classify_probe, prune__min_frames [EXTRACTED 1.00]
- **32-frame cross-repo contract** — prune__min_frames, data, stage_avis [EXTRACTED 1.00]
- **Pruning to de-id to classifier flow** — pruning, dicom_deidentification, view_classifier [EXTRACTED 1.00]

## Communities (30 total, 4 thin omitted)

### Community 0 - "Pixel Redaction & Config"
Cohesion: 0.08
Nodes (101): config.build_pixel_processor factory, Pydantic config schema (extra=forbid), OCR audit runs on post-blackout frames, pixel/base.py PixelProcessor Protocol + PixelResult, OCRAuditProcessor (easyOCR), BaseModel, ApplyToFields, AuditConfig (+93 more)

### Community 1 - "Audit Log Subsystem"
Cohesion: 0.06
Nodes (74): ActionCode, ActionCode, _count_actions(), _file_record_to_dict(), FileRecord, PHI-free audit log writer for the dicom-deid pipeline.  Records every action the, Render a FileRecord as a JSON-safe dict.      Tag tuples render as 8-char upperc, What was done to a single DICOM tag. (+66 more)

### Community 2 - "Synthetic PHI Test Fixtures"
Cohesion: 0.06
Nodes (71): FileDataset, _attach_pixel_data(), _attach_us_region(), create_minimal_dicom(), create_phi_laden_test_file(), find_injected_phi(), inject_phi_into(), Synthetic PHI injection for testing the de-identification pipeline.  This module (+63 more)

### Community 3 - "De-id Pipeline Orchestration (cross-repo)"
Cohesion: 0.06
Nodes (57): _discover_dicom_files(), _extract_us_region(), _has_dicm_marker(), _process_one_file(), Pipeline orchestrator.  Walks an input directory, processes each DICOM file thro, Run the de-identification pipeline on a directory.      Args:         input_dir:, Yield DICOM files inside ``input_dir`` in deterministic order.      A file is co, Return the bounding box (x0, y0, x1, y1) that covers all ultrasound     regions (+49 more)

### Community 4 - "Pixel Write-back"
Cohesion: 0.08
Nodes (50): _describe(), _has_color_channel(), Write a modified pixel array back into a DICOM as **uncompressed** data.  Philip, Replace ``ds`` pixel data with ``array``, stored uncompressed.      Mutates ``ds, Return ``(n_frames, rows, columns, samples_per_pixel)``., write_pixels_uncompressed(), Dataset, ndarray (+42 more)

### Community 5 - "Post-hoc Verification"
Cohesion: 0.07
Nodes (44): _check_action_consistency(), _check_alignment(), _check_deid_markers(), _check_pseudonym_formats(), _collect_present_tags(), Issue, main(), Post-hoc verification of a ``dicom-deid`` run.  Takes an audit log JSON file and (+36 more)

### Community 6 - "3D-Render Pruning Gap (cross-repo)"
Cohesion: 0.06
Nodes (43): 3D Render Filter Plan (tabled), 3D renders exported as 2D US Multi-frame (known gap), DERIVED + no-ultrasound-regions discriminator, SequenceOfUltrasoundRegions (0018,6011), Color-space double-conversion guard, DataElement, dicom-deid conda env (Python 3.11), Ordered exclusion rules (first match wins) (+35 more)

### Community 7 - "Audit Log Data Model"
Cohesion: 0.09
Nodes (32): FileRecord / TagAction data model, PHI-free audit log by construction, AuditLog, Add one file's audit record to this run., Write the JSON + CSV files and return their paths.          Idempotent: calling, Accumulates per-file records; writes JSON + CSV on finalization.      Use as a c, BaseException, Counter (+24 more)

### Community 8 - "Header Anonymization Rules"
Cohesion: 0.06
Nodes (40): anonymize._coerce_age_90plus, anonymize.py TAG_RULES (PS 3.15 rule table), audit/log.py AuditLog (PHI-free), AVI export gated on pixels_modified, cli.py (dicom-deid command, typer), JPEG/YBR color space correction trap, conda run --no-capture-output on Windows, date_offset.py DateOffsetter (per-patient date shift) (+32 more)

### Community 9 - "Frame Contract & View Classifier (cross-repo)"
Cohesion: 0.07
Nodes (31): src/data.py (N_FRAMES * SAMPLE_PERIOD), _MIN_FRAMES = 32 (cross-repo contract), integration/stage_avis.py (decode-based safety net), CLASS_LIST (model output contract / class order), Fixed clip sampling (16 frames, sample_period=2, min 32 frames), DICOM DEIDENTIFICATION sibling project, echonet/tee-view-classifier (upstream fork source), Fork patch: check cap.read() success flag (+23 more)

### Community 10 - "Anonymization Tests"
Cohesion: 0.20
Nodes (28): _add_unknown_tag(), _apply(), Dataset, Tests for ``header.anonymize``.  Properties pinned down:  1. Patient identifier-, test_accession_number_emptied_not_removed(), test_age_90_capped_at_090y(), test_age_under_90_passes_through(), test_device_serial_number_always_removed() (+20 more)

### Community 11 - "Config Loading & Tests"
Cohesion: 0.24
Nodes (24): load_config(), Load and validate a YAML config file.      Raises:         ConfigError: if the f, Path, Tests for ``config.load_config`` and the Pydantic schema.  Two complementary pro, A misspelled Option name must be rejected (extra=forbid + enum).      This is th, Above the 3650-day cap (~10 years)., test_allowlist_hex_pairs_loaded_as_tuples(), test_empty_allowlist_is_valid() (+16 more)

### Community 13 - "OCR Residual-Text Audit"
Cohesion: 0.17
Nodes (14): _crop_frame(), _default_reader_factory(), _frame_hw(), _OCRReader, ``OCRAuditProcessor`` — residual-text audit pass after blackout.  Runs OCR on a, Return up to ``n`` (index, frame) pairs spread across all frames., Crop a single frame to the ultrasound sector bounding box., Minimal interface we need from an OCR engine. (+6 more)

### Community 14 - "CLI Entry Point"
Cohesion: 0.12
Nodes (15): callback, main(), Command-line entry point for the ``dicom-deid`` pipeline.  Thin wrapper around `, De-identify a directory of DICOM files using the supplied config., _version_callback(), Allow ``python -m dicom_deid`` to invoke the CLI.  The console-script entry poin, is_eager, dir_okay (+7 more)

### Community 15 - "Private Tag Policy"
Cohesion: 0.23
Nodes (15): apply_private_tag_policy(), Private tag policy.  DICOM tags whose group number is odd are *private* — define, Apply the configured private-tag policy to a dataset in place.      Args:, _dataset_with_public_and_private(), Dataset, Tests for ``header.private_tags``.  Properties pinned down:  1. ``STRICT_REMOVE`, A small dataset with mixed public and private tags for most tests., test_allowlist_records_detail_field() (+7 more)

### Community 16 - "Pixel Blackout Processors"
Cohesion: 0.24
Nodes (10): dtype, _black_value(), _clamp(), _locate_image_axes(), Pixel PHI redaction processors.  ``FixedRegionBlackoutProcessor`` — blacks out o, Return ``(height, width, row_axis, col_axis)`` for any DICOM array shape.      H, The pixel value that reads as black in the given color space., Any (+2 more)

### Community 18 - "Banner Measurement Tool"
Cohesion: 0.40
Nodes (4): load_first_frame(), main(), ndarray, Path

### Community 19 - "Design Rationale & Docs"
Cohesion: 0.50
Nodes (4): dicom-deid portable de-identification pipeline, Portability as the scientific contribution, Two-phase de-identification design, docs/architecture.md (design walk-through)

### Community 20 - "Pixel Processor Protocol"
Cohesion: 0.50
Nodes (3): Apply this processor's logic to one DICOM's pixel data.          Args:, Any, ndarray

## Knowledge Gaps
- **34 isolated node(s):** `Path`, `torch>=1.12`, `torchvision>=0.13`, `CLAUDE.md project guidance`, `Path` (+29 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `run_pipeline()` connect `De-id Pipeline Orchestration (cross-repo)` to `Pixel Redaction & Config`, `Audit Log Subsystem`, `Synthetic PHI Test Fixtures`, `Post-hoc Verification`, `3D-Render Pruning Gap (cross-repo)`, `Audit Log Data Model`, `CLI Entry Point`?**
  _High betweenness centrality (0.132) - this node is a cross-community bridge._
- **Why does `AuditLog` connect `Audit Log Data Model` to `Audit Log Subsystem`, `De-id Pipeline Orchestration (cross-repo)`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Why does `prune() exclusion pipeline` connect `3D-Render Pruning Gap (cross-repo)` to `Frame Contract & View Classifier (cross-repo)`, `De-id Pipeline Orchestration (cross-repo)`?**
  _High betweenness centrality (0.081) - this node is a cross-community bridge._
- **Are the 47 inferred relationships involving `FixedRegionBlackoutProcessor` (e.g. with `ConfigError` and `PS315Profile`) actually correct?**
  _`FixedRegionBlackoutProcessor` has 47 INFERRED edges - model-reasoned connections that need verification._
- **Are the 49 inferred relationships involving `FractionalRegion` (e.g. with `ConfigError` and `PS315Profile`) actually correct?**
  _`FractionalRegion` has 49 INFERRED edges - model-reasoned connections that need verification._
- **Are the 42 inferred relationships involving `CompositePixelProcessor` (e.g. with `ConfigError` and `PS315Profile`) actually correct?**
  _`CompositePixelProcessor` has 42 INFERRED edges - model-reasoned connections that need verification._
- **Are the 45 inferred relationships involving `OCRAuditProcessor` (e.g. with `ConfigError` and `PS315Profile`) actually correct?**
  _`OCRAuditProcessor` has 45 INFERRED edges - model-reasoned connections that need verification._