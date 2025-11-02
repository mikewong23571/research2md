---

# README

## TermDive

A tiny pipeline that turns a term into a structured PDF and a clean Markdown summary—using LLMs end-to-end.

### Why

* Consistent research prompts for new terms
* One-click PDF export of findings
* Automatic structure extraction → Markdown
  **Optional**: Replace step 3 with `microsoft/markitdown` to extract Markdown directly from the PDF.

### Pipeline

1. **Deep-search**: Send a standard prompt to ChatGPT/Gemini for the target term; save result as **PDF**.
2. **Analyze**: An agent parses the PDF to produce a content **outline/structure**.
3. **Summarize**: The agent generates **Markdown** from the outline + source.
   **Optional**: Replace step 3 with `microsoft/markitdown` to extract Markdown directly from the PDF.

### Usage

```bash
python -m termdive.cli "quantum computing"
```

The CLI accepts a handful of flags:

* `--provider` / `--model`: choose between `openai` (default) or `gemini` and specify a model name.
* `--no-pdf`, `--no-md`: disable downstream stages.
* `--use-markitdown`: generate an additional Markdown file via the MarkItDown-inspired extractor.
* `--output-dir`: choose where artifact directories should be created (default: `./artifacts`).

Results are written beneath `artifacts/<run-id>/` with a manifest enumerating produced files.

### License

MIT
