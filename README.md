# Bhutan Assessment Workspace

Run both **Item analysis** and **Result analysis** from one Streamlit app.
The first screen lets teachers choose a tool. Each tool's menu links back to
that screen and to the other tool. English and Dzongkha share one language setting.

## Run the combined app

```sh
python -m pip install -r requirements.txt
streamlit run app.py
```

For Streamlit hosting, deploy this entire directory and select `app.py` as the
entry point. Include `result_analysis/` (including its assets), `assets/`,
`static/`, `templates/`, and `data/`. The sibling Result analysis directory is
not required at runtime. Do not deploy virtual environments or student uploads.

## Project layout

- `app.py`: shared router; landing screen is the default route.
- `components/workspace.py`: tool chooser, switcher and session helpers.
- `pages/`, `analysis/`, `utils/`, `components/`: Item Analysis.
- `result_analysis/`: bundled Result Analysis code, translations and assets.
- `tests/test_result_*.py`: Result Analysis regression tests.

Result Analysis was copied from the root of the existing Result analysis project,
not its older nested copies. Its original directory is unchanged. Future edits to
the combined app should be made here; edits to the original project do not sync
automatically. Analysis formulas and workbook formats remain separate.

For regression checks, install `requirements-dev.txt` and run `python -m pytest -q`.

Completed result data stays in memory during the session. The Result Analysis
“Clear session data” action clears that tool's records without clearing Item
Analysis results. Refreshing or closing a session may require uploading again.

---

# ITEM ANALYZER
**Made for Educators in Bhutan** — item analysis for MCQ, True/False, Fill-in-the-Blank, Matching and written items,
plus test-distribution statistics (t-tests and z-tests).

Author: **Karma Dorji** · karmastar024@gmail.com

## Features
- Dashboard explaining Difficulty (p), Discrimination (D) and Distractor Efficiency (DE), with formulas and worked examples
- Decision rules per item type; every decision shows the **exact reason** (e.g. *REVIEW – Difficulty is high (p = 0.87).*)
- Upload validation with friendly messages (no tracebacks), sample data for every type
- Test distribution: descriptive statistics, histogram, box plot, one-sample t-test and z-test
- Downloads: Excel templates and PDF analysis reports
- English and Dzongkha interface, templates, charts and reports
- Privacy: files are processed in memory only; nothing is stored or sent anywhere

## Supported item types
| Type | Category | Statistics |
|---|---|---|
| MCQ | Selected-response | p, D, **DE** |
| True or False | Selected-response | p, D (DE not applicable) |
| Matching | Selected-response | p, D (each prompt = 1 item) |
| Fill in the Blanks | Short constructed-response | p, D |
| Short / Long Answer, Essay | Written constructed-response | normalized p, score-based D |

## Statistical methods
- **p** = correct ÷ students (binary) · **p** = mean score ÷ max score (written, *normalized difficulty*)
- **D** = (U − L) ÷ g with top/bottom 27% groups (binary) · (mean_upper − mean_lower) ÷ max (written)
- **DE** = functional distractors ÷ distractors × 100 (functional = chosen by ≥ 5% of students), MCQ only
- **Decision:** DISCARD if D<0, p=0, p=1 (or DE=0% for MCQ) → REVISE if D<0.20 and p∉[0.20,0.80] → REVIEW if either → RETAIN
- Test distribution interface: one-sample t and one-sample z (σ known)

Full formulas are on the in-app **Methodology** page.

## Installation
```bash
git clone https://github.com/karmastar024-bit/item-analysis-app.git && cd item-analysis-app
pip install -r requirements.txt
streamlit run app.py
```
Tests: `python -m pytest tests -q`

## Streamlit Community Cloud
Main file path: `app.py` · Python 3.10+ · dependencies from `requirements.txt`.

## Data format
All Excel templates use `Student ID`, `Name`, `Total Score`, `Q1`, `Q2`, … .
The gold KEY/MAX row sits above the navy column headers; student rows follow the headers.
Student details are blue, overall scores teal, and response rows alternate pale blue and white.
- **MCQ:** `templates/mcq_template.xlsx`, sheet `MCQ`. Name and Total Score are required. Total Score includes MCQ + all sections and is used for discrimination grouping.
- **True/False, Fill, Matching:** corresponding Excel templates in `templates/` use KEY for answers (Fill: alternatives separated by `|`). Include Name and the overall Total Score used to rank students for the upper and lower groups.
- **Written:** `templates/written_template.xlsx` uses MAX for each item's maximum score; student cells hold awarded scores. Include Name and the overall Total Score used to rank students for the upper and lower groups.
Legacy CSV/Excel files with `StudentID` and KEY/MAX below the headers remain supported.

## Sample data
`data/` — `sample_mcq_*.xlsx`, `sample_true_false.csv`, `sample_fill_blank.csv`, `sample_matching.csv`, `sample_written.csv`
(regenerate with `python -m utils.make_samples`). They contain deliberately flawed items.

## Project structure
```
app.py            router, header, footer          item_analyzer.py   original MCQ engine (kept)
pages/            home, mcq (original UI), true_false, fill_blank, matching,
                  written_response, score_statistics, guides, binary_common
analysis/         difficulty, discrimination, distractor, decision, scoring,
                  binary_analysis, written_analysis, statistical_tests
components/       navigation, footer, charts, tables, explanations
utils/            data_validation, file_handlers, translations, make_samples
```
`pages/score_statistics.py` is deliberately **not** named `statistics.py`: that would shadow Python's standard-library module.

## Known limitations
- Dzongkha covers only a few interface strings; long explanations are English (missing keys fall back to English). Needs native-speaker review.
- MCQ accepts one `.xlsx` workbook; other item types accept CSV or Excel.
- Item statistics are unstable below ~30 students (the app warns).
- PDF reports cover item-analysis results and summary charts; test-distribution results are CSV only.
- Matching has no partial credit within a prompt.
- Not yet tested in a real browser with a long-lived session (automated tests use Streamlit's headless harness).

## Future development
More languages (Spanish, French, Hindi), full Dzongkha, reliability (KR-20 / Cronbach's α), non-parametric tests, PDF for statistics.
