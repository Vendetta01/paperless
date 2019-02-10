#!/usr/bin/env python3

import os
import sys
import argparse
import tempfile
import pathlib
import subprocess
import pdf2image
import pyocr
import langdetect
import iso639
import locale
import PyPDF2 as pypdf
import pdftotext
from shutil import copyfile


__VERSION__="0.2alpha"
TESS_DEF_LANG = 'eng'


class CSPException(BaseException):
    pass


class TesseractCAPINotFound(CSPException):
    def __init__(self):
        super(TesseractCAPINotFound, self).__init__()
        self.msg = "Error: pyocr.get_available_tools(): 'Tesseract (C-API)' not found"
    def __str__(self):
        return self.msg


class TesseractLanguageMissing(CSPException):
    def __init__(self, lang):
        super(TesseractLanguageMissing, self).__init__()
        self.msg = "Error: Tesseract language missing: {}".format(lang)
    def __str__(self):
        return self.msg


class PDFImageTXTPagesMismatch(CSPException):
    def __init__(self, n_img, n_txt):
        super(TesseractLanguageMissing, self).__init__()
        self.msg = "Error: Mismatch of number of pages between input pdf and OCR text only pdf: input pdf: {0}: txt pdf: {1}".format(n_img, n_txt)
    def __str__(self):
        return self.msg


def tesseract_language_installed(lang):
    """tesseract_language_installed()
    """
    # TODO:
    # check if specified language is installed
    results = subprocess.run(['tesseract', '--list-langs'],
            stdout=subprocess.PIPE).stdout.decode('utf-8').split("\n")[1:-1]

    if (lang not in results):
        return False

    return True


def guess_language(ocr, image):
    """guess_language()
    """

    try:
        # ocr image
        raw_text = ocr.image_to_string(image, lang=TESS_DEF_LANG)

        # try language detection
        lang_iso639 = iso639.find(langdetect.detect(raw_text))
        if (lang_iso639['iso639_2_t'] != ""):
            lang = lang_iso639['iso639_2_t']
        else:
            lang = lang_iso639['iso639_2_b']

        # check if language is installed
        if (not tesseract_language_installed(lang)):
            raise TesseractLanguageMissing(lang)
    except Exception as e:
        lang = TESS_DEF_LANG

    return lang


def merge_output_pdfs(pdf_img, pdf_txts, pdf_out):
    """merge_output_pdfs()
    """
    pypdf_img = pypdf.PdfFileReader(pdf_img)
    out = pypdf.PdfFileWriter()

    if (pypdf_img.getNumPages() != len(pdf_txts)):
        raise PDFImageTXTPagesMismatch(pypdf_img.getNumPages(), len(pdf_txts))

    for i, pdf_txt in enumerate(pdf_txts):
        pypdf_txt = pypdf.PdfFileReader(pdf_txt)
        page_img  = pypdf_img.pages[i]
        page_txt  = pypdf_txt.pages[0]
        # rescale text only to input
        page_txt.scaleTo(float(page_img.mediaBox[2]), float(page_img.mediaBox[3]))
        page_txt.mergePage(page_img)
        out.addPage(page_txt)

    # explicit delete to close file
    del pypdf_img

    with open(pdf_out, "wb") as o:
        out.write(o)

    return


def create_pdf_from_ocr_images(fname, pdf_out, dpi):
    """create_pdf_from_ocr_images()
    """
    # TODO:
    # 1.) X set up tesseract
    # 2.) convert pdf to images
    # 3.) guess language from middle page
    # 4.) create transparent text only pdf
    # 5.) merge text only pdf and inital file

    # set up ocr
    ocr = None
    for i in range(0, len(pyocr.get_available_tools())):
        if (pyocr.get_available_tools()[i].get_name() ==
                "Tesseract (C-API)"):
            ocr = pyocr.get_available_tools()[i]
            break

    if (ocr is None):
        raise TesseractCAPINotFound()

    # convert pdf to images
    images = pdf2image.convert_from_path(fname, dpi=dpi, fmt='tiff')

    # guess language
    lang = guess_language(ocr, images[int(len(images)/2)])

    # ocr images and create text only pdf
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_txts = []
        for i,image in enumerate(images):
            tmp_fname = pathlib.Path(tmpdir) / pathlib.Path("{:0>10d}".format(i))
            pdf_txts.append(tmp_fname.as_posix() + ".pdf")
            ocr.image_to_pdf(image=image,
                    output_file=str(tmp_fname.as_posix()),
                    lang=lang, textonly=True)
        # merge
        merge_output_pdfs(fname, pdf_txts, pdf_out)

    return


def delete_text_layer_from_pdf(fname):
    """delete_text_layer_from_pdf()
    """
    # Create temp file name
    f, pdf_tmp_name = tempfile.mkstemp()

    # copy file to temp
    copyfile(fname, pdf_tmp_name)

    # Call ghostscript
    try:
        subprocess.run(['gs', '-o', fname, '-sDEVICE=pdfwrite',
            '-dFILTERTEXT', pdf_tmp_name], check=True)
    except:
        os.remove(pdf_tmp_name)
        raise

    # delete temp file
    os.remove(pdf_tmp_name)

    return


def main(argv):
    # fix for bug in tesseract: set LC_ALL to "C"
    locale.setlocale(locale.LC_ALL, "C")

    parser = argparse.ArgumentParser(description="Program description")
    parser.add_argument("input_pdf", type=str, nargs="+",
            help="file to convert into searchable pdf")
    parser.add_argument("-f", "--force", dest="force",
            action="store_const", const=True, default=False,
            help="unless specified, pdfs containing text are skipped")
    parser.add_argument("-i", "--inplace", dest="inplace",
            action="store_const", const=True, default=False,
            help="write output directly to input file")
    parser.add_argument("-d", "--dpi", dest="dpi", default=300,
            help="dpi used for internal conversion to image")
    parser.add_argument("-V", "--version", action="version",
            version="%(prog)s {}".format(__VERSION__))

    args = parser.parse_args()

    for fname in args.input_pdf:
        # check file existence and if text is available else skip
        try:
            f = open(fname, "rb")
            pdf = pdftotext.PDF(f)
            pdf_has_text = False
            if (len(pdf) > 0 and pdf[0]):
                pdf_has_text = True
        except FileNotFoundError:
            print("Warning: File '{}' not found, skipping!".format(fname))
            continue
        else:
            f.close()

        if (not args.force and pdf_has_text):
            print("Warning: File '{}' contains text, skipping!".format(fname))
            continue

        if (args.force and pdf_has_text):
            print("Warning: File '{}' contains text but --force is set, deleting old text layer".format(fname))
            delete_text_layer_from_pdf(fname)


        pdf_out = fname
        if (not args.inplace):
            pdf_out = pdf_out + ".ocred.pdf"

        # ocr images and create pdf
        create_pdf_from_ocr_images(fname, pdf_out, args.dpi)

    return


if __name__ == '__main__':
    main(sys.argv)

