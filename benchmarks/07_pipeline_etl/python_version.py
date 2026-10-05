# Benchmark 07: Python Inverted Function Call Pipeline

raw_data = list(range(20000))

# Inverted nesting: list(map(..., filter(...)))
res = list(
    map(
        lambda x: x * 3 + 1,
        filter(
            lambda x: x % 3 == 0,
            raw_data
        )
    )
)

print(f"ETL Count: {len(res)}, First: {res[0]}, Last: {res[-1]}")
