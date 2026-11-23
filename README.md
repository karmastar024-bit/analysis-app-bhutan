# Bhutan Assessment Workspace

A Streamlit app for educators in Bhutan, combining **Item analysis** and **Result analysis** in one workspace.

The initial dashboard lets teachers choose either tool. The **Home** icon always returns to Assessment workspace, and each tool's menu links to the other tool. Both share the English/Dzongkha language setting, Bhutanese classroom and valley artwork, and glass-style interface. The browser icon combines an open book, Himalayan peak and saffron sun.

Created by **Karma Dorji** · [karmastar024@gmail.com](mailto:karmastar024@gmail.com)

## Choose the right tool

| Tool | Use it to | Available analyses |
|---|---|---|
| Item analysis | Review how individual questions perform and identify items to retain, review, revise or discard | Multiple choice, true or false, fill in the blanks, matching, written responses, and test distribution |
| Result analysis | Understand achievement in a subject, across a class, or between sections of the same grade | Individual subject analysis, class result analysis, and section comparison |

Both tools provide Excel templates, fictional samples, charts and PDF reports. Their workbook formats are different: download the template from the analysis you intend to use.

## Item analysis

### Features

- **Multiple choice:** difficulty, discrimination, distractor efficiency, and functional/non-functional distractor options for each question.
- **True or false, fill in the blanks and matching:** difficulty, discrimination, recommendations and explanations.
- **Written responses and essays:** analysis of awarded marks relative to each item's maximum score.
- **Results:** student/item counts, mean score, sample standard deviation, minimum and maximum scores; score distribution; and a direct item-by-item results table. Summary scores and charts describe the selected item type, rather than the overall examination score.
- **PDF reports:** results, distribution charts and item tables. MCQ reports also include distractor details by question. The download button appears after the results.
- **Test distribution:** descriptive statistics, histogram and box plot, with a choice of one-sample t-test or z-test against a target mean. The z-test requires a known population standard deviation. Its PDF includes the distribution chart and hypothesis-test results.
- **Guides:** explanations of item statistics, decision rules, methodology and data formats.

### Upload workflow

1. Choose an item type and download its Excel template.
2. Enter student ID, **Name**, and the overall **Total Score**, then complete each student's responses or awarded marks.
3. For MCQ, true/false, fill-in-the-blanks and matching, enter answers in the gold **KEY** row above the question headers. Separate alternative accepted fill-in-the-blanks answers with `|`.
4. For written responses, enter each item's maximum mark in the **MAX** row and awarded marks in the student rows.
5. Upload the workbook, run the analysis, review the results and download the PDF.

Name and overall Total Score are required. **The upper and lower 27% groups are ranked using the supplied overall Total Score**, not the sum of marks in the selected item type. Item-type scores are used for that type's displayed summary and distribution.

MCQ uses an `.xlsx` workbook. Other item types accept supported CSV or Excel layouts. Legacy `StudentID` headers and KEY/MAX rows below the headers remain supported. Test Distribution uses its own upload template with student details and total scores.

### Item statistics

- **Difficulty (p):** proportion correct for binary items; mean awarded mark divided by maximum mark for written items.
- **Discrimination (D):** difference between upper- and lower-group performance. Written-item differences are normalized by maximum marks.
- **Distractor efficiency (DE):** percentage of incorrect options selected by at least 5% of students. The correct answer is excluded from distractor classification.
- **Recommendations:** the app checks discard conditions first, then revision and review conditions. Raw statistics determine the recommendation; rounding is for display only. Explanations appear in the table's Why column.

Full formulas and thresholds are available in the in-app Methodology and Decision Rules pages. Recommendations support teacher review; they do not replace professional judgment.

## Result analysis

### Individual subject analysis

Set the subject name and maximum marks, then upload the matching mark sheet. Outputs include:

- Descriptive statistics and pass rate, with blank and absent counts shown separately.
- Score distribution and score-band charts and tables.
- IQR-based outlier identification; outliers remain included in the statistics.
- Gender and residence comparisons, including group means and pass rates.
- Top and bottom student lists, with raw marks alongside percentage scores.
- A PDF report containing the analysis and charts, with optional selected student lists.

### Class result analysis

Choose the Key Stage, class, pathway and applicable subjects. The analysis provides:

- Class overview: enrolled, assessed and complete records; mean performance; passed-all and passed-at-least-one rates; average total marks; and observed failure counts.
- Per-subject statistics, score distributions, pass rates, diagnosis and subject-strength comparisons.
- Gender and residence comparisons.
- Student rankings, support lists and missing-assessment follow-up information.
- A class PDF report with summary cards, charts and optional selected student lists.

### Section comparison

Upload and save at least two sections of the same grade. Sections can be re-uploaded or removed before completing the analysis. Outputs include:

- Section comparisons and composite rankings, including tied ranks.
- Subject-by-section statistics and comparisons.
- Combined grade results using the class-analysis views.
- Optional comparisons with teacher-entered previous-year, Dzongkhag and national benchmarks. National inputs are offered for Classes VI, VIII, X and XII; no benchmark figures are invented or preloaded.
- A PDF report covering the section/grade analysis and supplied benchmarks.

### Result Analysis workbook and workflow

1. Select the analysis and its subject/class settings.
2. Download the matching blank template or fictional sample.
3. Complete the workbook without renaming, reordering or removing required columns.
4. Upload it and correct any validation messages. For section comparison, save each validated section, then select **Finish uploading & Analyse**.
5. Review the results. Select **Prepare PDF Report**, then **Download PDF Report**. Enable **Include selected student lists in PDF** when needed.

The generated workbook contains:

| Sheet | Contents |
|---|---|
| Report Details | School Name, Academic Year, Class, Teacher Name and Subjects. School and academic year are required. |
| Marks | Student ID, Student Name, Gender, Residence, Section, then the selected subject columns. |
| Settings | Subject names and their maximum marks. |
| Instructions | Guidance for completing the workbook. |

Validation checks column order, required metadata, duplicate IDs, numeric ranges and formula cells. Section files must agree on school, year, class, subjects and maximum marks; student IDs must be unique across sections. The validator limits each workbook to 10 MB, 10,000 students and 50 columns, with an 80 MB expanded-workbook limit.

### Result Analysis calculation rules

- The pass threshold is **40%**, inclusive. Subject statistics use percentage marks so subjects with different maximum marks can be compared.
- Blank and Absent marks are excluded independently per subject and counted separately; they are not converted to zero.
- Overall averages use available subjects with equal subject weighting. Totals and overall student rankings require complete records.
- Passed-all rates use complete records as the denominator. Passed-at-least-one rates use students with at least one valid mark. The denominators are displayed.
- Standard deviation uses the sample definition (`ddof=1`). Unavailable statistics are shown as unavailable, not zero.
- Subject-strength and section-ranking formulas, diagnosis thresholds and interpretation guidance are documented in the tool's **Methodology** page and `result_analysis/core/subjects_config.py`.

The configured curriculum and thresholds are application rules, not a claim of independent certification as current national policy.

## English and Dzongkha

The shared language control changes interface text, instructions, template labels, chart labels and PDF reports. Dzongkha mode uses Dzongkha numerals and ordinal question labels, including:

- MCQ: **གདམ་ཁ་ཅན་གྱི་དྲི་བ**
- KEY: **དྲི་བའི་ལན**
- Q1: **དྲི་བ་དང་པ**; Q2: **དྲི་བ་གཉིས་པ**

Translated templates normalize to the same calculation fields as English templates. Student names and entered data are preserved. Language changes do not alter marks or analytical results.

Bundled Tibetan fonts and HarfBuzz shaping support stacked characters in PDF text and chart labels. Font licenses are included with the assets. Excel may use a local fallback font if the specified Tibetan font is not installed. Dzongkha terminology can be reviewed in the translation catalogues under `utils/` and `result_analysis/core/`.

## Install and run

Use Python 3.12 to match the development environment. From this combined project's folder:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

On Windows, activate with `.venv\Scripts\activate` instead. If using an existing Python environment, skip the first two commands.

Only one Streamlit process and one entry point, **`app.py`**, are needed. The original sibling Result Analysis project is not required at runtime. Changes to that original folder do not automatically update this bundled copy; maintain the combined version here.

## Deployment

Deploy the combined project with `app.py` as the entry point and `requirements.txt` for dependencies. Include `.streamlit/config.toml` and all runtime folders listed below, particularly both sets of fonts and artwork. Exclude virtual environments, caches, temporary test output and actual student files.

After deployment, check both workspaces, language switching, template uploads and PDF downloads before sharing the app. Local use processes uploads on your computer; hosted use sends them to the hosting server.

## Privacy and session data

Uploaded records and generated reports are processed in server memory for the current session. The app does not intentionally save uploaded student records to disk, a database or an external analytics service. Blank templates and fictional samples may be cached separately from student data.

Result Analysis's **Session → Clear session data** removes that tool's session records without clearing Item Analysis results. Losing a browser session or restarting the server may require re-uploading. Downloaded reports contain student data; hiding names does not anonymize student IDs.

## Project structure

```text
app.py                         Shared Streamlit router and browser icon
components/workspace.py        Initial dashboard, tool switcher, session helpers
components/navigation.py       Item Analysis header and navigation
pages/                         Item Analysis pages and guides
analysis/                      Item scoring and statistical calculations
utils/                         Item upload validation, templates and translations
report_extras.py                Item and hypothesis-test PDF reports
item_analyzer.py                MCQ analysis engine
assets/                        Shared styling, favicon and Tibetan fonts
static/                        Item Analysis / shared dashboard artwork
templates/                     Item Analysis workbook templates
data/                          Fictional Item Analysis samples
result_analysis/
  workspace.py                 Result Analysis navigation and overview
  views/                       Subject, class and section workflows
  core/                        Validation, statistics, templates, charts, PDFs,
                               curriculum configuration and translations
  assets/                      Result Analysis styling and licensed fonts
  static/                      Result Analysis artwork
  sample_data/                 Fictional Result Analysis samples
.streamlit/config.toml         Shared Streamlit configuration
tests/                         Both tools' regression and integration checks
requirements.txt               Runtime dependencies
requirements-dev.txt           Test dependencies
```

## Verification and practical limits

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Tests cover item calculations, workbook validation, missing marks, pass boundaries, section compatibility, rankings, translation round trips, PDF generation and shared navigation. The combined baseline passed 186 tests; the subsequent Home/icon update passed 28 targeted checks, including a new Home-navigation test. Live browser checks have also covered the shared dashboard and switching between tools.

Small samples can make item statistics and group comparisons unstable. The app shows relevant warnings. Matching uses whole-prompt scoring rather than partial credit. Result Analysis benchmark comparisons require figures supplied by the teacher; automatic benchmark retrieval is not configured. Large PDF reports take longer to prepare than screen summaries. Review terminology, interpretations and exported student details before using or sharing reports.
