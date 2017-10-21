#!/usr/bin/env python

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO

def convert_pdf_to_txt(path):
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    fp = open(path, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    maxpages = 0
    caching = True
    pagenos=set()

    for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password,caching=caching, check_extractable=True):
        interpreter.process_page(page)

    text = retstr.getvalue()

    fp.close()
    device.close()
    retstr.close()
    return text


to1 = open('tw1.txt', 'w')
to2 = open('tw2.txt', 'w')
to3 = open('tw3.txt', 'w')

to1.write(convert_pdf_to_txt('pdfs/image-0002.pdf'))
to2.write(convert_pdf_to_txt('ocr_pdf/DPG_20170105.pdf'))
to3.write(convert_pdf_to_txt('text_pdf/text_pdf.pdf'))

to1.close()
to2.close()
to3.close()



