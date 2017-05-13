"""
A utils for Markdown

html : render markdown to html
toc : Get the Table of Content
extract_images: Return a list of images, can be used to extract the top image

"""

import os
import markdown
from markdown.treeprocessors import Treeprocessor
from markdown.extensions import Extension
from jinja2.nodes import CallBlock
from jinja2.ext import Extension as JExtension

###
# This extension will extract all the images from the doc
class ExtractImagesExtension(Extension):
    def extendMarkdown(self, md, md_globals):
        ext = ExtractImagesTreeprocessor(md)
        md.treeprocessors.add("imageextractor", ext, "_end")

class ExtractImagesTreeprocessor(Treeprocessor):
    def run(self, root):
        "Find all images and append to markdown.images. "
        self.markdown.images = []
        for image in root.getiterator("img"):
            self.markdown.images.append(image.attrib["src"])

###

# LazyImageExtension
# An extension to delay load of images on the page
class LazyImageExtension(Extension):
    def extendMarkdown(self, md, md_globals):
        ext = LazyImageTreeprocessor(md)
        md.treeprocessors.add("lazyimage", ext, "_end")

class LazyImageTreeprocessor(Treeprocessor):
    def run(self, root):
        for image in root.getiterator("img"):
            image.set("data-src", image.attrib["src"])
            image.set("src", "")
            image.set("class", "lazy")


# EMBED
# [[embed]](http://)
# An extension to delay load of images on the page.
# It adds the class oembed in the link
class OEmbedExtension(Extension):
    def extendMarkdown(self, md, md_globals):
        ext = OEmbedTreeprocessor(md)
        md.treeprocessors.add("oembedextension", ext, "_end")

class OEmbedTreeprocessor(Treeprocessor):
    def run(self, root):
        for a in root.getiterator("a"):
            if a.text.strip() == "[embed]":
                a.text = ""
                a.set("class", "oembed")
                a.set("target", "_blank")

# ------------------------------------------------------------------------------
def html(text, lazy_images=False):
    """
    To render a markdown format text into HTML.

    - If you want to also build a Table of Content inside of the markdow,
    add the tags: [TOC]
    It will include a <ul><li>...</ul> of all <h*>

    :param text:
    :param lazy_images: bool - If true, it will activate the LazyImageExtension
    :return:
    """
    extensions = [
        'markdown.extensions.nl2br',
        'markdown.extensions.sane_lists',
        'markdown.extensions.toc',
        'markdown.extensions.tables',
        OEmbedExtension()
    ]
    if lazy_images:
        extensions.append(LazyImageExtension())

    return markdown.markdown(text, extensions=extensions)

def toc(text):
    """
    Return a table of context list
    :param text:
    :return:
    """
    extensions = ['markdown.extensions.toc']
    mkd = markdown.Markdown(extensions=extensions)
    html = mkd.convert(text)
    return mkd.toc


def extract_images(text):
    """
    Extract all images in the content
    :param text:
    :return:
    """
    extensions = [ExtractImagesExtension()]
    mkd = markdown.Markdown(extensions=extensions)
    html = mkd.convert(text)
    return mkd.images

# ------------------------------------------------------------------------------


class MarkdownTagExtension(JExtension):
    tags = set(['markdown'])

    def __init__(self, environment):
        super(MarkdownTagExtension, self).__init__(environment)
        environment.extend(
            markdowner=markdown.Markdown(extensions=['extra'])
        )

    def parse(self, parser):
        lineno = next(parser.stream).lineno
        body = parser.parse_statements(
            ['name:endmarkdown'],
            drop_needle=True
        )
        return CallBlock(
            self.call_method('_markdown_support'),
            [],
            [],
            body
        ).set_lineno(lineno)

    def _markdown_support(self, caller):
        block = caller()
        block = self._strip_whitespace(block)
        return self._render_markdown(block)

    def _strip_whitespace(self, block):
        lines = block.split('\n')
        whitespace = ''
        output = ''

        if (len(lines) > 1):
            for char in lines[1]:
                if (char == ' ' or char == '\t'):
                    whitespace += char
                else:
                    break

        for line in lines:
            output += line.replace(whitespace, '', 1) + '\r\n'

        return output.strip()

    def _render_markdown(self, block):
        block = self.environment.markdowner.convert(block)
        return block


class MarkdownExtension(JExtension):

    options = {}
    file_extensions = '.md'

    def preprocess(self, source, name, filename=None):
        if (not name or
           (name and not os.path.splitext(name)[1] in self.file_extensions)):
            return source
        return html(source)


# Markdown
mkd = markdown.Markdown(extensions=[
    'markdown.extensions.nl2br',
    'markdown.extensions.sane_lists',
    'markdown.extensions.toc',
    'markdown.extensions.tables'
])


def convert(text):
    """
    Convert MD text to HTML
    :param text:
    :return:
    """
    html = mkd.convert(text)
    mkd.reset()
    return html


def get_toc(text):
    """
    Extract Table of Content of MD
    :param text:
    :return:
    """
    mkd.convert(text)
    toc = mkd.toc
    mkd.reset()
    return toc
