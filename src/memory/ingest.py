"""Load the company documents, cut them into chunks, and store them in Qdrant.

Run it from the project root:

    python -m src.memory.ingest            # add or update documents
    python -m src.memory.ingest --rebuild  # delete everything first

Each chunk gets a stable id made from its file and position, so running
the command again updates chunks instead of adding duplicates.
"""

import argparse
import uuid
from collections.abc import Callable
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.settings import get_settings
from src.memory import long_term
from src.utils.logger import get_logger

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

logger = get_logger(__name__)


def ingest(folder: Path, rebuild: bool = False) -> int:
    """Store every supported file in `folder`. Returns the number of chunks."""
    if rebuild:
        long_term.reset_collection()
    chunks = split_documents(load_documents(folder))
    if chunks:
        long_term.add_documents(chunks, ids=[_chunk_id(chunk) for chunk in chunks])
    return len(chunks)


def load_documents(folder: Path) -> list[Document]:
    """Read every file whose extension has a loader. Other files are skipped."""
    documents = []
    for path in sorted(folder.rglob("*")):
        loader = LOADERS.get(path.suffix.lower())
        if loader is None or not path.is_file():
            continue
        source = path.relative_to(folder).as_posix()
        documents.append(Document(page_content=loader(path), metadata={"source": source}))
    return documents


def split_documents(documents: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP, add_start_index=True
    )
    return splitter.split_documents(documents)


def _chunk_id(chunk: Document) -> str:
    key = f"{chunk.metadata['source']}:{chunk.metadata['start_index']}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, key))


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_pdf(path: Path) -> str:
    import pymupdf

    with pymupdf.open(path) as pdf:
        return "\n".join(page.get_text() for page in pdf)


def _read_docx(path: Path) -> str:
    import docx

    return "\n".join(paragraph.text for paragraph in docx.Document(str(path)).paragraphs)


# Which function reads which file type. A new file type = one new line.
LOADERS: dict[str, Callable[[Path], str]] = {
    ".md": _read_text,
    ".txt": _read_text,
    ".pdf": _read_pdf,
    ".docx": _read_docx,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Load company documents into Qdrant.")
    parser.add_argument("--rebuild", action="store_true", help="delete stored documents first")
    parser.add_argument("--source", type=Path, help="folder to read (default: KNOWLEDGE_BASE_DIR)")
    args = parser.parse_args()

    folder = args.source or get_settings().knowledge_base_dir
    count = ingest(folder, rebuild=args.rebuild)
    logger.info("Stored %d chunks from %s", count, folder)


if __name__ == "__main__":
    main()
