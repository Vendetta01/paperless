import os
import subprocess

from django.conf import settings
from documents.parsers import DocumentParser, ParseError
from .pdftextract import PDFTextract



class TextPDFDocumentParser(DocumentParser):
    """
    This parser reads text directly from PDF files. Used for already OCRed
    files or real text pdfs.
    """

    CONVERT = settings.CONVERT_BINARY

    def get_thumbnail(self):
        """
        The thumbnail of a PDF is just a 500px wide image of the first page.
        """

        run_convert(
            self.CONVERT,
            "-scale", "500x500",
            "-alpha", "remove",
            self.document_path+'[0]', os.path.join(self.tempdir, "thumbnail-0000.png")
        )

        return os.path.join(self.tempdir, "thumbnail-0000.png")

    def get_text(self):
        # Return text from PDF here
        return PDFTextract().getText(self.document_path)



def run_convert(*args):

    environment = os.environ.copy()
    if settings.CONVERT_MEMORY_LIMIT:
        environment["MAGICK_MEMORY_LIMIT"] = settings.CONVERT_MEMORY_LIMIT
    if settings.CONVERT_TMPDIR:
        environment["MAGICK_TMPDIR"] = settings.CONVERT_TMPDIR

    subprocess.Popen(args, env=environment).wait()


