import pytest
from src.layer2.guard import validate, GuardError

ALLOWED = {"collections_cases", "customers"}
PROT = {"gender_code"}


@pytest.mark.parametrize("sql", [
    "DROP TABLE customers",
    "DELETE FROM customers",
    "UPDATE customers SET segment='x'",
    "INSERT INTO customers VALUES (1)",
    "CREATE TABLE t AS SELECT 1",
    "ALTER TABLE customers ADD COLUMN x INT",
    "SELECT 1; DROP TABLE customers",
    "SELECT * FROM hidden.benchmark_dev_answers",
    "SELECT * FROM raw.customers",
    "SELECT * FROM read_csv('labels/benchmark_dev_answers.csv')",
    "SELECT * FROM benchmark_questions",
    "SELECT gender_code, count(*) FROM customers GROUP BY 1",
    "COPY customers TO 'x.csv'",
    "ATTACH 'x.db'",
    "PRAGMA table_info('customers')",
    "INSTALL httpfs",
])
def test_blocked(sql):
    with pytest.raises(GuardError):
        validate(sql, ALLOWED, 100, PROT)


def test_allowed_and_limited():
    out = validate("SELECT segment, count(*) n FROM customers GROUP BY 1", ALLOWED, 100, PROT)
    assert "LIMIT 100" in out


def test_cte_ok():
    out = validate("WITH x AS (SELECT * FROM collections_cases) SELECT count(*) FROM x", ALLOWED, 100, PROT)
    assert "LIMIT" in out
