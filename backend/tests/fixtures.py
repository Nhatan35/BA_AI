"""Generated synthetic documents; no patient records or original-kit edits."""

import io

from docx import Document
from openpyxl import Workbook
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

DEMO = (
    "Patients may request cancellation of an appointment.\n"
    "The exact cancellation deadline has not yet been decided.\n"
    "Receptionists may assist patients with cancellation."
)


def synthetic_files():
    pdf = PdfWriter()
    page = pdf.add_blank_page(width=612, height=792)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})}
    )
    stream = DecodedStreamObject()
    stream.set_data(b"BT /F1 12 Tf 40 700 Td (Synthetic cancellation source.) Tj ET")
    page[NameObject("/Contents")] = stream
    output = io.BytesIO()
    pdf.write(output)
    document = Document()
    document.add_heading("Cancellation", level=1)
    document.add_paragraph("Synthetic paragraph before table")
    table = document.add_table(rows=1, cols=2)
    table.cell(0, 0).text, table.cell(0, 1).text = "Actor", "Cancellation"
    document.add_paragraph("Synthetic paragraph after table")
    word = io.BytesIO()
    document.save(word)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Booking"
    sheet.append(["Actor", "Statement"])
    sheet.append(["Receptionist", "Cancellation assistance"])
    sheet.append(["Formula", "=1+1"])
    spreadsheet = io.BytesIO()
    workbook.save(spreadsheet)
    return {
        "txt": ("demo.txt", DEMO.encode(), "text/plain"),
        "md": ("demo.md", "# Hủy lịch\n\nSynthetic cancellation".encode(), "text/markdown"),
        "pdf": ("demo.pdf", output.getvalue(), "application/pdf"),
        "docx": (
            "demo.docx",
            word.getvalue(),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ),
        "csv": ("demo.csv", b'Actor,Statement\nReceptionist,"Cancellation, assistance"\n', "text/csv"),
        "xlsx": (
            "demo.xlsx",
            spreadsheet.getvalue(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
    }
