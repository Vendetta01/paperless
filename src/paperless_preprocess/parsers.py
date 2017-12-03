import itertools
import os
import re
import subprocess
from multiprocessing.pool import Pool

import langdetect
import pyocr
import PyPDF2 as pypdf
from django.conf import settings
from documents.parsers import DocumentParser, ParseError
from PIL import Image
from pyocr.libtesseract.tesseract_raw import \
    TesseractError as OtherTesseractError
from pyocr.tesseract import TesseractError
from paperless_tesseract.languages import ISO639
from paperless_tesseract.parsers import OCRError


class PreprocessDocumentParser(DocumentParser):
    """
    This parser reads text directly from PDF files. Used for already OCRed
    files or real text pdfs.
    """

    CONVERT = settings.CONVERT_BINARY
    DENSITY = settings.CONVERT_DENSITY if settings.CONVERT_DENSITY else 300
    THREADS = int(settings.OCR_THREADS) if settings.OCR_THREADS else None
    #UNPAPER = settings.UNPAPER_BINARY
    DEFAULT_OCR_LANGUAGE = settings.OCR_LANGUAGE
    

    def get_thumbnail(self):
        return

    def get_text(self):
        return
    
    def preprocess(self):
        # First convert input file to tiff
        tmpfile = os.path.splitext(
            os.path.basename(self.document_path))[0]
        # remove force preprocess flag
        if (os.path.splitext(tmpfile)[1] == ".preprocess"):
            tmpfile = os.path.splitext(tmpfile)[0]
        
        run_convert(
            self.CONVERT,
            "-density", str(self.DENSITY),
            "-depth", "8",
            self.document_path,
            os.path.join(self.tempdir, tmpfile+"-%04d.tiff")
        )
        
        # Get a sorted list of converted images
        tiffs = []
        for f in os.listdir(self.tempdir):
            if f.endswith(".tiff"):
                tiffs.append(os.path.join(self.tempdir, f))

        tiffs = sorted(filter(lambda __: os.path.isfile(__), tiffs))
        
        pdf_txts = []
        for tiff in tiffs:
            pdf_txts.append(tiff+".text")
        
        # Now run tesseract and create textonlypdf
        #pdf_img = self.document_path
        pdf_txts = self._get_pdf_ocr(tiffs, pdf_txts)
        
        # Rescale and combine text pdf and original file
        pdf_img = self.document_path
        if (not self.document_path.lower().endswith(".pdf")):
            pdf_img = os.path.join(self.tempdir, tmpfile+".img.pdf")
            run_convert(
                self.CONVERT,
                self.document_path,
                pdf_img
            )
        
        pdf_out = re.sub("(\.preprocess)*(\.[^\.]+)$", ".preprocessed.pdf",
                         self.document_path)
        
        self._mergeOutputPDF(pdf_img, pdf_txts, pdf_out)

        return
    
    def _mergeOutputPDF(self, pdf_img, pdf_txts, pdf_out):
        pypdf_img = pypdf.PdfFileReader(open(pdf_img, 'rb'))
        out = pypdf.PdfFileWriter()
        
        timax = len(pdf_txts)
        ti = 0      # index of txt file
        pypdf_txt = pypdf.PdfFileReader(open(pdf_txts[ti], 'rb'))
        tpi = 0     # page number within currently open txt
        tpimax = pypdf_txt.getNumPages()

        for i in range(0, pypdf_img.getNumPages()):
            if (tpi >= tpimax):
                ti += 1
                if (ti >= timax):
                    # Something is seriously wrong, for now just break
                    break
                pypdf_txt = pypdf.PdfFileReader(open(pdf_txts[ti], 'rb'))
                tpi = 0
                tpimax = pypdf_txt.getNumPages()

            page_img = pypdf_img.pages[i]
            page_txt = pypdf_txt.pages[tpi]
            page_txt.scaleTo(page_img.mediaBox[2], page_img.mediaBox[3])
            page_txt.mergePage(page_img)
            out.addPage(page_txt)
            tpi += 1

        with open(pdf_out, 'wb') as o:
            out.write(o)

        return


    def _guess_language(self, imgs):
        """
        OCR a single page and try to guess language
        """
        
        # Since the division gets rounded down by int, this calculation works
        # for every edge-case, i.e. 1
        middle = int(len(imgs) / 2)
        raw_text = image_to_string([imgs[middle], self.DEFAULT_OCR_LANGUAGE])
        
        try:
            guess = langdetect.detect(raw_text)
            self.log("debug", "Language detected: {}".format(guess))
            return guess
        except Exception as e:
            self.log("warning", "Language detection error: {}".format(e))


    def _get_pdf_ocr(self, imgs, pdf_txts):
        """
        OCR the input images after a trial run to guess the language
        """

        if not imgs:
            raise OCRError("No images found")

        self.log("info", "OCRing the document (guess language)")

        guessed_language = self._guess_language(imgs)
        
        
        self.log("info", "OCRing the document (create text only pdf)")

        if not guessed_language or guessed_language not in ISO639:
            self.log("warning", "Language detection failed!")
            if settings.FORGIVING_OCR:
                self.log(
                    "warning",
                    "As FORGIVING_OCR is enabled, we're going to make the "
                    "best with what we have."
                )
                return self._pdf_ocr(imgs, pdf_txts, self.DEFAULT_OCR_LANGUAGE)
            raise OCRError("Language detection failed")

        try:
            return self._pdf_ocr(imgs, pdf_txts, ISO639[guessed_language])
        except pyocr.pyocr.tesseract.TesseractError:
            if settings.FORGIVING_OCR:
                self.log(
                    "warning",
                    "OCR for {} failed, but we're going to stick with what "
                    "we've got since FORGIVING_OCR is enabled.".format(
                        guessed_language
                    )
                )
                return self._pdf_ocr(imgs, pdf_txts, self.DEFAULT_OCR_LANGUAGE)
            raise OCRError(
                "The guessed language is not available in this instance of "
                "Tesseract."
            )



    def _pdf_ocr(self, imgs, pdf_txts, lang):
        """
        Performs a single OCR attempt.
        """

        if not imgs:
            return []

        self.log("info", "Parsing for {}".format(lang))
        
        langs = []
        textonlys = []
        for img in imgs:
            langs.append(lang)
            textonlys.append(True)

        #with Pool(processes=self.THREADS) as pool:
        #    pool.map(image_to_pdf, list(zip(imgs, pdf_txts, langs, textonlys)))
        
        # image_to_pdf somehow gets stuck when using pool.map
        # for now just use serial process
        results = list(map(image_to_pdf,
                           list(zip(imgs, pdf_txts, langs, textonlys))))

        return results



def image_to_pdf(args):
    img, pdf_txt, lang, textonly = args

    ocr = pyocr.get_available_tools()[0]
    for i in range(0, len(pyocr.get_available_tools())):
        if (pyocr.get_available_tools()[i].get_name() == 'Tesseract (C-API)'):
            ocr = pyocr.get_available_tools()[i]
            break

    with Image.open(os.path.join(PreprocessDocumentParser.SCRATCH, img)) as f:
        if ocr.can_detect_orientation():
            try:
                orientation = ocr.detect_orientation(f, lang='osd')
                f = f.rotate(orientation["angle"], expand=1)
            except (TesseractError, OtherTesseractError):
                pass
            ocr.image_to_pdf(f, pdf_txt, lang=lang, textonly=textonly)
            return pdf_txt+".pdf"


def image_to_string(args):
    img, lang = args
    
    ocr = pyocr.get_available_tools()[0]
    for i in range(0, len(pyocr.get_available_tools())):
        if (pyocr.get_available_tools()[i].get_name() == 'Tesseract (C-API)'):
            ocr = pyocr.get_available_tools()[i]
            break

    with Image.open(os.path.join(PreprocessDocumentParser.SCRATCH, img)) as f:
        if ocr.can_detect_orientation():
            try:
                orientation = ocr.detect_orientation(f, lang='osd')
                f = f.rotate(orientation["angle"], expand=1)
            except (TesseractError, OtherTesseractError):
                pass
        return ocr.image_to_string(f, lang=lang)


def run_convert(*args):

    environment = os.environ.copy()
    if settings.CONVERT_MEMORY_LIMIT:
        environment["MAGICK_MEMORY_LIMIT"] = settings.CONVERT_MEMORY_LIMIT
    if settings.CONVERT_TMPDIR:
        environment["MAGICK_TMPDIR"] = settings.CONVERT_TMPDIR

    subprocess.Popen(args, env=environment).wait()


