import re

from .parsers import TextPDFDocumentParser
from .pdfwrapper import PDFWrapper


class ConsumerDeclaration(object):

    MATCHING_FILES = re.compile("^.*\.pdf$")

    @classmethod
    def handle(cls, sender, **kwargs):
        return cls.test

    @classmethod
    def test(cls, doc):
        # Implement correct test here

        if (cls.MATCHING_FILES.match(doc.lower()) and PDFWrapper().hasText(doc)):
            return {
                "parser": TextPDFDocumentParser,
                "weight": 10
            }

        return None
