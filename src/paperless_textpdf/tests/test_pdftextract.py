#!/usr/bin/env python3

from pdftextract import PDFTextract


print(PDFTextract().getText('/home/storm/paperless_data/consume/onepage_ocr_pdf.pdf'))

print("----------------------------------")

if (not PDFTextract().getText('/home/storm/paperless_data/consume/onepage_scanned_pdf.pdf')):
    print("no ff")
else:
    print("ff")

if (not PDFTextract().getText('/home/storm/paperless_data/consume/onepage_scanned_pdf.pdf', rawtext=True)):
    print("no ff")
else:
    print("ff")


print("----------------------------------")


print("1page:")
if (PDFTextract().hasText('/home/storm/paperless_data/consume/1page.pdf')):
    print("hasText=True")
else:
    print("hasText=False")


print("2page:")
if (PDFTextract().hasText('/home/storm/paperless_data/consume/2page.pdf')):
    print("hasText=True")
else:
    print("hasText=False")

