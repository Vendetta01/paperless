import re

from .parsers import RasterisedDocumentParser


class ConsumerDeclaration(object):

    MATCHING_FILES_FORCE_PARSER = re.compile("^.*\.rasterised\.(pdf|jpg|jpeg|gif|png|tiff?|pnm|bmp)$")
    MATCHING_FILES = re.compile("^.*\.(pdf|jpg|jpeg|gif|png|tiff?|pnm|bmp)$")

    @classmethod
    def handle(cls, sender, **kwargs):
        return cls.test

    @classmethod
    def test(cls, doc):
        # First check if file name contains rasterised, then overrule
        # all other parsers and force the use of this one
        if cls.MATCHING_FILES_FORCE_PARSER.match(doc.lower()):
            return {
                "parser": RasterisedDocumentParser,
                "weight": 100
            }
        
        if cls.MATCHING_FILES.match(doc.lower()):
            return {
                "parser": RasterisedDocumentParser,
                "weight": 0
            }

        return None
