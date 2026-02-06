# Integrations

Pygramattic Reports integrates with several third-party systems and libraries to handle disparate inputs and outputs.

## Data Sources

### Pandas (Core)
We use `pandas` as the intermediate representation for all data.
*   **Version**: 2.0+
*   **Usage**: All loaders convert inputs into a `pd.DataFrame`.

### Google Workspace
(Optional) Support for ingesting from Google Sheets and Docs.
*   **Library**: `google-api-python-client`
*   **Auth**: Service Account JSON or OAuth flow.
*   **Env Var**: `GOOGLE_APPLICATION_CREDENTIALS`

### Microsoft Office
*   **Excel (.xlsx)**: Read/Write support via `openpyxl`.
*   **Word (.docx)**: Read support via `python-docx` (experimental write support planned).
*   **PowerPoint (.pptx)**: Write support via `python-pptx`.

## AI Providers

### OpenAI / Anthropic
Used for "AI Generated" sections.
*   **Connection**: HTTP API.
*   **Configuration**: `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`.
*   **Usage**: Summarization logic in `src/pygramattic_reports/ai/`.

## Local Testing w/ Mocks
For development, external integrations (Google, OpenAI) should be mocked.
*   See `tests/conftest.py` for `MockClaudeClient` and dataset fixtures.
*   Use `SectionSource.STATIC` to bypass external data requirements during template design.
