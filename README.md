# Formula 1 Podium Prediction

CSEN 903, Milestone 1. We predict whether a driver finishes on the podium (top three) in a Formula 1 race, using only information available after qualifying and before the race starts.

The whole pipeline is in one notebook, [formula-1.ipynb](formula-1.ipynb): data audit, cleaning, three data-engineering questions, feature engineering, five models, ablation, explainability and an inference function.

## Results

| Model | Validation PR-AUC (2020–2021) | Test PR-AUC (2022–2024) |
| :--- | ---: | ---: |
| Grid ≤ 3 rule (baseline) | 0.648 | 0.647 |
| Logistic regression | 0.728 | 0.711 |
| Random forest | 0.739 | 0.710 |
| LightGBM (selected) | 0.743 | 0.709 |
| Neural network | 0.738 | 0.701 |

- The 21 pre-race features are worth about 0.06 PR-AUC over the starting grid alone.
- The four learned models cannot be told apart on the test seasons; model complexity adds nothing measurable.
- The starting position carries most of the signal, recent results of the driver and team add the rest, and race context adds nothing.

## Repository layout

| Path | Contents |
| :--- | :--- |
| [formula-1.ipynb](formula-1.ipynb) | The notebook, 11 sections, Tasks 1–38 |
| [archive/](archive/) | The 14 raw CSV tables (Ergast data, 1950–2024). Never modified. |
| [figures/](figures/) | Every figure the notebook saves, at 300 DPI |
| [report/](report/) | The analytical report. `report.md` is the text; `md_to_latex.py` turns it into `report.tex` for submission (compile on Overleaf with the `figures/` folder uploaded beside it, or locally from `report/`), as the brief requires a Word or LaTeX report exported to PDF |
| [docs/notebook_guide.md](docs/notebook_guide.md) | Walk-through of every task and figure |
| [docs/decision_log.md](docs/decision_log.md) | Every judgment call, with its evidence (DEC-001 to DEC-033) |
| [docs/status_and_next_steps.md](docs/status_and_next_steps.md), [docs/project_status.pdf](docs/project_status.pdf) | Current status and open items |
| [docs/milestone_1.md](docs/milestone_1.md), [docs/milestone_1_plan.md](docs/milestone_1_plan.md) | The brief and the team plan |

## Running the notebook

**Locally**

```bash
pip install -r requirements.txt
jupyter notebook formula-1.ipynb   # then Run All
```

The notebook finds the data in `archive/` by itself. A full run takes a few minutes; the slowest cells are the hyperparameter searches and the neural network.

**On Kaggle**

1. Add the dataset [Formula 1 World Championship (1950–2024)](https://www.kaggle.com/datasets/rohanrao/formula-1-world-championship-1950-2020) to the notebook. `resolve_dataset_dir()` looks under `/kaggle/input` first.
2. Run All.
3. If `shap` or `lime` is not preinstalled, the notebook installs it itself; this needs Internet turned on in the notebook settings.
4. Read the last cell, **Run Check**. It compares the headline numbers quoted in the notebook text and the report with the numbers of this run, and says which ones differ, if any.

The result paragraphs in the notebook and the report quote numbers from the local run. If the Run Check reports a difference, check the text that quotes that number against the new outputs.

## Method in brief

- **Data contract.** One row per `(raceId, driverId)`; target `podium = (positionOrder <= 3)`.
- **Leakage control.** A blacklist of race-outcome columns, enforced by `assert_leakage_safe()`. Every history feature uses `shift(1)` by date, and two tests check that no feature changes when the outcomes of the current and later races are scrambled.
- **Split by season.** Train up to 2019, validation 2020–2021, test from 2022.
- **Metric.** PR-AUC is the main metric (about 15% of rows are podiums); ROC-AUC and F1 are reported beside it on all three splits.
- **One use of the test seasons for model comparison.** Hyperparameters, thresholds and the selected model were fixed on validation first.
