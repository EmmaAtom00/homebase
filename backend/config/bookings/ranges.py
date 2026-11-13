from datetime import UTC, date, datetime, time

from django.db.backends.postgresql.psycopg_any import DateTimeTZRange


def stay_range(check_in: date, check_out: date) -> DateTimeTZRange:
    return DateTimeTZRange(
        datetime.combine(check_in, time.min, tzinfo=UTC),
        datetime.combine(check_out, time.min, tzinfo=UTC),
        bounds="[)",
    )
