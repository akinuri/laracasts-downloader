import os

def load_env_file(path=".env"):
    if not os.path.isfile(path):
        return
    with open(path, "r", encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())

def get_required_env(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            "Missing required %s. Copy .env.example to .env and fill in your Laracasts cookies." % name
        )
    return value
