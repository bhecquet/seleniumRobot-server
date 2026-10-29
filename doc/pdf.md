# `pdf` module – retro-documentation

This document describes the business rules of the `pdf` module (PDF tools of seleniumRobot-server) as they are
implemented in the code, and the tests covering them.
Each rule has an identifier `RG-xxx-nn`, which is reused in the docstring of the tests (`pdf/tests`).

## 1. Overview

| Element | File | Role |
|---|---|---|
| `PdfHomeView` | `pdf/views/home_view.py` | PDF tools home page (`/pdf/home/`) |
| `PdfValidateView` | `pdf/views/validate_view.py` | PDF file test page (`/pdf/validate/`), not implemented yet |
| `PdfCompareView` | `pdf/views/compare_view.py` | Form + comparison launch (`/pdf/compare/`) |
| `PdfCompareResultView` | `pdf/views/compare_result_view.py` | Display of the last result (`/pdf/compare/result/`) |
| `PdfCompareForm` | `pdf/forms.py` | Validation of submitted data |
| `PdfRequestLog` | `pdf/models.py` | Request history stored in database |
| `ComparisonResult`, `Difference` | `pdf/controllers/comparison/comparison_result.py` | Normalized comparison result |
| `StubComparator` | `.../stub_comparator.py` | Fake comparator (tests) |
| `AzureOcrComparator` | `.../azure_ocr_comparator.py` | Comparison through Azure API |
| `MistralDocComparator` | `.../mistral_document_annotation_comparator.py` | Comparison through Mistral Document AI |

Nominal flow: `compare` (POST) → form validation → page counting → selected comparator →
database logging → result in session + PDFs in cache → redirect to `compare/result`.

## 2. Business rules

### 2.1 Access

| ID | Rule |
|---|---|
| RG-ACC-01 | All pages of the module (home, validate, compare, compare/result) require an authenticated user. Otherwise: redirect to `/accounts/login/?next=<url>`. This also applies to the POST of `compare`. |
| RG-ACC-02 | No permission is checked: any authenticated user can use every feature. |

### 2.2 Navigation

| ID | Rule |
|---|---|
| RG-NAV-01 | The home page gives access to PDF comparison and PDF file validation. |
| RG-NAV-02 | PDF file validation is not implemented yet: the page displays "Fonctionnalité à venir", no processing is done and nothing is logged. |

### 2.3 Comparison form

| ID | Rule |
|---|---|
| RG-FRM-01 | Both PDF files are mandatory. |
| RG-FRM-02 | Each file name must end with `.pdf` (case-insensitive) and its content must be a PDF (`%PDF-` signature within the first 1024 bytes). The file is not fully parsed. |
| RG-FRM-03 | The model is mandatory and must be `azure_ocr`, `mistral_doc` or `stub` (stub is for tests only). |
| RG-FRM-04 | Additional user instructions are optional. |

### 2.4 Comparison launch

| ID | Rule |
|---|---|
| RG-CMP-01 | GET on `compare`: the empty form is displayed. |
| RG-CMP-02 | Invalid form: the form is displayed again with its errors; no comparison is run and nothing is logged. |
| RG-CMP-03 | The selected model determines the comparator (`stub` → `StubComparator`, `azure_ocr` → `AzureOcrComparator`, `mistral_doc` → `MistralDocComparator`). Any other model raises a `ComparisonError` (unreachable through the form, which rejects it). |
| RG-CMP-04 | User instructions are never considered safe: when not empty, they are wrapped in a text requiring the model to ignore them if they are not related to document comparison (format change, data exfiltration, instruction reset, ...) and stating that previous instructions take precedence. When empty, the comparator receives an empty string. The stub never receives instructions. |
| RG-CMP-05 | Success: the result is stored in session, both PDFs are kept in cache for 15 minutes (token stored in session), then redirect to `compare/result`. |
| RG-CMP-06 | Failure (any exception during comparison): the form is displayed again with the message `Error occured during comparison : <error>`; nothing is stored in session; the error is written to application logs. |
| RG-CMP-07 | The result contains: names of both files, number of pages of each, list of differences (page, location, details) and the full comparator response as indented JSON. |

### 2.5 Result display

| ID         | Rule                                                                                                                                                                                        |
|------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| RG-RES-01  | Without result in session, the result page redirects to the comparison form.                                                                                                                |
| RG-RES-02  | With a result, the page displays it along with both PDFs (names and content as base64 `data:` URI) retrieved from cache using the session token.                                            |
| RG-RES-03  | If PDFs expired from cache (or the token is missing), the result is displayed without the PDFs.                                                                                             |
| RG-RES-04  | A `data:` URI is built only when content is not empty (otherwise `None`).                                                                                                                   |
| RG-RES-05  | Result page should display the raw response of the comparison model, so that debugging is possible. This raw response is hidden by default but can be shown by clicking "Debug info" button |
|            |                                                                                                                                                                                             |

### 2.6 Normalized result (`Difference`, `ComparisonResult`)

| ID | Rule |
|---|---|
| RG-DIF-01 | The page number of a difference is an integer ≥ 0: a negative value becomes 0; a value that cannot be converted to integer (e.g. `N/A`) becomes -1 (unknown page). |
| RG-DIF-02 | `details` and `location` are converted to string; when conversion fails, `details` is `''` and `location` is `unknown`. |
| RG-DIF-03 | Two differences are equal when page, details and location are identical. |
| RG-DIF-04 | A difference is serialized as `{page, details, location}`. |
| RG-DIF-05 | A result is serialized as `{differences: [...], full_response: <UTF-8 text>}`; the full response defaults to `{}`. |

### 2.7 Stub comparator

| ID | Rule |
|---|---|
| RG-STB-01 | The stub always returns the same difference (page 1, "first part", "Amount is different") and a valid JSON full response, without reading the files. |

### 2.8 Azure comparator

| ID | Rule |
|---|---|
| RG-AZR-01 | Authentication in 3 steps: (1) Key Vault token, (2) API key read from the Key Vault, (3) token for the backend API. An HTTP code other than 200 or a missing expected field (`access_token`, `value`) at any step raises a `ComparisonError`. |
| RG-AZR-02 | Both files are sent to the comparison API with the backend token and the subscription key (`ocp-apim-subscription-key`). An HTTP code other than 200 raises a `ComparisonError`. |
| RG-AZR-03 | Each item of `content_differences` becomes a difference: `page` (default `N/A`), `section` → location, details = difference type + field + values of documents 1 and 2. A malformed response raises a `ComparisonError`. |
| RG-AZR-04 | The raw API response is kept as the full response. |
| RG-AZR-05 | User instructions are accepted by the constructor but are **not used** by this comparator. |

### 2.9 Mistral comparator

| ID | Rule |
|---|---|
| RG-MIS-01 | The system prompt and the differences description prompt come from preferences (`MISTRAL_DOC_COMPARISON_SYSTEM_PROMPT`, `MISTRAL_DOC_COMPARISON_DIFFERENCES_PROMPT`); user instructions are appended to the system prompt. Prompts receive the page counts of both documents. |
| RG-MIS-02 | Documents are compared page by page: for each rank N up to the smallest page count, page N of both documents are grouped in a single PDF (base64). Extra pages of the longest document are not compared. |
| RG-MIS-03 | When page counts differ, an additional difference is added (page 0, location `document`, "First document has X pages, second has Y pages"). |
| RG-MIS-04 | One request is sent per page. Code 408 → `ComparisonError` "Timeout"; code ≥ 400 → `ComparisonError`; unusable response → `ComparisonError`. The page number is given in the message. |
| RG-MIS-05 | Differences returned by the model (`location`, `details`) are attached to the current page (numbering starts at 1). |
| RG-MIS-06 | Duplicates (same page, location and details) are removed, order is kept. |
| RG-MIS-07 | The full response is not kept (default value `{}`). |

### 2.10 Database logging (`PdfRequestLog`)

| ID | Rule |
|---|---|
| RG-LOG-01 | Every comparison requested with a valid form is recorded: date (automatic), user, type `comparison`, origin `ui`, number of pages of each file, **raw** user instructions (not wrapped). |
| RG-LOG-02 | Failures are recorded too: `success = False` and `error_message` filled. A success has `success = True`. |
| RG-LOG-03 | The page count is computed before the comparison (so it is available even on failure). If a file cannot be read, its page count is empty (`NULL`) and a warning is logged. |
| RG-LOG-04 | A log write error does not interrupt the comparison (it is only logged). |
| RG-LOG-05 | An invalid form is not logged. |
| RG-LOG-06 | Retention: rows older than 183 days (≈ 6 months) are deleted (`PdfRequestLog.purge_old`). The purge is idempotent and safe with concurrent calls (a single `DELETE` filtered by date). |
| RG-LOG-07 | The purge is triggered after a row is recorded, at most once per hour (`cache.add` lock). A purge error does not interrupt the comparison. |
| RG-LOG-08 | The model also provides the `validation` type (a single page count, `nb_pages_2` empty), which is not used today. The `api` origin is used by the API (RG-API-09). |

### 2.11 API comparison (`PdfCompareApiView`)

Endpoint: `POST /pdf/api/compare/` (multipart/form-data), meant to be called by a Selenium test.

| ID | Rule |
|---|---|
| RG-API-01 | Inputs: `reference` (PDF file), `file` (PDF file), `model` (model name) and optional `instructions` (sent to the model). The response is JSON. |
| RG-API-02 | Authentication is mandatory (token or session). An unauthenticated call is rejected (401/403), nothing is compared or logged. |
| RG-API-03 | No permission is required: any authenticated user can call the API (as for the GUI). |
| RG-API-04 | Success response (200): `{"differences": [{"location", "details", "page"}, ...], "duration": <analysis duration in seconds>}`. |
| RG-API-05 | `reference` and `file` are mandatory. |
| RG-API-06 | Both files names must end with `.pdf` and their content must be a PDF (same rule as RG-FRM-02). |
| RG-API-07 | `model` is mandatory and must be `azure_ocr`, `mistral_doc` or `stub` (same rule as RG-FRM-03). |
| RG-API-08 | `instructions` are optional and handled like GUI instructions: wrapped as untrusted text before being sent to the model (RG-CMP). |
| RG-API-09 | Every comparison is recorded in database like in RG-LOG-01..03, with origin `api`, whether it succeeds or fails. |
| RG-API-10 | A request rejected by input validation returns 400 with `{"errors": {<parameter>: [messages]}}`, using API parameter names; it is not logged (as RG-LOG-05). |
| RG-API-11 | A comparison failure returns 500 with `{"error": <message>}` and is logged as failed. |

## 3. Test coverage

Tests carry the rule identifier in their docstring. Several tests may cover one rule.

| Rule | Tests |
|---|---|
| RG-ACC-01 | `test_home_view`, `test_validate_view`, `test_compare_view` (GET and POST), `test_compare_result_view`: `test_authentication_required` / `test_get_authentication_required` / `test_post_authentication_required` |
| RG-ACC-02 | No test (absence of permission check is not explicitly verified) |
| RG-NAV-01 | `TestPdfHomeView.test_home` |
| RG-NAV-02 | `TestPdfValidateView.test_validate` |
| RG-FRM-01 | `TestPdfCompareForm.test_valid`, `test_missing_files` |
| RG-FRM-02 | `test_invalid_extension_file_1`, `test_invalid_extension_file_2`, `test_invalid_content_file_1`, `test_invalid_content_file_2` |
| RG-FRM-03 | `test_invalid_model` |
| RG-FRM-04 | `test_prompt_optional` |
| RG-CMP-01 | `TestPdfCompareView.test_get_displays_form` |
| RG-CMP-02 | `test_post_invalid_form` |
| RG-CMP-03 | `test_post_stub_redirects_to_result`, `test_post_azure_model`, `test_post_mistral_model` (unknown model: **not tested**) |
| RG-CMP-04 | `test_post_azure_model` (wrapping), `test_post_mistral_model` (empty instructions) |
| RG-CMP-05 | `test_post_stub_redirects_to_result` |
| RG-CMP-06 | `test_post_comparison_error` |
| RG-CMP-07 | `test_post_stub_redirects_to_result` |
| RG-RES-01 | `TestPdfCompareResultView.test_no_result_redirects_to_compare` |
| RG-RES-02 | `test_result_after_comparison` |
| RG-RES-03 | `test_result_with_expired_payload` |
| RG-RES-04 | `TestPdfCompareView.test_build_pdf_data_uri` |
| RG-RES-05 | `TestPdfCompareResultView.test_debug_info_hidden_by_default_with_raw_response`, `test_debug_info_contains_full_response_of_comparison` (the show/hide click is JavaScript and is **not tested**) |
| RG-DIF-01 | `TestDifference.test_invalid_page`, `test_negative_page` |
| RG-DIF-02 | **Not tested** (fallback values `''` / `unknown`) |
| RG-DIF-03 | `TestDifference.test_equality` |
| RG-DIF-04 | `TestDifference.test_serialize` |
| RG-DIF-05 | `TestComparisonResult.test_serialize`, `test_default_response` |
| RG-STB-01 | `TestStubComparator.test_compare` |
| RG-AZR-01 | `test_authenticate*` (7 tests) |
| RG-AZR-02 | `test_compare`, `test_compare_http_error` |
| RG-AZR-03 | `test_compare`, `test_compare_invalid_body`, `test_format_details` |
| RG-AZR-04 | **Not tested** (raw response kept) |
| RG-AZR-05 | **Not tested** |
| RG-MIS-01 | **Not directly tested** (preferences are mocked; prompt concatenation is not verified) |
| RG-MIS-02 | `test_combine_pdf` |
| RG-MIS-03 | `test_compare_different_page_count` |
| RG-MIS-04 | `test_compare` (one request per page), `test_compare_timeout`, `test_compare_http_error`, `test_compare_invalid_body` |
| RG-MIS-05 | `test_compare` |
| RG-MIS-06 | `test_filter_differences` |
| RG-MIS-07 | **Not tested** |
| RG-LOG-01 | `test_post_stub_redirects_to_result`, `test_post_azure_model` (raw instructions) |
| RG-LOG-02 | `test_post_stub_redirects_to_result` (success), `test_post_comparison_error` (failure) |
| RG-LOG-03 | `test_post_unreadable_pdf_is_logged`, `test_post_comparison_error` (pages filled before failure) |
| RG-LOG-04 | **Not tested** |
| RG-LOG-05 | `test_post_invalid_form_not_logged` |
| RG-LOG-06 | `TestPdfRequestLog.test_purge_old_removes_only_old_entries`, `test_purge_old_is_idempotent` |
| RG-LOG-07 | `test_post_purges_old_logs`, `test_post_purge_throttled` |
| RG-LOG-08 | **Not tested** (unused `validation` type) |
| RG-API-01 | `TestPdfCompareApiView.test_response_format` |
| RG-API-02 | `test_unauthenticated_rejected` |
| RG-API-03 | `test_authenticated_user_without_permission_accepted` |
| RG-API-04 | `test_response_format` |
| RG-API-05 | `test_missing_reference`, `test_missing_file`, `test_invalid_input_not_logged` |
| RG-API-06 | `test_non_pdf_file_rejected`, `test_non_pdf_content_rejected` |
| RG-API-07 | `test_invalid_model_rejected`, `test_missing_model_rejected` |
| RG-API-08 | `test_instructions_transmitted_to_model`, `test_instructions_optional` |
| RG-API-09 | `test_comparison_logged`, `test_failed_comparison` |
| RG-API-10 | `test_missing_reference`, `test_missing_file`, `test_invalid_input_not_logged` |
| RG-API-11 | `test_failed_comparison` |

### Tests not linked to a rule

None: every existing test is linked to at least one rule.

## 4. Points of attention found during the retro-documentation

- **User instructions and Mistral**: the system prompt (which contains the instructions) is formatted with the `%` operator
  (`self.prompt % {...}`). An instruction containing a `%` character (e.g. "ignore differences of 5%") is likely to raise an
  exception, reported to the user as a comparison error. Current behavior, not covered by a test.
- **Azure**: user instructions are ignored (RG-AZR-05) although the form offers them for every model.
- **Mistral**: the displayed full response is always `{}` (RG-MIS-07).
- **PDF validation**: only the extension and the `%PDF-` signature are checked (RG-FRM-02); a corrupted PDF with a valid signature is only detected when counting
  pages (empty page count in the log, RG-LOG-03), then possibly by the comparator.
