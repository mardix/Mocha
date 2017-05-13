"""
A jade extension that embed jade markup in the .html file

{% jade %}


{% endjade %}

"""

import re
import pyjade
from jinja2.ext import Extension
from pyjade.utils import process
from pyjade.ext.jinja import Compiler
from jinja2 import (TemplateSyntaxError, nodes)


begin_tag_rx = r'\{%\-?\s*jade.*?%\}'
end_tag_rx = r'\{%\-?\s*endjade\s*\-?%\}'

begin_tag_m = re.compile(begin_tag_rx)
end_tag_m = re.compile(end_tag_rx)


def convert(text, filename=None):
    return process(text, filename=filename, compiler=Compiler)

class TemplateIndentationError(TemplateSyntaxError): pass


class JadeTagExtension(Extension):
    tags = set(['jade'])

    def _get_lineno(self, source):
        matches = re.finditer(r"\n", source)
        if matches:
            return len(tuple(matches))
        return 0

    def preprocess(self, source, name, filename=None):
        ret_source = ''
        start_pos = 0

        while True:
            tag_match = begin_tag_m.search(source, start_pos)
            if tag_match:
                end_tag = end_tag_m.search(source, tag_match.end())
                if not end_tag:
                    raise TemplateSyntaxError('Expecting "endjade" tag',
                                              self._get_lineno(source[:start_pos]))

                jade_source = source[tag_match.end(): end_tag.start()]
                jade_source = convert(jade_source)

                try:
                    ret_source += source[start_pos: tag_match.start()] + jade_source
                except TemplateIndentationError as e:
                    raise TemplateSyntaxError(e.message, e.lineno, name=name, filename=filename)
                except TemplateSyntaxError as e:
                    raise TemplateSyntaxError(e.message, e.lineno, name=name, filename=filename)
                start_pos = end_tag.end()
            else:
                ret_source += source[start_pos:]
                break

        return ret_source


