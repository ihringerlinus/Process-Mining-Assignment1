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


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Session 5

    ## Task 5.1

    ### Task 5.1 - Hypothesis

    We expect *Payment* to be repeated most often, because offenders pay in instalments. This is repetition, but not necessarily rework caused by an error. We expect *Create Fine* and *Add penalty* to occur only once per case, and the appeal activities to repeat rarely.
    """)
    return


@app.cell
def _(ACTIVITY, CASE_ID, TIMESTAMP, event_log_t5, mo, pd):
    # how often each activity occurs in each case
    activity_counts = event_log_t5.groupby([CASE_ID, ACTIVITY]).size().rename('n').reset_index()

    _rework_summary = activity_counts.groupby(ACTIVITY).agg(
        cases=('n', 'size'),
        cases_with_rework=('n', lambda s: (s > 1).sum()),
        extra_executions=('n', lambda s: (s - 1).sum()),
        max_repetitions=('n', 'max'),
    ).sort_values(['cases_with_rework', 'cases'], ascending=False)
    _rework_summary['rework share %'] = (100 * _rework_summary['cases_with_rework'] / _rework_summary['cases']).round(2)

    _rework_rows = activity_counts[activity_counts['n'] > 1]
    _n_cases = event_log_t5[CASE_ID].nunique()
    _n_rework = _rework_rows[CASE_ID].nunique()
    _n_extra = _rework_summary['extra_executions'].sum()

    # are the repetitions direct (A, A) or do other activities lie between them (A, B, A)?
    _previous = event_log_t5.groupby(CASE_ID)[ACTIVITY].shift()
    _direct = (_previous == event_log_t5[ACTIVITY]).sum()

    # several payments of one case on the same day: same amount (double booking?) or different amounts?
    _payments = event_log_t5[event_log_t5[ACTIVITY] == 'Payment']
    _same_day = _payments[_payments.duplicated([CASE_ID, TIMESTAMP], keep=False)]
    _same_day_groups = _same_day.groupby([CASE_ID, TIMESTAMP])['paymentAmount'].nunique()

    mo.vstack([
        _rework_summary,
        mo.md(f"""
    - Cases with rework: **{num(_n_rework)}** of {num(_n_cases)} (**{_n_rework / _n_cases:.2%}**)
    - Extra executions: **{num(_n_extra)}** of {num(len(event_log_t5))} events (**{_n_extra / len(event_log_t5):.2%}**)
    - Activities that are repeated in at least one case: **{sorted(_rework_rows[ACTIVITY].unique())}**
    - Direct repetitions (self loops): **{num(_direct)}**, repetitions with other activities in between: **{num(_n_extra - _direct)}**
    - Days on which one case has several payments: **{num(len(_same_day_groups))}**, of which with identical amounts: **{num((_same_day_groups == 1).sum())}**
    """),
        pd.crosstab(_rework_rows[ACTIVITY], _rework_rows['n']),
    ])
    return (activity_counts,)


@app.cell
def _(ACTIVITY, activity_counts, px):
    _distribution = (
        activity_counts[activity_counts[ACTIVITY] == 'Payment']['n']
        .value_counts().sort_index().rename('cases').reset_index()
    )
    _distribution['n'] = _distribution['n'].astype(str)

    _fig = px.bar(
        _distribution, x='n', y='cases', text='cases', log_y=True, width=700,
        title='Number of payments per case (cases with at least one payment, log scale)',
        labels={'n': 'Payment events in the case', 'cases': 'Cases'},
    )
    _fig.update_traces(textposition='outside', cliponaxis=False)
    _fig.update_layout(bargap=0.2, xaxis_type='category')
    _fig
    return


@app.cell
def _(ACTIVITY, CASE_ID, activity_counts, case_log_s3, event_log_t5, mo, pd):
    def _penalty_between_payments(variant):
        _positions = [_i for _i, _activity in enumerate(variant) if _activity == 'Payment']
        return 'Add penalty' in variant[_positions[0]:_positions[-1]]

    _short = {
        'Create Fine': 'CF', 'Send Fine': 'SF', 'Insert Fine Notification': 'IFN', 'Add penalty': 'AP',
        'Payment': 'P', 'Send for Credit Collection': 'SCC', 'Appeal to Judge': 'AJ',
        'Insert Date Appeal to Prefecture': 'IDAP', 'Send Appeal to Prefecture': 'SAP',
        'Receive Result Appeal from Prefecture': 'RRAP', 'Notify Result Appeal to Offender': 'NRAO',
    }

    # all cases with at least one payment, enriched with what we need to explain the repetitions
    payment_cases = case_log_s3[case_log_s3.index.isin(
        activity_counts.loc[activity_counts[ACTIVITY] == 'Payment', CASE_ID]
    )].copy()
    payment_cases['n_payments'] = activity_counts[activity_counts[ACTIVITY] == 'Payment'].set_index(CASE_ID)['n']
    payment_cases['penalty_between'] = payment_cases['seq_variant'].apply(_penalty_between_payments)
    _appeals = event_log_t5.loc[event_log_t5[ACTIVITY].isin(['Appeal to Judge', 'Insert Date Appeal to Prefecture']), CASE_ID].unique()
    payment_cases['appeal'] = payment_cases.index.isin(_appeals)
    payment_cases['initial_amount'] = event_log_t5.groupby(CASE_ID)['amount'].first()
    payment_cases['total_expense'] = event_log_t5.groupby(CASE_ID)['expense'].sum()
    payment_cases['total_paid'] = event_log_t5.groupby(CASE_ID)['paymentAmount'].sum().round(2)
    payment_cases['first_payment'] = event_log_t5[event_log_t5[ACTIVITY] == 'Payment'].groupby(CASE_ID)['paymentAmount'].first()
    payment_cases['variant'] = payment_cases['seq_variant'].apply(lambda v: ' > '.join(_short[_a] for _a in v))

    _bands = pd.cut(payment_cases['n_payments'], [0, 1, 2, 3, 5, 9, 99], labels=['1', '2', '3', '4-5', '6-9', '10+'])
    _by_band = payment_cases.groupby(_bands, observed=True).agg(
        cases=('n_payments', 'size'),
        median_initial_amount=('initial_amount', 'median'),
        appeal_share=('appeal', 'mean'),
        fully_paid_share=('paid', 'mean'),
    ).round(3)

    _rework = payment_cases[payment_cases['n_payments'] > 1]
    _by_penalty = _rework.groupby('penalty_between').agg(
        cases=('paid', 'size'), fully_paid=('paid', 'sum'), fully_paid_share=('paid', 'mean'),
    ).round(3)

    # the two dominating variants of the repetitions
    _a = _rework[_rework['variant'] == 'CF > SF > IFN > AP > P > P']
    _b = _rework[_rework['variant'] == 'CF > SF > IFN > P > AP > P']
    _a_first_is_due = (_a['first_payment'] - (_a['initial_amount'] + _a['total_expense'])).abs() < 0.01
    _b_paid_is_due = (_b['total_paid'] - (_b['initial_amount'] + _b['total_expense'])).abs() <= 1

    _o = _rework['final_outstanding_amount']
    mo.vstack([
        mo.md("Cases with at least one payment, by number of payments:"),
        _by_band,
        mo.md("Cases with rework, by whether *Add penalty* lies between the first and the last payment:"),
        _by_penalty,
        mo.md("Most frequent variants of the cases with rework (CF = Create Fine, SF = Send Fine, IFN = Insert Fine Notification, AP = Add penalty, P = Payment):"),
        _rework['variant'].value_counts().head(5),
        mo.md(f"""
    - Outstanding amount at the end of the cases with rework: below 0: **{num((_o < 0).sum())}**, exactly 0: **{num((_o == 0).sum())}**, up to 1: **{num(((_o > 0) & (_o <= 1)).sum())}**, above 1: **{num((_o > 1).sum())}**
    - *CF > SF > IFN > AP > P > P*: **{num(len(_a))}** cases, fully paid: **{_a['paid'].mean():.1%}**, first payment = initial amount + expenses: **{num(_a_first_is_due.sum())}** ({_a_first_is_due.mean():.1%})
    - *CF > SF > IFN > P > AP > P*: **{num(len(_b))}** cases, fully paid: **{_b['paid'].mean():.1%}**, sum of both payments = initial amount + expenses (± 1): **{num(_b_paid_is_due.sum())}** ({_b_paid_is_due.mean():.1%})
    """),
    ])
    return (payment_cases,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 5.1a - Result

    The hypothesis is confirmed, and more clear-cut than we expected: **_Payment_ is the only activity that repeats at all**. All other activities, including the appeal activities, occur at most once per case.

    | Measure | Value |
    |---|---|
    | Cases with rework | 7'542 of 150'370 (5.02 %), or 10.82 % of the 69'715 cases with a payment |
    | Extra executions | 7'886 of 561'470 events (1.40 %) |
    | Cases with exactly 2 payments | 7'366 (97.7 % of the cases with rework) |
    | Cases with 6 or more / 10 or more payments | 27 / 9 |
    | Maximum | 15 payments (case C20817) |

    The distribution has a long tail, so few repetitions per case and many repetitions in a case are two different phenomena (see the chart and the table by number of payments above). We found three things we did not expect:

    1. **Half of the cases with rework do not end fully paid.** Only 50.7 % reach an outstanding amount of 0 or less, against 90.8 % of the cases with a single payment. Paying several times does not mean paying everything.
    2. **Two variants make up 93 % of the cases with rework, and they end very differently.** In *... Add penalty > Payment > Payment* (3'736 cases) 93.7 % are fully paid. In *... Payment > Add penalty > Payment* (3'301 cases) only 1.9 % are.
    3. **Many payments go together with high fines and appeals.** The median initial amount rises from 35 (one payment) to 656 (ten or more), and the share of cases with an appeal from 1.1 % to 77.8 %.

    *Rework* is the slides' term for any repeated activity. The payments are not rework in the sense of an error being corrected. Of the 29 days on which a case has several payments, none has two identical amounts, so we find no sign of accidental double booking on the same day.
    """)
    return


@app.cell
def _(ACTIVITY, event_log_t5, mo, show_case):
    _cols = [ACTIVITY, 'amount', 'expense', 'paymentAmount', 'cum_payment_amount', 'outstanding_amount']

    mo.vstack([
        mo.md("**A10009:** 2 payments after the penalty"),
        show_case(event_log_t5, 'A10009', _cols),
        mo.md("**A10798:** 2 payments, the penalty lies between them"),
        show_case(event_log_t5, 'A10798', _cols),
        mo.md("**A18543:** 2 payments, the first one settles everything before the penalty"),
        show_case(event_log_t5, 'A18543', _cols),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 5.1b - Cases with a small number of repetitions

    - **A10009 (2 payments, fully paid).** The offender pays 35, exactly the initial fine plus expenses (22 + 13), 10 days after the penalty was added. A month later follows 22, exactly the penalty. *Hypothesis:* The offender pays the sum named in the original notice without knowing about the penalty, and receives a reminder for the difference. This pattern is typical: in 71.7 % of the 3'736 cases of this variant the first payment equals initial amount plus expenses.
    - **A10798 (2 payments, not fully paid).** The offender pays 22 within the 60 days after the notification, i.e. the fine without the expenses. On day 60 the penalty is added, and 10 days later the offender pays the missing 13. The outstanding amount stays at 22, exactly the penalty. *Hypothesis:* The offender pays the fine and the expenses separately and considers the matter closed. The penalty is added automatically on day 60, because the debt is not yet settled on that day. In 97.5 % of the 3'301 cases of this variant the two payments add up to initial amount plus expenses (± 1), and the time from notification to penalty is exactly 60 days in every case (Task 6.2).
    - **A18543 (2 payments, overpaid by 13).** The offender pays the full 35 after 46 days, but the penalty is still added 14 days later, and four days later the offender pays another 35. *Hypothesis:* The penalty should not have been applied. It is triggered by the date, without taking the payment into account, or the payment was registered with a delay. The offender reacts to the resulting reminder and pays the same sum again, which leaves an overpayment.
    """)
    return


@app.cell
def _(ACTIVITY, event_log_t5, mo, payment_cases, show_case):
    _cols = [ACTIVITY, 'amount', 'expense', 'paymentAmount', 'cum_payment_amount', 'outstanding_amount']

    mo.vstack([
        mo.md("The cases with 10 or more payments:"),
        payment_cases.loc[
            payment_cases['n_payments'] >= 10,
            ['n_payments', 'initial_amount', 'total_paid', 'final_outstanding_amount', 'appeal', 'variant'],
        ].sort_values('n_payments', ascending=False),
        mo.md("**C20817:** 15 payments, the highest number in the log"),
        show_case(event_log_t5, 'C20817', _cols),
        mo.md("**C10852:** 10 payments"),
        show_case(event_log_t5, 'C10852', _cols),
        mo.md("**V18908:** 10 payments, then credit collection"),
        show_case(event_log_t5, 'V18908', _cols),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 5.1b - Cases with a high number of repetitions

    - **C20817 (15 payments).** After an initial fine of 779 the offender appeals to a judge, the penalty is added, and six months later 15 payments of 52 follow at roughly monthly intervals. They add up to 780, almost exactly the initial fine, and then stop. 779.50 stay outstanding, which is the penalty. *Hypothesis:* The offender cannot pay such a high fine at once and has an instalment plan based on the initial amount, possibly as a result of the appeal. In that case the penalty is not really owed, and our outstanding amount is too high. C13062, C18190 and C19108 show the same pattern.
    - **C10852 (10 payments).** Here the fine (312.97) is doubled by the penalty, and an appeal to the prefecture follows. Then come 10 payments of exactly 62.59 at roughly monthly intervals, which add up to 625.90. *Hypothesis:* This is also an instalment plan, but one calculated on the amount including the penalty: one tenth each, up to a rounding difference of 0.05.
    - **V18908 (10 payments, then credit collection).** The offender pays 10 instalments of 30, starting eight months after the penalty. Two and a half months after the last instalment the case goes to credit collection with only 25.50 outstanding. *Hypothesis:* The offender stops just before the end, perhaps assuming the debt is paid, and the case is handed over because of a date or a remaining balance, regardless of how much has already been paid.

    **Reflection.** The repetitions have two different causes: (a) offenders splitting a payment, typically into two parts around the penalty, and (b) instalment plans for high fines, often after an appeal. In (a) the repetition is at least partly created by the process itself, because the penalty is added on a fixed day and offenders then pay a second time.
    """)
    return


@app.cell
def _(ACTIVITY, CASE_ID, TIMESTAMP, case_log_s3, event_log_t5, px):
    # Calendar time in Italy without a time zone. Differences between these values are
    # exact days, also across daylight saving changes (in UTC they would be off by an hour).
    event_log_s5 = event_log_t5.copy()
    event_log_s5['local_time'] = event_log_s5[TIMESTAMP].dt.tz_convert('Europe/Rome').dt.tz_localize(None)

    _local_time = event_log_s5.groupby(CASE_ID)['local_time']
    case_log_s5 = case_log_s3.copy()
    case_log_s5['start'] = _local_time.first()
    case_log_s5['end'] = _local_time.last()
    case_log_s5['duration_days'] = (case_log_s5['end'] - case_log_s5['start']).dt.days
    case_log_s5['last_activity'] = event_log_s5.groupby(CASE_ID)[ACTIVITY].last()


    def first_time(activity):
        # time of the first occurrence of an activity in each case
        _events = event_log_s5[event_log_s5[ACTIVITY] == activity]
        return _events.groupby(CASE_ID)['local_time'].first()


    def delay_days(first, second):
        # days between the first occurrences of two activities, for cases that have both
        return (first_time(second) - first_time(first)).dropna().dt.days


    def day_chart(days, title, max_days=None, log_y=False):
        # one bar per day. Plotting counts instead of raw values keeps the notebook small.
        _counts = days.value_counts().sort_index().rename('cases').rename_axis('days').reset_index()
        if max_days is not None:
            _counts = _counts[_counts['days'].between(0, max_days)]
        _fig = px.bar(_counts, x='days', y='cases', log_y=log_y, title=title, width=800,
                      labels={'days': 'Days', 'cases': 'Cases'})
        _fig.update_traces(marker_line_width=0)
        _fig.update_layout(bargap=0)
        return _fig


    def monthly_counts(times, name='cases'):
        # number of timestamps per calendar month
        return (times.dt.to_period('M').dt.to_timestamp().value_counts().sort_index()
                .rename(name).rename_axis('month').reset_index())

    return (
        case_log_s5,
        day_chart,
        delay_days,
        event_log_s5,
        first_time,
        monthly_counts,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Task 5.2

    ### Task 5.2a - Hypothesis

    We expect arrivals to follow the work of the police. At the level of the year we expect the numbers to be fairly stable, but fewer cases at the end of the log, which stops in June 2013. Within the year we expect a dip in August (holidays) and within the week fewer new fines on weekends. We do not expect a pattern within the month.
    """)
    return


@app.cell
def _(case_log_s5, mo, monthly_counts, pd, px):
    from visualizations import calendar_heatmap

    _start = case_log_s5['start']

    _monthly = px.bar(monthly_counts(_start), x='month', y='cases', width=800,
                      title='Case arrivals per month', labels={'month': 'Month', 'cases': 'Arriving cases'})

    # drift year by year: one row per year, one column per month
    _by_year_month = pd.crosstab(_start.dt.year.rename('year'), _start.dt.month.rename('month'))
    _heatmap = px.imshow(_by_year_month, color_continuous_scale='Blues', aspect='auto', width=800, height=500,
                         title='Case arrivals by year and month',
                         labels={'x': 'Month', 'y': 'Year', 'color': 'Arriving cases'})
    _heatmap.update_yaxes(dtick=1)
    _heatmap.update_xaxes(dtick=1)

    _weekday_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    _weekday = _start.dt.dayofweek.value_counts().reindex(range(7), fill_value=0)
    _weekday_fig = px.bar(x=_weekday_names, y=_weekday.values, width=600, title='Case arrivals per weekday',
                          labels={'x': 'Weekday', 'y': 'Arriving cases'})

    _day = _start.dt.day.value_counts().sort_index()
    _day_fig = px.bar(x=_day.index, y=_day.values, width=800, title='Case arrivals per day of the month',
                      labels={'x': 'Day of the month', 'y': 'Arriving cases'})

    # the calendar view of the lecture, for the year with the most arrivals
    _busiest_year = int(_start.dt.year.value_counts().idxmax())
    _calendar = calendar_heatmap(_start.dt.normalize().value_counts().sort_index().rename('cases'),
                                 year=_busiest_year, value_format=',.0f',
                                 title=f'Case arrivals per day in {_busiest_year}')

    mo.vstack([
        _monthly,
        _heatmap,
        mo.md("Arriving cases per year:"),
        _by_year_month.sum(axis=1).rename('cases'),
        _weekday_fig,
        _day_fig,
        _calendar,
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 5.2a - Result

    Our hypothesis is only confirmed for the end of the log and for the day of the month. The pattern within the year and the week is the opposite of what we expected.

    1. **Strong summer peak.** July (27'227 cases) and August (26'614) together make up 35.8 % of all arrivals, more than three times a month such as January (6'306). We expected a dip in August. *Interpretation:* The traffic in this area seems to be highest during the holidays, as in a tourist region.
    2. **Weekends are the busiest days.** Saturday (25'092) and Sunday (25'627) are about a quarter above the weekdays (18'678 to 21'469). We expected the opposite. In the calendar of the year 2000 this is mainly a summer effect: Sundays have 111 to 212 new fines in July, but only 3 to 14 in January. *Interpretation:* This fits the summer peak. The date seems to be the date of the offence rather than of the office work.
    3. **Drift from year to year.** The number of arrivals falls from 15'336 in 2000 to 8'565 in 2003, recovers to 15'114 in 2006, and then falls again to 4'018 in 2012 (2013 only runs until June). The summer peak remains in all years, but it is low in 2003 and 2012. January 2004 has only 90 cases. *Interpretation:* The log cannot explain these changes. Possible causes are changes in staff, in controls or in the data collection.
    4. **Hardly any pattern within the month.** Days 1 to 30 have between 4'339 and 5'902 arrivals, and day 31 is lower simply because it exists in only seven months. The 15th is the highest (5'902). *Question:* Is this caused by the holiday on 15 August?

    ### Task 5.2b - Hypothesis

    A case counts as closed at its last recorded event. We expect closures to be less even than arrivals. Paid cases close soon after they arrive, so they should follow the arrival pattern. Cases that end with *Send for Credit Collection* should close in large batches, because handing over to an agency is an administrative step. Cases of the last years may look closed although they are still running, because the log stops in June 2013.
    """)
    return


@app.cell
def _(case_log_s5, mo, monthly_counts, pd, px):
    _arrivals = monthly_counts(case_log_s5['start'], 'arrivals').set_index('month')
    _closures = monthly_counts(case_log_s5['end'], 'closures').set_index('month')
    _flow = pd.concat([_arrivals, _closures], axis=1).fillna(0).astype(int).sort_index()
    # cases that have arrived but not yet reached their last recorded event
    _flow['open cases'] = (_flow['arrivals'] - _flow['closures']).cumsum()

    _compare = px.line(_flow.reset_index(), x='month', y=['arrivals', 'closures'], width=800,
                       title='Case arrivals and closures per month',
                       labels={'month': 'Month', 'value': 'Cases', 'variable': ''})
    _open = px.line(_flow.reset_index(), x='month', y='open cases', width=800,
                    title='Open cases at the end of each month',
                    labels={'month': 'Month', 'open cases': 'Open cases'})

    # closures per month, split by the activity that closes the case
    _main_last = ['Payment', 'Send for Credit Collection', 'Send Fine']
    _last = case_log_s5['last_activity'].where(case_log_s5['last_activity'].isin(_main_last), 'Other')
    _month = case_log_s5['end'].dt.to_period('M').dt.to_timestamp().rename('month')
    _by_last = pd.crosstab(_month, _last.rename('last activity')).stack().rename('cases').reset_index()
    _split = px.bar(_by_last, x='month', y='cases', color='last activity', width=800,
                    category_orders={'last activity': _main_last + ['Other']},
                    title='Case closures per month, by last activity',
                    labels={'month': 'Month', 'cases': 'Closing cases', 'last activity': 'Last activity'})

    mo.vstack([
        _compare,
        _open,
        _split,
        mo.md("Last activity of the cases:"),
        case_log_s5['last_activity'].value_counts().rename('cases'),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 5.2b - Result

    The hypothesis is confirmed.

    1. **Closures come in large batches.** The ten months with the most closures contain between 4'386 and 9'712 closures each. An ordinary month has far fewer. The chart by last activity shows that these peaks are almost entirely *Send for Credit Collection* (58'997 cases end with this activity).
    2. **Paid cases follow the arrivals.** The 67'201 cases that end with *Payment* are spread evenly over time with no month above 1'251. This fits Task 5.3: most offenders pay within days.
    3. **Open cases form a sawtooth.** They grow between the batches and drop at each one. The highest value is 17'599 in March 2002, directly before the largest batch, which brings it down sharply. *Interpretation:* The work in progress is not driven by the amount of work but by the rare decision to hand cases over. The value reaches 0 at the end only by definition, because each case counts as closed at its last event.
    4. **Closed does not mean finished.** 20'755 cases end with *Send Fine* and 3'144 with *Send Appeal to Prefecture*. In June 2013, the last month of the log, 705 of the 842 closures are *Send Fine*. These cases are probably still running.

    *Finding:* A real closing event and a status for each fine are needed to tell a finished case from one that is waiting. *Recommendation data collection:* Record them.

    ### Task 5.2c - Hypothesis

    We expect *Send for Credit Collection* to happen in a few large batches, probably once or a few times a year, because a list of unpaid fines is handed over to an agency. We expect *Send Appeal to Prefecture* to be much rarer and more regular, because each appeal has its own deadline. It could still be sent in smaller batches, for example once a week.
    """)
    return


@app.cell
def _(ACTIVITY, event_log_s5, mo, monthly_counts, pd, px):
    _figures = []
    _rows = []
    for _activity in ['Send for Credit Collection', 'Send Appeal to Prefecture']:
        _times = event_log_s5.loc[event_log_s5[ACTIVITY] == _activity, 'local_time']
        _per_day = _times.dt.normalize().value_counts()
        _rows.append({
            'activity': _activity,
            'events': len(_times),
            'days with events': len(_per_day),
            'median events per active day': _per_day.median(),
            'max events on one day': _per_day.max(),
            'share of events on the 10 busiest days %': round(100 * _per_day.head(10).sum() / len(_times), 1),
            'first': _times.min().date(),
            'last': _times.max().date(),
        })
        _figures.append(px.bar(monthly_counts(_times), x='month', y='cases', width=800,
                               title=f'{_activity}: events per month',
                               labels={'month': 'Month', 'cases': 'Events'}))

    mo.vstack([pd.DataFrame(_rows).set_index('activity').T, *_figures])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 5.2c - Result

    **Send for Credit Collection is extremely batched, but less often than we expected.** All 59'013 events fall on just **11 days**, with a median of 5'011 cases per day and up to 9'136. The ten largest days hold 99.6 % of the events. The hand-overs are 9 to 25 months apart, so usually less than once a year. *Interpretation:* The hand-over is a rare administrative decision and not a regular step of the process.

    **Send Appeal to Prefecture is continuous, with one exception.** The 4'141 events are spread over 708 days, with a median of only 2 per active day, as we expected. But **520 events fall on one single day**, 25 December 2011, which also makes 2011 the busiest year (773 events). *Interpretation:* Normally each appeal is forwarded on its own. The exception looks like a catch-up or a data import, which Task 5.5 investigates.

    ## Task 5.3

    ### Task 5.3 - Hypothesis

    We expect two very different distributions. Fully paid cases should be short, with many cases closed within days or weeks, because the most frequent variant is *Create Fine > Payment*. Cases sent to credit collection should take much longer, probably between one and three years, because they run through sending, notification, a penalty after 60 days and then a long wait.
    """)
    return


@app.cell
def _(case_log_s5, day_chart, mo, pd):
    _groups = {
        'sent to credit collection': case_log_s5.loc[case_log_s5['credit_collection'], 'duration_days'],
        'fully paid': case_log_s5.loc[case_log_s5['paid'], 'duration_days'],
    }
    _summary = pd.DataFrame({
        _name: _days.describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9, 0.99]) for _name, _days in _groups.items()
    }).round(1)
    _summary.loc['share within 30 days %'] = [round(100 * (_d <= 30).mean(), 1) for _d in _groups.values()]
    _summary.loc['share within 1 year %'] = [round(100 * (_d <= 365).mean(), 1) for _d in _groups.values()]

    mo.vstack([
        mo.md("Case duration in days:"),
        _summary,
        *[day_chart(_days, f'Case duration, {_name}') for _name, _days in _groups.items()],
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 5.3 - Result

    | | Sent to credit collection | Fully paid |
    |---|---|---|
    | Cases | 59'013 | 60'287 |
    | Median | 638 days | 6 days |
    | Mean | 690.8 days | 93.7 days |
    | 10 % to 90 % | 497 to 987 days | 1 to 407 days |
    | Minimum to maximum | 273 to 3'437 days | 0 to 2'086 days |
    | Within 30 days | 0.0 % | 70.3 % |
    | Within 1 year | 0.2 % | 88.6 % |

    The hypothesis is confirmed. The two distributions hardly overlap in their main part.

    - **Sent to credit collection:** No case takes less than 273 days. The main hump lies around 570 days (about 1.6 years), with a second one around 960 days. Such humps fit the rare batches of Task 5.2c: the duration mainly depends on which batch a case ends up in. 70 % of these cases are closed within two years.
    - **Fully paid:** More than half (55.3 %) of the cases are closed within 7 days, followed by a sharp drop: 2'872 cases on day 7 but only 1'385 on day 8. The rest forms a long, flat tail with small humps around 240 and 480 days. These are late payers who pay after the penalty. The difference between the mean (93.7) and the median (6) shows how skewed the distribution is.

    *Question:* Why does the number of payments drop so sharply after 7 days? Is there a deadline or a reduced amount?

    ## Task 5.4

    ### Task 5.4 - Hypothesis

    - *Create Fine > Send Fine*: a long and wide delay with a sharp drop at a legal deadline.
    - *Send Fine > Insert Fine Notification*: short, about one to two weeks for the post.
    - *Insert Fine Notification > Add penalty*: almost always exactly 60 days (Task 5.1).
    - *Add penalty > Send for Credit Collection*: long and wide, with visible steps if the fines are handed over in batches (Task 5.2c).
    """)
    return


@app.cell
def _(day_chart, delay_days, mo, pd):
    SUBPROCESS = ['Create Fine', 'Send Fine', 'Insert Fine Notification', 'Add penalty', 'Send for Credit Collection']

    _rows = []
    _figures = []
    for _first, _second in zip(SUBPROCESS, SUBPROCESS[1:]):
        _days = delay_days(_first, _second)
        _top = _days.value_counts().head(3)
        _rows.append({
            'delay': f'{_first} > {_second}',
            'cases': len(_days),
            'negative': int((_days < 0).sum()),
            'same day': int((_days == 0).sum()),
            'median': _days.median(),
            'mean': round(_days.mean(), 1),
            '90th percentile': _days.quantile(0.9),
            'max': _days.max(),
            'most frequent delays (days: cases)': ', '.join(f'{int(_d)}: {num(_n)}' for _d, _n in _top.items()),
        })
        _figures.append(day_chart(_days[_days >= 0], f'{_first} > {_second}'))

    mo.vstack([pd.DataFrame(_rows).set_index('delay'), *_figures])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 5.4a - Result

    - **Create Fine > Send Fine** (103'987 cases, median 88 days): The distribution has two humps, around 50 and around 130 days, and it **breaks off abruptly at about 150 days**. 2'894 fines are sent on the day they are created.
    - **Send Fine > Insert Fine Notification** (79'860 cases, median 15 days): The delay is short as we expected, 90 % within 30 days. It has several peaks (Task 5.4d) and single extreme cases of up to 432 days.
    - **Insert Fine Notification > Add penalty** (79'860 cases): **All cases have exactly 60 days**, with no exception (Task 6.2). This delay does not vary at all, which no manual step would achieve. The penalty seems to be calculated by the system, not carried out by a person.
    - **Add penalty > Send for Credit Collection** (59'013 cases, median 488 days): This is by far the longest delay, with a spread from 209 to 3'331 days. Instead of a smooth curve it has many narrow spikes, for example at 396 and 343 days, because many penalties from the same days meet the same batch.

    ### Task 5.4b - Result

    1. **Hand over to credit collection regularly, for example every month or quarter.** *Add penalty > Send for Credit Collection* is the largest delay (median 488 days), and it comes from waiting for rare batches (Task 5.5), not from any work. Regular hand-overs would shorten the cycle time by many months. Debts are probably also easier to collect while they are recent, and offenders would be treated more equally.
    2. **Check the balance before adding the penalty.** The fixed 60 days show that the step is automatic. Penalties are also added when nothing or only a few euros are outstanding (Task 4.2a, Task 5.1). A check would avoid penalties that are not justified, as well as complaints and overpayments.
    3. **Send fines earlier, with a fixed internal target.** The humps in *Create Fine > Send Fine* show that many letters go out shortly before the deadline, and 2'405 cases (2.3 %) lie behind 150 days. A target well below the deadline reduces the risk of losing a fine. It also shortens the time until the offender can pay.
    4. **Offer electronic notification where possible.** *Send Fine > Insert Fine Notification* takes 15 days at the median, with a second peak of letters that apparently need longer (Task 5.4d). Electronic delivery would make this step faster and cheaper. The expenses for the offender would also fall.

    ### Task 5.4c - Hypothesis

    If there is a legal deadline for sending the letter, the distribution of *Create Fine > Send Fine* should end abruptly at that delay, because the police sends just in time and has to give up on a fine after that. Since most letters go within Italy, this drop should mark the deadline for Italy, while a small tail behind it belongs to letters sent abroad.
    """)
    return


@app.cell
def _(day_chart, delay_days, mo, pd):
    _days = delay_days('Create Fine', 'Send Fine')

    _thresholds = [30, 60, 90, 120, 150, 180, 240, 360, 720]
    _cumulative = pd.DataFrame({
        'cases sent within': [int((_days <= _t).sum()) for _t in _thresholds],
        'share %': [round(100 * (_days <= _t).mean(), 2) for _t in _thresholds],
    }, index=pd.Index(_thresholds, name='days'))

    # cases per 10 days, to see where the distribution breaks off
    _bins = (_days // 10 * 10).value_counts().sort_index().rename('cases').rename_axis('from day').to_frame()
    _bins['change to the previous 10 days %'] = (100 * _bins['cases'].pct_change()).round(1)

    mo.vstack([
        day_chart(_days, 'Create Fine > Send Fine, first 400 days', max_days=400),
        _cumulative,
        mo.md("Cases per 10 days:"),
        _bins[_bins.index <= 400],
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 5.4c - Result

    **The distribution suggests a deadline of about 150 days.**

    - The number of cases per 10 days stays at about 10'000 up to day 140 (9'998 for days 130 to 139), and then falls to 5'071 and to **370** from day 150 on. Per day it falls from 627 on day 145 to 77 on day 150 and to 30 on day 151, after which it stays at about this low level.
    - **97.69 % of the letters are sent within 150 days.** So the rule is almost always kept, and the many letters shortly before the limit suggest that the police uses all of the time it has.
    - The remaining 2'405 cases (2.31 %) form a thin, slowly falling tail, which fits letters abroad with a longer deadline. Only 36 cases are later than 360 days.

    This fits the Italian road traffic law: article 201 prescribed 150 days until the law 120/2010 shortened the time to 90 days ([edotto](https://edotto.com/articolo/notifica-pi-breve-per-le-multe)). Task 5.7 shows the effect of this change.

    ### Task 5.4d - Hypothesis

    We expect several peaks in the transit time *Send Fine > Insert Fine Notification*. Case C20817 (Task 5.1) has both events on the same day as *Create Fine*, so we expect a peak at 0 days for fines handed over directly. Letters by post should form a second peak after about one to two weeks. There could be a later peak for letters that could not be delivered at the first attempt. `notificationType` may separate the groups, because it tells whether the fine refers to the owner or the driver.
    """)
    return


@app.cell
def _(ACTIVITY, CASE_ID, delay_days, event_log_s5, mo, px):
    _days = delay_days('Send Fine', 'Insert Fine Notification')
    _notification = event_log_s5[event_log_s5[ACTIVITY] == 'Insert Fine Notification'].groupby(CASE_ID)['notificationType'].first()

    _table = _days.rename('days').to_frame().join(_notification)
    _counts = _table[_table['days'].between(0, 60)].value_counts(['days', 'notificationType']).rename('cases').reset_index()

    _fig = px.bar(_counts, x='days', y='cases', color='notificationType', width=800,
                  title='Send Fine > Insert Fine Notification, first 60 days',
                  labels={'days': 'Days', 'cases': 'Cases', 'notificationType': 'Notification type'})
    _fig.update_traces(marker_line_width=0)
    _fig.update_layout(bargap=0)

    _top = _days.value_counts().head(15).rename('cases').rename_axis('days').to_frame()
    _top['share %'] = (100 * _top['cases'] / len(_days)).round(2)

    mo.vstack([
        _fig,
        mo.md(f"Cases: **{num(len(_days))}**, median **{_days.median():g}** days. The 15 most frequent transit times:"),
        _top,
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 5.4d - Result

    We see **three major peaks**. A much smaller shoulder at 25 to 26 days belongs to the tail of the third one.

    1. **0 days (2'893 cases, 3.6 %).** The fine is sent and notified on the same day. Almost all of them have also been created on that day (Task 6.1c), so we interpret them as fines handed over directly, without the post. The three such cases that we inspected in Task 5.1 also have no postal expenses. This should be verified for all of them.
    2. **About 7 days (6 to 8 days with 4'228 to 4'794 cases per day).** This is the main peak: letters delivered by post at the first attempt.
    3. **About 18 days (17 to 19 days with 3'152 to 3'247 cases per day).** It lies about 10 to 11 days behind the second peak, with a clear dip in between (14 days: 2'162 cases). *Interpretation:* The offender was not reached at the first attempt, and the letter counts as delivered only after a fixed waiting period. The log cannot confirm this, so it remains a hypothesis.

    Our expectation for `notificationType` is not confirmed. Only 134 of these cases have the type C, most of them at 0 days (132), but 2'761 of the cases at 0 days have the type P. So this attribute does not separate the peaks.

    ## Task 5.5

    ### Task 5.5 - Hypothesis

    The performance spectrum shows every case as a line from one activity to the next. If *Send for Credit Collection* happens in batches, the lines from *Add penalty* should converge on a few points in time, with a large spread of waiting times per batch. For *Send Appeal to Prefecture* we expect shorter, more parallel lines from *Insert Date Appeal to Prefecture*, with smaller batches.
    """)
    return


@app.cell
def _(
    ACTIVITY,
    CASE_ID,
    TIMESTAMP,
    delay_days,
    event_log_s5,
    first_time,
    mo,
    pd,
):
    from event_enricher import event_add_relative_log_time
    from visualizations import performance_spectrum

    # the helpers need days since the start of the log in `rel_log_time`
    _log = event_add_relative_log_time(event_log_s5[[CASE_ID, ACTIVITY, TIMESTAMP, 'local_time']].copy(), time_col='local_time')
    _log['rel_log_time'] = _log['rel_log_time'].dt.days

    _spectra = []
    _batch_tables = []
    for _source, _target in [('Add penalty', 'Send for Credit Collection'),
                             ('Insert Date Appeal to Prefecture', 'Send Appeal to Prefecture')]:
        _wait = delay_days(_source, _target)
        # only cases with both activities, in an empty case log that the helper may extend
        _cases = pd.DataFrame(index=_wait.index)
        _spectrum = performance_spectrum(_cases, _log, _source, _target)
        _spectrum.update_layout(title=f'Performance spectrum: {_source} > {_target}', width=900, height=450)
        _spectra.append(_spectrum)

        _dates = first_time(_target).reindex(_wait.index).dt.normalize().rename('date')
        _batches = _wait.groupby(_dates).agg(['size', 'min', 'median', 'max']).rename(columns={
            'size': 'cases', 'min': 'shortest wait', 'median': 'median wait', 'max': 'longest wait'})
        _batch_tables.extend([
            mo.md(f"""
    **{_source} > {_target}**

    - Cases: **{num(len(_wait))}**, on **{num(len(_batches))}** different days, median **{_batches['cases'].median():g}** cases per day
    - Crossing lines in the spectrum above are FIFO violations.
    - The 10 largest batches:
    """),
            _batches.sort_values('cases', ascending=False).head(10),
        ])

    mo.vstack([*_spectra, *_batch_tables])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 5.5 - Result

    **Add penalty > Send for Credit Collection.** The spectrum confirms the batches and shows three new things.

    - **A minimum age instead of a fixed period.** Each batch collects penalties of a wide range of dates. The shortest wait per batch is at least 209 days (for example 315 days on 10.04.2002 and 301 on 26.03.2012). So a case seems to need a minimum age of roughly 7 to 14 months before it can be included.
    - **The process is not FIFO.** The longest wait in a batch is much longer than the time since the previous batch: 3'331 days on 26.03.2012, 1'806 days on 28.02.2006. These cases were skipped by several earlier batches. Their median wait also varies strongly, from 368 days (10.01.2003) to 713 days (26.03.2012).
    - **The waiting time depends on when the fine happens to fall.** Two offenders with the same debt can wait years apart for the hand-over.
    - **Dates that look administrative.** Batches fall on 25.12.2004, 28.02.2006 and 28.02.2007, and on the 10th of the month in 2002 to 2004. Christmas Day suggests a booking date in a system, not the day of real work.

    **Insert Date Appeal to Prefecture > Send Appeal to Prefecture.** Normally there are small batches with a short wait: the largest regular days have 44 to 79 cases and a median wait of 35 to 56 days, with a range of 20 to 127 days. Our hypothesis holds for these.

    The exception is **25.12.2011 with 520 cases, a median wait of 1'507.5 days and up to 4'272 days**, almost 12 years. On this day some appeals even have a wait of -48 days, so they are sent before their appeal date. Task 5.2c therefore has to be refined: 2011 is not a year with many appeals. Instead a backlog of old appeals seems to have been entered at once on a public holiday, probably in a clean-up of the data. *Recommendation data collection:* Distinguish the date of the real event from the date of its entry.

    ## Task 5.6

    ### Task 5.6 - Hypothesis

    For a fixed article we expect the initial fine amount to be a step function of time: a few fixed amounts that are raised at the same date for all cases when the law changes. We expect the steps every few years, in line with inflation. Several parallel amounts per article could be caused by more specific offences under the same article.

    Choose an article in the menu below. The example in the result is the preselected article, the most frequent one in the log.
    """)
    return


@app.cell
def _(case_log_s5, mo):
    _article_counts = case_log_s5['article'].value_counts()
    _options = {f'Article {_article:g} ({num(_n)} cases)': _article for _article, _n in _article_counts.items()}
    article_select = mo.ui.dropdown(options=_options, value=next(iter(_options)), label='Article', searchable=True)
    article_select
    return (article_select,)


@app.cell
def _(article_select, case_log_s5, mo, px):
    _cases = case_log_s5[case_log_s5['article'] == article_select.value]
    _month = _cases['start'].dt.to_period('M').dt.to_timestamp().rename('month')

    # one bubble per combination of month and amount
    _bubbles = _cases.groupby([_month, 'initial_amount']).size().rename('cases').reset_index()
    _fig = px.scatter(_bubbles, x='month', y='initial_amount', size='cases', size_max=25, width=850,
                      title=f'Initial fine amount over time, article {article_select.value:g}',
                      labels={'month': 'Month of Create Fine', 'initial_amount': 'Initial fine amount', 'cases': 'Cases'})

    # when does each amount first and last occur?
    _amounts = _cases.groupby('initial_amount')['start'].agg(['size', 'min', 'max']).rename(
        columns={'size': 'cases', 'min': 'first', 'max': 'last'})
    _amounts['first'] = _amounts['first'].dt.date
    _amounts['last'] = _amounts['last'].dt.date

    mo.vstack([
        _fig,
        mo.md("The 15 most frequent amounts of this article:"),
        _amounts.sort_values('cases', ascending=False).head(15).sort_values('first'),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 5.6 - Result

    **Article 157 (68'074 cases, stopping and parking).** The hypothesis is confirmed. At any time there is essentially one amount, and it changes in clear steps around 1 January:

    | Period | Initial fine amount |
    |---|---|
    | 2000 | 31.30 |
    | 2001 | 32.80 |
    | 2002 | 32.00 |
    | 2003 to 2004 | 33.60 |
    | 2005 to 2006 | 35.00 |
    | 2007 to 2008 | 36.00 |
    | 2009 to 2010 | 38.00 |
    | 2011 to 2012 | 39.00 |
    | 2013 | 41.00 |

    - From 2003 on, the amount rises **every two years by about 3 to 6 %**, in line with an adjustment for inflation.
    - The only decrease is from 32.80 to 32.00 in 2002, the year in which the euro cash was introduced. *Question:* Is this a result of the conversion?
    - The old amount is used for only a few days into the new year (for example 33.60 until 09.01.2005). This suggests that the date of the offence decides on the amount, and that some fines are entered with a short delay.
    - Two single cases have about double the amount (65.60 in 2001 and 71.00 in 2005). They are probably errors or special cases.

    *Finding:* Comparing amounts over the years, as in Task 2.5, should take this drift into account. An interactive menu is included above, so other articles can be studied in the same way.

    ## Task 5.7

    ### Task 5.7 - Hypothesis

    If the sharp drop of Task 5.4c comes from a legal deadline that existed for the whole log, the distribution for cases that start after 1 September 2010 should keep the same shape. The date in the task suggests that something changes around then, so we expect a different distribution: possibly a shift of the peak or a different limit. Fines of the last months have had less time to be sent, but this should matter little, because the log runs for almost three more years.
    """)
    return


@app.cell
def _(case_log_s5, day_chart, delay_days, mo, pd):
    _all = delay_days('Create Fine', 'Send Fine')
    _recent = _all[_all.index.isin(case_log_s5.index[case_log_s5['start'] > pd.Timestamp('2010-09-01')])]

    _groups = {'full log': _all, 'cases starting after 1 Sept 2010': _recent}
    _summary = pd.DataFrame({
        _name: _days.describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9, 0.99]) for _name, _days in _groups.items()
    }).round(1)
    _summary.loc['most frequent delay'] = [_d.value_counts().idxmax() for _d in _groups.values()]

    mo.vstack([
        _summary,
        day_chart(_recent, 'Create Fine > Send Fine, cases starting after 1 Sept 2010, first 400 days', max_days=400),
        day_chart(_all, 'Create Fine > Send Fine, full log, first 400 days', max_days=400),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 5.7 - Result

    | Create Fine > Send Fine | Full log | Starting after 1 Sept 2010 |
    |---|---|---|
    | Cases | 103'987 | 10'721 |
    | Median | 88 days | 50 days |
    | Mean | 87.5 days | 54.8 days |
    | 75th percentile | 121 days | 59 days |
    | 90th percentile | 136 days | 90 days |
    | Within 60 days | 31.6 % | 76.7 % |
    | Within 90 days | 52.1 % | 90.3 % |

    **The distribution changes clearly.** The second hump around 130 days has disappeared, and there is only one peak around 48 to 54 days. The hard limit at 150 days has been replaced by a clear drop at about 60 days: from 267 cases on day 59 to 170 on day 60, to 115 on day 61.

    **Interpretation.** This fits the change of article 201 by the law 120/2010, which shortened the deadline from 150 to 90 days ([edotto](https://edotto.com/articolo/notifica-pi-breve-per-le-multe)). So the 150 days of Task 5.4c only apply to the time before this change, and the full log mixes two regimes. The drop at 60 days instead of 90 makes sense if the notification must arrive within the deadline: 60 days for sending plus up to 30 days of transit (the 90th percentile of Task 5.4) gives 90 days. This shows why concept drift matters: a single distribution for the full log would hide the change.

    About 10 % of the cases are still later than 90 days. These could be letters abroad or cases whose owner had to be identified first. The source does not tell us the exact date from which the new rule applied, so the date of 1 September comes from the task.
    """)
    return


@app.cell
def _(ACTIVITY, case_log_s5, mo):
    def has_activity(activity):
        # does the case contain the activity at least once?
        return case_log_s5['seq_variant'].apply(lambda variant: activity in variant)


    def rule_report(applicable, violating):
        # the numbers that Task 6.1 asks for; both arguments are numbers of cases
        _kept = applicable - violating
        return mo.md(f"""
    - Cases to which the constraint applies: **{num(applicable)}** of {num(len(case_log_s5))}
    - **Violating cases: {num(violating)}** ({violating / applicable:.2%} of the applicable cases)
    - Precision of "if ... then ...": **{_kept / applicable:.4f}**
    """)


    RULE_COLUMNS = [ACTIVITY, 'amount', 'expense', 'paymentAmount', 'dismissal', 'notificationType', 'outstanding_amount']
    return RULE_COLUMNS, has_activity, rule_report


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Session 6

    ## Task 6.1

    ### Task 6.1a - Hypothesis

    *Whenever a case has Insert Fine Notification then also Add penalty is present.* Task 4.2a already showed that both activities occur in the same 79'860 cases, so we expect **no violation**. This is surprising from a business point of view, because an offender who pays in time should not get a penalty.
    """)
    return


@app.cell
def _(RULE_COLUMNS, event_log_s5, has_activity, mo, rule_report, show_case):
    _notified = has_activity('Insert Fine Notification')
    _violating = _notified & ~has_activity('Add penalty')
    _violating_ids = _violating[_violating].index

    mo.vstack([
        rule_report(int(_notified.sum()), int(_violating.sum())),
        mo.md(f"**Violating case {_violating_ids[0]}**") if len(_violating_ids) else mo.md("There is no violating case."),
        show_case(event_log_s5, _violating_ids[0], RULE_COLUMNS) if len(_violating_ids) else mo.md(""),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 6.1a - Result

    **0 of the 79'860 applicable cases violate the constraint**, so it is valid, as expected. There is therefore no violating case to inspect.

    **Reflection.** The perfect result is itself suspicious. From a business point of view a fine that is notified and then paid in time should not get a penalty. Yet in this log such a fine does not exist. Together with Task 6.2 this suggests that *Insert Fine Notification* is not recorded when the letter arrives, but only when a fine is still unpaid at the end of the 60 days, together with the penalty. An offender who pays in time would then have no notification in the log at all, as in the variant *Create Fine > Send Fine > Payment*. *Recommendation data collection:* Record each notification when it happens.

    ### Task 6.1b - Hypothesis

    *Send Appeal to Prefecture is always eventually followed by Receive Result Appeal from Prefecture.* The table in Task 5.1 shows 4'141 cases with *Send Appeal to Prefecture* but only 999 with *Receive Result Appeal from Prefecture*, so we expect **at least about 3'100 violations**, roughly three quarters of the appeals. Part of them could be appeals still running at the end of the log, but most should be results that were not recorded.
    """)
    return


@app.cell
def _(
    RULE_COLUMNS,
    case_log_s5,
    event_log_s5,
    first_time,
    has_activity,
    mo,
    pd,
    rule_report,
    show_case,
):
    _send, _receive = 'Send Appeal to Prefecture', 'Receive Result Appeal from Prefecture'


    def _violates(variant):
        _positions = [_i for _i, _a in enumerate(variant) if _a == _send]
        return any(_receive not in variant[_i + 1:] for _i in _positions)


    _applicable = has_activity(_send)
    _violating = case_log_s5.loc[_applicable, 'seq_variant'].apply(_violates)
    _violating_ids = _violating[_violating].index

    _sent_year = first_time(_send).dt.year.rename('year of Send Appeal')
    _by_year = pd.DataFrame({
        'appeals': _sent_year.value_counts(),
        'violating': _sent_year[_sent_year.index.isin(_violating_ids)].value_counts(),
    }).fillna(0).astype(int).sort_index()

    # what happens to a violating case after the appeal was sent?
    _last_activity = case_log_s5.loc[_violating_ids, 'last_activity'].value_counts().rename('cases')

    mo.vstack([
        rule_report(int(_applicable.sum()), int(_violating.sum())),
        mo.md("Appeals and violations by year:"),
        _by_year,
        mo.md("Last activity of the violating cases:"),
        _last_activity,
        mo.md(f"**Violating case {_violating_ids[0]}**") if len(_violating_ids) else mo.md("There is no violating case."),
        show_case(event_log_s5, _violating_ids[0], RULE_COLUMNS) if len(_violating_ids) else mo.md(""),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 6.1b - Result

    **3'224 of the 4'141 applicable cases violate the constraint (77.86 %).** The number matches our hypothesis.

    **Reflection.** Our explanation of appeals that are still running is not sufficient: the violations are not concentrated at the end of the log, but occur in all years (for example 90 of 145 in 2000 and 380 of 480 in 2007). In 3'144 of the violating cases *Send Appeal to Prefecture* is the very last event. So in most cases the process leaves the log at this point, and it is unclear whether the prefecture ever answered.

    **Case A10001.** The fine of 36 is notified on 25.07.2007, and the appeal is entered on 02.08.2007. The penalty is added on 23.09.2007, and the appeal is sent on 24.09.2007. On this last event `dismissal` changes to **#**, which means dismissed by the prefecture, although no result was received. *Interpretation:* The result seems to be stored as the code on the sending event, instead of as a separate event. This cannot explain all of the violations, since Task 3.1 found only 2'073 dismissed cases in the whole log.

    *Questions:* How many of the violating cases have this code? What happened to the others? *Recommendation data collection:* Always record the result of an appeal as an event with its date.

    ### Task 6.1c - Hypothesis

    *If Send Fine is on the same day as Create Fine, so is Insert Fine Notification.* In the few cases we have seen with this pattern (C20817, C17607, C19089 in Task 5.1) all three events fall on one day, which suggests a fine that is handed over directly. So we expect the constraint to hold with **very few violations**.
    """)
    return


@app.cell
def _(
    RULE_COLUMNS,
    case_log_s5,
    event_log_s5,
    first_time,
    mo,
    rule_report,
    show_case,
):
    _created = first_time('Create Fine').dt.normalize()
    _sent = first_time('Send Fine').dt.normalize().reindex(case_log_s5.index)
    _notified = first_time('Insert Fine Notification').dt.normalize().reindex(case_log_s5.index)

    _applicable = _sent == _created.reindex(case_log_s5.index)
    # a missing notification counts as a violation: it is not on the same day
    _violating = _applicable & (_notified != _created.reindex(case_log_s5.index))
    _violating_ids = _violating[_violating].index

    mo.vstack([
        rule_report(int(_applicable.sum()), int(_violating.sum())),
        mo.md(f"""
    - Violating cases without any *Insert Fine Notification*: **{num(_notified[_violating].isna().sum())}**
    - Violating cases with a notification on a later day: **{num(_notified[_violating].notna().sum())}**
    """),
        mo.md(f"**Violating case {_violating_ids[0]}**") if len(_violating_ids) else mo.md("There is no violating case."),
        show_case(event_log_s5, _violating_ids[0], RULE_COLUMNS) if len(_violating_ids) else mo.md(""),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 6.1c - Result

    **167 of the 2'894 applicable cases violate the constraint (5.77 %).** 118 of them have no notification at all, and 49 have one on a later day. The hypothesis of very few violations holds only approximately. The rule has a precision of 0.94, so it is a strong pattern but not a rule of the process.

    **Case C10130.** The fine of 131.20 is created and sent on 07.08.2001, and expenses of 6.71 are charged. The notification follows only on 15.09.2001, 39 days later. The fine is not paid, and the case goes on to a penalty and to credit collection. *Interpretation:* Unlike the cases in Task 5.4d, this is apparently a real letter by post, because there are postal expenses. It only happens to have been sent on the day the fine was created. So a *Send Fine* on the first day has two meanings, and the log can only separate them by its other attributes.

    ### Task 6.1d - Hypothesis

    *If the outstanding amount after an event is 0 or less, then there is no further event.* We expect **some hundreds of violations**: Task 4.2b showed 362 cases of *Create Fine > Payment > Send Fine*, in which the fine is sent after it was paid, and Task 5.1 showed payments after a fine was settled, for example A18543. Most of the following events should therefore be *Send Fine* or *Add penalty*.
    """)
    return


@app.cell
def _(
    ACTIVITY,
    CASE_ID,
    RULE_COLUMNS,
    event_log_s5,
    mo,
    pd,
    rule_report,
    show_case,
):
    _log = event_log_s5[[CASE_ID, ACTIVITY, 'outstanding_amount', 'local_time']].copy()
    _next = _log.groupby(CASE_ID)
    _log['next_activity'] = _next[ACTIVITY].shift(-1)
    _log['next_time'] = _next['local_time'].shift(-1)

    _settled = _log[_log['outstanding_amount'] <= 0]
    _violating_events = _settled[_settled['next_activity'].notna()]
    _violating_ids = _violating_events[CASE_ID].unique()

    # the most frequent kind of violation is the most useful one to inspect
    _pair = _violating_events.groupby([ACTIVITY, 'next_activity']).size().idxmax()
    _example = _violating_events[(_violating_events[ACTIVITY] == _pair[0]) & (_violating_events['next_activity'] == _pair[1])][CASE_ID].iloc[0]

    mo.vstack([
        rule_report(int(_settled[CASE_ID].nunique()), len(_violating_ids)),
        mo.md(f"""
    - Violating events: **{num(len(_violating_events))}**
    - Of which the next event is on the same day, so the order is unknown (Task 2.1): **{num((_violating_events['next_time'] == _violating_events['local_time']).sum())}**
    """),
        mo.md("Violating events, by the activity (rows) and the activity that follows it (columns):"),
        pd.crosstab(_violating_events[ACTIVITY], _violating_events['next_activity']),
        mo.md(f"**Violating case {_example}**, of the most frequent kind (*{_pair[0]}* followed by *{_pair[1]}*)"),
        show_case(event_log_s5, _example, RULE_COLUMNS),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 6.1d - Result

    **728 of the 60'783 applicable cases violate the constraint (1.20 %)**, with 774 violating events. The applicable cases are those that reach an outstanding amount of 0 or less at some event. The order of the events is unknown for 33 of them, because they are on the same day. The hypothesis of some hundreds of violations is confirmed.

    **Which events follow?** Mostly *Send Fine* after a payment (540 events), as expected from Task 4.2b, then a further *Payment* (117), which leads to an overpayment, and *Add penalty* after a payment (36). We expected more penalties here. There are also 31 cases of *Create Fine > Send Fine* in which the amount is already 0 or less when the fine is created.

    **Case A1161.** The fine of 35 is created on 15.08.2006 and paid in full on 12.12.2006. Two days later, on 14.12.2006, it is sent anyway, which adds expenses of 11. The offender pays these on 30.12.2006, and then nothing more is outstanding. *Interpretation:* The letter was probably already prepared when the payment arrived, or the payment was only registered later. Either way the offender pays expenses for a letter that should not have been necessary. This is the same improvement as in Task 4.2c: check for payments immediately before sending.

    **Reflection.** With a precision of 0.988 the rule is nearly valid. It is therefore useful as a monitoring rule for detecting unnecessary work.

    ### Task 6.1e - Hypothesis

    *Credit collection happens not earlier than 180 and not later than 730 days after Insert Fine Notification.* The penalty comes after 60 days, so collection before 180 days would be unusual, and we expect a legal limit of about two years at the upper end. We expect the rule to hold for **most cases, with a small number of late violations**, because the fines are handed over in batches (Task 5.2c).
    """)
    return


@app.cell
def _(
    RULE_COLUMNS,
    day_chart,
    delay_days,
    event_log_s5,
    has_activity,
    mo,
    rule_report,
    show_case,
):
    _days = delay_days('Insert Fine Notification', 'Send for Credit Collection')
    _early, _late = _days[_days < 180], _days[_days > 730]
    _without_notification = has_activity('Send for Credit Collection') & ~has_activity('Insert Fine Notification')

    _examples = []
    if len(_early):
        _examples += [mo.md(f"**Earliest case {_early.idxmin()}** ({_early.min():g} days)"),
                      show_case(event_log_s5, _early.idxmin(), RULE_COLUMNS)]
    if len(_late):
        _examples += [mo.md(f"**Latest case {_late.idxmax()}** ({_late.max():g} days)"),
                      show_case(event_log_s5, _late.idxmax(), RULE_COLUMNS)]

    mo.vstack([
        rule_report(len(_days), len(_early) + len(_late)),
        mo.md(f"""
    - Earlier than 180 days: **{num(len(_early))}**, later than 730 days: **{num(len(_late))}**
    - Median **{_days.median():g}** days, minimum {_days.min():g}, maximum {_days.max():g}
    - Cases with credit collection but without a notification, which we leave out: **{num(_without_notification.sum())}**
    """),
        day_chart(_days, 'Insert Fine Notification > Send for Credit Collection'),
        *_examples,
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 6.1e - Result

    **11'258 of the 59'013 applicable cases violate the constraint (19.08 %).** All of them are too late, none is too early. Every case with credit collection also has a notification. Our hypothesis of a small number of violations is refuted. The rule is clearly not kept in practice, even though the median of 548 days lies well inside the limits.

    - **Lower limit (180 days):** It is always kept. The shortest delay is 269 days. So the limit could be reached far earlier in principle, but this is never used.
    - **Upper limit (730 days):** About one in five cases is late, with a maximum of 3'391 days.

    **Case N40905 (the latest one).** A fine of 19 is created on 28.10.2002, notified on 13.12.2002 and raised by the penalty on 11.02.2003. It is then handed over only on 26.03.2012, more than **nine years** after the notification and for only 49. *Interpretation:* The case was skipped by many batches (Task 5.5). If the constraint is a legal limit, such a claim could no longer be enforceable, and the cost of collecting it could easily exceed its value.

    **Reflection.** The late cases are a direct result of the rare and non-FIFO batches. More regular hand-overs (Task 5.4b), combined with a check of the oldest cases first, would remove most of these violations.

    ## Task 6.2

    ### Task 6.2 - Constraint and hypothesis

    **Constraint:** *Add penalty happens exactly 60 days after Insert Fine Notification.*

    We expect this to be satisfied in almost all cases, because the delays in Task 5.1 are 60 days at the median and at both quartiles. It would show that the penalty is added automatically on a fixed date, which matters for the penalties on nearly paid fines in Task 5.1. We expect exceptions at most where appeals interrupt the process.
    """)
    return


@app.cell
def _(
    RULE_COLUMNS,
    case_log_s5,
    delay_days,
    event_log_s5,
    mo,
    rule_report,
    show_case,
):
    _days = delay_days('Insert Fine Notification', 'Add penalty')
    _other = _days[_days != 60]

    _top = _days.value_counts().head(10).rename('cases').rename_axis('days').to_frame()
    _top['share %'] = (100 * _top['cases'] / len(_days)).round(2)

    # are the exceptions cases with an appeal?
    _appeal_activities = ['Appeal to Judge', 'Insert Date Appeal to Prefecture']
    _exception_has_appeal = case_log_s5.loc[_other.index, 'seq_variant'].apply(
        lambda variant: any(_a in variant for _a in _appeal_activities))

    mo.vstack([
        rule_report(len(_days), len(_other)),
        mo.md(f"""
    - Exceptions that contain an appeal: **{num(_exception_has_appeal.sum())}** of {num(len(_other))}
    - Delay between the two activities, shortest and longest: **{_days.min():g}** and **{_days.max():g}** days
    """),
        mo.md("The 10 most frequent delays:"),
        _top,
        mo.md(f"**Exception {_other.index[0]}**") if len(_other) else mo.md("There is no exception."),
        show_case(event_log_s5, _other.index[0], RULE_COLUMNS) if len(_other) else mo.md(""),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 6.2 - Result

    **0 of the 79'860 applicable cases violate the constraint.** All of them have exactly 60 days between the two activities, even more than we expected. There are no exceptions for appeals either.

    **Reflection.** In real work, a delay of exactly the same length in every case, including weekends and holidays, is not plausible. At least one of the two dates must therefore be calculated by the system, not observed: the penalty is set for day 60, or one of the two events is entered afterwards. Together with Task 6.1a this has three consequences:

    - It supports our hypothesis in Task 5.1 that the penalty is added automatically on a fixed date, so that it also hits offenders who have paid almost everything or who pay right around this time.
    - This delay should not be counted as waiting time that can be improved, because it results from the rule itself.
    - *Insert Fine Notification* may not reliably show the actual delivery date. The transit times in Task 5.4d should therefore be read with care.

    *Recommendation data collection:* Record the real time of the delivery and the rule that triggered the penalty.

    ## Task 6.3

    ### Task 6.3 - Approach and hypothesis

    We convert our BPMN model from Task 4.3 into a Petri net and align each of the 48 variants of the fine object sub-log with it. An alignment shows which steps of a variant the model cannot follow. Black transitions of the Petri net appear as `None` and are ignored.

    From Task 4.3 we expect about 31 of the 48 variants not to fit. We expect some of them to be behaviour that the model should allow. Our candidate is a fine that is partly paid and then sent to credit collection: *Create Fine > Send Fine > Insert Fine Notification > Add penalty > Payment > Send for Credit Collection*. Our model lets a payment only end the case or lead to a further payment, but handing over a remaining debt makes business sense.
    """)
    return


@app.cell
def _(fine_object_variant, mo, pd, pm4py):
    import warnings as _warnings
    from pm4py.objects.log.obj import Event as _Event, EventLog as _EventLog, Trace as _Trace

    _counts = fine_object_variant.value_counts()
    _rows = []
    with _warnings.catch_warnings():
        _warnings.simplefilter('ignore')  # pm4py marks some of these helper functions as deprecated
        _net, _initial, _final = pm4py.convert_to_petri_net(pm4py.read_bpmn(str(mo.notebook_dir() / 'fine_object.bpmn')))
        for _variant, _n in _counts.items():
            _log = _EventLog([_Trace([_Event({'concept:name': _a}) for _a in _variant])])
            _result = pm4py.conformance_diagnostics_alignments(_log, _net, _initial, _final)[0]
            # (>>, None) is a silent step of the model and no deviation
            _moves = [_move for _move in _result['alignment'] if _move[0] != _move[1] and _move[1] is not None]
            _rows.append({
                'variant': _variant,
                'cases': _n,
                'fitness': round(_result['fitness'], 3),
                'only in the log': ', '.join(_m[0] for _m in _moves if _m[1] == '>>'),
                'only in the model': ', '.join(_m[1] for _m in _moves if _m[0] == '>>'),
            })

    conformance_table = pd.DataFrame(_rows)
    _not_fitting = conformance_table[conformance_table['fitness'] < 1]
    _shown = _not_fitting.assign(variant=_not_fitting['variant'].apply(' > '.join)).reset_index(drop=True)

    mo.vstack([
        mo.md(f"""
    - Variants that fit the model: **{(conformance_table['fitness'] == 1).sum()}** of {len(conformance_table)}
    - Cases that fit the model: **{num(conformance_table.loc[conformance_table['fitness'] == 1, 'cases'].sum())}** of {num(conformance_table['cases'].sum())}. This should agree with Task 4.3.
    """),
        mo.md("All variants that are not a trace of the model, with the deviating steps:"),
        _shown,
    ])
    return (conformance_table,)


@app.cell
def _(
    ACTIVITY,
    RULE_COLUMNS,
    conformance_table,
    event_log_s5,
    fine_object_variant,
    mo,
    show_case,
):
    REPORTED_VARIANT = ('Create Fine', 'Send Fine', 'Insert Fine Notification', 'Add penalty',
                        'Payment', 'Send for Credit Collection')

    _row = conformance_table[conformance_table['variant'].apply(lambda variant: variant == REPORTED_VARIANT)]
    _cases = fine_object_variant[fine_object_variant.apply(lambda variant: variant == REPORTED_VARIANT)].index
    _events = event_log_s5[event_log_s5['case:concept:name'].isin(_cases)]
    _at_collection = _events[_events[ACTIVITY] == 'Send for Credit Collection']['outstanding_amount']

    mo.vstack([
        mo.md(f"""
    **{' > '.join(REPORTED_VARIANT)}**

    - Cases: **{num(len(_cases))}**, fitness on the model: **{_row['fitness'].iloc[0] if len(_row) else 'variant not found'}**
    - Only in the log: **{_row['only in the log'].iloc[0] if len(_row) else ''}**, only in the model: **{_row['only in the model'].iloc[0] if len(_row) else ''}**
    - Cases with something still outstanding at *Send for Credit Collection*: **{num((_at_collection > 0).sum())}** of {num(len(_at_collection))}
    - Outstanding amount at that point: median **{_at_collection.median():g}**, minimum {_at_collection.min():g}, maximum {_at_collection.max():g}
    """),
        mo.md(f"**Case {_cases[0]}**") if len(_cases) else mo.md("There is no case of this variant."),
        show_case(event_log_s5, _cases[0], RULE_COLUMNS) if len(_cases) else mo.md(""),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 6.3a - Result

    *Create Fine > Send Fine > Insert Fine Notification > Add penalty > Payment > Send for Credit Collection*

    This variant occurs in **1'523 cases** and is not a trace of the BPMN model. Its fitness is 0.875, and the alignment shows *Payment* as the step that only occurs in the log. The model confirms the numbers of Task 4.3: 17 of the 48 variants and 120'535 of the 150'370 cases fit.

    ### Task 6.3b - Result

    **We consider this behaviour expected.** In 1'521 of the 1'523 cases something is still outstanding at credit collection, with a median of 38. In case A1017, for example, the offender pays 32 (the fine of 21 and the expenses of 11) after the penalty was added, and the remaining 21.50 is handed over two years later. The offender pays only part of the fine with its penalty, and the police hands the remaining debt over to the collection agency. The model is wrong here, because it treats every payment as if it ended the case or led to another payment.

    **Update of the BPMN model.** Add a third outgoing flow to the XOR gateway G5 behind *Payment*, leading to *Send for Credit Collection*. The model stays sound, because this is only one more branch of an XOR split and the graph still has no AND gateway. The update allows more than intended: *Create Fine > Payment > Send for Credit Collection* would also fit, although a fine is normally only handed over after the penalty. To exclude this, the model would need a separate *Payment* task behind *Add penalty*, which leads to either credit collection or the end of the process.
    """)
    return


if __name__ == "__main__":
    app.run()
