#!/usr/bin/env python3
"""
push_updates.py

Petit utilitaire local pour ajouter, committer et pousser vers GitHub les fichiers modifiés
dans ce dépôt.

Usage recommandé depuis la racine du projet :

    python push_updates.py --dry-run
    python push_updates.py --message "Add chapter 4 attention debug notes"

Exemples :

    # Voir ce qui serait poussé sans rien modifier
    python push_updates.py --dry-run

    # Ajouter tous les fichiers modifiés, créer un commit, pousser la branche courante
    python push_updates.py -m "Update chapter 4 experiments"

    # Pousser seulement certains fichiers
    python push_updates.py -m "Add attention debug traces" ch04/01_main-chapter-code/gpt.py

    # Créer/changer vers une branche de travail avant commit
    python push_updates.py --branch lab-ch04-attention-debug -m "Add chapter 4 attention debug traces"

    # Faire git pull --rebase avant de pousser
    python push_updates.py --pull-first -m "Update notes"

Ce script ne stocke aucun token GitHub. Il utilise ta configuration Git locale :
GitHub CLI, SSH, ou credential helper déjà configuré sur ton Mac.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


SENSITIVE_PATTERNS = [
    ".env",
    "id_rsa",
    "id_ed25519",
    "credentials",
    "secret",
    "secrets",
    "token",
    "apikey",
    "api_key",
    "private_key",
    "questrade",
]


def run(cmd: list[str], *, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess[str]:
    """Run a shell command safely without shell=True."""
    print("$", " ".join(cmd))
    return subprocess.run(
        cmd,
        text=True,
        capture_output=capture,
        check=check,
    )


def repo_root() -> Path:
    result = run(["git", "rev-parse", "--show-toplevel"], capture=True)
    return Path(result.stdout.strip())


def current_branch() -> str:
    result = run(["git", "branch", "--show-current"], capture=True)
    return result.stdout.strip()


def ensure_git_repo() -> None:
    try:
        run(["git", "rev-parse", "--is-inside-work-tree"], capture=True)
    except subprocess.CalledProcessError:
        print("Erreur : ce dossier ne semble pas être un dépôt Git.", file=sys.stderr)
        sys.exit(1)


def has_sensitive_name(path: str) -> bool:
    lower = path.lower()
    return any(pattern in lower for pattern in SENSITIVE_PATTERNS)


def get_changed_files() -> list[str]:
    result = run(["git", "status", "--porcelain"], capture=True)
    files: list[str] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        # Porcelain format: XY path, sometimes with rename "old -> new"
        raw = line[3:].strip()
        if " -> " in raw:
            raw = raw.split(" -> ", 1)[1].strip()
        files.append(raw)
    return files


def print_status() -> None:
    run(["git", "status", "--short"], check=False)


def confirm_sensitive(files: list[str], assume_yes: bool) -> None:
    suspicious = [f for f in files if has_sensitive_name(f)]
    if not suspicious:
        return

    print("\nAttention : certains fichiers ressemblent possiblement à des fichiers sensibles :")
    for f in suspicious:
        print(f"  - {f}")

    if assume_yes:
        print("Option --yes détectée : poursuite malgré l'avertissement.")
        return

    answer = input("Continuer quand même ? Tape exactement YES pour continuer : ")
    if answer != "YES":
        print("Arrêt volontaire. Aucun commit/push effectué.")
        sys.exit(1)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ajouter, committer et pousser les fichiers modifiés vers GitHub."
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Fichiers précis à ajouter. Si vide, ajoute tous les changements suivis/non suivis.",
    )
    parser.add_argument(
        "-m",
        "--message",
        default=None,
        help="Message de commit. Obligatoire sauf avec --dry-run.",
    )
    parser.add_argument(
        "--branch",
        default=None,
        help="Nom de branche à créer ou utiliser avant commit.",
    )
    parser.add_argument(
        "--remote",
        default="origin",
        help="Nom du remote Git. Défaut : origin.",
    )
    parser.add_argument(
        "--pull-first",
        action="store_true",
        help="Exécute git pull --rebase avant le commit/push.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Affiche ce qui serait fait, sans ajouter, committer ou pousser.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Ne demande pas de confirmation en cas de nom de fichier suspect.",
    )
    args = parser.parse_args()

    ensure_git_repo()
    root = repo_root()
    print(f"Racine du dépôt : {root}")
    print(f"Branche courante : {current_branch() or '(détachée ou inconnue)'}")

    changed = get_changed_files()
    if not changed:
        print("Aucun changement local détecté. Rien à pousser.")
        return 0

    print("\nChangements détectés :")
    print_status()

    selected_files = args.files if args.files else changed
    confirm_sensitive(selected_files, args.yes)

    if args.dry_run:
        print("\nMode dry-run : aucune action effectuée.")
        print("Fichiers qui seraient ajoutés :")
        for f in selected_files:
            print(f"  - {f}")
        if args.branch:
            print(f"Branche qui serait utilisée/créée : {args.branch}")
        if args.pull_first:
            print("Un git pull --rebase serait exécuté avant le commit.")
        print("Commande finale probable : git push -u origin <branche>")
        return 0

    if not args.message:
        print("Erreur : fournis un message de commit avec -m ou --message.", file=sys.stderr)
        print("Exemple : python push_updates.py -m \"Update chapter 4 notes\"", file=sys.stderr)
        return 2

    if args.branch:
        existing = run(["git", "branch", "--list", args.branch], capture=True).stdout.strip()
        if existing:
            run(["git", "checkout", args.branch])
        else:
            run(["git", "checkout", "-b", args.branch])

    branch = current_branch()
    if not branch:
        print("Erreur : impossible de déterminer la branche courante.", file=sys.stderr)
        return 2

    if args.pull_first:
        run(["git", "pull", "--rebase", args.remote, branch])

    if args.files:
        run(["git", "add", *args.files])
    else:
        run(["git", "add", "-A"])

    # Recheck staged changes before commit
    staged = run(["git", "diff", "--cached", "--name-only"], capture=True).stdout.strip()
    if not staged:
        print("Aucun changement indexé. Rien à committer.")
        return 0

    print("\nFichiers indexés :")
    print(staged)

    run(["git", "commit", "-m", args.message])
    run(["git", "push", "-u", args.remote, branch])

    print("\nTerminé : changements poussés vers GitHub.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
