import importlib.util
required = ["duckdb","pandas","pyarrow"]
missing = [m for m in required if importlib.util.find_spec(m) is None]
print(",".join(missing))
