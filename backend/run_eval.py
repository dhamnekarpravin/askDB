import asyncio
import json
import sys

from app.executor import run_query
from app.llm import LLMError
from app.sql_generator import generate_valid_sql


def normalize(result: dict):
    """Compare values only, ignoring column names and row order."""
    rows = []
    for row in result["rows"]:
        values = tuple(
            round(float(v), 2) if isinstance(v, (int, float)) else str(v)
            for v in row.values()
        )
        rows.append(values)
    return sorted(rows)


async def main():
    with open("eval_set.json", encoding="utf-8") as f:
        cases = json.load(f)

    passed = 0
    for i, case in enumerate(cases, 1):
        q = case["question"]
        try:
            expected = normalize(run_query(case["reference_sql"]))
            got = await generate_valid_sql(q)
            ok = normalize(got) == expected
            note = f"attempts={got['attempts']}"
        except LLMError as e:
            ok, note = False, f"error: {e.message}"
        except Exception as e:
            ok, note = False, f"error: {e}"

        passed += ok
        print(f"{i:>2}. {'PASS' if ok else 'FAIL'}  {q}  ({note})")
        if not ok and "got" in locals():
            print(f"      model SQL: {got['sql']}")

        await asyncio.sleep(2)  # be gentle with free-model rate limits

    print(f"\nAccuracy: {passed}/{len(cases)} = {passed / len(cases):.0%}")


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))