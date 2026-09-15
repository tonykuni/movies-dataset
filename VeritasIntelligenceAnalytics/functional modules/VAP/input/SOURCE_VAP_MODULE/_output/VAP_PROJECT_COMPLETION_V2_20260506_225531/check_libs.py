import importlib.util
missing = [m for m in ["duckdb","pandas","pyarrow"] if importlib.util.find_spec(m) is None]
print(",".join(missing))
