import re

from .parsers import TextPDFDocumentParser
from .pdftextract import PDFTextract


class ConsumerDeclaration(object):

    MATCHING_FILES_FORCE_PARSER = re.compile("^.*\.textpdf\.\.pdf$")
    MATCHING_FILES = re.compile("^.*\.pdf$")

    @classmethod
    def handle(cls, sender, **kwargs):
        return cls.test

    @classmethod
    def test(cls, doc):
        # First check if file name contains rasterised, then overrule
        # all other parsers and force the use of this one
        if cls.MATCHING_FILES_FORCE_PARSER.match(doc.lower()):
            return {
                "parser": TextPDFDocumentParser,
                "weight": 100
            }

        # We have to assign a weight larger than preprocess here
        # to correctly process text pdfs

        if (cls.MATCHING_FILES.match(doc.lower()) and
                PDFTextract().hasText(doc)):
            return {
                "parser": TextPDFDocumentParser,
                "weight": 20
            }

        return None
