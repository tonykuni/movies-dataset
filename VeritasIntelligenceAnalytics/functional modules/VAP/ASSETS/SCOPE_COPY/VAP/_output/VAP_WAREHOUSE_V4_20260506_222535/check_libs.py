import importlib.util
missing = [m for m in ["duckdb","pyarrow","pandas"] if importlib.util.find_spec(m) is None]
print(",".join(missing))
