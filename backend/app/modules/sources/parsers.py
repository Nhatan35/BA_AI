"""Bounded extraction only; documents are data and never approval/instructions."""

import csv
import importlib.metadata
import io
import json
import os
import subprocess
import sys
import unicodedata
import zipfile
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from threading import BoundedSemaphore
from typing import Protocol

from docx import Document
from docx.text.paragraph import Paragraph
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from pypdf import PdfReader

from app.core.config import get_settings
from app.core.errors import fail

FORMATS = {
    ".txt": ("text/plain", {"text/plain"}),
    ".md": ("text/markdown", {"text/markdown", "text/plain", "text/x-markdown"}),
    ".pdf": ("application/pdf", {"application/pdf"}),
    ".docx": (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    ),
    ".csv": ("text/csv", {"text/csv", "application/csv", "text/plain", "application/vnd.ms-excel"}),
    ".xlsx": (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
    ),
}


def validate_upload(filename: str, mime: str, content: bytes) -> tuple[str, str]:
    if (
        not filename
        or len(filename) > 240
        or any(c in filename for c in "/\\:")
        or any(ord(c) < 32 for c in filename)
    ):
        fail(422, "INVALID_FILENAME", "Use a simple filename without paths.")
    extension = Path(filename).suffix.lower()
    if extension not in FORMATS:
        fail(415, "UNSUPPORTED_FORMAT", "Supported formats: TXT, MD, text PDF, DOCX, CSV and XLSX.")
    canonical, declared = FORMATS[extension]
    if mime.split(";", 1)[0].lower() not in declared | {"application/octet-stream"}:
        fail(415, "MIME_MISMATCH", "The declared file type does not match its extension.")
    if not content:
        fail(422, "EMPTY_FILE", "The uploaded file is empty.")
    if len(content) > get_settings().upload_max_bytes:
        fail(413, "FILE_TOO_LARGE", "The file exceeds the configured upload limit.")
    if extension == ".pdf" and not content.startswith(b"%PDF-"):
        fail(415, "SIGNATURE_MISMATCH", "The file signature does not match its extension.")
    if extension in {".docx", ".xlsx"} and not content.startswith(b"PK\x03\x04"):
        fail(415, "SIGNATURE_MISMATCH", "The file signature does not match its extension.")
    if extension in {".txt", ".md", ".csv"}:
        try:
            decoded = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            fail(415, "INVALID_ENCODING", "Text and CSV files must use UTF-8 encoding.")
        if any(ord(c) < 32 and c not in "\n\r\t" for c in decoded):
            fail(415, "BINARY_TEXT", "A text file contains unsupported binary characters.")
    return extension, canonical


@dataclass
class Limits:
    csv_max_rows: int
    spreadsheet_max_sheets: int
    spreadsheet_max_rows: int
    spreadsheet_max_columns: int
    parse_max_characters: int
    parse_max_sections: int
    parse_max_pages: int
    parse_max_expanded_bytes: int

    @classmethod
    def configured(cls):
        settings = get_settings()
        return cls(**{key: getattr(settings, key) for key in cls.__dataclass_fields__})


class ParseFailure(Exception):
    def __init__(self, code="CORRUPT_OR_UNREADABLE", status="FAILED"):
        self.code, self.status = code, status


class DocumentParser(Protocol):
    def parse(self, content: bytes, limits: Limits) -> dict: ...


def display_reference(locator: dict) -> str:
    start, end = locator["start"], locator.get("end", locator["start"])
    span = str(start) if start == end else f"{start}–{end}"
    kind = locator["kind"]
    if kind == "LINE":
        return f"Lines {span}"
    if kind == "PDF_PAGE":
        return f"Pages {span}"
    if kind == "DOCX_PARAGRAPH":
        return f"{locator.get('heading', '')} · Paragraphs {span}".strip(" ·")
    if kind == "DOCX_TABLE":
        return f"{locator.get('heading', '')} · Table {locator['table']}, rows {span}".strip(" ·")
    cols = locator.get("column_start", "A"), locator.get("column_end", "A")
    cells = f"{cols[0]}{start}:{cols[1]}{end}"
    return f"{locator['sheet']}!{cells}" if kind == "XLSX" else f"CSV!{cells} (rows {span})"


class StructuredParser:
    def __init__(self, extension: str):
        self.extension = extension

    def parse(self, content: bytes, limits: Limits) -> dict:
        sections, characters = [], 0
        metadata = {}

        def append(text, locator, cells=None):
            nonlocal characters
            # PostgreSQL text cannot contain NUL; preserve other extracted Unicode.
            text = text.replace("\x00", "")
            characters += len(text)
            if characters > limits.parse_max_characters or len(sections) >= limits.parse_max_sections:
                raise ParseFailure("EXTRACTION_LIMIT")
            sections.append(
                {
                    "text": text,
                    "search_text": unicodedata.normalize("NFC", text),
                    "locator": locator,
                    "display_reference": display_reference(locator),
                    "cells": cells or {},
                }
            )

        stream = io.BytesIO(content)
        if self.extension in {".txt", ".md"}:
            for number, line in enumerate(content.decode("utf-8-sig").splitlines(), 1):
                append(line, {"kind": "LINE", "start": number})
            metadata["line_count"] = len(sections)
        elif self.extension == ".csv":
            reader = csv.reader(io.StringIO(content.decode("utf-8-sig"), newline=""), strict=True)
            for number, row in enumerate(reader, 1):
                if number > limits.csv_max_rows or len(row) > limits.spreadsheet_max_columns:
                    raise ParseFailure("CSV_LIMIT")
                cells = {get_column_letter(i): value for i, value in enumerate(row, 1)}
                append(
                    "\t".join(row),
                    {
                        "kind": "CSV",
                        "start": number,
                        "column_start": "A",
                        "column_end": get_column_letter(max(1, len(row))),
                    },
                    cells,
                )
                if number == 1:
                    metadata["headers"] = row
            metadata["row_count"] = len(sections)
        elif self.extension == ".pdf":
            reader = PdfReader(stream, strict=True)
            if reader.is_encrypted:
                raise ParseFailure("ENCRYPTED_PDF", "UNSUPPORTED")
            if len(reader.pages) > limits.parse_max_pages:
                raise ParseFailure("PDF_PAGE_LIMIT")
            for number, page in enumerate(reader.pages, 1):
                contents = page.get_contents()
                if contents and len(contents.get_data()) > limits.parse_max_expanded_bytes:
                    raise ParseFailure("PDF_STREAM_LIMIT")
                append(page.extract_text() or "", {"kind": "PDF_PAGE", "start": number})
            metadata["page_count"] = len(sections)
            if not any(item["text"].strip() for item in sections):
                raise ParseFailure("NO_EXTRACTABLE_TEXT", "UNSUPPORTED_OR_OCR_REQUIRED")
        else:
            self.check_package(content, limits)
            if self.extension == ".docx":
                document = Document(stream)
                paragraph, table, heading = 0, 0, ""
                for item in document.iter_inner_content():
                    if isinstance(item, Paragraph):
                        paragraph += 1
                        if item.style and item.style.name.startswith("Heading"):
                            heading = item.text[:200]
                        append(item.text, {"kind": "DOCX_PARAGRAPH", "start": paragraph, "heading": heading})
                    else:
                        table += 1
                        for number, row in enumerate(item.rows, 1):
                            cells = {get_column_letter(i): cell.text for i, cell in enumerate(row.cells, 1)}
                            append(
                                "\t".join(cells.values()),
                                {"kind": "DOCX_TABLE", "table": table, "start": number, "heading": heading},
                                cells,
                            )
                metadata.update(paragraph_count=paragraph, table_count=table)
            elif self.extension == ".xlsx":
                workbook = load_workbook(
                    stream, read_only=True, data_only=False, keep_links=False, keep_vba=False
                )
                try:
                    if len(workbook.worksheets) > limits.spreadsheet_max_sheets:
                        raise ParseFailure("XLSX_SHEET_LIMIT")
                    metadata["sheets"] = []
                    for sheet in workbook.worksheets:
                        if (sheet.max_row or 0) > limits.spreadsheet_max_rows or (
                            sheet.max_column or 0
                        ) > limits.spreadsheet_max_columns:
                            raise ParseFailure("XLSX_DIMENSION_LIMIT")
                        metadata["sheets"].append(
                            {"name": sheet.title, "rows": sheet.max_row, "columns": sheet.max_column}
                        )
                        for number, row in enumerate(sheet.iter_rows(), 1):
                            if (
                                number > limits.spreadsheet_max_rows
                                or len(row) > limits.spreadsheet_max_columns
                            ):
                                raise ParseFailure("XLSX_DIMENSION_LIMIT")
                            cells = {
                                get_column_letter(i): str(cell.value) if cell.value is not None else ""
                                for i, cell in enumerate(row, 1)
                            }
                            if any(cells.values()):
                                append(
                                    "\t".join(cells.values()),
                                    {
                                        "kind": "XLSX",
                                        "sheet": sheet.title,
                                        "start": number,
                                        "column_start": "A",
                                        "column_end": get_column_letter(max(1, len(row))),
                                    },
                                    cells,
                                )
                finally:
                    workbook.close()
        if not any(item["text"].strip() for item in sections):
            raise ParseFailure("NO_EXTRACTABLE_TEXT")
        metadata.update(character_count=characters, section_count=len(sections))
        return {"sections": sections, "metadata": metadata}

    def check_package(self, content, limits):
        with zipfile.ZipFile(io.BytesIO(content)) as package:
            entries = package.infolist()
            if len(entries) > 10000 or sum(i.file_size for i in entries) > limits.parse_max_expanded_bytes:
                raise ParseFailure("ARCHIVE_EXPANSION_LIMIT")
            expected = "word/document.xml" if self.extension == ".docx" else "xl/workbook.xml"
            if expected not in package.namelist():
                raise ParseFailure("PACKAGE_TYPE_MISMATCH", "UNSUPPORTED")
            for entry in entries:
                if "vbaproject" in entry.filename.lower() or entry.flag_bits & 1:
                    raise ParseFailure("ACTIVE_OR_ENCRYPTED_PACKAGE", "UNSUPPORTED")
                if entry.filename.endswith((".xml", ".rels")):
                    xml = package.read(entry).lower()
                    if b"<!doctype" in xml or b"<!entity" in xml or b"macroenabled" in xml:
                        raise ParseFailure("ACTIVE_XML_PACKAGE", "UNSUPPORTED")


def parser_identity(extension: str):
    package = {".pdf": "pypdf", ".docx": "python-docx", ".xlsx": "openpyxl"}.get(extension)
    return (package, importlib.metadata.version(package)) if package else ("python-utf8-csv", "1")


def isolated_parse(content: bytes, extension: str) -> dict:
    """Fresh bounded-duration process; no DB credentials, persistence or remote calls."""
    import base64

    settings = get_settings()
    slots = parse_slots()
    if not slots.acquire(blocking=False):
        return {"status": "FAILED", "error": "PARSER_CAPACITY_RETRY"}
    payload = {
        "content": base64.b64encode(content).decode("ascii"),
        "extension": extension,
        "limits": asdict(Limits.configured()),
    }
    environment = {
        key: value
        for key, value in os.environ.items()
        if key.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "LANG"}
    }
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        result = subprocess.run(
            [sys.executable, "-m", "app.modules.sources.parse_worker"],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=settings.parse_timeout_seconds,
            cwd=Path(__file__).resolve().parents[3],
            env=environment,
            check=False,
        )
        if result.returncode != 0:
            return {"status": "FAILED", "error": "PARSER_PROCESS_FAILED"}
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        return {"status": "FAILED", "error": "PARSER_TIMEOUT"}
    except (OSError, ValueError):
        return {"status": "FAILED", "error": "PARSER_PROCESS_FAILED"}
    finally:
        slots.release()


@lru_cache
def parse_slots():
    return BoundedSemaphore(get_settings().parse_max_concurrent)
