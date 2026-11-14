import re

import toons


def schema_text_to_toon(schema_text: str) -> str:
    """Convert retrieved schema text into TOON via the official toons serializer."""
    lines = [line.strip() for line in (schema_text or "").splitlines() if line.strip()]
    if not lines:
        return toons.dumps({"tables": []})

    tables: list[dict[str, list[str] | str]] = []
    current: dict[str, list[str] | str] | None = None

    for line in lines:
        if line.startswith("Table: "):
            if current:
                tables.append(current)
            current = {
                "name": line.replace("Table: ", "", 1).strip(),
                "columns": [],
                "foreign_keys": [],
            }
            continue

        if current is None:
            continue

        if line.startswith("Columns: "):
            cols = line.replace("Columns: ", "", 1).strip()
            current["columns"] = [c.strip() for c in cols.split(",") if c.strip()]
            continue

        if line.startswith("Foreign keys: "):
            fks = line.replace("Foreign keys: ", "", 1).strip()
            current["foreign_keys"] = [fk.strip() for fk in fks.split(";") if fk.strip()]

    if current:
        tables.append(current)

    return toons.dumps({"tables": tables})


