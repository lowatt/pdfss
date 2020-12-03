"""
``pdfss``
---------

The PDF Scraping System provides generic helpers to extract information from
pdf/text files.

All PDF manipulation is based on the underlying PDFMiner_ library.

High-level functions
~~~~~~~~~~~~~~~~~~~~

.. autofunction:: iter_pdf_ltpages
.. autofunction:: pdf2text

Low-level text manipulation
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The "c\\_\\*" functions family are *converters* turning a string into something
else. First part of the name describes the accepted string, second part the
returned type or types. For instance :func:`c_amount_float_unit` convert a
string like `"345 €"` into a float (`345.`) and a unit (`'€'`).

.. autofunction:: c_amount_float
.. autofunction:: c_amount_float_unit
.. autofunction:: c_dmy_date
.. autofunction:: c_percent_float
.. autofunction:: c_str_period
.. autofunction:: c_str_float
.. autofunction:: c_str_float_unit
.. autofunction:: colon_right


PDF data extraction API
~~~~~~~~~~~~~~~~~~~~~~~

This module provides the basis for a powerful PDF data extraction system. It's
based on PDFMiner_, which generate a structure of `ltobjects`_ constructed from
PDF data.

The problem with `ltobjects` is that they are in arbitrary order, not consistent
with the visual display of the PDF. Hence our implementation that attempt to
reorder things into logical text groups.

On top of the API is the :func:relayout function. This function will return a
hierarchy of objects: :class:LinesGroup, which hold a list of :class:Line which
itself hold a list of :class:TextBlock. How line and text are grouped may be
controlled using :func:relayout arguments.

.. _ltobjects: https://euske.github.io/pdfminer/programming.html#layout
.. _PDFMiner: https://euske.github.io/pdfminer/index.html

.. autofunction:: relayout
.. autoclass:: LinesGroup
.. autoclass:: Line
.. autoclass:: TextBlock
.. autofunction:: default_line_grouper
.. autofunction:: default_text_merger
.. autoclass:: LineInfo

Dump PDF data structures
~~~~~~~~~~~~~~~~~~~~~~~~
.. autofunction:: py_dump
.. autofunction:: dump_pdf_structure

"""  # noqa

from __future__ import generator_stop

from bisect import bisect
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from functools import partial
from io import BytesIO, TextIOWrapper
import logging
import re
import sys

from pdfminer.high_level import extract_text_to_fp
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import (
    LAParams, LTAnno, LTChar, LTContainer, LTCurve, LTFigure, LTImage, LTLine,
    LTPage, LTRect, LTTextBox, LTTextBoxHorizontal, LTTextLine,
)
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage


LOGGER = logging.getLogger('lowatt.pdfss')

DEFAULT_SKIP_CLASSES = (
    LTCurve, LTFigure, LTImage, LTLine, LTRect,
)


# High-level functions #################################################

def pdf2text(stream):
    """Return a text stream from a PDF stream."""
    bytes_stream = BytesIO()
    extract_text_to_fp(stream, bytes_stream, laparams=LAParams())
    bytes_stream.seek(0)
    return TextIOWrapper(bytes_stream, 'utf-8')


def iter_pdf_ltpages(stream, pages=None):
    """Return a generator on :class:!`pdfminer.layout.LTPage` of each page in the
    given PDF `stream`.

    If `pages` is given, it should be a list of page numbers to yield (starting
    by 1).
    """
    rsrcmgr = PDFResourceManager(caching=True)
    laparams = LAParams()
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)

    for n, pdfpage in enumerate(PDFPage.get_pages(stream)):
        if pages is None or (n+1) in pages:
            interpreter.process_page(pdfpage)
            yield device.get_result()


# Low-level text manipulation ##########################################

def c_dmy_date(date_string):
    """Return a date formatted as string like 22/04/2018 to a class:`datetime.date`
    instance.

    >>> c_dmy_date('09/05/2018')
    datetime.date(2018, 5, 9)
    >>> c_dmy_date('09/05/18')
    datetime.date(2018, 5, 9)
    """
    parts = date_string.split('/')
    if len(parts[-1]) == 2:
        parts[-1] = '20' + parts[-1]
    return date(*(int(part) for part in reversed(parts)))


def c_amount_float(value):
    """
    >>> c_amount_float('25 028,80 €')
    25028.8
    >>> c_amount_float('25 028,80 EUR')
    25028.8
    >>> c_amount_float('25 028,80')
    25028.8
    >>> c_amount_float('4,326 c€ ')
    0.04326
    """
    value = value.replace('€', '').lower().replace('eur', '').strip()
    if value[-1] == 'c':
        value = value[:-1]
        factor = 0.01
    else:
        factor = 1
    return round(c_str_float(value) * factor, 6)


def c_amount_float_unit(value):
    """
    >>> c_amount_float_unit('25 028,80 €/mois')
    (25028.8, 'mois')
    """
    amount_str, unit = value.split('/')
    return (c_amount_float(amount_str), unit.strip())


def c_percent_float(value):
    """
    >>> c_percent_float('20,00%')
    20.0
    """
    return c_str_float(value.replace('%', ''))


def c_str_period(value):
    """
    >>> c_str_period('du 01/05/2018 au 31/05/2018')
    (datetime.date(2018, 5, 1), datetime.date(2018, 5, 31))
    """
    from_date_str, to_date_str = value.split(' au ')
    from_date_str = from_date_str.replace('du ', '')
    return (c_dmy_date(from_date_str), c_dmy_date(to_date_str))


def c_str_float_unit(value):
    """
    >>> c_str_float_unit('25 028 kWh')
    (25028, 'kWh')
    >>> c_str_float_unit('- 25 028.2 € / W')
    (-25028.2, '€ / W')
    """
    float_str, unit = re.split(r'(?=[^-\d,\. ]+)', value.strip(), 1)
    return c_str_float(float_str.strip()), unit.strip()


def c_str_float(value):
    """
    >>> c_str_float('25 028,80')
    25028.8
    >>> c_str_float('25')
    25
    """
    value = value.replace(' ', '').replace(',', '.')
    try:
        return int(value)
    except ValueError:
        return float(value)


def colon_right(line):
    """
    >>> colon_right('colon separated : value')
    'value'
    """
    return line.split(':')[-1].strip()


# PDF data extraction API ##############################################

@dataclass
class LineInfo:
    """Simple data class holding information about a line necessary for line
    grouping.

    """
    y0: float
    font_name: str
    font_size: float


def default_line_grouper(
        font_size_diff_factor=0.15,
        min_y_diff=1.1,
):
    """Return a line grouper function suitable for `group_line` argument of
    :func:`relayout`, configured with arguments.

    :param font_size_diff_factor: number that will be multiplied with the
      greatest font size to give the maximum font size difference allowed - if
      two line's font sizes are greater than this maximum, they can't be
      grouped.

    :param min_y_diff: minimum value of allowed Y diff, which is first computed
      using lines'font size diff, but this minimum value is picked if diff is
      lower than this value. If two line's Y0 coordinate diff is greater than
      the resulting allowed diff, they can't be grouped.

    """
    def default_group_line(linfo, latest_linfo):
        """Default line grouping function, merging lines if font size are compatible and
        Y coordinate diff is below some factor of font size, considering bold
        font variant.

        """
        allowed_diff = (
            max(latest_linfo.font_size, linfo.font_size) * font_size_diff_factor
        )
        diff = abs(latest_linfo.font_size - linfo.font_size)
        if ((linfo.font_name.endswith('-bold')
             and not latest_linfo.font_name.endswith('-bold'))
            or
            (latest_linfo.font_name.endswith('-bold')
             and not linfo.font_name.endswith('-bold'))):
            allowed_y_diff = diff * 1.5
        else:
            allowed_y_diff = diff

        # take care allowed_y_diff may be 0, 1.1 found empirically
        allowed_y_diff = max(allowed_y_diff, min_y_diff)
        if diff < allowed_diff \
           and (latest_linfo.y0 - linfo.y0) <= allowed_y_diff:
            return True

        return False

    return default_group_line


def default_text_merger(width_factor=1.4):
    """Return a text merger function suitable for `merge_text` argument of
    :func:`relayout`, configured with arguments.

    :param width_factor: factor to apply to character's width. If spacing
      between previous block and new character is lesser than the result,
      character is appended to the block, else a new block is created.

    """
    def default_merge_text(block, ltchar):
        width = ltchar.width * width_factor
        if (ltchar.x0 - block.x1) <= width:
            return True

        return False

    return default_merge_text


def default_iter_text(ltobj, skip_classes=None):
    if skip_classes is not None and isinstance(ltobj, skip_classes):
        return

    if isinstance(ltobj, (LTPage, LTContainer)):
        for subltobj in ltobj._objs:
            yield from default_iter_text(subltobj, skip_classes)

    elif isinstance(ltobj, (LTChar, LTAnno)):
        yield ltobj

    else:
        assert False, ltobj


def relayout(
        ltobj, skip_classes=DEFAULT_SKIP_CLASSES, skip_text=None,
        iter_text=default_iter_text,
        ltchar_filter=None,
        merge_text=default_text_merger(),
        group_line=default_line_grouper(),
):
    """Return a list of :class:LinesGroup for given PDFMiner `ltobj` instance.

    :param skip_classes: tuple of PDFMiner classes that should be skipped (not
      recursed in)

    :param skip_text: set of text block that should be skipped before attempt to
      regroup lines - this is useful when some text in the margin clutter lines
      of desired text

    :param ltchar_filter: function taking a `LTChar` instance as argument and
      return `False` if it should not be considered, else `True`

    :param iter_text: function used to recurs on `ltobj` and yield `LTChar` /
      `LTAnno` instances.

    :param merge_text: function used to control text merging, taking a
      :class:TextBlock as first argument and a `LTChar` instance as second
      argument and returning `True` if the character should be added to the
      block, else `False` `LTAnno` instances.

    :param group_line: function used to control line grouping, taking
      two :class:LineInfo as argument and returning `True` if they should
      begrouped, else `False`. Default to :func:default_group_line.

    """
    def iter_ltchar_index_items(items):
        for _, ltchars in sorted(items):
            for ltchar in ltchars:
                yield ltchar

    # Collect ltchar instances
    ltline_index = defaultdict(partial(defaultdict, list))
    latest_is_anno = False
    for lttext in iter_text(ltobj, skip_classes):
        if isinstance(lttext, LTAnno):
            latest_is_anno = True
            continue

        # remember ltchar was preceeded by a LTAnno
        lttext.add_space_left = latest_is_anno
        latest_is_anno = False

        if ltchar_filter is not None and not ltchar_filter(lttext):
            continue

        key = (lttext.y0, lttext.fontname.lower(), lttext.fontsize)
        ltchar_index = ltline_index[key]
        ltchar_index[lttext.x0].append(lttext)

    # Regroup lines which may be out of sync because of different font size
    # (eg. bold vs standard font)
    latest = None
    for key, ltchar_index in sorted(ltline_index.items(), reverse=True):

        if skip_text is not None and \
           _dump_ltchar_index(ltchar_index) in skip_text:
            ltline_index.pop(key)
            continue

        if latest is not None:
            linfo = LineInfo(*key)
            latest_key, latest_ltchar_index = latest
            latest_linfo = LineInfo(*latest_key)
            assert (latest_linfo.y0 - linfo.y0) >= 0
            if group_line(linfo, latest_linfo):
                ltchar_index.update(latest_ltchar_index)
                ltline_index.pop(latest_key)

        latest = key, ltchar_index

    # Turn ltline_index into index of Line / TextBlock objects
    lines = []
    for (y0, font_name, font_size), ltchar_index in sorted(
            ltline_index.items(), reverse=True,
    ):
        line = Line(font_name, font_size, y0, merge_text)
        lines.append(line)

        for ltchar in iter_ltchar_index_items(ltchar_index.items()):
            line.append(ltchar)

    # Search for column groups
    group_index = {}
    previous_line_group = None
    for line in lines:
        group = _line_group(line, group_index, previous_line_group)
        group.append(line)
        previous_line_group = group

    return sorted(
        (group for groups in group_index.values() for group in groups),
        key=lambda group: -group[0].y0,
    )


def _line_group(line, group_index, previous_line_group):
    """Return :class:LinesGroup in which `line` should be added, given `group_index`
    (groups indexed per their x start index, i.e. {x0: [LinesGroup]}) and
    `previous_line_group` (the group in which line above the current one has
    been added).
    """
    start_index = line.blocks[0].x0

    if previous_line_group is not None:
        # search if start index is some column of the previous line
        # XXX consider x1 on right aligned column
        for idx, block in enumerate(previous_line_group[-1].blocks):
            if block.x0 == start_index:
                group = previous_line_group
                while idx:
                    line.insert_blank_at(0)
                    idx -= 1
                return group

    try:
        group = group_index[start_index][-1]
    except KeyError:
        group = LinesGroup()
        group_index[start_index] = [group]
        return group

    # create a new group if there are too much vertical spacing
    # between the previous line and the current line
    if (group[-1].y0 - line.y0) > (line.font_size * 2):
        group = LinesGroup()
        group_index[start_index].append(group)
    # or if previous line overlap x coordinate
    elif (previous_line_group[-1].blocks[-1].x1 > line.blocks[0].x0
          and previous_line_group[-1].blocks[0].x0 < line.blocks[-1].x1):
        group = LinesGroup()
        group_index[start_index].append(group)

    return group


def _dump_ltchar_index(ltchar_index):
    """Return string representation of :func:relayout ltchar_index data structure,
    for debugging purpose.

    """
    def ltchar_text(ltchar, i):
        text = ltchar.get_text()
        if i > 0 and ltchar.add_space_left:
            text = ' ' + text
        return text

    return ''.join(
        ltchar_text(ltchar, i)
        for i, (_, ltchars) in enumerate(sorted(ltchar_index.items()))
        for ltchar in ltchars
    )


def _dump_ltline_index(ltline_index):
    """Return string representation of :func:relayout ltline_index data structure,
    for debugging purpose.

    """
    res = []
    for key, ltchar_index in sorted(ltline_index.items(), reverse=True):
        res.append('{}: {}'.format(key, _dump_ltchar_index(ltchar_index)))
    return '\n'.join(res)


class LinesGroup(list):
    """A list of :class:`Line` logically grouped."""


class Line:
    """A logical line, holding a list of text blocks."""

    def __init__(self, font_name, font_size, y0, merge_text):
        self.font_name = font_name
        self.font_size = font_size
        # ordered list of ltchar.x0, use index to get matching ltline from
        # :attr:`blocks`
        self._block_index = []
        # slave list of block
        self.blocks = []
        self.y0 = y0
        self.merge_text = merge_text

    def __repr__(self):
        blocks_str = []
        for block in self.blocks:
            blocks_str.append(repr(block))
        return '[{}: {}]'.format(self.font_size, ', '.join(blocks_str))

    def __str__(self):
        blocks_str = []
        for block in self.blocks:
            blocks_str.append(str(block))

        return '[{}]'.format(', '.join(blocks_str))

    def insert_blank_at(self, index):
        self.blocks.insert(0, TextBlock('', 0, 0, 0))
        self._block_index.insert(0, 0)

    def append(self, ltchar):
        if ltchar.width == 0:
            # some chars (picto) have width = 0, set it relative to font size
            # arbitrarily, it's still better than 0. 10 division factor was
            # found empirically.
            assert ltchar.fontsize
            ltchar.width = ltchar.fontsize / 10
            ltchar.x1 = ltchar.x0 + ltchar.width

        index = bisect(self._block_index, ltchar.x1)

        if index > 0 and self.merge_text(self.blocks[index - 1], ltchar):
            block = self.blocks[index - 1]
            text = ltchar.get_text()
            if ltchar.add_space_left:
                text = ' ' + text
            block.append(text, ltchar.x0, ltchar.x1, ltchar.fontsize)
            self._block_index[index - 1] = ltchar.x1
        else:
            block = TextBlock(ltchar.get_text(), ltchar.x0, ltchar.x1,
                              ltchar.fontsize)
            self.blocks.insert(index, block)
            self._block_index.insert(index, ltchar.x1)

        assert len(self.blocks) == len(self._block_index)


class TextBlock:
    """A logical group of text.

    :attr text: the text contained in the block
    :attr x0: the left coordinate of the whole block
    :attr x1: the right coordinate of the whole block
    :attr latest_x0: the left coordinate of the latest char in the block
    """

    def __init__(self, text, x0, x1, font_size):
        self.text = text
        self.x0 = x0
        self.x1 = x1
        self.latest_x0 = x0

    def __repr__(self):
        return '<{!r} ({}, {})]>'.format(
            self.text, self.x0, self.x1)

    def __str__(self):
        return '<{!r}>'.format(self.text)

    def append(self, text, x0, x1, font_size):
        assert self.x0 <= x0, (self.x0, x0, self.text, text)
        assert self.x1 <= x1, (self.x1, x1, self.text, text)
        self.x1 = x1
        self.text += text
        self.latest_x0 = x0


# Dump PDF data structures #############################################

def dump_pdf_structure(filepath, pages=None, file=sys.stdout):
    """Print PDFMiner's structure extracted from the given PDF file, to help
    debugging or building scrapers.

    If `pages` is given, it should be a list of page numbers to yield (starting
    by 1).

    Print by default on stdout but you may give an alternate `file` stream into
    which data will be written.
    """
    with open(filepath, 'rb') as stream:
        for i, page in enumerate(iter_pdf_ltpages(stream, pages=pages)):
            print('{} page {}'.format('*'*80, i+1))
            objstack = [('', o) for o in reversed(page._objs)]
            while objstack:
                prefix, b = objstack.pop()
                if type(b) in [LTTextBox, LTTextLine, LTTextBoxHorizontal]:
                    print(prefix, b, file=file)
                    objstack += ((prefix + '  ', o) for o in reversed(b._objs))
                else:
                    print(prefix, b, file=file)


def py_dump(filepath, out=sys.stdout, pages=None,
            skip_classes=DEFAULT_SKIP_CLASSES):
    """Dump PDF `filepath` file as an importable python structure in `out` stream.

    :param filepath: path to the PDF file.

    :param out: optional output file stream, default to sys.stdout.

    :param pages: optional list of page numbers to dump (starting by 1).

    :param skip_classes: tuple of PDFMiner layout classes that shoult not be
      dumped.

    """
    print('from pdfminer.layout import *', file=out)
    print('from pdfss import ltobj\n\n', file=out)

    with open(filepath, 'rb') as input_stream:
        for i, page in enumerate(iter_pdf_ltpages(input_stream, pages=pages)):
            print('\npage{} = '.format(i+1), file=out, end='')
            py_dump_ltobj(page, out=out, skip_classes=skip_classes)


def py_dump_ltobj(ltobj, out=sys.stdout, skip_classes=None, indent=0):
    """Dump PDFMiner `ltobj` object as an importable python structure in `out`
    stream.

    :param ltobj: PDFMiner LT object to dump.

    :param out: optional output file stream, default to sys.stdout.

    :param skip_classes: tuple of PDFMiner layout classes that shoult not be
      dumped.

    :param indent: indentation level of the object, default to 0.

    """
    if skip_classes is not None and isinstance(ltobj, skip_classes):
        return

    if isinstance(ltobj, LTContainer):
        print('{}ltobj({}, {}, ['.format('  ' * indent,
                                         ltobj.__class__.__name__,
                                         _clean_ltobj_dict(ltobj.__dict__)),
              file=out)
        for subltobj in ltobj._objs:
            py_dump_ltobj(subltobj, out, skip_classes, indent + 1)
        print('{}]){}'.format('  ' * indent, ',' if indent else ''),
              file=out)

    else:
        print('{}ltobj({}, {}),'.format('  ' * indent,
                                        ltobj.__class__.__name__,
                                        _clean_ltobj_dict(ltobj.__dict__)),
              file=out)


class ltobj:
    """Class used to reimport object dumped by :func:`py_dump`.

    **You should not use this directly**.
    """
    def __init__(self, __class__, __dict__, objs=None):
        self.__class__ = __class__
        self.__dict__ = __dict__
        if objs is not None:
            self._objs = objs
        if 'x0' in __dict__:
            # bbox necessary for repr() but not exported
            self.bbox = (self.x0, self.y0, self.x1, self.y1)


def _clean_ltobj_dict(__dict__):
    """Return a dictionary from an ltobj's __dict__, removing entries that should
    not be exported and rounding float for better readability.
    """
    def round_value(v):
        if isinstance(v, float):
            return round(v, 2)
        if isinstance(v, tuple):
            return tuple(round_value(item) for item in v)
        return v

    return {k: round_value(v) for k, v in __dict__.items()
            if k not in {'_objs', 'bbox', 'graphicstate', 'groups', 'ncs'}}


def _ltchar_record_fontsize_init(self, matrix, font, fontsize, *args, **kwargs):
    ltchar_init(self, matrix, font, fontsize, *args, **kwargs)
    self.fontsize = fontsize


ltchar_init = LTChar.__init__
LTChar.__init__ = _ltchar_record_fontsize_init


########################################################################

if __name__ == '__main__':
    if len(sys.argv) >= 3:
        pages = [int(arg) for arg in sys.argv[2:]]
    else:
        pages = None
    py_dump(sys.argv[1], pages=pages)
