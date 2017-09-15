
import re
import textract


class PDFTextract():
    def getText(self, fname, rawtext=False):
        text = textract.process(fname).decode('utf-8')

        if (rawtext):
            return text
        else:
            return self.strip_excess_whitespace(text)


    def hasText(self, fname, rawtext=False):
        if (self.getText(fname, rawtext)):
            return True
        else:
            return False


    def strip_excess_whitespace(self, text):
        no_form_feed = re.sub(r"\f", "", text)
        collapsed_spaces = re.sub(r"([^\S\r\n]+)", " ", no_form_feed)
        no_leading_whitespace = re.sub(
            "([\n\r]+)([^\S\n\r]+)", '\\1', collapsed_spaces)
        no_trailing_whitespace = re.sub("([^\S\n\r]+)$", '', no_leading_whitespace)
        return no_trailing_whitespace

