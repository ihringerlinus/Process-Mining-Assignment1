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

    return mo, pd, pm4py


@app.cell
def _(pm4py):
    event_log_from_disk = pm4py.read_xes('C:\\DATA\\HSG\\ProcessMining\\Process-Mining-Assignment1\\Road_Traffic_Fine_Management_Process.xes', variant="rustxes")
    print(len(event_log_from_disk), 'events read.')
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
    Wir erwarten sekundengenaue Zeitstempel, da die Events von einem IT-System erfasst werden.
    """)
    return


@app.cell
def _(TIMESTAMP, event_log, mo):
    _ts = event_log[TIMESTAMP]
    if _ts.dt.tz is not None:
        _ts = _ts.dt.tz_convert('Europe/Rome')

    mo.md(f"""
    - Zeitzone im Log: **{event_log[TIMESTAMP].dt.tz}**
    - Events mit Stunde ≠ 0: **{(_ts.dt.hour != 0).sum()}**
    - Events mit Minute ≠ 0: **{(_ts.dt.minute != 0).sum()}**
    - Events mit Sekunde ≠ 0: **{(_ts.dt.second != 0).sum()}**
    """)
    return


@app.cell
def _(CASE_ID, TIMESTAMP, event_log, mo):
    _same_day = event_log.duplicated([CASE_ID, TIMESTAMP], keep=False)
    mo.md(f"""
    Events, die im selben Case denselben Tag haben wie ein anderes Event: **{_same_day.sum()}**,
    verteilt auf **{event_log.loc[_same_day, CASE_ID].nunique()}** Cases
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Die Hypothese ist widerlegt: Alle Timestamps sind tagesgenau (Mitternacht italienischer Zeit; im Log als UTC gespeichert, wodurch ohne Umrechnung 22:00/23:00 Uhr erscheint). Konsequenzen: (1) Durchlaufzeiten können nur in Tagen gemessen werden. (2) Bei Events am selben Tag im selben Case ist die Reihenfolge nicht durch den Timestamp bestimmt; 21308 Events in 9166 Cases sind betroffen. Für Enrichments wie kumulierte Zahlungen verwenden wir daher die Originalreihenfolge des Logs als zweites Sortierkriterium.
    Finding (Datenerfassung): Uhrzeit mit erfassen, damit die Reihenfolge von Events am selben Tag eindeutig ist.
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
    ### Task 2.2a – Hypothese

    Jede Aktivität hat nur die Attribute, die für sie fachlich relevant sind (z. B. `paymentAmount` bei *Payment*, `expense` bei *Send Fine*). Da das Log aus einem Verwaltungssystem stammt, das bestimmte Felder pro Schritt erzwingt, erwarten wir kaum fehlende Werte. Wir vermuten aber, dass fehlende Information teils nicht als leerer Wert, sondern als Standardwert (z. B. `0` oder `NIL`) gespeichert ist.
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
    ### Task 2.2a – Ergebnis

    **Fehlende Werte (`NaN`):** Nur ein Attribut ist unvollständig: `lastSent` fehlt bei **1'631 von 79'860** *Insert Fine Notification*-Events (ca. 2 %). Alle anderen Attribute sind in den Schemas, zu denen sie gehören, vollständig.

    **Nullwerte:** Die Prüfung auf `0` zeigt, dass die Vollständigkeit teilweise nur formal ist:

    - `totalPaymentAmount` ist bei *Create Fine* in **allen 150'370** Events `0`. Fachlich plausibel (zu Beginn ist noch nichts bezahlt), das Attribut wird bei *Create Fine* also nur mit einem Startwert initialisiert.
    - `points` ist bei *Create Fine* in **146'822 von 150'370** Fällen `0`; nur rund 3'500 Bussen führen zu Punkteabzug. Hier bedeutet `0` vermutlich "keine Punkte", ein fehlender Wert lässt sich davon aber nicht unterscheiden.
    - `amount` ist bei **36** *Create Fine*- und **18** *Add penalty*-Events `0`. Eine Busse bzw. ein Strafzuschlag von 0 ist fachlich unerwartet.
    - Bei *Payment* ist `paymentAmount` in **3** Events `0` und `totalPaymentAmount` in **2** Events `0`. Eine Zahlung über 0 bzw. eine kumulierte Zahlungssumme von 0 *nach* einer Zahlung widerspricht der Bedeutung der Aktivität (Datenfehler oder Stornierung/Korrektur?).
    - `expense` ist bei *Send Fine* in **2'860 von 103'987** Events `0` (ca. 2.8 %). Möglicherweise wurden diese Bussen ohne Postkosten zugestellt, oder die Kosten wurden nicht erfasst.
    - `matricola` ist bei allen **555** *Appeal to Judge*-Events `0` und enthält damit keinerlei Information.

    **Fazit:** Die Hypothese ist teilweise bestätigt. Echte fehlende Werte sind selten, aber `0` wird als Standardwert verwendet und verdeckt möglicherweise fehlende Information.

    **Findings:**

    - Warum fehlt `lastSent` bei 1'631 Notifications? Haben diese Cases einen anderen Verlauf?
    - Cases mit `amount = 0` inspizieren.
    - Die 3 *Payment*-Events mit `paymentAmount = 0` inspizieren: Gehören sie zu den 2 Events mit `totalPaymentAmount = 0`? (relevant für Task 2.4b)
    - Unterscheiden sich Cases mit `expense = 0` im weiteren Verlauf, z. B. bei *Insert Fine Notification*?
    - *Empfehlung Datenerfassung:* Nicht erfasste Werte als leer (`NULL`) statt als `0` speichern, damit "nicht vorhanden" und "nicht erfasst" unterscheidbar sind. `matricola` korrekt befüllen oder entfernen.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 2.2b – Hypothese

    Wir erwarten, dass die Geldbeträge mehreren Aktivitäten gemeinsam sind: `amount` bei *Create Fine* (ursprüngliche Busse) und *Add penalty* (Busse mit Zuschlag), `totalPaymentAmount` bei *Create Fine* und *Payment*. Fachliche Attribute wie `points` oder `vehicleClass` sollten exklusiv bei *Create Fine* vorkommen. `totalPaymentAmount` ist laut Namen kumulativ; bei `amount` vermuten wir, dass es bei *Add penalty* den neuen Gesamtbetrag (also einen kumulativen Wert) enthält.
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
    ### Task 2.2b – Ergebnis

    Es gibt vier geteilte (nicht-globale) Attribute:

    | Attribut | Aktivitäten | Typ | Klassifikation |
    |---|---|---|---|
    | `totalPaymentAmount` | Create Fine, Payment | numerisch | **case-kumulativ** |
    | `amount` | Create Fine, Add penalty | numerisch | **case-kumulativ** |
    | `org:resource` | Create Fine, Appeal to Judge | kategorial | – |
    | `dismissal` | Create Fine, Send Appeal to Prefecture, Appeal to Judge | kategorial | – |

    **`amount`:** Bei *Add penalty* beträgt `amount` fast immer rund das **Doppelte** des Betrags bei *Create Fine* (Verhältnis 1.96–2.06 in den häufigsten Fällen). Das Attribut enthält also den neuen Gesamtbetrag inklusive Strafzuschlag und nicht nur den Zuschlag selbst. Es ist damit kumulativ innerhalb eines Cases.

    **`totalPaymentAmount`:** In Cases mit mehreren Zahlungen entspricht `totalPaymentAmount` der Summe der bisherigen `paymentAmount`-Werte (z. B. Case A10009: 35 + 22 = 57). Es ist damit kumulativ innerhalb eines Cases; das inkrementelle Gegenstück ist `paymentAmount`. Ob die Summe in allen Cases stimmt, prüfen wir in Task 2.4b.

    **Fazit:** Die Hypothese ist für die numerischen Attribute bestätigt. Nicht erwartet hatten wir, dass auch `org:resource` und `dismissal` geteilt sind. Bei `dismissal` ist das plausibel, da bei den Einsprache-Aktivitäten über eine Aufhebung entschieden wird.

    **Findings:**

    - Der Strafzuschlag verdoppelt die Busse nicht exakt (Verhältnisse von 1.96 bis 2.06, Ausreisser bei 2.5 und 4). Mögliche Ursachen: Rundung, unterschiedliche Regeln je Artikel oder zusätzliche Gebühren. Weiter untersuchen.
    - `org:resource` ist nur bei *Create Fine* und *Appeal to Judge* erfasst. Für alle anderen Schritte ist nicht nachvollziehbar, wer sie ausgeführt hat. *Empfehlung Datenerfassung:* Ressource bei allen Aktivitäten erfassen.
    - Die Benennung ist uneinheitlich: `totalPaymentAmount` zeigt im Namen an, dass es kumulativ ist, `amount` nicht. *Empfehlung:* z. B. in `totalFineAmount` umbenennen.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 2.3 – Case-Inspektion

    Wir wählen Case **A10009**, weil er laut Task 2.2b mehrere Zahlungen enthält und damit viele Attribute im Zusammenspiel zeigt.

    **Hypothese:** Wir erwarten den typischen Ablauf einer nicht sofort bezahlten Busse: *Create Fine* → *Send Fine* (mit Versandkosten) → *Insert Fine Notification* → *Add penalty* (Busse verdoppelt, da nicht fristgerecht bezahlt) → Zahlungen in Raten, bis der Gesamtbetrag aus Busse, Zuschlag und Kosten beglichen ist.
    """)
    return


@app.cell
def _(ACTIVITY, CASE_ID, TIMESTAMP, event_log):
    _case_id = 'A10009'
    _cols = [TIMESTAMP, ACTIVITY, 'amount', 'expense', 'paymentAmount', 'totalPaymentAmount',
             'points', 'article', 'vehicleClass', 'notificationType', 'lastSent',
             'dismissal', 'org:resource', 'matricola']
    case_2_3 = event_log[event_log[CASE_ID] == _case_id][_cols].copy()
    case_2_3[TIMESTAMP] = case_2_3[TIMESTAMP].dt.tz_convert('Europe/Rome').dt.date
    print(case_2_3.to_string())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 2.3 – Ergebnis: Case A10009

    - **20.03.2007 – Create Fine:** Eine Busse von **22 €** wird ausgestellt, gestützt auf Artikel 7, für ein Fahrzeug der Klasse A. Es gibt keinen Punkteabzug (`points = 0`). Erfasst wurde sie von Ressource 537. `dismissal = NIL` ist der Anfangswert (keine Aufhebung), `totalPaymentAmount = 0` (noch nichts bezahlt).
    - **17.07.2007 – Send Fine:** Die Busse wird erst **119 Tage** nach der Ausstellung verschickt. Dabei fallen **13 €** Versandkosten (`expense`) an.
    - **23.07.2007 – Insert Fine Notification:** **6 Tage** nach dem Versand wird die Zustellung registriert. Empfänger ist der Fahrzeughalter (`notificationType = P`). `lastSent` hat ebenfalls den Wert P.
    - **21.09.2007 – Add penalty:** Genau **60 Tage** nach der Zustellung wird ein Strafzuschlag erhoben. `amount` steigt auf **44 €**, also auf das Doppelte der ursprünglichen Busse. Das passt zu einer 60-tägigen Zahlungsfrist, die verstrichen ist, ohne dass bezahlt wurde.
    - **01.10.2007 – Payment:** 10 Tage später zahlt der Halter **35 €** (`totalPaymentAmount = 35`). Das entspricht genau der ursprünglichen Busse plus Versandkosten (22 + 13).
    - **31.10.2007 – Payment:** Einen Monat später folgt eine zweite Zahlung von **22 €**. Damit sind insgesamt **57 €** bezahlt, was exakt dem geschuldeten Gesamtbetrag entspricht: 44 € (Busse inkl. Zuschlag) + 13 € (Kosten). Der Case ist abgeschlossen.

    **Interpretation:** Die Hypothese ist bestätigt. Der Case folgt dem erwarteten Ablauf, und die Beträge sind konsistent: `amount` ist kumulativ (Busse inkl. Zuschlag), `totalPaymentAmount` summiert die Zahlungen korrekt, und am Ende ist kein Betrag mehr offen. Die erste Zahlung entspricht genau dem Betrag *ohne* Zuschlag. Vermutlich hat der Halter zunächst nur die ursprüngliche Forderung beglichen, ohne vom Zuschlag zu wissen, und den Zuschlag dann nachbezahlt. Der ganze Case dauert **225 Tage**, davon entfallen allein 119 Tage auf die Zeit bis zum Versand.

    **Findings:**

    - Zwischen *Create Fine* und *Send Fine* liegen fast 4 Monate. Wie lange dauert das im Durchschnitt, und gibt es gesetzliche Fristen dafür? (Kandidat für die Performance-Analyse in Session 6)
    - `lastSent` (Bedeutung unbekannt) stimmt in diesem Case mit `notificationType` überein (P). Eine Kreuztabelle über alle 79'860 *Insert Fine Notification*-Events zeigt aber, dass das nicht generell gilt: Nur in rund 58 % der Fälle sind die Werte gleich. `lastSent` hat zudem einen zusätzlichen Wert **N** (30'313 Events, fast alle bei `notificationType = P`), und in 1'380 Fällen steht `notificationType = P` mit `lastSent = C`, umgekehrt nie. Das Attribut ist also nicht redundant, seine Bedeutung bleibt aber unklar. *Empfehlung Datenerfassung:* Attribute und ihre Wertebereiche dokumentieren.
    - Zahlen Offender nach einem Zuschlag häufig zuerst nur den ursprünglichen Betrag? Das könnte auf eine unklare Kommunikation des Zuschlags hindeuten (Verbesserungsvorschlag für den Prozess).
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
    """)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
