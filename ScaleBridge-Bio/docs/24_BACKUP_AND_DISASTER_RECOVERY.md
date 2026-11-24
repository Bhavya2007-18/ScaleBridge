# 24 — Database Backup and Disaster Recovery Runbook

**Purpose:** Document the automated database backup, validation, and restoration strategy for ScaleBridge Bio.  
**Domain:** F — Infrastructure, Security & Quality  
**Owner:** Person 4 (Reporting, DevOps & Quality Lead)  

---

## 1. Overview & Objectives

In bioprocess decision support, customer process passport data, vessel capability envelopes, and historical assessments constitute high-value proprietary intellectual property.

The ScaleBridge Bio disaster recovery architecture guarantees:
- **Recovery Point Objective (RPO):** < 24 hours for automated cold dumps; point-in-time recovery on Render managed PostgreSQL.
- **Recovery Time Objective (RTO):** < 30 minutes to restore a database from an encrypted, compressed backup snapshot.
- **Integrity Guarantee:** Every backup generates a cryptographic SHA-256 sidecar checksum (`.sha256`) that is validated before and after restoration.

---

## 2. Backup Utility (`app/core/backup.py`)

The automated backup tool supports both local development (SQLite) and production (PostgreSQL 16):

```bash
# Execute manual backup with immediate verification
python ScaleBridge-Bio/scripts/backup_db.py --dest ./var/backups --verify
```

### Key Operations:
1. **Timestamping & Format:** Creates archives named `scalebridge_[pg_]backup_YYYYMMDD_HHMMSSZ.[db|sql].gz`.
2. **Compression:** In-memory streaming gzip compression minimizing disk I/O and storage volume.
3. **Cryptographic Checksum:** Writes a sidecar `.sha256` file containing the hexadecimal hash.
4. **Non-blocking Execution:** Runs against PostgreSQL using `pg_dump --clean --if-exists` without taking the database offline.

---

## 3. Production Render Backup Strategy

On Render managed PostgreSQL 16:
1. **Automated Platform Backups:** Render executes automated daily snapshots preserved in secure cloud object storage.
2. **Secondary Offsite Replication:** An automated cron task runs `backup_db.py` daily at `02:00 UTC` and mirrors compressed snapshots into the S3 bucket (`scalebridge-files/backups/`).
3. **Retention Policy:**
   - Daily backups retained for 30 days.
   - Weekly backups retained for 12 weeks.
   - Monthly backups retained for 12 months.

---

## 4. Restoration Runbook

### Scenario A: SQLite Restoration (Development / Staging)
```bash
# 1. Stop backend service
# 2. Decompress archive into database location
gunzip -c ./var/backups/scalebridge_backup_20261123_000000Z.db.gz > ./var/scalebridge.db
# 3. Restart server
make run
```

### Scenario B: PostgreSQL Restoration (Production)
```bash
# 1. Verify archive SHA-256 checksum
sha256sum -c scalebridge_pg_backup_20261123_000000Z.sql.gz.sha256

# 2. Restore into target PostgreSQL database
gunzip -c scalebridge_pg_backup_20261123_000000Z.sql.gz | psql "$DATABASE_URL"

# 3. Verify database connectivity and schema
curl -f http://localhost:8000/api/v1/health/ready
```

---

## 5. Security & Compliance
- Backup archives contain encrypted-at-rest data.
- Never commit backup archives (`*.db`, `*.sql`, `*.gz`) to Git (enforced via `.gitignore`).
- Only administrators (`org_admin`) and CI/CD service accounts have write access to backup targets.
