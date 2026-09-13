param(
    [int]$Port = 8766
)

python -m uvicorn index:app --app-dir api --host 127.0.0.1 --port $Port
