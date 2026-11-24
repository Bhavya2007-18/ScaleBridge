#!/usr/bin/env python3
"""CLI utility to create and verify ScaleBridge Bio database backups.

Usage:
    python scripts/backup_db.py [--dest ./var/backups] [--verify]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.backup import backup_database, verify_backup_integrity


def main() -> None:
    parser = argparse.ArgumentParser(description="ScaleBridge Bio Database Backup Utility")
    parser.add_argument("--dest", default="./var/backups", help="Directory where backups are saved")
    parser.add_argument("--verify", action="store_true", help="Verify backup integrity immediately after creation")
    args = parser.parse_args()

    print(f"[*] Initiating database backup to: {args.dest}")
    archive_path = backup_database(args.dest)
    print(f"[+] Backup successfully generated: {archive_path}")

    if args.verify:
        valid = verify_backup_integrity(archive_path)
        if valid:
            print("[+] SHA-256 and archive integrity verified.")
        else:
            print("[-] Backup verification failed!", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
