"""Policy-document retrieval for questions answered from reference documents.

Only the current version of each document is searched (superseded_by empty), so the
answer never quotes a retired policy. Chunks keep doc_id, version and section for citations."""
from __future__ import annotations
import pickle, re
from pathlib import Path
import pandas as pd
from rank_bm25 import BM25Okapi

_TOK = re.compile(r"[a-zà-ÿ0-9]+")


def _read(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        return "\n".join((p.extract_text() or "") for p in PdfReader(str(path)).pages)
    return path.read_text(encoding="utf-8", errors="ignore")


def _chunks(text: str, size: int = 1200):
    """Split at headings so each chunk carries the section it came from."""
    section, buf = "intro", []

    def flush():
        body = "\n".join(b for b in buf if b).strip()
        for i in range(0, len(body), size):
            yield section, body[i:i + size]

    for para in re.split(r"\n\s*\n", text):
        head = re.match(r"\s*(#+\s*.+|\d+(\.\d+)*\s+[A-Z].{0,80})\s*$", para.split("\n")[0])
        if head and buf:
            yield from flush()
            buf = []
        if head:
            section = head.group(1).strip("# ").strip()[:60]
        buf.append(para.strip())
    if buf:
        yield from flush()


class DocIndex:
    def __init__(self, con, data_dir: str, cache: str):
        self.cache = Path(cache)
        if self.cache.exists():
            self.chunks = pickle.loads(self.cache.read_bytes())
        else:
            self.chunks = self._build(con, Path(data_dir))
            self.cache.write_bytes(pickle.dumps(self.chunks))
        self.bm25 = BM25Okapi([_TOK.findall(c["text"].lower()) for c in self.chunks]) if self.chunks else None

    def _build(self, con, root: Path) -> list[dict]:
        try:
            docs = con.execute("SELECT * FROM main.reference_documents").df()
        except Exception:
            return []
        out = []
        for _, d in docs.iterrows():
            current = pd.isna(d.get("superseded_by")) or str(d.get("superseded_by")).strip() in ("", "nan", "None")
            fp = str(d.get("file_path", ""))
            path = root / fp
            if not path.exists():
                hits = list(root.rglob(Path(fp).name)) if fp else []
                if not hits:
                    continue
                path = hits[0]
            for sec, txt in _chunks(_read(path)):
                out.append({"doc_id": d.get("doc_id"), "title": d.get("title"), "version": d.get("version"),
                            "language": d.get("language"), "current": current, "section": sec, "text": txt})
        return out

    def search(self, query: str, k: int = 5, current_only: bool = True) -> list[dict]:
        if not self.bm25:
            return []
        q = _TOK.findall(query.lower())
        scores = self.bm25.get_scores(q)
        qs = set(q)
        cand = [i for i, c in enumerate(self.chunks)
                if (c["current"] or not current_only) and qs & set(_TOK.findall(c["text"].lower()))]
        cand.sort(key=lambda i: (-scores[i], -len(qs & set(_TOK.findall(self.chunks[i]["text"].lower())))))
        return [self.chunks[i] for i in cand[:k]]
