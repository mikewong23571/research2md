# TermDive Implementation Plan

## Architecture Overview
- **CLI Layer (`termdive` entrypoint)**: Orchestrates runs, parses flags, resolves provider/exporter/generator strategies.
- **Core Pipeline Module (`pipeline/`)**: `RunManager` coordinates provider calls, PDF export, analysis, Markdown generation, and artifact manifesting.
- **Provider Abstraction (`providers/`)**: Vendor-agnostic adapter interface with concrete implementations (OpenAI, Gemini) built atop the Claude Agent SDK for prompt orchestration, enabling consistent invocation, retries, and trace metadata.
- **PDF Handling (`export/pdf_exporter.py`)**: Encapsulates LLM response-to-PDF conversion and persistence, supporting deterministic formatting.
- **Analysis Layer (`analysis/`)**: Parses PDFs to structured outlines/entities via deterministic parsing pipeline.
- **Markdown Generation (`markdown/`)**: Converts structure + raw content into clean Markdown; optional MarkItDown extraction path.
- **Artifacts & Observability (`artifacts/`)**: Versioned directory containing raw prompts, LLM outputs, PDFs, structures, Markdown, manifest, and run metadata.

## Repository Layout
```
termdive/
  README.md
  pyproject.toml
  termdive/
    __init__.py
    cli.py
    config.py
    logging.py
    pipeline/run_manager.py
    providers/
      __init__.py
      base.py
      openai_adapter.py
      gemini_adapter.py
      claude_agent_client.py
    prompts/
      deep_search_v1.prompt
      analysis_outline_v1.prompt
    export/
      __init__.py
      pdf_exporter.py
    analysis/
      __init__.py
      analyzer_agent.py
      parsers.py
    markdown/
      __init__.py
      generator.py
      markitdown_extractor.py
    artifacts/
      manifest.py
    tests/
      unit/
      golden/
  scripts/
    run_golden_tests.sh
```

## Interface Specifications
### ProviderAdapter
- `call(prompt: PromptRequest) -> ProviderResponse`
- `get_metadata() -> Dict`
- Responsibilities: vendor-agnostic request formatting, retry logic, deterministic defaults, emitting trace IDs.

### PDFExporter
- `export(response: ProviderResponse, output_path: Path) -> PDFArtifact`
- Responsibilities: convert response text to PDF, embed metadata (prompt ID, provider, timestamp).

### AnalyzerAgent
- `analyze(pdf_path: Path) -> AnalysisStructure`
- Responsibilities: parse PDF, extract outline/sections/entities, versioned prompt usage via Claude Agent SDK.

### MarkdownGenerator
- `generate(structure: AnalysisStructure, pdf_path: Path, output_path: Path) -> MarkdownArtifact`
- Responsibilities: produce clean Markdown, inject citations, maintain provenance references.

### MarkItDownExtractor (optional)
- `extract(pdf_path: Path) -> MarkdownDraft`
- Responsibilities: direct markdown extraction via `microsoft/markitdown`, fallback/compare pipeline.

## CLI Sequence (`termdive run "term"`)
1. Parse CLI flags (`--provider`, `--pdf`, `--md`, `--use-markitdown`, `--output-dir`).
2. Initialize run ID + artifact root (`artifacts/{timestamp}-{term_slug}/`).
3. Load config + secrets from `.env` or env vars.
4. Instantiate provider adapter (OpenAI/Gemini) via Claude Agent SDK wrapper.
5. Render deep-search prompt (versioned) using term + config.
6. Call provider (`temperature=0`, deterministic settings).
7. Persist raw response (`artifacts/.../responses/deep_search.json`).
8. Export PDF (`artifacts/.../pdf/deep_search.pdf`).
9. If `--pdf=false`, skip PDF and downstream steps.
10. Analyze PDF → `structure.json` (`artifacts/.../analysis/structure.json`).
11. Generate Markdown from structure + PDF → `artifacts/.../markdown/deep_search.md`.
12. If `--use-markitdown`, run MarkItDown extractor and save `markitdown.md`.
13. Update artifact manifest (`artifacts/.../manifest.json`) with hash, timestamps, versions.
14. Emit summary to console (paths, run ID).

## Dependencies & Rationale
- **Python 3.11**: mature ecosystem, CLI ergonomics.
- **Claude Agent SDK**: primary interface layer for LLM calls, providing tooling compliance with requirement.
- **OpenAI / Google Generative AI client libs**: provider-specific HTTP interactions where needed.
- **pydantic**: data models for prompts/responses/manifests with validation.
- **click or typer**: ergonomic CLI creation (deterministic argument parsing).
- **reportlab or weasyprint**: deterministic PDF generation from text.
- **pdfminer.six** or `pypdf` + `pdfplumber`: parse PDF text for analysis.
- **microsoft/markitdown**: optional Markdown extraction.
- **rich**: optional pretty CLI output/logging.
- **pytest**: testing framework.
- **pytest-golden**: manage golden file comparisons.
- **python-dotenv**: load `.env`.
- **structlog**: structured logging with run IDs.

## Prompt Templates
- `deep_search_v1.prompt`: standardized deep research request with sections (context, term definition, subtopics, references). Parameterized by `{term}`, `{run_id}`, `{version}`.
- `analysis_outline_v1.prompt`: instructs analyzer to produce JSON outline (sections, summaries, entities) using Claude Agent SDK.

## Pseudocode
### `run_manager.run(term)`
```
config = load_config(flags)
run_id = generate_run_id(term)
artifact_paths = init_artifacts(run_id, config.output_dir)
provider = ProviderFactory.create(config.provider, config, claude_client)
deep_prompt = render_prompt("deep_search_v1", term, run_id)
response = provider.call(deep_prompt)
save_json(response.raw, artifact_paths.responses / "deep_search.json")
if flags.pdf:
    pdf_artifact = pdf_exporter.export(response, artifact_paths.pdf / "deep_search.pdf")
    update_manifest(run_id, pdf_artifact)
    if flags.md:
        structure = analyzer_agent.analyze(pdf_artifact.path)
        save_json(structure.to_dict(), artifact_paths.analysis / "structure.json")
        md_artifact = markdown_generator.generate(structure, pdf_artifact.path,
                                                 artifact_paths.markdown / "deep_search.md")
        update_manifest(run_id, md_artifact)
        if flags.use_markitdown:
            markitdown_md = markitdown_extractor.extract(pdf_artifact.path)
            write_text(markitdown_md, artifact_paths.markdown / "deep_search_markitdown.md")
            update_manifest(run_id, markitdown_md)
finalize_run(run_id, manifest)
return Summary(run_id, artifact_paths)
```

### `provider.call(prompt)`
```
request = build_request(prompt, temperature=0, max_tokens=config.max_tokens)
response = claude_client.execute(
              provider_name=config.provider,
              model=config.model,
              request=request,
              metadata={"run_id": prompt.run_id, "prompt_version": prompt.version})
return ProviderResponse(
    text=response.text,
    tokens=response.usage,
    raw=response.raw_json,
    prompt_version=prompt.version)
```

### `pdf_analyze(pdf_path)`
```
text = pdf_reader.extract_text(pdf_path)
structured_prompt = render_prompt("analysis_outline_v1", text_snippet(text), metadata)
analysis_response = claude_client.execute(provider=config.analysis_provider, ...)
structure = parse_json(analysis_response.text)
structure.entities = entity_extractor(text)
return AnalysisStructure(structure)
```

### `md_generate(structure, pdf_path)`
```
text_blocks = pdf_reader.extract_text_blocks(pdf_path)
md = []
for section in structure.sections:
    md.append(format_heading(section.title, section.level))
    md.append(section.summary)
    relevant_blocks = map_entities_to_blocks(section.entities, text_blocks)
    md.extend(convert_blocks_to_markdown(relevant_blocks))
md_document = "\n\n".join(md)
write_text(md_document, output_path)
return MarkdownArtifact(path=output_path, hash=hash(md_document))
```

## Environment & Configuration
- `.env` keys: `TERMDIVE_OPENAI_API_KEY`, `TERMDIVE_GEMINI_API_KEY`, `CLAUDE_AGENT_API_KEY`, `TERMDIVE_DEFAULT_PROVIDER`, `TERMDIVE_OUTPUT_DIR`.
- Flags:
  - `--provider {openai|gemini}`
  - `--model NAME`
  - `--pdf/--no-pdf`
  - `--md/--no-md`
  - `--use-markitdown`
  - `--output-dir PATH`
  - `--prompt-version`
  - `--analysis-provider`
- Precedence: CLI > env vars > defaults.

## Testing Approach
- Unit tests for provider adapters using mocked Claude Agent SDK responses.
- Unit tests for PDF exporter ensuring reproducible output with fixtures.
- Analyzer + Markdown generator tests with fixture PDFs and expected structures.
- Golden file tests comparing produced Markdown with expected outputs.
- CLI integration smoke tests via `pytest` invoking subprocess with known term, verifying artifact manifest.

## Observability
- Structured logging with `run_id`, `prompt_version`, `provider`.
- Artifact manifest JSON containing file paths, hashes, created timestamps, prompt versions, provider metadata, usage statistics.
- Optional CLI summary table showing token usage and artifact locations.
- Future: plug into OpenTelemetry via Claude Agent SDK hooks.

## Risks & Mitigations
- **Provider Rate Limits**: queue/retry with exponential backoff; cache responses by term + prompt version.
- **Provider Drift**: versioned prompts and manifesting model/version for reproducibility; allow pinning models.
- **PDF Fidelity**: deterministic PDF renderer and cross-validate with MarkItDown extraction; store raw response.
- **Analysis Accuracy**: fallback heuristics when LLM returns malformed JSON; schema validation and repair.
- **Artifact Explosion**: enforce cleanup policies and configurable retention.

## MVP vs Follow-ups
- **MVP**: CLI orchestrator, OpenAI adapter via Claude Agent SDK, PDF export, analyzer prompt, Markdown generator, artifact manifest, minimal logging, deterministic defaults.
- **Follow-ups**: Gemini adapter, MarkItDown integration, enhanced entity extraction, UI dashboard, remote artifact storage (S3), caching layer, parallel term processing.
