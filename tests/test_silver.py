"""Silver normalisers (DuckDB macros) and table rules on tiny in-memory tables."""
import duckdb
import pytest
from src.layer1.silver import MACROS, DFI0812_DETECT, build_table


@pytest.fixture()
def con():
    c = duckdb.connect()
    c.execute(MACROS)
    return c


def v(con, sql, *args):
    return con.execute(f"SELECT {sql}", list(args)).fetchone()[0]


@pytest.mark.parametrize("raw,want", [
    ("416-555-0199", "+14165550199"), ("(613) 943-2548", "+16139432548"), ("4163466908", "+14163466908"),
    ("+1 514 368 3648", "+15143683648"), ("438.987.9848", "+14389879848"), ("+1 (365) 881 7097", "+13658817097"),
    ("418-330-612", None),            # 9 digits: truncated, not guessable
    ("+1 204 889 694", None),         # truncated number behind a +1 prefix (area code would start with 1)
    ("1234567890", None),             # area code cannot start with 1
    ("367897xxx58", None),            # masked card phone
    (None, None)])
def test_norm_phone(con, raw, want):
    assert v(con, "norm_phone(?)", raw) == want


def test_phone_mask(con):
    assert v(con, "phone_mask(?)", "367897XXX58") == "367897xxx58"
    assert v(con, "phone_mask(?)", "4165550199") is None


@pytest.mark.parametrize("raw,want", [
    ("H3J 4K1", "H3J 4K1"), ("B3L5E4", "B3L 5E4"), ("vOn6c8", "V0N 6C8"), ("LOC 7B0", "L0C 7B0"),
    ("T3V 1AO", "T3V 1A0"), ("L5E OY9", "L5E 0Y9"), ("h3j-4k1", "H3J 4K1"), ("12345", None), ("ABCDEF", None),
    (None, None)])
def test_norm_postal(con, raw, want):
    assert v(con, "norm_postal(?)", raw) == want


def test_email_and_province(con):
    assert v(con, "norm_email(?)", "  ASHLEEMORGAN06@EXAMPLE.CA ") == "ashleemorgan06@example.ca"
    assert v(con, "norm_email(?)", "   ") is None
    for raw, want in [("Ont.", "ON"), ("B.C.", "BC"), ("Alta.", "AB"), ("Quebec", "QC"), ("PQ", "QC"),
                      ("Man.", "MB"), ("N.S.", "NS"), ("on", "ON"), ("YT", "YT")]:
        assert v(con, "norm_province(?)", raw) == want


def test_cif_padding(con):
    assert v(con, "pad_cif(?)", "42328458") == "0042328458"
    assert v(con, "pad_cif(?)", "7654278") == "0007654278"
    assert v(con, "pad_cif(?)", "0041677698") == "0041677698"     # already 10 digits: unchanged
    assert v(con, "pad_cif(?)", "CX123") == "CX123"               # not a CIF: unchanged
    assert v(con, "pad_cif(?)", None) is None


def test_crm_dob_unambiguous_formats(con):
    assert str(v(con, "crm_dob_best(?, NULL)", "2007-10-27")) == "2007-10-27"
    assert str(v(con, "crm_dob_best(?, NULL)", "11/21/1980")) == "1980-11-21"   # only MM/DD is valid
    assert str(v(con, "crm_dob_best(?, NULL)", "21/11/1980")) == "1980-11-21"   # only DD/MM is valid
    assert str(v(con, "crm_dob_best(?, NULL)", "Aug 06 1979")) == "1979-08-06"
    assert v(con, "crm_dob_ambiguous(?)", "11/21/1980") is False
    assert v(con, "crm_dob_alt(?, NULL)", "11/21/1980") is None
    assert v(con, "crm_dob_best(?, NULL)", "not a date") is None


def test_crm_dob_ambiguous_keeps_both_readings(con):
    raw = "03/04/1985"                      # 3 Apr (DD/MM) or 4 Mar (MM/DD)
    assert v(con, "crm_dob_ambiguous(?)", raw) is True
    # CRM's own date_of_birth picks the reading; the other one is kept as dob_alt
    assert str(v(con, "crm_dob_best(?, DATE '1985-03-04')", raw)) == "1985-03-04"
    assert str(v(con, "crm_dob_alt(?, DATE '1985-03-04')", raw)) == "1985-04-03"
    # no CRM date: day-first best guess
    assert str(v(con, "crm_dob_best(?, NULL)", raw)) == "1985-04-03"
    assert str(v(con, "crm_dob_alt(?, NULL)", raw)) == "1985-03-04"
    assert v(con, "crm_dob_ambiguous(?)", "05/05/1985") is False   # same either way


def _run():
    return {"run_ts": "2026-10-03 00:00:00", "sample_n": None, "run_id": "test"}


def _fix_log(con):
    con.execute("CREATE SCHEMA silver; CREATE TABLE silver.fix_log (run_ts TIMESTAMP, table_name VARCHAR, "
                "rule VARCHAR, rows_affected BIGINT, rows_in BIGINT, example_before VARCHAR, "
                "example_after VARCHAR, sample_n BIGINT, run_id VARCHAR)")


def test_dfi0812_detection_and_repair(con):
    _fix_log(con)
    con.execute("""CREATE TABLE external AS SELECT * FROM (VALUES
        ('EQ-1', 'BUR_202609', TIMESTAMP '2026-09-16 06:00', '0000000001', 0, 1, 2, 9),
        ('EQ-2', 'BUR_202609', TIMESTAMP '2026-09-16 06:00', '0000000002', 9, 0, 1, 2),
        ('EQ-3', 'BUR_202609', TIMESTAMP '2026-09-16 06:00', '0000000003', 11, 1, 1, 3),
        ('EQ-4', 'BUR_202609', TIMESTAMP '2026-09-16 06:00', '0000000004', 2, 2, 3, 8))
        t(bureau_request_id, batch_id, file_received_ts, bank_subject_ref,
          inquiries_hard_3m, inquiries_hard_6m, inquiries_hard_12m, inquiries_soft_12m)""")
    # EQ-2 and EQ-3 were loaded rotated (true values 0,1,2,9 and 1,1,3,11); EQ-1 and EQ-4 are clean
    detected = con.execute(f"SELECT list(bureau_request_id ORDER BY 1) FROM external WHERE {DFI0812_DETECT}").fetchone()[0]
    assert detected == ["EQ-2", "EQ-3"]
    build_table(con, "external", _run(), None, log=lambda *_: None)
    rows = {r[0]: r[1:] for r in con.execute("""SELECT bureau_request_id, inquiries_hard_3m, inquiries_hard_6m,
        inquiries_hard_12m, inquiries_soft_12m, dq_flags, dfi0812_as_loaded FROM silver.external""").fetchall()}
    assert rows["EQ-1"][:4] == (0, 1, 2, 9) and rows["EQ-1"][4] == []
    assert rows["EQ-2"][:4] == (0, 1, 2, 9) and rows["EQ-2"][4] == ["repaired_DFI0812"]
    assert rows["EQ-2"][5] == "[9,0,1,2]"                        # values as loaded are kept for audit
    assert rows["EQ-3"][:4] == (1, 1, 3, 11)
    assert rows["EQ-4"][:4] == (2, 2, 3, 8)
    for r in rows.values():                                       # every row is now consistent
        assert r[0] <= r[1] <= r[2]
    logged = dict(con.execute("SELECT rule, rows_affected FROM silver.fix_log").fetchall())
    assert logged["flag:repaired_DFI0812"] == 2


def test_contact_history_drift_orphans_and_duplicates(con):
    _fix_log(con)
    con.execute("""CREATE TABLE collections_cases AS SELECT 'CS-1' AS case_id;
        CREATE TABLE contact_history AS SELECT * FROM (VALUES
            ('CT-1', 'CS-1', 'call', NULL, 'NA', 'outbound_call', 'A-1', 'CH_20260928', TIMESTAMP '2026-09-28 02:00'),
            ('CT-2', 'CS-1', 'call', NULL, 'NA', 'outbound_call', 'A-1', 'CH_20260928', TIMESTAMP '2026-09-28 02:00'),
            ('CT-3', 'CS-1', NULL, 'sms', 'SENT', 'sms_reminder', 'A-1', 'CH_20260928', TIMESTAMP '2026-09-28 02:00'),
            ('CT-4', 'CS-9', 'email', NULL, 'SENT', 'email_reminder', 'A-1', 'CH_20260928', TIMESTAMP '2026-09-28 02:00'))
            t(contact_id, case_id, channel, channel_v2, outcome_code, treatment_code, crm_customer_id, batch_id, extract_ts);
        CREATE TABLE agent_notes AS SELECT 'CT-2' AS contact_id;
        CREATE TABLE promises_to_pay AS SELECT NULL::VARCHAR AS contact_id;
        CREATE TABLE call_transcripts AS SELECT NULL::VARCHAR AS contact_id;""")
    # CT-1/CT-2 identical except id, CT-2 referenced by a note; CT-3 written after the channel_v2 rename;
    # CT-4 points to a case that does not exist
    build_table(con, "contact_history", _run(), None, log=lambda *_: None)
    rows = {r[0]: r[1:] for r in con.execute(
        "SELECT contact_id, channel, outcome_code, treatment_code, dq_flags FROM silver.contact_history").fetchall()}
    assert set(rows) == {"CT-2", "CT-3", "CT-4"}                  # referenced copy survives
    assert rows["CT-2"][1] == "NA"                                # 'NA' = no answer, kept as a code
    assert rows["CT-2"][2] == "outbound_call"                     # canonical lower-case code untouched
    assert rows["CT-3"][0] == "sms" and "channel_from_v2" in rows["CT-3"][3]
    assert "orphan_case" in rows["CT-4"][3]
    assert "channel_v2" not in [r[0] for r in con.execute("DESCRIBE silver.contact_history").fetchall()]
    assert con.execute("SELECT removed_id, kept_id FROM silver.contact_history_duplicates").fetchall() == [("CT-1", "CT-2")]


def test_agent_note_placeholders(con):
    _fix_log(con)
    con.execute("""CREATE TABLE agent_notes AS SELECT * FROM (VALUES
        ('N-1', 'NA', 'NOTES_20260928', TIMESTAMP '2026-09-01'), ('N-2', 'LM', 'NOTES_20260928', TIMESTAMP '2026-09-01'),
        ('N-3', 'Customer lost job, NA for now', 'NOTES_20260928', TIMESTAMP '2026-09-01'),
        ('N-4', '-', 'NOTES_20260928', TIMESTAMP '2026-09-01')) t(note_id, note_text, batch_id, last_edited_ts)""")
    build_table(con, "agent_notes", _run(), None, log=lambda *_: None)
    rows = dict(con.execute("SELECT note_id, note_text FROM silver.agent_notes").fetchall())
    assert rows == {"N-1": None, "N-2": "LM", "N-3": "Customer lost job, NA for now", "N-4": None}
    assert str(con.execute("SELECT max(extract_ts) FROM silver.agent_notes").fetchone()[0]) == "2026-09-28 00:00:00"
