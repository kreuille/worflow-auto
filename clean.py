"""
clean.py — Remplace les secrets par des placeholders avant un commit.

Utilise un fichier .env pour lire les vrais secrets.
Ne contient AUCUN secret en dur.

Usage :
  1. Copie env.example vers .env et remplis tes valeurs
  2. python clean.py          → remplace secrets par placeholders
  3. python clean.py --inject → remplace placeholders par secrets (pour dev local)
"""

import os, sys, glob

ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")


def load_env(path):
    """Charge les variables depuis un fichier .env (format KEY=VALUE)."""
    env = {}
    if not os.path.exists(path):
        return env
    with open(path, encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip()
    return env


def get_mapping(env):
    """Construit le mapping secret_reel → placeholder depuis le .env."""
    mapping = {}
    pairs = [
        ("ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_API_KEY"),
        ("N8N_API_KEY", "YOUR_N8N_API_KEY"),
        ("N8N_URL", "YOUR_N8N_URL"),
        ("AUTODEBUG_WORKFLOW_ID", "YOUR_AUTODEBUG_WORKFLOW_ID"),
        ("TELEGRAM_CHAT_ID", "TON_TELEGRAM_CHAT_ID"),
        ("GENERATOR_WORKFLOW_ID", "YOUR_GENERATOR_WORKFLOW_ID"),
        ("PROJECT_ID", "YOUR_PROJECT_ID"),
    ]
    for env_key, placeholder in pairs:
        value = env.get(env_key, "")
        if value and value != placeholder:
            mapping[value] = placeholder
    return mapping


def find_files():
    """Trouve tous les JSON et HTML récursivement, exclut .git et .env."""
    files = glob.glob("**/*.json", recursive=True) + glob.glob("**/*.html", recursive=True)
    return [f for f in files if ".git" not in f and ".env" not in f]


def replace_in_files(files, mapping, direction="clean"):
    """Remplace dans les fichiers. direction='clean' ou 'inject'."""
    if direction == "inject":
        mapping = {v: k for k, v in mapping.items()}

    changed_count = 0
    for f in files:
        with open(f, encoding="utf-8") as fp:
            content = fp.read()
        original = content
        for find, replace in mapping.items():
            content = content.replace(find, replace)
        if content != original:
            with open(f, "w", encoding="utf-8") as fp:
                fp.write(content)
            print(f"  \u2713 nettoyé — {f}")
            changed_count += 1
        else:
            print(f"    inchangé — {f}")
    return changed_count


def verify_no_secrets(files, mapping):
    """Vérifie qu'aucun secret ne reste dans les fichiers."""
    found = False
    for f in files:
        with open(f, encoding="utf-8") as fp:
            content = fp.read()
        for secret in mapping:
            if secret in content:
                print(f"  \u26a0\ufe0f  SECRET TROUVÉ dans {f} : {secret[:20]}...")
                found = True
    return found


def main():
    inject_mode = "--inject" in sys.argv

    env = load_env(ENV_FILE)
    if not env:
        print(f"Erreur : fichier .env introuvable ou vide ({ENV_FILE})")
        print("Copie env.example vers .env et remplis tes valeurs.")
        sys.exit(1)

    mapping = get_mapping(env)
    if not mapping:
        print("Aucun secret trouvé dans .env — rien à faire.")
        sys.exit(0)

    files = find_files()
    direction = "inject" if inject_mode else "clean"
    action = "Injection des secrets" if inject_mode else "Nettoyage des secrets"

    print(f"\n{action} ({len(mapping)} mappings, {len(files)} fichiers)...\n")
    changed = replace_in_files(files, mapping, direction)

    if not inject_mode:
        print(f"\nVérification finale...")
        has_leaks = verify_no_secrets(files, mapping)
        if has_leaks:
            print("\n\u274c Des secrets sont encore présents !")
            sys.exit(1)

    print(f"\nFait. {changed} fichier(s) modifié(s).")


if __name__ == "__main__":
    main()
