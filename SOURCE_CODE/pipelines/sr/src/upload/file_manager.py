import hashlib, sqlite3, os, time, logging
from pathlib import Path
from typing import Optional
import anthropic

logger      = logging.getLogger(__name__)
DB_PATH     = Path(__file__).parent / "upload_registry.db"
BETA_HEADER = "files-api-2025-04-14"

class FileManager:
    def __init__(self, api_key: Optional[str] = None):
        self.client = anthropic.Anthropic(
            api_key=api_key or os.environ["ANTHROPIC_API_KEY"],
        )
        self._init_db()

    def _init_db(self):
        con = sqlite3.connect(DB_PATH)
        con.execute("""CREATE TABLE IF NOT EXISTS file_registry (
            sha256 TEXT PRIMARY KEY, file_id TEXT NOT NULL,
            filename TEXT, size_bytes INTEGER,
            uploaded_at TEXT DEFAULT (datetime('now')))""")
        con.commit(); con.close()

    def _lookup(self, sha256):
        con = sqlite3.connect(DB_PATH)
        row = con.execute("SELECT file_id FROM file_registry WHERE sha256=?",
                          (sha256,)).fetchone()
        con.close(); return row[0] if row else None

    def _register(self, sha256, file_id, filename, size_bytes):
        con = sqlite3.connect(DB_PATH)
        con.execute("INSERT OR REPLACE INTO file_registry VALUES (?,?,?,?,datetime('now'))",
                    (sha256, file_id, filename, size_bytes))
        con.commit(); con.close()

    def upload_pdf(self, pdf_path: Path) -> dict:
        content = pdf_path.read_bytes()
        sha256  = hashlib.sha256(content).hexdigest()
        existing = self._lookup(sha256)
        if existing:
            logger.info(f"[CACHE HIT] {pdf_path.name} -> {existing}")
            return {"file_id": existing, "filename": pdf_path.name,
                    "size_bytes": len(content), "sha256": sha256, "cached": True}
        logger.info(f"[UPLOAD] {pdf_path.name}")
        up = self.client.beta.files.upload(
            file=(pdf_path.name, content, "application/pdf"),
            betas=[BETA_HEADER])
        self._register(sha256, up.id, pdf_path.name, len(content))
        return {"file_id": up.id, "filename": pdf_path.name,
                "size_bytes": len(content), "sha256": sha256, "cached": False}

    def upload_directory(self, directory: Path, pattern="*.pdf") -> list[dict]:
        pdfs = sorted(directory.glob(pattern))
        if not pdfs: raise FileNotFoundError(f"No PDFs in {directory}")
        records = []
        for pdf in pdfs:
            records.append(self.upload_pdf(pdf)); time.sleep(0.1)
        return records

    def delete_file(self, file_id: str):
        self.client.beta.files.delete(file_id, betas=[BETA_HEADER])
        con = sqlite3.connect(DB_PATH)
        con.execute("DELETE FROM file_registry WHERE file_id=?", (file_id,))
        con.commit(); con.close()

    def list_remote_files(self):
        return list(self.client.beta.files.list(limit=500, betas=[BETA_HEADER]).data)

    def reconcile_registry(self):
        remote = {f.id for f in self.list_remote_files()}
        con    = sqlite3.connect(DB_PATH)
        rows   = con.execute("SELECT sha256, file_id FROM file_registry").fetchall()
        stale  = [(s,f) for s,f in rows if f not in remote]
        for sha, fid in stale:
            con.execute("DELETE FROM file_registry WHERE sha256=?", (sha,))
            logger.warning(f"[RECONCILE] Removed stale: {fid}")
        con.commit(); con.close()

def local_records(pdf_dir: Path, pattern: str = "*.pdf") -> list[dict]:
    """
    Build upload records from local PDF paths without calling any API.
    Produces the same dict structure as FileManager.upload_pdf() but sets
    file_id=None and adds pdf_path so downstream stages use vision fallback.
    """
    import hashlib
    pdfs = sorted(Path(pdf_dir).glob(pattern))
    if not pdfs:
        raise FileNotFoundError(f"No PDFs in {pdf_dir}")
    records = []
    for p in pdfs:
        content = p.read_bytes()
        records.append({
            "file_id":    None,
            "pdf_path":   str(p),
            "filename":   p.name,
            "size_bytes": len(content),
            "sha256":     hashlib.sha256(content).hexdigest(),
            "cached":     False,
        })
    return records
