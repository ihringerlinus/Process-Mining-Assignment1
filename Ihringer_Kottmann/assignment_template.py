import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Assignment 1

    Linus Ihringer and Paul Kottmann
    """)
    return


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import plotly.express as px
    import plotly.io as _pio
    import pm4py

    # Swiss number format in all charts: decimal point, apostrophe as thousands separator
    _pio.templates[_pio.templates.default].layout.separators = ".'"
    return mo, pd, pm4py, px


@app.function
def num(value, decimals=0):
    # Swiss number format: apostrophe as thousands separator, e.g. 150'370
    return f"{value:,.{decimals}f}".replace(",", "'")


@app.cell
def _(mo, pm4py):
    # The log is not in the repo (see .gitignore): put the unpacked .xes file in the repo root.
    _log_path = mo.notebook_dir().parent / 'Road_Traffic_Fine_Management_Process.xes'
    event_log_from_disk = pm4py.read_xes(str(_log_path), variant="rustxes")
    print(num(len(event_log_from_disk)), 'events read.')
    event_log_from_disk
    return (event_log_from_disk,)


@app.cell
def _(event_log_from_disk):
    CASE_ID = 'case:concept:name'
    ACTIVITY = 'concept:name'
    TIMESTAMP = 'time:timestamp'

    event_log = event_log_from_disk.copy()
    event_log['original_order'] = range(len(event_log))
    event_log = event_log.sort_values([CASE_ID, TIMESTAMP, 'original_order']).reset_index(drop=True)

    event_log.dtypes
    return ACTIVITY, CASE_ID, TIMESTAMP, event_log


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Session 1

    ## Task 1.1

    ### a) What time interval does the log cover?

    **Hypothesis:** Since this is a real-world administrative log, we expect it to cover several years. Timestamps are probably recorded as dates only, not with an exact time of day.
    """)
    return


@app.cell
def _(event_log_from_disk, mo):
    _start = event_log_from_disk["time:timestamp"].min()
    _end = event_log_from_disk["time:timestamp"].max()
    mo.md(f"""
    | | |
    |---|---|
    | **Start** | {_start:%d.%m.%Y %H:%M %Z} |
    | **End** | {_end:%d.%m.%Y %H:%M %Z} |
    | **Duration** | {_end - _start} |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Answer:** The log covers **01.01.2000 to 18.06.2013** (local Italian time), i.e. about **13.5 years** (4'917 days).

    In the raw data, the timestamps are stored in UTC: the first is 31.12.1999 23:00 UTC and the last is 17.06.2013 22:00 UTC. Converted to Italian time (CET = UTC+1 in winter, CEST = UTC+2 in summer), both fall exactly at **midnight**. This strongly suggests that the timestamps only have **day granularity** and that the time component is an artefact of the time zone conversion.

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

    **Hypothesis:** We expect a small number of vehicle classes (e.g., car, motorcycle, truck), roughly 3–6 distinct values, with cars being the vast majority.
    """)
    return


@app.cell
def _(event_log_from_disk, mo):
    mo.vstack([
        mo.md(f"**{event_log_from_disk['vehicleClass'].nunique()}** distinct values (excluding empty values):"),
        event_log_from_disk["vehicleClass"].value_counts(dropna=False),
        mo.md(num(event_log_from_disk["case:concept:name"].nunique())),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Answer:** vehicleClass has **4 distinct values**: A (146'712 events), C (2'456), M (1'198) and R (4). In addition, 411'100 events have no value (NaN).

    The four values add up to exactly **150'370**, which is the number of cases in the log. Together with the NaN events, this gives exactly the total of 561'470 events. So vehicleClass is most likely recorded **only once per case, on the Create Fine event**. The many empty values are therefore not missing data but a consequence of how the log is structured: vehicleClass is effectively a **case attribute**.

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

    **Hypothesis:** Most fines are probably for minor offences such as parking, so we expect a median of roughly €30–50. The minimum should be above 0 (a fine without an amount makes little sense), and the maximum might be a few hundred to a few thousand euros for serious offences.
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
    - **max: 4'351**

    The median matches the expectation of mostly minor offences (a typical parking fine). The minimum and maximum are surprising.

    **Reflection / recommendation:** We recommend investigating:

    1. **Fines with amount 0:** How many are there? Which articles do they concern, and what happens to these cases (dismissal, payment, credit collection)? They could be data entry errors, placeholders, or a special legal category.
    2. **Outliers at the top (up to 4'351):** Are these legitimate serious offences? Check which articles they belong to and whether they are plausible.
    3. **Currency and unit:** The log starts in 2000, but the euro was introduced as cash in 2002. It should be checked whether early amounts are in lire, converted, or consistent over time (e.g., by plotting amount over time).
    4. **Distribution:** A histogram of amount, ideally per article, would show whether there are a few standard amounts and where the outliers lie.
    5. **Documentation:** The currency and meaning of amount should be documented explicitly.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### d) How many events have a value > 0 for the attribute points? What are the associated activities? How many cases are affected?

    **Hypothesis:** Penalty points are only deducted for more serious offences, while most fines (e.g., parking) carry no points. We expect only a small share of cases, maybe a few percent, to have points > 0. Since points are initialized at Create Fine, we expect Create Fine to be the only associated activity.
    """)
    return


@app.cell
def _(event_log_from_disk, mo):
    _pts = event_log_from_disk[event_log_from_disk["points"] > 0]
    mo.vstack([
        mo.md(
            f"**{num(len(_pts))}** events with points > 0, "
            f"affecting **{num(_pts['case:concept:name'].nunique())}** cases. "
            "Associated activities:"
        ),
        _pts["concept:name"].value_counts(),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Answer:** **3'548 events** have points > 0. All of them are **Create Fine** events, and they affect **3'548 cases**, i.e. exactly one event per case. That is about **2.4 %** of all 150'370 cases.

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
    **Hypothesis:** From Task 1.1a we expect day granularity: the first and the last timestamp of the log both fall exactly at midnight in Italian time. Here we verify this for all events.
    """)
    return


@app.cell
def _(TIMESTAMP, event_log, mo):
    _ts = event_log[TIMESTAMP]
    if _ts.dt.tz is not None:
        _ts = _ts.dt.tz_convert('Europe/Rome')

    mo.md(f"""
    - Time zone in the log: **{event_log[TIMESTAMP].dt.tz}**
    - Events with hour ≠ 0: **{(_ts.dt.hour != 0).sum()}**
    - Events with minute ≠ 0: **{(_ts.dt.minute != 0).sum()}**
    - Events with second ≠ 0: **{(_ts.dt.second != 0).sum()}**
    """)
    return


@app.cell
def _(CASE_ID, TIMESTAMP, event_log, mo):
    _same_day = event_log.duplicated([CASE_ID, TIMESTAMP], keep=False)
    mo.md(f"""
    Events that fall on the same day as another event of the same case: **{num(_same_day.sum())}**,
    spread over **{num(event_log.loc[_same_day, CASE_ID].nunique())}** cases
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The hypothesis is confirmed: all timestamps have day granularity (midnight in Italian time; stored as UTC in the log, so that 22:00/23:00 appears without conversion). Consequences: (1) Throughput times can only be measured in days. (2) For events on the same day in the same case the order is not determined by the timestamp; 21'308 events in 9'166 cases are affected. For enrichments such as cumulative payments we therefore use the original order of the log as the second sorting criterion.
    Finding (data collection): record the time of day as well, so that the order of events on the same day is unambiguous.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Task 2.2
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 2.2a - Hypothesis

    Each activity only has the attributes that are relevant for it from a business point of view (e.g. `paymentAmount` for *Payment*, `expense` for *Send Fine*). Since the log comes from an administrative system that enforces certain fields per step, we expect hardly any missing values. We suspect, however, that missing information is partly stored not as an empty value but as a default value (e.g. `0` or `NIL`).
    """)
    return


@app.cell
def _(ACTIVITY, CASE_ID, TIMESTAMP, event_log):
    schema_attrs = [c for c in event_log.columns
                    if c not in [CASE_ID, ACTIVITY, TIMESTAMP, 'original_order']]

    schema_counts = event_log[schema_attrs].notna().groupby(event_log[ACTIVITY]).sum()
    schema_counts.insert(0, 'n_events', event_log.groupby(ACTIVITY).size())
    schema_counts
    return schema_attrs, schema_counts


@app.cell
def _(pd, schema_attrs, schema_counts):
    _rows = []
    for _act, _row in schema_counts.iterrows():
        _n = _row['n_events']
        for _attr in schema_attrs:
            if 0 < _row[_attr] < _n:
                _rows.append({'activity': _act, 'attribute': _attr,
                              'events': _n, 'missing': _n - _row[_attr]})
    missing_values = pd.DataFrame(_rows)
    missing_values
    return


@app.cell
def _(ACTIVITY, event_log, schema_attrs):
    _num_cols = event_log[schema_attrs].select_dtypes('number').columns
    zero_counts = (event_log[_num_cols] == 0).groupby(event_log[ACTIVITY]).sum()
    zero_counts.T
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 2.2a - Result

    **Missing values (`NaN`):** Only one attribute is incomplete: `lastSent` is missing in **1'631 of 79'860** *Insert Fine Notification* events (about 2 %). All other attributes are complete in the schemas they belong to.

    **Zero values:** The check for `0` shows that the completeness is partly only formal:

    - `totalPaymentAmount` is `0` in **all 150'370** *Create Fine* events. This is plausible from a business point of view (nothing has been paid at the beginning), so at *Create Fine* the attribute is only initialized with a start value.
    - `points` is `0` in **146'822 of 150'370** cases at *Create Fine*; only about 3'500 fines lead to a deduction of points. Here `0` probably means "no points", but a missing value cannot be distinguished from it.
    - `amount` is `0` in **36** *Create Fine* events and **18** *Add penalty* events. A fine or a penalty of 0 is unexpected from a business point of view.
    - At *Payment*, `paymentAmount` is `0` in **3** events and `totalPaymentAmount` is `0` in **2** events. A payment of 0, or a cumulative payment total of 0 *after* a payment, contradicts the meaning of the activity (data error, or cancellation/correction?).
    - `expense` is `0` in **2'860 of 103'987** *Send Fine* events (about 2.8 %). Possibly these fines were delivered without postal costs, or the costs were not recorded.
    - `matricola` is `0` in all **555** *Appeal to Judge* events and therefore carries no information at all.

    **Conclusion:** The hypothesis is partly confirmed. Truly missing values are rare, but `0` is used as a default value and possibly hides missing information.

    **Findings:**

    - Why is `lastSent` missing in 1'631 notifications? Do these cases take a different course?
    - Inspect the cases with `amount = 0`.
    - Inspect the 3 *Payment* events with `paymentAmount = 0`: do they belong to the 2 events with `totalPaymentAmount = 0`? (relevant for Task 2.4b)
    - Do cases with `expense = 0` differ in their further course, e.g. at *Insert Fine Notification*?
    - *Recommendation data collection:* Store values that were not recorded as empty (`NULL`) instead of `0`, so that "not present" and "not recorded" can be distinguished. Fill `matricola` correctly or remove it.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 2.2b - Hypothesis

    We expect the monetary amounts to be shared by several activities: `amount` by *Create Fine* (original fine) and *Add penalty* (fine with penalty), `totalPaymentAmount` by *Create Fine* and *Payment*. Business attributes such as `points` or `vehicleClass` should occur exclusively at *Create Fine*. According to its name, `totalPaymentAmount` is cumulative; for `amount` we suspect that at *Add penalty* it contains the new total amount (i.e. a cumulative value).
    """)
    return


@app.cell
def _(event_log, pd, schema_attrs, schema_counts):
    _in_schema = schema_counts[schema_attrs] > 0

    shared_attrs = pd.DataFrame({
        'n_activities': _in_schema.sum(),
        'activities': _in_schema.apply(lambda col: ', '.join(col.index[col])),
        'numeric': [pd.api.types.is_numeric_dtype(event_log[a]) for a in schema_attrs],
    })
    shared_attrs = shared_attrs[(shared_attrs['n_activities'] > 1) &
                                (shared_attrs['n_activities'] < len(schema_counts))]
    shared_attrs
    return


@app.cell
def _(ACTIVITY, CASE_ID, event_log):
    _initial = event_log[event_log[ACTIVITY] == 'Create Fine'].set_index(CASE_ID)['amount']
    _pen = event_log[event_log[ACTIVITY] == 'Add penalty'][[CASE_ID, 'amount']].copy()
    _pen['initial_amount'] = _pen[CASE_ID].map(_initial)
    _pen['ratio'] = (_pen['amount'] / _pen['initial_amount']).round(2)
    _pen['ratio'].value_counts().head(10)
    return


@app.cell
def _(ACTIVITY, CASE_ID, TIMESTAMP, event_log):
    _pay = event_log[event_log[ACTIVITY] == 'Payment'].copy()
    _pay['n_payment'] = _pay.groupby(CASE_ID).cumcount() + 1
    _multi = _pay[_pay.groupby(CASE_ID)[CASE_ID].transform('size') > 1]
    _multi[[CASE_ID, TIMESTAMP, 'n_payment', 'paymentAmount', 'totalPaymentAmount']].head(15)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 2.2b - Result

    There are four shared (non-global) attributes:

    | Attribute | Activities | Type | Classification |
    |---|---|---|---|
    | `totalPaymentAmount` | Create Fine, Payment | numerical | **case-cumulative** |
    | `amount` | Create Fine, Add penalty | numerical | **case-cumulative** |
    | `org:resource` | Create Fine, Appeal to Judge | categorical | - |
    | `dismissal` | Create Fine, Send Appeal to Prefecture, Appeal to Judge | categorical | - |

    **`amount`:** At *Add penalty*, `amount` is almost always about **twice** the amount at *Create Fine* (ratio 1.96 to 2.06 in the most frequent cases). The attribute therefore contains the new total amount including the penalty, and not only the penalty itself. It is thus cumulative within a case.

    **`totalPaymentAmount`:** In cases with several payments, `totalPaymentAmount` equals the sum of the `paymentAmount` values so far (e.g. case A10009: 35 + 22 = 57). It is thus cumulative within a case; its incremental counterpart is `paymentAmount`. Whether the sum is correct in all cases is something we check in Task 2.4b.

    **Conclusion:** The hypothesis is confirmed for the numerical attributes. We had not expected `org:resource` and `dismissal` to be shared as well. For `dismissal` this is plausible, because the appeal activities decide about a dismissal.

    **Findings:**

    - The penalty does not double the fine exactly (ratios from 1.96 to 2.06, outliers at 2.5 and 4). Possible causes: rounding, different rules per article, or additional fees. To be investigated further.
    - `org:resource` is only recorded at *Create Fine* and *Appeal to Judge*. For all other steps it cannot be traced who performed them. *Recommendation data collection:* record the resource for all activities.
    - The naming is inconsistent: the name `totalPaymentAmount` indicates that it is cumulative, the name `amount` does not. *Recommendation:* rename it, e.g. to `totalFineAmount`.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 2.3 - Case inspection

    We choose case **A10009** because, according to Task 2.2b, it contains several payments and therefore shows many attributes in interaction.

    **Hypothesis:** We expect the typical course of a fine that is not paid immediately: *Create Fine* → *Send Fine* (with postal expenses) → *Insert Fine Notification* → *Add penalty* (fine doubled because it was not paid in time) → payments in instalments until the total of fine, penalty and expenses is settled.
    """)
    return


@app.cell
def _(ACTIVITY, CASE_ID, TIMESTAMP, event_log):
    _case_id = 'A10009'
    _cols = [TIMESTAMP, ACTIVITY, 'amount', 'expense', 'paymentAmount', 'totalPaymentAmount',
             'points', 'article', 'vehicleClass', 'notificationType', 'lastSent',
             'dismissal', 'org:resource', 'matricola']
    case_2_3 = event_log[event_log[CASE_ID] == _case_id][_cols].copy()
    case_2_3[TIMESTAMP] = case_2_3[TIMESTAMP].dt.tz_convert('Europe/Rome').dt.strftime('%d.%m.%Y')
    print(case_2_3.to_string())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 2.3 - Result: case A10009

    - **20.03.2007, Create Fine:** A fine of **22 €** is issued, based on article 7, for a vehicle of class A. No points are deducted (`points = 0`). It was recorded by resource 537. `dismissal = NIL` is the initial value (no dismissal), `totalPaymentAmount = 0` (nothing paid yet).
    - **17.07.2007, Send Fine:** The fine is only sent **119 days** after it was issued. This causes postal expenses of **13 €** (`expense`).
    - **23.07.2007, Insert Fine Notification:** **6 days** after the fine was sent, the notification is registered. The recipient is the car owner (`notificationType = P`). `lastSent` also has the value P.
    - **21.09.2007, Add penalty:** Exactly **60 days** after the notification a penalty is added. `amount` rises to **44 €**, i.e. to twice the original fine. This fits a payment deadline of 60 days that has passed without a payment.
    - **01.10.2007, Payment:** 10 days later the owner pays **35 €** (`totalPaymentAmount = 35`). This is exactly the original fine plus the postal expenses (22 + 13).
    - **31.10.2007, Payment:** One month later a second payment of **22 €** follows. In total **57 €** have now been paid, which is exactly the total amount due: 44 € (fine including penalty) + 13 € (expenses). The case is closed.

    **Interpretation:** The hypothesis is confirmed. The case follows the expected course, and the amounts are consistent: `amount` is cumulative (fine including penalty), `totalPaymentAmount` sums up the payments correctly, and at the end no amount is outstanding. The first payment is exactly the amount *without* the penalty. Presumably the owner first settled only the original claim without knowing about the penalty, and paid the penalty afterwards. The whole case takes **225 days**, of which 119 days alone pass before the fine is sent.

    **Findings:**

    - Almost 4 months lie between *Create Fine* and *Send Fine*. How long does this take on average, and are there legal deadlines for it? (candidate for the performance analysis in Session 6)
    - `lastSent` (meaning unknown) agrees with `notificationType` in this case (P). A cross table over all 79'860 *Insert Fine Notification* events shows, however, that this does not hold in general: the values are equal in only about 58 % of the cases. `lastSent` also has an additional value **N** (30'313 events, almost all of them with `notificationType = P`), and in 1'380 cases `notificationType = P` occurs together with `lastSent = C`, but never the other way round. So the attribute is not redundant, but its meaning remains unclear. *Recommendation data collection:* document the attributes and their value ranges.
    - Do offenders often pay only the original amount first after a penalty has been added? This could point to an unclear communication of the penalty (suggestion for improving the process).
    """)
    return


@app.cell
def _(ACTIVITY, event_log, pd):
    _notif = event_log[event_log[ACTIVITY] == 'Insert Fine Notification']
    pd.crosstab(_notif['notificationType'], _notif['lastSent'], dropna=False)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Task 2.4

    ### Task 2.4 - Hypothesis

    We expect our own running sum of `paymentAmount` to match the existing attribute `totalPaymentAmount` in almost all events, because the two were consistent in case A10009 (Task 2.3).

    We expect a small number of deviations from two sources we already know: the three *Payment* events with `paymentAmount = 0` (Task 2.2a), and cases with several payments on the same day, where the order of events is not determined by the timestamp (Task 2.1).
    """)
    return


@app.cell
def _(ACTIVITY, CASE_ID, event_log):
    event_log_t4 = event_log.copy()
    event_log_t4['cum_payment_amount'] = (
        event_log_t4['paymentAmount'].fillna(0)
        .groupby(event_log_t4[CASE_ID]).cumsum()
        .round(2)
    )
    event_log_t4[[CASE_ID, ACTIVITY, 'paymentAmount', 'totalPaymentAmount', 'cum_payment_amount']].head(10)
    return (event_log_t4,)


@app.cell
def _(ACTIVITY, CASE_ID, TIMESTAMP, event_log_t4):
    _cols = [TIMESTAMP, ACTIVITY, 'paymentAmount', 'totalPaymentAmount', 'cum_payment_amount']
    _case = event_log_t4[event_log_t4[CASE_ID] == 'A10009'][_cols].copy()
    _case[TIMESTAMP] = _case[TIMESTAMP].dt.tz_convert('Europe/Rome').dt.strftime('%d.%m.%Y')
    _case
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 2.4a - Result

    We inspect case **A10009**, which contains two payments. Before the first payment, `cum_payment_amount` is 0. After the first payment of 35 it is 35, and after the second payment of 22 it is 57 (35 + 22). The enrichment is computed correctly for this case.

    In this case our running sum also equals the existing attribute `totalPaymentAmount` at both *Payment* events (35 and 57).
    """)
    return


@app.cell
def _(ACTIVITY, CASE_ID, event_log_t4, mo):
    _filled = event_log_t4[event_log_t4['totalPaymentAmount'].notna()].copy()
    _filled['deviation'] = (_filled['totalPaymentAmount'] - _filled['cum_payment_amount']).round(2)
    deviations = _filled[_filled['deviation'] != 0]

    mo.vstack([
        mo.md(f"""
    - Events compared: **{num(len(_filled))}**
    - Deviating events: **{len(deviations)}** in **{deviations[CASE_ID].nunique()}** cases
    - Sum of all deviations: **{num(deviations['deviation'].sum(), 2)}**
    """),
        _filled[ACTIVITY].value_counts(),
        deviations[ACTIVITY].value_counts(),
        deviations['deviation'].describe().round(2),
    ])
    return


@app.cell
def _(ACTIVITY, CASE_ID, TIMESTAMP, event_log_t4, mo):
    _pay = event_log_t4[event_log_t4[ACTIVITY] == 'Payment'].copy()
    _pay['deviation'] = (_pay['totalPaymentAmount'] - _pay['cum_payment_amount']).round(2)

    # how many payments does the case have on that same day?
    _pay['payments_same_day'] = _pay.groupby([CASE_ID, TIMESTAMP])[ACTIVITY].transform('size')

    # our running sum at the end of that day
    _pay['end_of_day_sum'] = _pay.groupby([CASE_ID, TIMESTAMP])['cum_payment_amount'].transform('last')
    _pay['deviation_end_of_day'] = (_pay['totalPaymentAmount'] - _pay['end_of_day_sum']).round(2)

    _dev = _pay[_pay['deviation'] != 0]
    real_deviations = _pay[_pay['deviation_end_of_day'] != 0]
    _last = _pay.groupby(CASE_ID).tail(1)

    mo.vstack([
        mo.md(f"""
    - Deviating events on a day with more than one payment in the case: **{(_dev['payments_same_day'] > 1).sum()}** of **{len(_dev)}**
    - Deviating events with `paymentAmount = 0`: **{(_dev['paymentAmount'] == 0).sum()}**
    - Deviations left if `totalPaymentAmount` is read as the total at the end of the day: **{len(real_deviations)}** events in **{real_deviations[CASE_ID].nunique()}** cases
    - Cases whose final `totalPaymentAmount` differs from the sum of all payments: **{(_last['deviation_end_of_day'] != 0).sum()}** (sum of differences: **{num(_last['deviation_end_of_day'].sum(), 2)}**)
    """),
        _dev[[CASE_ID, TIMESTAMP, 'paymentAmount', 'totalPaymentAmount', 'cum_payment_amount', 'deviation', 'payments_same_day']].head(15),
        real_deviations[[CASE_ID, TIMESTAMP, 'paymentAmount', 'totalPaymentAmount', 'cum_payment_amount', 'deviation_end_of_day']].head(15),
    ])
    return


@app.cell
def _(CASE_ID, TIMESTAMP):
    def show_case(log, case_id, columns):
        # all events of one case; timestamps shown as dates in Italian time
        case = log[log[CASE_ID] == case_id][[TIMESTAMP] + columns].copy()
        case[TIMESTAMP] = case[TIMESTAMP].dt.tz_convert('Europe/Rome').dt.strftime('%d.%m.%Y')
        return case

    return (show_case,)


@app.cell
def _(ACTIVITY, CASE_ID, TIMESTAMP, event_log_t4, mo, show_case):
    _cols = [ACTIVITY, 'amount', 'expense', 'paymentAmount', 'totalPaymentAmount', 'cum_payment_amount']
    _zero = event_log_t4[(event_log_t4[ACTIVITY] == 'Payment') & (event_log_t4['paymentAmount'] == 0)]

    mo.vstack([
        mo.md("**Case A12292:** two payments on the same day"),
        show_case(event_log_t4, 'A12292', _cols),
        mo.md("**Case A22233:** deviation that is not explained by same-day payments"),
        show_case(event_log_t4, 'A22233', _cols),
        mo.md("**Case C17607:** deviation that is not explained by same-day payments"),
        show_case(event_log_t4, 'C17607', _cols),
        mo.md("**All *Payment* events with `paymentAmount = 0`**"),
        _zero[[CASE_ID, TIMESTAMP, 'paymentAmount', 'totalPaymentAmount', 'cum_payment_amount']],
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 2.4b - Result

    **Comparison.** `totalPaymentAmount` is filled for 227'971 events (150'370 *Create Fine*, 77'601 *Payment*). It differs from our running sum in **95 events in 77 cases**, all of them *Payment* events (0.12 % of all payments). The stored total is always **higher**, by 1.98 to 180 (median 46), in total 5'322.14.

    **Interpretation.** There are two causes.

    1. **Several payments on the same day (28 events, 27 cases).** In case A12292 two payments (49 and 87) are registered on 22.09.2008, and both events already show the total at the end of that day (136). This follows from the day granularity (Task 2.1) and is not an error. Read as "total at the end of the day", these deviations disappear. (32 deviating events lie on such days, but 4 of them still deviate at the end of the day.)
    2. **Real inconsistencies (67 events, 50 cases).** In these cases the final `totalPaymentAmount` also differs from the sum of all payments, by 2'296.87 in total. Two cases point in opposite directions:
        - **A22233:** The payments of 49 and 38 add up to 87, exactly the amount due. The stored total shows 98 and then 136, so the first payment is counted twice. Here the stored total is wrong.
        - **C17607:** The offender pays instalments of 50. At the eleventh the stored total jumps from 500 to 600, and the last payment brings it to 687.75, exactly the initial fine amount. A *Payment* event of 50 seems to be missing. Here the stored total is right and the log is incomplete.

    Of the three payments with `paymentAmount = 0` (Task 2.2a) only one deviates (S89610, stored total 33.6).

    **Conclusion.** The hypothesis is partly confirmed. `totalPaymentAmount` is correct for 99.88 % of the *Payment* events, and same-day payments cause deviations as expected. We did not expect that they explain less than a third of the deviations and that in 50 cases the stored total and the payment events contradict each other.

    **Findings:**

    - The log alone cannot tell a double-counted payment from a missing *Payment* event. The 50 cases should be checked against the source system. Are *Payment* events also missing in cases where no stored total reveals it?
    - *Recommendation data collection:* Validate a derived total when it is written, and record the time of day (Task 2.1) so that payments on the same day can be ordered.
    - For Task 2.5 we use our own sum `cum_payment_amount`, because it is defined for every event. The choice only matters for the 50 cases above.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Task 2.5 (Part 2: outstanding amount)

    ### Task 2.5 (Part 2) - Hypothesis

    We define the outstanding amount after each event as: fine amount currently due (including the penalty, if added) + expenses recorded so far - payments made so far.

    Every case starts with the full fine outstanding, and the outstanding amount can only drop to 0 at a *Payment* event. Even if every one of the 77'601 *Payment* events settled a fine completely, 483'869 of the 561'470 events (86 %) would still have an outstanding amount > 0. Because some payments are only partial (as the first payment in case A10009), we expect **slightly more than 86 %** of all events to have `outstanding_amount > 0`. We expect at most a few negative values, since nobody should pay more than is due.
    """)
    return


@app.cell
def _(ACTIVITY, CASE_ID, event_log_t4):
    event_log_t5 = event_log_t4.copy()

    # Preliminary attribute 1: the fine amount that is currently due.
    # `amount` is case-cumulative (Task 2.2b), so its latest value already includes the penalty.
    event_log_t5['latest_amount'] = event_log_t5.groupby(CASE_ID)['amount'].ffill()

    # Preliminary attribute 2: all expenses recorded so far in the case.
    event_log_t5['cum_expense'] = (
        event_log_t5['expense'].fillna(0)
        .groupby(event_log_t5[CASE_ID]).cumsum()
        .round(2)
    )

    # Preliminary attribute 3 is `cum_payment_amount` from Task 2.4.
    event_log_t5['outstanding_amount'] = (
        event_log_t5['latest_amount'] + event_log_t5['cum_expense'] - event_log_t5['cum_payment_amount']
    ).round(2)

    event_log_t5[[CASE_ID, ACTIVITY, 'amount', 'expense', 'paymentAmount',
                  'latest_amount', 'cum_expense', 'cum_payment_amount', 'outstanding_amount']].head(10)
    return (event_log_t5,)


@app.cell
def _(ACTIVITY, event_log_t5, mo, show_case):
    _cols = [ACTIVITY, 'amount', 'expense', 'paymentAmount',
             'latest_amount', 'cum_expense', 'cum_payment_amount', 'outstanding_amount']

    mo.vstack([
        mo.md(f"Events without a value for `outstanding_amount`: **{event_log_t5['outstanding_amount'].isna().sum()}**"),
        mo.md("**Case A10009:** paid in two instalments"),
        show_case(event_log_t5, 'A10009', _cols),
        mo.md("**Case A100:** never paid"),
        show_case(event_log_t5, 'A100', _cols),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 2.5a (Part 2) - Result

    We define three preliminary event enrichments and combine them: `outstanding_amount = latest_amount + cum_expense - cum_payment_amount`.

    - `latest_amount`: the latest value of `amount` in the case. `amount` is case-cumulative (Task 2.2b), so after *Add penalty* it already contains the fine including the penalty.
    - `cum_expense`: the running sum of `expense` in the case.
    - `cum_payment_amount`: the running sum of `paymentAmount` from Task 2.4.

    **Case A10009** (paid in two instalments):

    - *Create Fine:* 22 are outstanding (the fine).
    - *Send Fine:* 35 (22 + 13 expenses).
    - *Insert Fine Notification:* unchanged, 35.
    - *Add penalty:* 57 (the fine doubles to 44, plus 13 expenses).
    - *Payment* of 35: 22 remain.
    - *Payment* of 22: 0 remain.

    This matches a manual calculation and the interpretation of this case in Task 2.3: after the second payment nothing is outstanding.

    **Case A100** (never paid): 35 after *Create Fine*, 46 after *Send Fine* (expenses of 11) and 82.50 after *Add penalty* (71.50 + 11). The fine is sent for credit collection with 82.50 still outstanding.

    The enrichment is computed correctly in both cases, and every event has a value.
    """)
    return


@app.cell
def _(ACTIVITY, CASE_ID, event_log_t5, mo, pd):
    _o = event_log_t5['outstanding_amount']

    _by_activity = pd.DataFrame({
        'events': event_log_t5.groupby(ACTIVITY).size(),
        'outstanding > 0': (_o > 0).groupby(event_log_t5[ACTIVITY]).sum(),
        'outstanding = 0': (_o == 0).groupby(event_log_t5[ACTIVITY]).sum(),
        'outstanding < 0': (_o < 0).groupby(event_log_t5[ACTIVITY]).sum(),
    }).sort_values('events', ascending=False)

    # outstanding amount after the last event of each case
    _last = event_log_t5.groupby(CASE_ID).tail(1)
    _final = _last['outstanding_amount']

    # robustness: the same count if the stored total is used instead of our own running sum
    _stored_total = event_log_t5.groupby(CASE_ID)['totalPaymentAmount'].ffill()
    _alt = (event_log_t5['latest_amount'] + event_log_t5['cum_expense'] - _stored_total).round(2)

    # cases with a dismissal value other than the initial value NIL
    _dismissed = event_log_t5.loc[
        event_log_t5['dismissal'].notna() & (event_log_t5['dismissal'] != 'NIL'), CASE_ID].unique()
    _final_dismissed = _final[_last[CASE_ID].isin(_dismissed)]

    mo.vstack([
        mo.md(f"""
    - Events with `outstanding_amount > 0`: **{num((_o > 0).sum())}** of {num(len(_o))} ({(_o > 0).mean():.2%})
    - Events with `outstanding_amount = 0`: **{num((_o == 0).sum())}** ({(_o == 0).mean():.2%})
    - Events with `outstanding_amount < 0`: **{num((_o < 0).sum())}** ({(_o < 0).mean():.2%})
    - Events with an outstanding amount > 0 if the stored `totalPaymentAmount` is used instead of our own sum: **{num((_alt > 0).sum())}**
    """),
        _by_activity,
        mo.md(f"""
    **After the last event of each case** ({num(len(_final))} cases):

    - outstanding amount > 0: **{num((_final > 0).sum())}** cases ({(_final > 0).mean():.1%}), in total {num(_final[_final > 0].sum(), 2)}
    - outstanding amount = 0: **{num((_final == 0).sum())}** cases ({(_final == 0).mean():.1%})
    - outstanding amount < 0: **{num((_final < 0).sum())}** cases ({(_final < 0).mean():.1%}), in total {num(_final[_final < 0].sum(), 2)}
    - cases with a dismissal value other than NIL: **{num(len(_final_dismissed))}**, of which **{num((_final_dismissed > 0).sum())}** still show an outstanding amount > 0
    """),
        mo.md("Last activity of the cases that end with an outstanding amount > 0:"),
        _last.loc[_final > 0, ACTIVITY].value_counts(),
        mo.md("Most frequent final values of the overpaid cases:"),
        _final[_final < 0].value_counts().head(5),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 2.5b (Part 2) - Result

    **500'406 of the 561'470 events (89.12 %) have an outstanding amount > 0.** 59'793 events (10.65 %) have an outstanding amount of exactly 0 and 1'271 events (0.23 %) a negative one.

    The hypothesis is confirmed for the share: we expected slightly more than 86 %. The table per activity shows why it is higher. Outside of *Payment* practically every event has an outstanding amount > 0. Of the 77'601 *Payment* events, 59'701 settle the amount due exactly, but **16'642 (21.4 %) leave a positive outstanding amount**. The hypothesis is not confirmed for the overpayments: 1'258 *Payment* events lead to a negative outstanding amount, which is more than "a few".

    After the last event of each case, 90'080 cases (59.9 %) still have an outstanding amount (8.4 million in total), 59'104 cases (39.3 %) are settled exactly and 1'186 cases (0.8 %) are overpaid.

    **Findings:**

    - Most open cases end as expected with *Send for Credit Collection* (58'994). But **20'735 cases end with *Send Fine*** and 6'940 end with a *Payment* that did not cover the amount due. Are these cases still running at the end of the log, or is this leakage in the process?
    - The overpayments are small and systematic: 5.16 (196 cases), 0.01 (166 cases) and 5.17 (87 cases). 0.01 looks like a rounding difference. 5.16 corresponds to 10'000 lire (1 EUR = 1'936.27 lire), possibly a fee from before the euro that was not recorded as `expense` (see the currency question in Task 1.1c).
    - `outstanding_amount` ignores dismissals, as the task defines it: 2'574 of the 2'577 cases with a `dismissal` value other than NIL still show an outstanding amount > 0, although a dismissed fine is not owed (relevant for Session 3).
    - The result barely depends on the payment total used: with the stored `totalPaymentAmount`, 500'360 events have an outstanding amount > 0 (46 fewer).
    - *Recommendation data collection:* Record the amount still due and the reason why a case is closed (paid, dismissed, written off) as case attributes.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Task 2.5 (Part 3: case log)

    A case attribute is an attribute that has at most one distinct value per case. We first determine which attributes of the log fulfil this definition and then build the case log from them.
    """)
    return


@app.cell
def _(CASE_ID, event_log):
    _attributes = [c for c in event_log.columns if c not in [CASE_ID, 'original_order']]
    _max_values = event_log.groupby(CASE_ID)[_attributes].nunique().max().sort_values()

    case_attributes = _max_values[_max_values <= 1].index.tolist()
    _max_values.rename('max. number of distinct values per case').to_frame()
    return (case_attributes,)


@app.cell
def _(ACTIVITY, CASE_ID, TIMESTAMP, case_attributes, event_log):
    _cases = event_log.groupby(CASE_ID)

    case_log_initial = _cases.agg(
        start_time=(TIMESTAMP, 'first'),
        end_time=(TIMESTAMP, 'last'),
        no_of_events=(ACTIVITY, 'count'),
    )
    # first() returns the first non-missing value of the case, which is the only one for a case attribute
    case_log_initial[case_attributes] = _cases[case_attributes].first()
    case_log_initial
    return (case_log_initial,)


@app.cell
def _(ACTIVITY, CASE_ID, case_log_initial, event_log, mo):
    case_log_t5 = case_log_initial.copy()
    case_log_t5['initial_amount'] = event_log.groupby(CASE_ID)['amount'].first()

    # check: the first value of `amount` in a case is the amount of its Create Fine event
    _create_fine = event_log[event_log[ACTIVITY] == 'Create Fine'].set_index(CASE_ID)['amount']
    _different = (case_log_t5['initial_amount'] != _create_fine.reindex(case_log_t5.index)).sum()

    mo.vstack([
        mo.md(f"""
    - Cases in the case log: **{num(len(case_log_t5))}**, columns: **{case_log_t5.shape[1]}**
    - Cases without a value for `initial_amount`: **{case_log_t5['initial_amount'].isna().sum()}**
    - Cases where `initial_amount` differs from the `amount` of the *Create Fine* event: **{_different}**
    """),
        case_log_t5[['start_time', 'end_time', 'no_of_events', 'article', 'vehicleClass', 'points', 'expense', 'initial_amount']].head(10),
    ])
    return (case_log_t5,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 2.5 (Part 3) - Case log

    Eight attributes have at most one distinct value per case and are therefore case attributes: `article`, `vehicleClass`, `points`, `expense`, `notificationType`, `lastSent`, `matricola` and `lifecycle:transition`. The last one is constant in the whole log ("complete") and carries no information. `org:resource`, `dismissal`, `amount` and the two payment attributes are not case attributes, because they can change within a case.

    The initial case log has one row per case (150'370 rows). Besides the case attributes it contains the start time, the end time and the number of events of the case, as in the lecture. `initial_amount` is the first value of `amount` in the case. For every case it equals the `amount` of the *Create Fine* event, and no case is without a value.

    ### Task 2.5a (Part 3) - Hypothesis

    We already know the minimum (0), the median (35) and the maximum (4'351) of the initial amount from Task 1.1c. Fines are set by law per offence, so we expect a discrete distribution with only a few standard amounts instead of a smooth curve. We expect it to be strongly right-skewed: the bulk of the cases close to the median of 35 (minor offences such as parking) and a thin tail of rare, expensive offences up to 4'351.
    """)
    return


@app.cell
def _(case_log_t5, mo, px):
    _amount = case_log_t5['initial_amount']
    # the amounts are discrete, so we plot the number of cases per distinct amount
    _counts = _amount.value_counts().rename_axis('initial_amount').reset_index(name='cases')

    _fig_zoom = px.histogram(_counts[_counts['initial_amount'] <= 100], x='initial_amount', y='cases', histfunc='sum',
                             title='Initial fine amount up to 100 (bin width 1, linear y-axis)')
    _fig_zoom.update_traces(xbins=dict(start=0, end=101, size=1))
    _fig_zoom.update_layout(yaxis_title='number of cases', bargap=0.1, height=380)

    _fig_all = px.histogram(_counts, x='initial_amount', y='cases', histfunc='sum', log_y=True,
                            title='Initial fine amount, all cases (bin width 25, logarithmic y-axis)')
    _fig_all.update_traces(xbins=dict(start=0, end=4375, size=25))
    _fig_all.update_layout(yaxis_title='number of cases (log)', bargap=0.1, height=380)

    mo.vstack([_fig_zoom, _fig_all])
    return


@app.cell
def _(case_log_t5, mo, pd):
    _amount = case_log_t5['initial_amount']

    _top = _amount.value_counts().head(8)
    _top_table = pd.DataFrame({
        'cases': _top,
        'share %': (100 * _top / len(_amount)).round(2),
        'cumulative share %': (100 * _top.cumsum() / len(_amount)).round(2),
    })

    _year = case_log_t5['start_time'].dt.tz_convert('Europe/Rome').dt.year.rename('year of Create Fine')
    _per_year = pd.DataFrame({
        'cases': _amount.groupby(_year).size(),
        'most frequent initial_amount': _amount.groupby(_year).agg(lambda s: s.mode().iloc[0]),
        'share of this amount %': _amount.groupby(_year).agg(lambda s: round(100 * s.value_counts().iloc[0] / len(s), 1)),
    })

    mo.vstack([
        mo.md(f"""
    - Distinct values of `initial_amount`: **{_amount.nunique()}**
    - Skewness: **{_amount.skew():.1f}**
    - Cases with an initial amount of 0: **{(_amount == 0).sum()}**, of 500 or more: **{(_amount >= 500).sum()}**
    """),
        _amount.describe(percentiles=[.05, .25, .5, .75, .95, .99]).round(2),
        mo.md("The eight most frequent values:"),
        _top_table,
        mo.md("The most frequent value per year:"),
        _per_year,
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 2.5b (Part 3) - Result

    **Visualization.** The amounts are discrete, so we plot the number of cases per amount in two histograms: the range up to 100 with a linear y-axis (95 % of the cases), and the full range with a logarithmic y-axis, which makes the rare high amounts visible.

    **Observation 1: the distribution consists of a few spikes.** The 150'370 cases share only 113 distinct amounts, and the eight most frequent ones (31.30, 32, 32.80, 33.60, 35, 36, 38 and 39) cover 75.8 % of all cases. Half of the cases lie between 32.80 and 38 (lower and upper quartile).

    **Observation 2: the spikes are one standard fine that is raised over time, not eight different offences.** In every year a single amount dominates, and it rises stepwise: 31.30 (2000), 32.80 (2001), 32 (2002), 33.60 (2003 and 2004), 35 (2005 and 2006), 36 (2007 and 2008), 38 (2009 and 2010), 39 (2011 and 2012) and 41 (2013). From 2003 on the step comes every two years. Amounts from different years are therefore not directly comparable.

    **Hypothesis.** Confirmed: the distribution is discrete and strongly right-skewed (skewness 17.0). 99 % of the fines are at most 155, but 364 fines are 500 or more and the maximum is 4'351. We did not expect that the position of the main spike depends on the year.

    **Findings:**

    - The share of the dominant amount falls from 87.9 % (2004 and 2005) to 50.3 % (2011). Did the mix of offences change, or were additional tariffs introduced?
    - The 36 fines with an amount of 0 and the 364 fines of 500 or more should be inspected (see Task 1.1c).
    - The standard amounts of 2000 and 2001 (31.30 and 32.80) are not round. They correspond to 60'600 and 63'500 lire (1 EUR = 1'936.27 lire), which suggests that amounts from before 2002 were recorded in lire and converted. See also Task 2.7.
    - *Recommendation:* Compare amounts only within a year, or relative to the standard amount of the year.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Task 2.6

    ### Task 2.6 - Hypothesis

    `amount` only changes at Add penalty (Task 2.2b), and there it is about twice the initial amount. We therefore expect two groups of cases and nothing else: cases without a penalty on the line final = initial, and cases with a penalty close to the line final = 2 x initial. The log has 79'860 Add penalty events for 150'370 cases, so we expect about 53 % of the cases in the second group. No case should have a final amount below the initial amount.
    """)
    return


@app.cell
def _(CASE_ID, case_log_t5, event_log):
    case_log_t6 = case_log_t5.copy()
    case_log_t6['final_amount'] = event_log.groupby(CASE_ID)['amount'].last()

    # final amount as a multiple of the initial amount (not defined for an initial amount of 0)
    case_log_t6['amount_ratio'] = (
        case_log_t6['final_amount'] / case_log_t6['initial_amount'].where(case_log_t6['initial_amount'] > 0)
    ).round(3)

    case_log_t6[['initial_amount', 'final_amount', 'amount_ratio']].head(10)
    return (case_log_t6,)


@app.cell
def _(case_log_t6, mo, px):
    # many cases share the same combination of amounts, so we plot one bubble per combination
    _pairs = (
        case_log_t6.groupby(['initial_amount', 'final_amount']).size()
        .rename('cases').reset_index()
    )
    _plot = _pairs[_pairs['initial_amount'] > 0]

    _fig = px.scatter(_plot, x='initial_amount', y='final_amount', size='cases', size_max=45,
                      log_x=True, log_y=True, opacity=0.6,
                      title='Initial vs. final fine amount (one bubble per combination, area = number of cases, log axes)')
    _fig.update_traces(marker_sizemin=3)
    _range = [_plot['initial_amount'].min(), _plot['initial_amount'].max()]
    _fig.add_scatter(x=_range, y=_range, mode='lines', name='final = initial',
                     line=dict(dash='dot', width=1))
    _fig.add_scatter(x=_range, y=[2 * _range[0], 2 * _range[1]], mode='lines', name='final = 2 x initial',
                     line=dict(dash='dash', width=1))
    _fig.update_layout(height=520)

    _same = case_log_t6['final_amount'] == case_log_t6['initial_amount']
    _higher = case_log_t6['final_amount'] > case_log_t6['initial_amount']
    _lower = case_log_t6['final_amount'] < case_log_t6['initial_amount']
    _ratio = case_log_t6.loc[_higher, 'amount_ratio']

    # is the final amount determined by the initial amount? share of the most frequent final amount per initial amount
    _increased = case_log_t6[_higher]
    _most_frequent_final = _increased.groupby('initial_amount')['final_amount'].agg(lambda s: s.value_counts().iloc[0]).sum()

    mo.vstack([
        _fig,
        mo.md(f"""
    - final = initial: **{num(_same.sum())}** cases ({_same.mean():.1%})
    - final > initial: **{num(_higher.sum())}** cases ({_higher.mean():.1%})
    - final < initial: **{num(_lower.sum())}** cases
    - Distinct combinations of initial and final amount: **{len(_pairs)}**
    - `amount_ratio` of the cases with final > initial: median **{_ratio.median():.3f}**, 1 % quantile {_ratio.quantile(0.01):.3f}, 99 % quantile {_ratio.quantile(0.99):.3f}, minimum {_ratio.min():.3f}, maximum {_ratio.max():.3f}
    - Share of these cases with a ratio between 1.95 and 2.07: **{_ratio.between(1.95, 2.07).mean():.2%}**, with a final amount of exactly twice the initial amount: {(_increased['final_amount'] == 2 * _increased['initial_amount']).mean():.1%}
    - Share of these cases that have the most frequent final amount for their initial amount: **{_most_frequent_final / len(_increased):.1%}**
    """),
        mo.md("The ten most frequent combinations:"),
        _pairs.sort_values('cases', ascending=False).head(10),
        mo.md("Combinations with a ratio above 2.2:"),
        _pairs[(_pairs['initial_amount'] > 0) & (_pairs['final_amount'] / _pairs['initial_amount'].where(_pairs['initial_amount'] > 0) > 2.2)]
            .sort_values('cases', ascending=False).head(8),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 2.6 - Result

    **Visualization.** The 150'370 cases have only 195 distinct combinations of initial and final amount. A scatter plot with one point per case would hide this, so we plot one bubble per combination, with the number of cases as bubble area. Both axes are logarithmic. The 36 cases with an initial amount of 0 cannot be shown on a logarithmic axis; their final amount is 0 as well.

    **Description.** All bubbles lie on two parallel lines. 70'528 cases (46.9 %) lie on the line final = initial, 79'842 cases (53.1 %) lie above it and none below. For the cases above the line the final amount is almost exactly twice the initial amount: the median ratio is 2.039, and 99.96 % of them have a ratio between 1.95 and 2.07. Only 30 cases in 11 combinations have a clearly higher ratio, between 2.5 and 4. All of them are expensive offences with an initial amount of 259 or more.

    **Interpretation.** The two lines are the two groups of the hypothesis: fines without a penalty and fines with a penalty. The share of 53.1 % matches the 79'860 *Add penalty* events (79'842 cases plus the 18 cases in which the amount is 0 before and after the penalty). The hypothesis is confirmed.

    We did not expect that the penalty is not a surcharge that varies from case to case. The final amount is determined by the initial amount: 99.7 % of the cases with a penalty have the most frequent final amount for their initial amount, e.g. 35 becomes 71.50, 36 becomes 74, 38 becomes 77.50 and 33.60 becomes 68.77. The factor is close to 2 but usually not exactly 2 (only 18.9 % of these cases are doubled exactly).

    A possible explanation from outside the log (our assumption, not verified against the legal text): under the Italian traffic code the offender may pay the minimum of the statutory range of a fine within 60 days after the notification, and afterwards half of the statutory maximum is due. A range from 36 to 148 would give 148 / 2 = 74. This would also explain the ratios of 2.5 and 4 for some expensive offences, whose maximum is a different multiple of the minimum, and it fits the 60 days between notification and penalty in case A10009 (Task 2.3).

    **Findings:**

    - 46.9 % of the cases never receive a penalty. Which of them were paid within the deadline, which were dismissed, and which were simply not followed up (compare the 20'735 cases that end with *Send Fine* in Task 2.5b of Part 2)?
    - Because the penalty overwrites `amount`, the initial amount can only be recovered from the *Create Fine* event. *Recommendation data collection:* record the base amount and the penalty as separate attributes.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Task 2.7

    ### Task 2.7 - Hypothesis

    We look at two attributes. For `article` we expect a few articles to dominate, with parking offences (article 157 according to the description of the log) in first place, and we expect penalty points only for a small group of articles (Task 1.1d: only 2.4 % of the cases have points). For `expense` we expect a fixed postal fee, i.e. one value for almost all cases that have a *Send Fine* event.
    """)
    return


@app.cell
def _(case_log_t6, mo, pd):
    _by_article = case_log_t6.groupby('article')
    _articles = pd.DataFrame({
        'cases': _by_article.size(),
        'median initial_amount': _by_article['initial_amount'].median(),
        'cases with points > 0': _by_article['points'].agg(lambda s: (s > 0).sum()),
    }).sort_values('cases', ascending=False)
    _articles.insert(1, 'share %', (100 * _articles['cases'] / len(case_log_t6)).round(2))
    _articles.insert(2, 'cumulative share %', (100 * _articles['cases'].cumsum() / len(case_log_t6)).round(2))
    _articles['share with points %'] = (100 * _articles['cases with points > 0'] / _articles['cases']).round(1)

    _with_points = case_log_t6[case_log_t6['points'] > 0]
    _points_table = pd.crosstab(_with_points['article'], _with_points['points'])
    _points_table = _points_table.loc[_points_table.sum(axis=1).sort_values(ascending=False).index].head(5)

    mo.vstack([
        mo.md(f"""
    - Distinct articles: **{case_log_t6['article'].nunique()}**
    - Cases with points > 0: **{num(len(_with_points))}**, spread over **{_with_points['article'].nunique()}** articles
    - Median initial amount with points: **{_with_points['initial_amount'].median():g}**, without points: **{case_log_t6.loc[case_log_t6['points'] == 0, 'initial_amount'].median():g}**
    """),
        mo.md("The eight most frequent articles:"),
        _articles.head(8),
        mo.md("Number of cases per article and number of points (the five articles with the most cases with points):"),
        _points_table,
    ])
    return


@app.cell
def _(case_log_t6, mo, pd, px):
    _expense = case_log_t6['expense']
    _year = case_log_t6['start_time'].dt.tz_convert('Europe/Rome').dt.year.rename('year of Create Fine')

    _per_year = pd.DataFrame({
        'most frequent expense': _expense.groupby(_year).agg(lambda s: s.mode().iloc[0]),
        'most frequent initial_amount': case_log_t6['initial_amount'].groupby(_year).agg(lambda s: s.mode().iloc[0]),
    })
    _per_year['expense in % of initial_amount'] = (
        100 * _per_year['most frequent expense'] / _per_year['most frequent initial_amount']).round(1)

    _fig = px.line(_per_year[['most frequent expense', 'most frequent initial_amount']], markers=True,
                   title='Most frequent expense and most frequent initial fine amount per year')
    _fig.update_layout(yaxis_title='amount', legend_title_text='', height=380)

    mo.vstack([
        mo.md(f"""
    - Cases with an `expense`: **{num(_expense.notna().sum())}**, without: **{num(_expense.isna().sum())}**
    - Distinct values of `expense`: **{_expense.nunique()}**, cases with an expense of 0: **{num((_expense == 0).sum())}**
    """),
        _fig,
        _per_year,
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 2.7 - Result

    **Fact 1 (`article` and `points`): three articles make up 91.7 % of all fines, and penalty points depend on the article but are not determined by it.**

    The log contains 66 distinct articles, but article 157 (stopping and parking, 45.27 %), article 7 (28.50 %) and article 158 (17.95 %) together account for 91.7 % of the cases. Points occur in only 3'548 cases, spread over 21 articles. Articles 157 and 7 never carry points. In article 158 only 1'619 of 26'990 cases (6.0 %) carry points, and then always exactly 2. In article 142 (speed limits, according to the Italian traffic code) 1'247 of 5'766 cases (21.6 %) carry points, with 2, 3, 5, 6 or 10 points. Cases with points have a median initial amount of 80, cases without points one of 35.

    So one article covers different offences, with and without points and with different numbers of points. The article number alone does not identify the offence.

    **Fact 2 (`expense`): the expense is not a fixed fee. It rises stepwise over the years and much faster than the fine.**

    103'987 cases have an expense (the cases with a *Send Fine* event) and 46'383 have none. There are 91 distinct values, and 2'860 cases have an expense of 0. The most frequent expense per year is 6.46 (2000), 6.71 (2001), 10 (2002 and 2003), 11 (2004 to 2006), 13 (2007), 13.50 (2008 to 2010), 15 (2011 and 2012) and 16 (2013). That is an increase of 148 %, while the standard fine rose by 31 % in the same period (from 31.30 to 41). Relative to the standard fine the expense grows from 20.6 % in 2000 to 39.0 % in 2013.

    The values of 2000 and 2001 correspond to 12'500 and 13'000 lire (1 EUR = 1'936.27 lire). Together with the standard fines of these years (Task 2.5b of Part 3) and the frequent overpayment of 5.16 = 10'000 lire (Task 2.5b of Part 2), this suggests an answer to the currency question of Task 1.1c: the log is in euro throughout, and the values from before 2002 were converted from lire.

    **Hypothesis.** Confirmed for `article` (parking offences dominate, points only for few articles). Not confirmed for `expense`: it is not one fixed value but changes over time.

    **Findings:**

    - *Recommendation data collection:* Record the offence more precisely than by the article number (e.g. the paragraph), so that the points and the amount can be checked against the offence. Why do only 6 % of the cases of article 158 carry points?
    - Why does the expense of the same year vary (91 distinct values, and 2'860 fines sent at an expense of 0)?
    - *Improvement of the process:* In 2013 the notification adds 39 % to a standard fine. Offenders who pay before the fine is sent avoid this cost, and the police saves the postage. Making early payment easier, or notifying electronically, could reduce both the expenses and the number of open cases.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Session 3

    ## Task 3.1

    ### Task 3.1 - Definition of the outcomes

    From the point of view of the police a fine can end in three ways. We define one Boolean indicator per outcome:

    | Outcome | Business meaning | Definition in the log |
    |---|---|---|
    | `paid` | The offender has paid everything that is due. | The case contains a *Payment*, and the outstanding amount after the last event is 0 or less (Task 2.5, Part 2). |
    | `credit_collection` | The fine was not paid and is handed over to a collection agency. | The case contains *Send for Credit Collection*. |
    | `dismissed` | The fine is cancelled after an appeal. | An event of the case has the `dismissal` value `#` (prefecture) or `G` (judge). |

    We deliberately do not define `paid` as "the case contains a *Payment*". Task 2.5 showed that 16'642 payments leave an amount outstanding, and a fine that is only partly paid is not settled from a business point of view. For `dismissed` we only use the two documented codes.

    ### Task 3.1 - Hypothesis

    From Task 2.5 (Part 2) we expect about 40 % of the cases to be `paid` (60'290 cases end with an outstanding amount of 0 or less) and about 39 % to end in `credit_collection` (59'013 *Send for Credit Collection* events). `dismissed` should be rare, below 2 % (2'577 cases have a dismissal value other than NIL, including the undocumented codes). That leaves roughly 20 % of the cases without any of the three outcomes, mainly the cases that end with *Send Fine* or with a *Payment* that does not cover the amount due (Task 2.5b).

    We expect the three outcomes to be almost mutually exclusive: a fine that is sent for credit collection is by definition unpaid, and a dismissed fine does not have to be paid. Small overlaps are possible, e.g. a payment that is registered around the hand-over to the collection agency.
    """)
    return


@app.cell
def _(ACTIVITY, CASE_ID, case_log_t6, event_log_t5):
    _cases = event_log_t5.groupby(CASE_ID)

    case_log_s3 = case_log_t6.copy()
    # the sequence of activities of the case (its sequential variant)
    case_log_s3['seq_variant'] = _cases[ACTIVITY].agg(tuple)
    # the outstanding amount after the last event of the case (Task 2.5, Part 2)
    case_log_s3['final_outstanding_amount'] = _cases['outstanding_amount'].last()

    # outcome 1: the offender has paid everything that is due
    case_log_s3['paid'] = (
        case_log_s3['seq_variant'].apply(lambda x: 'Payment' in x)
        & (case_log_s3['final_outstanding_amount'] <= 0)
    )
    # outcome 2: the unpaid fine is handed over to a collection agency
    case_log_s3['credit_collection'] = case_log_s3['seq_variant'].apply(lambda x: 'Send for Credit Collection' in x)
    # outcome 3: the fine is dismissed by the prefecture (#) or by the judge (G)
    _dismissed_cases = event_log_t5.loc[event_log_t5['dismissal'].isin(['#', 'G']), CASE_ID].unique()
    case_log_s3['dismissed'] = case_log_s3.index.isin(_dismissed_cases)

    OUTCOMES = ['paid', 'credit_collection', 'dismissed']
    case_log_s3[['seq_variant', 'final_outstanding_amount'] + OUTCOMES].head(10)
    return OUTCOMES, case_log_s3


@app.cell
def _(OUTCOMES, case_log_s3, mo, pd):
    _indicators = case_log_s3[OUTCOMES]

    _single = pd.DataFrame({
        'cases': _indicators.sum(),
        'share %': (100 * _indicators.mean()).round(2),
    })
    _pairs = pd.DataFrame([
        {'outcome 1': _a, 'outcome 2': _b, 'cases with both': int((_indicators[_a] & _indicators[_b]).sum())}
        for _i, _a in enumerate(OUTCOMES) for _b in OUTCOMES[_i + 1:]
    ])
    _number_of_outcomes = _indicators.sum(axis=1)

    mo.vstack([
        mo.md("Cases per outcome:"),
        _single,
        mo.md("Cases per combination of two outcomes:"),
        _pairs,
        mo.md(f"""
    - Cases with exactly one outcome: **{num((_number_of_outcomes == 1).sum())}** ({(_number_of_outcomes == 1).mean():.2%})
    - Cases with more than one outcome: **{num((_number_of_outcomes > 1).sum())}**, of which with all three: **{num((_number_of_outcomes == 3).sum())}**
    - Cases with **no outcome**: **{num((_number_of_outcomes == 0).sum())}** ({(_number_of_outcomes == 0).mean():.2%})
    """),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 3.1a - Result

    | Outcome | Cases | Share |
    |---|---|---|
    | `paid` | 60'287 | 40.09 % |
    | `credit_collection` | 59'013 | 39.25 % |
    | `dismissed` | 2'073 | 1.38 % |
    | no outcome | 29'000 | 19.29 % |

    Combinations of two outcomes: `paid` and `credit_collection` 2 cases, `paid` and `dismissed` 1 case, `credit_collection` and `dismissed` 0 cases. No case has all three outcomes. 121'367 cases (80.71 %) have exactly one outcome.

    The hypothesis is confirmed: the shares are close to the expected 40 %, 39 %, below 2 % and about 20 %. The outcomes are almost perfectly mutually exclusive, only 3 of 150'370 cases have two of them.
    """)
    return


@app.cell
def _(ACTIVITY, OUTCOMES, case_log_s3, event_log_t5, mo, pd, show_case):
    _cols = [ACTIVITY, 'amount', 'expense', 'paymentAmount', 'dismissal', 'outstanding_amount']
    _one_outcome = case_log_s3[OUTCOMES].sum(axis=1) == 1

    # the most frequent sequence of activities per outcome, to pick a typical case for each
    _rows = []
    for _o in OUTCOMES:
        _variants = case_log_s3.loc[case_log_s3[_o] & _one_outcome, 'seq_variant'].value_counts()
        _rows.append({
            'outcome': _o,
            'cases': int(case_log_s3[_o].sum()),
            'most frequent variant': ' > '.join(_variants.index[0]),
            'cases with this variant': int(_variants.iloc[0]),
        })

    _has = lambda activity: case_log_s3['seq_variant'].apply(lambda x: activity in x)
    _dismissed = case_log_s3['dismissed']

    mo.vstack([
        pd.DataFrame(_rows),
        mo.md(f"""
    - `paid` cases without a *Send Fine* event (paid before the fine was sent): **{num((case_log_s3['paid'] & ~_has('Send Fine')).sum())}**
    - `credit_collection` cases with at least one *Payment*: **{num((case_log_s3['credit_collection'] & _has('Payment')).sum())}**
    - `dismissed` cases with an *Add penalty* event: **{num((_dismissed & _has('Add penalty')).sum())}** of {num(_dismissed.sum())}
    - `dismissed` cases with a *Receive Result Appeal from Prefecture* event: **{num((_dismissed & _has('Receive Result Appeal from Prefecture')).sum())}** of {num(_dismissed.sum())}
    """),
        mo.md("**Outcome `paid`: case A10005**"),
        show_case(event_log_t5, 'A10005', _cols),
        mo.md("**Outcome `credit_collection`: case A100**"),
        show_case(event_log_t5, 'A100', _cols),
        mo.md("**Outcome `dismissed`: case A10001**"),
        show_case(event_log_t5, 'A10001', _cols),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 3.1b - Result

    For each outcome we inspect a case with the most frequent sequence of activities of that outcome.

    **`paid`, case A10005.** A fine of 36 is created on 20.03.2007 and paid in full one day later. There is no *Send Fine*, so no expenses arise, and no penalty. This is the typical paid case: 46'315 of the 60'287 paid cases consist of only *Create Fine* and *Payment*, and 46'327 paid cases were paid before the fine was sent. The process works best when the offender pays immediately.

    **`credit_collection`, case A100.** A fine of 35 is created on 02.08.2006 and sent more than four months later (expenses of 11). The notification is registered on 15.01.2007. Exactly 60 days later the penalty is added, and 82.50 are outstanding (71.50 + 11). Nothing is ever paid, and on 30.03.2009, two years after the penalty, the case is sent for credit collection. This is by far the most frequent path to credit collection (56'482 of 59'013 cases): the offender does not react at all.

    **`dismissed`, case A10001.** A fine of 36 is sent with expenses of 13 and notified on 25.07.2007. Eight days later the offender appeals to the prefecture (*Insert Date Appeal to Prefecture*). On 23.09.2007, exactly 60 days after the notification, the penalty is added although the appeal is pending. One day later the appeal is sent to the prefecture, and this event carries the dismissal value `#`. The case ends there. 87 are formally outstanding but no longer owed.

    **Findings:**

    - In the dismissed cases the penalty is almost always added (1'993 of 2'073 cases), apparently automatically 60 days after the notification and regardless of a pending appeal. *Improvement of the process:* suspend the penalty while an appeal is pending.
    - The dismissal by the prefecture is recorded on the *Send Appeal to Prefecture* event, and only 84 of the 2'073 dismissed cases contain a *Receive Result Appeal from Prefecture* event. So the log does not show when the decision was taken. Either the attribute was updated afterwards, or the appeal is deemed accepted without an explicit result. *Recommendation data collection:* record the decision as an event of its own with its date.
    """)
    return


@app.cell
def _(ACTIVITY, OUTCOMES, case_log_s3, event_log_t5, mo, show_case):
    _cols = [ACTIVITY, 'amount', 'expense', 'paymentAmount', 'dismissal', 'outstanding_amount']
    _several = case_log_s3[case_log_s3[OUTCOMES].sum(axis=1) > 1]

    mo.vstack([
        mo.md(f"Cases with more than one outcome: **{len(_several)}**"),
        _several[OUTCOMES + ['final_outstanding_amount', 'seq_variant']],
        mo.md("**`paid` and `credit_collection`: case N35881**"),
        show_case(event_log_t5, 'N35881', _cols),
        mo.md("**`paid` and `dismissed`: case S188064**"),
        show_case(event_log_t5, 'S188064', _cols),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 3.1c - Result

    Three cases have two outcomes: N35881 and S66168 (`paid` and `credit_collection`) and S188064 (`paid` and `dismissed`).

    **Case N35881 (`paid` and `credit_collection`).** The offender appeals to the prefecture against a fine of 32.80. The result is received and the dismissal value stays NIL, so the appeal was apparently rejected. The penalty is added and 79.03 are due (65.60 + 13.43 expenses). On 09.05.2002 the offender pays 79.30, slightly more than the amount due. Nevertheless the case is sent for credit collection on 10.01.2004, **20 months after it was paid in full**. The second case, S66168, has the same sequence of activities and is sent for credit collection on the same day, 10.01.2004. This looks like a batch run that did not take the payments into account. From the point of view of the offender this is a serious error: a debt that was paid is handed over to a collection agency.

    **Case S188064 (`paid` and `dismissed`).** The offender appeals to the prefecture against a fine of 80. The *Send Appeal to Prefecture* event of 22.01.2013 carries the dismissal value `#`. Five days later the penalty is added anyway (174 due), and the offender pays 95 and then 79, i.e. the full amount including the penalty. Either the dismissal value is wrong, or the offender paid a fine that had been dismissed and should get the money back.

    **Findings:**

    - Both combinations are contradictions and not legitimate double outcomes. They are rare (3 cases), but each of them is a potential complaint. *Improvement of the process:* check the outstanding amount and the dismissal status before a case is sent for credit collection and before a payment is accepted.
    - Both cases with `paid` and `credit_collection` went through a rejected appeal. Is the hand-over to credit collection triggered differently after an appeal?
    """)
    return


@app.cell
def _(ACTIVITY, OUTCOMES, case_log_s3, event_log_t5, mo, pd, show_case):
    _cols = [ACTIVITY, 'amount', 'expense', 'paymentAmount', 'dismissal', 'outstanding_amount']
    _none = case_log_s3[~case_log_s3[OUTCOMES].any(axis=1)]

    _last_activity = _none['seq_variant'].apply(lambda x: x[-1]).value_counts().rename('cases without outcome')
    _variants = _none['seq_variant'].apply(' > '.join).value_counts().head(5).rename('cases without outcome')

    _year = case_log_s3['start_time'].dt.tz_convert('Europe/Rome').dt.year.rename('year of Create Fine')
    _per_year = pd.DataFrame({
        'cases': case_log_s3.groupby(_year).size(),
        'cases without outcome': _none.groupby(_year.reindex(_none.index)).size(),
    })
    _per_year['share %'] = (100 * _per_year['cases without outcome'] / _per_year['cases']).round(1)

    _only_sent = _none['seq_variant'].apply(lambda x: x == ('Create Fine', 'Send Fine'))
    _with_payment = _none['seq_variant'].apply(lambda x: 'Payment' in x)

    mo.vstack([
        mo.md(f"""
    - Cases without outcome: **{num(len(_none))}** ({len(_none) / len(case_log_s3):.2%} of all cases)
    - of which with the variant *Create Fine > Send Fine*: **{num(_only_sent.sum())}** ({_only_sent.sum() / len(case_log_s3):.1%} of all cases)
    - of which with at least one *Payment*: **{num(_with_payment.sum())}**, with a median outstanding amount of **{_none.loc[_with_payment, 'final_outstanding_amount'].median():g}**
    """),
        mo.md("Last activity of the cases without outcome:"),
        _last_activity,
        mo.md("The five most frequent variants without outcome:"),
        _variants,
        mo.md("Cases without outcome per year:"),
        _per_year,
        mo.md("**No outcome, case A1** (variant *Create Fine > Send Fine*)"),
        show_case(event_log_t5, 'A1', _cols),
        mo.md("**No outcome, case A10798** (payments that do not cover the amount due)"),
        show_case(event_log_t5, 'A10798', _cols),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 3.1d - Result

    29'000 cases (19.29 %) have none of the three outcomes. They fall into three groups, and we inspect a case of the two large ones.

    **Group 1: the fine is sent and then nothing happens (20'731 cases end with *Send Fine*).** Case A1: a fine of 35 is created on 24.07.2006 and sent on 05.12.2006 with expenses of 11. No notification is registered, no penalty is added, nothing is paid, and the case is not sent for credit collection, although the log continues for another six and a half years. 20'385 cases, 13.6 % of all cases, consist of exactly these two events. Without a registered notification the 60 days until the penalty apparently never start, so the case is stuck. Possible reasons are that the fine could not be delivered, or that the notification was never entered.

    **Group 2: the offender pays, but not enough (6'938 cases end with a *Payment*).** Case A10798: 35 are due (fine 22 + expenses 13). The offender pays 22 within the 60 days and the remaining 13 on 20.10.2007, i.e. 35 in total. But the second payment comes ten days after the penalty was added on 10.10.2007, so 22 remain outstanding. Nothing happens afterwards. The offender has paid the original amount but not the penalty, and the police does not pursue the rest. Across all cases without outcome that contain a payment, the median outstanding amount is 35.17, roughly one standard fine.

    **Group 3: appeals without a visible end (1'331 cases).** These cases end with an appeal activity, most of them with *Send Appeal to Prefecture* (1'175), and have neither of the dismissal values `#` and `G`. The appeal is either still open or was rejected without any follow-up.

    **Is "no outcome" just "not finished yet"?** Only partly. For fines created in 2013, 64.4 % have no outcome, because the log ends in June 2013. But in every earlier year 13 % to 25 % of the cases have no outcome, also for fines that are more than ten years old. Most of these cases are therefore not still running. They are leakage: the process stops without a result.

    **Findings:**

    - About one in five fines is neither paid nor collected nor dismissed. The largest single cause is the missing notification after *Send Fine*. *Improvement of the process:* monitor fines that have been sent but not notified, and define what happens to them (send again, or close them explicitly).
    - Partial payers are apparently not sent for credit collection, while offenders who pay nothing are. Is this intended, e.g. because the remaining amount is small?
    - *Recommendation data collection:* record an explicit closing event with the reason (paid, dismissed, handed over, written off, undeliverable). Then every case has an outcome, and open cases can be told apart from abandoned ones.
    - The outcome `paid` depends on our definition of the amount due. With the simpler definition "the case contains a *Payment*" the cases of group 2 would count as paid.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Session 4

    ## Task 4.1

    ### Task 4.1 - Hypothesis

    The sequential variant of each case is already in the case log (`seq_variant`, Session 3). From Session 3 we know three very frequent variants: *Create Fine > Send Fine > Insert Fine Notification > Add penalty > Send for Credit Collection* (56'482 cases), *Create Fine > Payment* (46'315 paid cases) and *Create Fine > Send Fine* (20'385 cases). Together they are about 82 % of all cases, so we expect that **three variants are enough to cover 80 %** and that a long tail of rare variants follows.

    For the fine object sub-log we expect the number of variants to drop strongly, to less than half. The five appeal activities that are filtered out are rare, but they can occur at different positions and therefore create many variants.
    """)
    return


@app.cell
def _(case_log_s3, mo, pd):
    _variants = case_log_s3['seq_variant'].value_counts()
    variant_table = pd.DataFrame({
        'variant': [' > '.join(_v) for _v in _variants.index],
        'cases': _variants.values,
        'share %': (100 * _variants.values / len(case_log_s3)).round(2),
        'cumulative share %': (100 * _variants.values.cumsum() / len(case_log_s3)).round(2),
    })
    variant_table.index = pd.RangeIndex(1, len(variant_table) + 1, name='rank')

    # the smallest number of variants whose cumulative share reaches 80 %
    _needed = int((variant_table['cumulative share %'] < 80).sum()) + 1

    mo.vstack([
        mo.md(f"""
    - Sequential variants in the log: **{len(variant_table)}** for {num(len(case_log_s3))} cases
    - Variants needed to cover 80 % of the cases: **{_needed}** (they cover {variant_table['cumulative share %'].iloc[_needed - 1]} %)
    - Variants that occur in only one case: **{(variant_table['cases'] == 1).sum()}**
    """),
        variant_table.head(10),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 4.1a - Result

    The log has 231 sequential variants for 150'370 cases. **Three variants are enough to cover 80 % of the cases** (together 81.96 %). At the other end, 100 of the 231 variants occur in a single case. The hypothesis is confirmed. The process is far more standardized than the Sepsis process of the lecture, which has 846 variants for 1'050 cases.

    ### Task 4.1b - Result

    1. **Create Fine > Send Fine > Insert Fine Notification > Add penalty > Send for Credit Collection** (56'482 cases, 37.56 %): the fine is sent and notified, the offender does not react, a penalty is added and the fine is handed over to credit collection.
    2. **Create Fine > Payment** (46'371 cases, 30.84 %): the offender pays directly after the fine is created, before it is even sent.
    3. **Create Fine > Send Fine** (20'385 cases, 13.56 %): the fine is sent, and nothing else is ever recorded.
    4. **Create Fine > Send Fine > Insert Fine Notification > Add penalty > Payment** (9'520 cases, 6.33 %): the offender pays only after the notification and after the penalty has been added.

    The four variants together cover 88.29 % of the cases.
    """)
    return


@app.cell
def _(ACTIVITY, CASE_ID, event_log_t5, mo, pd):
    FINE_OBJECT_ACTIVITIES = ['Create Fine', 'Send Fine', 'Insert Fine Notification', 'Add penalty',
                              'Send for Credit Collection', 'Payment']

    fine_object_log = event_log_t5[event_log_t5[ACTIVITY].isin(FINE_OBJECT_ACTIVITIES)]
    fine_object_variant = fine_object_log.groupby(CASE_ID)[ACTIVITY].agg(tuple).rename('fine_object_variant')

    _removed = event_log_t5[~event_log_t5[ACTIVITY].isin(FINE_OBJECT_ACTIVITIES)]
    _all_variants = event_log_t5.groupby(CASE_ID)[ACTIVITY].agg(tuple)

    _counts = fine_object_variant.value_counts()
    _fine_table = pd.DataFrame({
        'variant': [' > '.join(_v) for _v in _counts.index],
        'cases': _counts.values,
        'share %': (100 * _counts.values / len(fine_object_variant)).round(2),
        'cumulative share %': (100 * _counts.values.cumsum() / len(fine_object_variant)).round(2),
    })
    _fine_table.index = pd.RangeIndex(1, len(_fine_table) + 1, name='rank')

    mo.vstack([
        mo.md(f"""
    | | Full log | Fine object sub-log |
    |---|---|---|
    | Events | {num(len(event_log_t5))} | {num(len(fine_object_log))} |
    | Cases | {num(event_log_t5[CASE_ID].nunique())} | {num(fine_object_log[CASE_ID].nunique())} |
    | Sequential variants | **{_all_variants.nunique()}** | **{fine_object_variant.nunique()}** |
    | Variants needed for 80 % of the cases | {int(((_all_variants.value_counts().cumsum() / len(_all_variants)) < 0.8).sum()) + 1} | {int((_fine_table['cumulative share %'] < 80).sum()) + 1} |

    - Events removed by the filter: **{num(len(_removed))}**, in **{num(_removed[CASE_ID].nunique())}** cases
    - Variants of the full log that contain at least one of the removed activities: **{_all_variants[_all_variants.apply(lambda x: any(_a not in FINE_OBJECT_ACTIVITIES for _a in x))].nunique()}**
    """),
        mo.md("Removed events per activity:"),
        _removed[ACTIVITY].value_counts(),
        mo.md("The ten most frequent variants of the fine object:"),
        _fine_table.head(10),
    ])
    return FINE_OBJECT_ACTIVITIES, fine_object_log, fine_object_variant


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 4.1c - Result

    The filter removes the five appeal activities: 10'779 events (1.9 % of all events) in 4'567 cases (3.0 % of all cases). No case disappears, because every case contains *Create Fine*.

    The number of sequential variants drops from **231 to 48**, i.e. by 79 %. Three variants are still enough to cover 80 % of the cases. The hypothesis is confirmed: 189 of the 231 variants of the full log contain an appeal activity. So 3 % of the cases produce more than 80 % of the variants, because an appeal can start at different points of the process and has several steps of its own. Without the appeals the behaviour of the fine itself becomes visible.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Task 4.2

    ### Task 4.2 - Process map and hypothesis

    We inspect the process map of the fine object sub-log in Disco. The log is imported into Disco, an attribute filter on the activity (mode "Keep selected") keeps only the six activities of the fine object, and the map is shown with absolute frequency and with both sliders (activities and paths) at 100 %. The numbers on the arrows count how often one activity is directly followed by another in the same case.

    **Hypothesis.** We expect one main path *Create Fine > Send Fine > Insert Fine Notification > Add penalty > Send for Credit Collection*, and a *Payment* that can leave this path after every step. We expect that a payment ends the case, that every fine that is sent is also notified, and that a penalty is only added to fines on which nothing was paid.
    """)
    return


@app.cell
def _(ACTIVITY, CASE_ID, fine_object_log, mo, pd):
    # the process map is inspected in Disco; the screenshot lies next to this notebook
    _screenshot = mo.notebook_dir() / 'disco_process_map.png'

    # cross-check of the numbers in the map: the same directly-follows frequencies computed in Python
    _next = fine_object_log.groupby(CASE_ID)[ACTIVITY].shift(-1).fillna('END')

    mo.vstack([
        mo.image(src=str(_screenshot)) if _screenshot.exists()
        else mo.md("**The screenshot `disco_process_map.png` is not there yet.** Export the process map of the fine object "
                   "from Disco (absolute frequency, both sliders at 100 %) and save it under this name in the folder of this notebook."),
        mo.md("Cross-check in Python: directly-follows frequencies of the fine object sub-log (rows: activity, columns: next activity):"),
        pd.crosstab(fine_object_log[ACTIVITY].rename('activity'), _next.rename('next activity')),
    ])
    return


@app.cell
def _(ACTIVITY, CASE_ID, fine_object_log, fine_object_variant, mo):
    _log = fine_object_log.copy()
    _log['previous_activity'] = _log.groupby(CASE_ID)[ACTIVITY].shift(1)
    _log['next_activity'] = _log.groupby(CASE_ID)[ACTIVITY].shift(-1)
    _log['outstanding_before'] = _log.groupby(CASE_ID)['outstanding_amount'].shift(1)

    _has = lambda activity: fine_object_variant.apply(lambda x: activity in x)
    _notified, _penalised = _has('Insert Fine Notification'), _has('Add penalty')

    _penalty_after_payment = _log[(_log[ACTIVITY] == 'Add penalty') & (_log['previous_activity'] == 'Payment')]
    _payment_after_notification = _log[(_log[ACTIVITY] == 'Payment') & (_log['previous_activity'] == 'Insert Fine Notification')]

    mo.vstack([
        mo.md(f"""
    **Send Fine**

    - Cases that end with *Send Fine*: **{num(((_log[ACTIVITY] == 'Send Fine') & _log['next_activity'].isna()).sum())}** of {num((_log[ACTIVITY] == 'Send Fine').sum())} fines that were sent

    **Insert Fine Notification and Add penalty**

    - Cases with *Insert Fine Notification*: **{num(_notified.sum())}**, cases with *Add penalty*: **{num(_penalised.sum())}**
    - Cases with a notification but without a penalty: **{num((_notified & ~_penalised).sum())}**, with a penalty but without a notification: **{num((~_notified & _penalised).sum())}**
    - *Payment* directly after *Insert Fine Notification*: **{num(len(_payment_after_notification))}**, of which **{num((_payment_after_notification['outstanding_amount'] <= 0).sum())}** settle the amount due
    - *Add penalty* directly after a *Payment*: **{num(len(_penalty_after_payment))}** cases, of which **{num((_penalty_after_payment['outstanding_before'] <= 0).sum())}** had nothing outstanding before the penalty
    """),
        mo.md("Most frequent outstanding amounts directly before a penalty that follows a payment:"),
        _penalty_after_payment['outstanding_before'].value_counts().head(5).rename('cases'),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 4.2a - Result

    The main path of the hypothesis is clearly visible (thick arrows), and all cases start with *Create Fine*. But three things are unexpected and should be investigated:

    1. **One in five fines that are sent ends right there.** 20'897 of the 103'987 *Send Fine* events are the last event of their case. We expected every fine that is sent to be notified. Without a notification there is no penalty and no credit collection, so these fines are lost (see Task 3.1d).
    2. **Notification and penalty always come together.** *Insert Fine Notification* and *Add penalty* occur in exactly the same 79'860 cases. There is not a single fine that is notified and then paid without a penalty. A *Payment* directly after the notification occurs 3'902 times, but only 35 of these payments settle the amount due, and all 3'902 are followed by a penalty. We expected many offenders to pay within the 60 days after the notification. Is *Insert Fine Notification* perhaps only entered for fines that are still unpaid when the penalty is due?
    3. **A penalty is added after a payment (3'902 cases).** In 3'866 of these cases something was still outstanding, but typically only a few euros (the most frequent amounts are 3.25, 5.16, 5.60 and 4.96): the offender paid the fine but not all of the expenses. This small rest triggers a penalty that roughly doubles the fine. In 36 cases nothing was outstanding and the penalty was added anyway.

    **Hypothesis.** The main path is confirmed. Our three other expectations are not: a payment does not always end the case (in the map *Payment* has arrows to every activity except *Create Fine*), not every fine that is sent is notified, and penalties are also added to fines on which something was paid.
    """)
    return


@app.cell
def _(
    ACTIVITY,
    CASE_ID,
    TIMESTAMP,
    case_log_s3,
    event_log_t5,
    fine_object_variant,
    mo,
    pd,
    show_case,
):
    # "follower filter": cases in which a Payment is directly followed by Send Fine
    def _directly_follows(variant, first, second):
        return any(_a == first and _b == second for _a, _b in zip(variant, variant[1:]))

    _selected = fine_object_variant[fine_object_variant.apply(_directly_follows, first='Payment', second='Send Fine')]
    _counts = _selected.value_counts()
    _variant_table = pd.DataFrame({
        'variant': [' > '.join(_v) for _v in _counts.index],
        'cases': _counts.values,
    })

    # the cases of the most frequent of these variants
    _variant = ('Create Fine', 'Payment', 'Send Fine')
    _cases = _selected[_selected.apply(lambda x: x == _variant)].index
    _case_log = case_log_s3.loc[_cases]
    _events = event_log_t5[event_log_t5[CASE_ID].isin(_cases)]
    _payment = _events[_events[ACTIVITY] == 'Payment'].set_index(CASE_ID)
    _sent = _events[_events[ACTIVITY] == 'Send Fine'].set_index(CASE_ID)
    _paid = _payment['paymentAmount'].reindex(_cases)
    _days = (_sent[TIMESTAMP] - _payment[TIMESTAMP]).dt.days

    mo.vstack([
        mo.md(f"Cases in which a *Payment* is directly followed by *Send Fine*: **{num(len(_selected))}**, in **{len(_counts)}** variants"),
        _variant_table.head(5),
        mo.md(f"""
    **Variant *Create Fine > Payment > Send Fine*: {num(len(_cases))} cases**

    - payment equal to the fine amount: **{num((_paid == _case_log['initial_amount']).sum())}**, higher: **{num((_paid > _case_log['initial_amount']).sum())}**, lower: **{num((_paid < _case_log['initial_amount']).sum())}**
    - days between the payment and *Send Fine*: median **{_days.median():g}**, maximum {_days.max():g}
    - outcome of these cases in Session 3: {num(case_log_s3.loc[_cases, 'paid'].sum())} `paid`, {num((~case_log_s3.loc[_cases, ['paid', 'credit_collection', 'dismissed']].any(axis=1)).sum())} without outcome
    """),
        mo.md("**Case A127**"),
        show_case(event_log_t5, 'A127', [ACTIVITY, 'amount', 'expense', 'paymentAmount', 'outstanding_amount']),
    ])
    return


@app.cell
def _(mo):
    _screenshot = mo.notebook_dir() / 'disco_follower_filter.png'

    mo.image(src=str(_screenshot)) if _screenshot.exists() else mo.md(
        "**The screenshot `disco_follower_filter.png` is not there yet.** Save a screenshot of the Disco variants view "
        "after the Follower filter (*Payment* directly followed by *Send Fine*) under this name in the folder of this notebook.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 4.2b - Result

    In Disco we add a **Follower filter** to the fine object sub-log: *Payment* directly followed by *Send Fine*. The Python cell above applies the same filter and gives the exact numbers. The filter selects 569 cases in 10 variants. The most frequent one is

    **Create Fine > Payment > Send Fine** (362 cases).

    It is unexpected because the fine is sent after it has been paid, and because the case then ends with *Send Fine*.

    ### Task 4.2c - Result

    **Case A127.** A fine of 35 is created on 02.08.2006 and paid in full two days later. Nothing is outstanding. Four months later, on 12.12.2006, the fine is sent anyway. This adds expenses of 11, which are never paid, and the case ends with 11 outstanding.

    The case is typical for the variant: in 312 of the 362 cases the payment is exactly the fine amount, and the fine is sent a median of 36 days after the payment.

    **Possible explanations.** Either the step *Send Fine* does not check whether the fine has been paid, or the payment was entered into the system only after the fine had been sent, with the date of the payment as timestamp. The log cannot tell these two apart, because it has no separate timestamp for the registration of a payment.

    **Findings:**

    - The offender did everything right and still receives a notification and is charged its cost. *Improvement of the process:* check for payments immediately before sending, and do not charge expenses for a fine that was paid before it was sent.
    - This also affects our outcome analysis: because of the unpaid expenses, 343 of the 362 cases have no outcome in Session 3, although the fine itself was paid. The share of `paid` cases is therefore slightly underestimated.
    - *Recommendation data collection:* record when a payment was received and when it was registered.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Task 4.3

    ### Task 4.3 - Model of the fine object

    Our current understanding of how the fine object **should** behave:

    1. A fine is created.
    2. The offender can pay at every stage. A payment, possibly in several instalments, ends the case.
    3. As long as the fine is not paid, the police takes the next step: send the fine, register the notification, add the penalty and finally send the fine for credit collection, which also ends the case.

    As a workflow graph, with XOR gateways only:

    | From | To |
    |---|---|
    | Start event | *Create Fine* |
    | *Create Fine* | gateway G1 (split) |
    | G1 | *Send Fine*, or gateway J (join in front of *Payment*) |
    | *Send Fine* | gateway G2 (split) |
    | G2 | *Insert Fine Notification*, or J |
    | *Insert Fine Notification* | gateway G3 (split) |
    | G3 | *Add penalty*, or J |
    | *Add penalty* | gateway G4 (split) |
    | G4 | *Send for Credit Collection*, or J |
    | J | *Payment* |
    | *Payment* | gateway G5 (split) |
    | G5 | gateway E (join in front of the end event), or back to J for a further payment |
    | *Send for Credit Collection* | E |
    | E | End event |

    The model allows exactly these sequences, where *Payment* can be repeated: *Create Fine > Payment*, *Create Fine > Send Fine > Payment*, *Create Fine > Send Fine > Insert Fine Notification > Payment*, *Create Fine > Send Fine > Insert Fine Notification > Add penalty > Payment* and *Create Fine > Send Fine > Insert Fine Notification > Add penalty > Send for Credit Collection*.

    **Soundness.** The graph has one start event and one end event, every node lies on a path from the start to the end, and all seven gateways are XOR gateways. An XOR split passes the token to exactly one branch, so there is always exactly one token. Without AND gateways there can be no deadlock (no AND join waits for a second token) and no lack of synchronization (no flow ever carries two tokens). The loop at *Payment* can always be left through G5. The model is therefore sound.

    The next cell compares this model with the log. The cell after it checks the BPMN file that we created with bpmn.io.
    """)
    return


@app.cell
def _(fine_object_variant, mo, pd):
    import re as _re

    # one letter per activity, so that the sequences of the model can be written as a regular expression
    _letter = {'Create Fine': 'C', 'Send Fine': 'S', 'Insert Fine Notification': 'N',
               'Add penalty': 'A', 'Payment': 'P', 'Send for Credit Collection': 'K'}
    # C, then: payment(s) | S payment(s) | S N payment(s) | S N A payment(s) | S N A K
    _model = _re.compile(r'C(P+|S(P+|N(P+|A(P+|K))))')

    _encoded = fine_object_variant.apply(lambda x: ''.join(_letter[_a] for _a in x))
    fits_model = _encoded.apply(lambda x: _model.fullmatch(x) is not None).rename('fits_model')

    _not_fitting = fine_object_variant[~fits_model].value_counts()

    mo.vstack([
        mo.md(f"""
    - Cases whose sequence of fine object activities is allowed by the model: **{num(fits_model.sum())}** of {num(len(fits_model))} ({fits_model.mean():.2%})
    - Variants of the fine object that are allowed by the model: **{fine_object_variant[fits_model].nunique()}** of {fine_object_variant.nunique()}
    """),
        mo.md("The most frequent variants that the model does not allow:"),
        pd.DataFrame({'variant': [' > '.join(_v) for _v in _not_fitting.index], 'cases': _not_fitting.values}).head(8),
    ])
    return


@app.cell
def _(FINE_OBJECT_ACTIVITIES, fine_object_variant, mo, pm4py):
    import warnings as _warnings
    from pm4py.objects.bpmn.obj import BPMN as _BPMN
    from pm4py.objects.log.obj import Event as _Event, Trace as _Trace

    _bpmn_file = mo.notebook_dir() / 'fine_object.bpmn'
    _svg_file = mo.notebook_dir() / 'fine_object.svg'

    if not _bpmn_file.exists():
        _output = mo.md("**The file `fine_object.bpmn` is not there yet.** Save the model from bpmn.io as `fine_object.bpmn` "
                        "and its picture as `fine_object.svg` in the folder of this notebook, then run this cell again.")
    else:
        _bpmn = pm4py.read_bpmn(str(_bpmn_file))
        _tasks = sorted(_n.get_name() for _n in _bpmn.get_nodes() if isinstance(_n, _BPMN.Task))
        _gateways = [_n for _n in _bpmn.get_nodes() if isinstance(_n, _BPMN.Gateway)]
        _other_gateways = [_n for _n in _gateways if not isinstance(_n, (_BPMN.ExclusiveGateway, _BPMN.ParallelGateway))]
        _starts = [_n for _n in _bpmn.get_nodes() if isinstance(_n, _BPMN.StartEvent)]
        _ends = [_n for _n in _bpmn.get_nodes() if isinstance(_n, _BPMN.EndEvent)]

        _counts = fine_object_variant.value_counts()
        with _warnings.catch_warnings():
            _warnings.simplefilter('ignore')  # pm4py marks these two helper functions as deprecated

            # soundness is checked on the Petri net that corresponds to the BPMN model
            _net, _initial, _final = pm4py.convert_to_petri_net(_bpmn)
            _sound = pm4py.check_soundness(_net, _initial, _final)
            _sound = _sound[0] if isinstance(_sound, tuple) else _sound

            # which variants of the fine object can be replayed on the model?
            _fitting_cases = sum(
                _count for _variant, _count in _counts.items()
                if pm4py.check_is_fitting(_Trace([_Event({'concept:name': _a}) for _a in _variant]), _net, _initial, _final)
            )

        _output = mo.vstack([
            mo.md(f"""
    **Checks of `{_bpmn_file.name}`**

    - Tasks in the model: {', '.join(_tasks)}
    - Activities of the fine object that are missing in the model: **{sorted(set(FINE_OBJECT_ACTIVITIES) - set(_tasks)) or 'none'}**
    - Tasks in the model that are not activities of the fine object: **{sorted(set(_tasks) - set(FINE_OBJECT_ACTIVITIES)) or 'none'}**
    - Start events: **{len(_starts)}**, end events: **{len(_ends)}**
    - Gateways: **{len(_gateways)}**, of which neither XOR nor AND: **{len(_other_gateways)}**
    - Sound: **{_sound}**
    - Cases whose sequence of fine object activities can be replayed on the model: **{num(_fitting_cases)}** of {num(int(_counts.sum()))} ({_fitting_cases / _counts.sum():.2%})
    """),
            mo.image(src=str(_svg_file)) if _svg_file.exists() else mo.md("The picture `fine_object.svg` is not there yet."),
        ])

    _output
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 4.3 - Result

    The BPMN model is stored as `fine_object.bpmn` and as picture `fine_object.svg` in the folder of the notebook. It was created with bpmn.io from the template and contains all six activities of the fine object. The cell above confirms that it is a workflow graph (one start event, one end event, only XOR gateways) and that it is sound.

    **Model and log.** 120'535 of the 150'370 cases (80.16 %) follow the model, in 17 of the 48 variants of the fine object. The model describes how the fine should behave, so the remaining 20 % are deviations and not errors of the model:

    - *Create Fine > Send Fine* (20'534 cases): the case stops after the fine was sent. In the model a fine that is sent must be paid or notified.
    - A penalty after a payment (3'305 cases with *... Insert Fine Notification > Payment > Add penalty > Payment*): in the model a payment ends the case.
    - *... Add penalty* as last activity (3'234 cases): in the model a penalty must be followed by a payment or by credit collection.
    - *Send for Credit Collection* after a payment (1'523 and 522 cases) and *Send Fine* after a payment (362 cases).

    **Decisions we took for the model:**

    - *Payment* is a single task with a loop, so that payments in instalments are allowed at every stage.
    - A payment is allowed between *Insert Fine Notification* and *Add penalty* without a penalty, because an offender who pays within the deadline should not be penalised. In the log this almost never happens (Task 4.2a).
    - We use no AND gateway. From the point of view of the fine the activities are strictly ordered, and nothing happens in parallel.
    - The model is deliberately strict. It does not contain the dead ends that we see in the log, because we regard them as leakage and not as intended behaviour.
    """)
    return


if __name__ == "__main__":
    app.run()
