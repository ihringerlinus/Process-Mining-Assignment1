import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Assigment 1 Template
    """)
    return


@app.cell
def _():
    import marimo as mo
    import pandas as pd 
    import pm4py

    return mo, pm4py


@app.cell
def _(pm4py):
    event_log_from_disk = pm4py.read_xes('C:\\DATA\\HSG\\ProcessMining\\Process-Mining-Assignment1\\Road_Traffic_Fine_Management_Process.xes', variant="rustxes")
    print(len(event_log_from_disk), 'events read.')
    event_log_from_disk
    return (event_log_from_disk,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Session 1

    ## Task 1.1

    ### a) What time interval does the log cover?

    **Hypothesis:** Since this is a real-world administrative log, I expect it to cover several years. Timestamps are probably recorded as dates only, not with an exact time of day.
    """)
    return


@app.cell
def _(event_log_from_disk, mo):
    _start = event_log_from_disk["time:timestamp"].min()
    _end = event_log_from_disk["time:timestamp"].max()
    mo.md(f"""
    | | |
    |---|---|
    | **Start** | {_start} |
    | **End** | {_end} |
    | **Duration** | {_end - _start} |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Answer:** The log covers **2000-01-01 to 2013-06-18** (local Italian time), i.e. about **13.5 years** (4,917 days).

    In the raw data, the timestamps are stored in UTC: the first is 1999-12-31 23:00 UTC and the last is 2013-06-17 22:00 UTC. Converted to Italian time (CET = UTC+1 in winter, CEST = UTC+2 in summer), both fall exactly at **midnight**. This strongly suggests that the timestamps only have **day granularity** and that the time component is an artefact of the time zone conversion.

    **Findings / further questions:**
    - Timestamps should be interpreted in the Europe/Rome time zone. Otherwise events are shifted to the previous day.
    - With day granularity, the order of events within the same day is unclear. This could matter for later analyses (e.g., process discovery).
    - The log ends abruptly in June 2013. Fines created shortly before are probably not finished yet (incomplete cases), which could distort duration or outcome analyses.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### b) How many distinct values for the attribute vehicleClass does the log have?

    **Hypothesis:** I expect a small number of vehicle classes (e.g., car, motorcycle, truck), roughly 3–6 distinct values, with cars being the vast majority.
    """)
    return


@app.cell
def _(event_log_from_disk, mo):
    mo.vstack([
        mo.md(f"**{event_log_from_disk['vehicleClass'].nunique()}** distinct values (excluding empty values):"),
        event_log_from_disk["vehicleClass"].value_counts(dropna=False),
        event_log_from_disk["case:concept:name"].nunique()
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Answer:** vehicleClass has **4 distinct values**: A (146,712 events), C (2,456), M (1,198) and R (4). In addition, 411,100 events have no value (NaN).

    The four values add up to exactly **150,370**, which is the number of cases in the log. Together with the NaN events, this gives exactly the total of 561,470 events. So vehicleClass is most likely recorded **only once per case, on the Create Fine event**. The many empty values are therefore not missing data but a consequence of how the log is structured: vehicleClass is effectively a **case attribute**.

    **Findings / further questions:**
    - The meaning of the codes is not documented. Plausible (unverified) interpretation based on Italian vehicle categories: A = autoveicoli (cars), M = motoveicoli (motorcycles), C = ciclomotori (mopeds), R = rimorchi (trailers). This should be confirmed with domain experts.
    - Recommendation for data representation: store vehicleClass as a case attribute and document the codes.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### c) What are min, median, max of the initial value of the attribute amount (Create Fine events)?

    Reflect the result: what do you recommend to be investigated further?

    **Hypothesis:** Most fines are probably for minor offences such as parking, so I expect a median of roughly €30–50. The minimum should be above 0 (a fine without an amount makes little sense), and the maximum might be a few hundred to a few thousand euros for serious offences.
    """)
    return


@app.cell
def _(event_log_from_disk):
    _create = event_log_from_disk[event_log_from_disk["concept:name"] == "Create Fine"]
    _create["amount"].agg(["min", "median", "max"]).to_frame("amount")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Answer:** For the Create Fine events, the initial amount is:
    - **min: 0**
    - **median: 35**
    - **max: 4,351**

    The median matches the expectation of mostly minor offences (a typical parking fine). The minimum and maximum are surprising.

        **Reflection / recommendation:** I recommend investigating:

    1. **Fines with amount 0:** How many are there? Which articles do they concern, and what happens to these cases (dismissal, payment, credit collection)? They could be data entry errors, placeholders, or a special legal category.
    2. **Outliers at the top (up to 4,351):** Are these legitimate serious offences? Check which articles they belong to and whether they are plausible.
    3. **Currency and unit:** The log starts in 2000, but the euro was introduced as cash in 2002. It should be checked whether early amounts are in lire, converted, or consistent over time (e.g., by plotting amount over time).
    4. **Distribution:** A histogram of amount, ideally per article, would show whether there are a few standard amounts and where the outliers lie.
    5. **Documentation:** The currency and meaning of amount should be documented explicitly.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### d) How many events have a value > 0 for the attribute points? What are the associated activities? How many cases are affected?

    **Hypothesis:** Penalty points are only deducted for more serious offences, while most fines (e.g., parking) carry no points. I expect only a small share of cases, maybe a few percent, to have points > 0. Since points are initialized at Create Fine, I expect Create Fine to be the only associated activity.
    """)
    return


@app.cell
def _(event_log_from_disk, mo):
    _pts = event_log_from_disk[event_log_from_disk["points"] > 0]
    mo.vstack([
        mo.md(
            f"**{len(_pts)}** events with points > 0, "
            f"affecting **{_pts['case:concept:name'].nunique()}** cases. "
            "Associated activities:"
        ),
        _pts["concept:name"].value_counts(),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Answer:** **3,548 events** have points > 0. All of them are **Create Fine** events, and they affect **3,548 cases**, i.e. exactly one event per case. That is about **2.4 %** of all 150,370 cases.

    As with vehicleClass, points are only set once at the creation of the fine and are effectively a **case attribute**. This confirms the hypothesis: most offences in this log are minor ones without point deductions.

    **Findings / further questions:**
    - Points are never updated during the process. If a fine is later dismissed (e.g., by the prefecture or a judge), the log still shows the points. It is unclear whether they were actually deducted. Recommendation: record the final status of the points deduction.
    - Which articles lead to points? Correlating points with article and amount could show whether the data is consistent.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Session 2

    ## Task 2.1
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Task 2.2
    """)
    return


if __name__ == "__main__":
    app.run()
