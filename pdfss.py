"""
``pdfss``
---------

Provides generic helpers to extract information from pdf/text files.

All PDF manipulation is based on the underlying PDFMiner_ library.

PDF data extraction API
~~~~~~~~~~~~~~~~~~~~~~~

This module provides the basis for a powerful PDF data extraction system. It's
based on a chain of *processors* in which are injected `ltobjects`_ constructed
from a PDF file by PDFMiner_.

Processor are python coroutine, instantiated given the previous processor in the
chain and a dictionary in which extracted data should be stored.

At the start of the chain is a generator that will yield *ltobjects* in depth
first order of their appearance in the pdf file (though that isn't necessary
related to the order of their visual appearance, which is all the difficulty of
extracting data from PDFs...). Each processor may decide to yield this data down
to the next processor or not, and must send back to its upward processor a flag
telling if the generator should recurse into the current object or
not. Processors also get from their upward processor the current state, and must
send back to it the new state. This may be clearer through the simple ascii art
diagram below: ::

  generator --[state, ltobj]--> processor 1 --[state, ltobj]--> processor 2
           <--[recurs, state]--            <--[recurs, state]--

Notice that *ltobject* classes that have the `get_text` interface gain a
`lower_text` property that returns a cached and downcased version of the text
they hold.

Also when all the objects of a page have been processed, a special 'end_of_page'
state associated to None as ltobject is yielded. If another page is following,
it will start from the previous state.

Once you get the idea:

- start writing your own processors to extract data from specific PDF
  files, usually with simplified prototype thanks to the
  :func:`simple_ltobj_processor` decorator;

- if your data doesn't come in the data you would expect by reading the table,
  you'll want to look at the :func:`build_store_tables_data_processor` processor
  builder and its :func:`regroup_lines` and :func:`regroup_wrapped_headers`
  companion functions;

- then give the PDF file you want to scrap and your processors chain, usually
  preceded by :data:!`BASE_PROCESSORS`, to the :func:`scrap_ltpage` entry point
  function.

.. _ltobjects: https://euske.github.io/pdfminer/programming.html#layout
.. _PDFMiner: https://euske.github.io/pdfminer/index.html

.. autofunction:: scrap_ltpage
.. autodata::BASE_PROCESSORS
.. autofunction:: simple_ltobj_processor
.. autofunction:: build_store_tables_data_processor
.. autofunction:: regroup_lines
.. autofunction:: regroup_wrapped_headers
.. autofunction:: iter_tables_data_columns
.. autofunction:: build_skip_block_starting_with_processor
.. autofunction:: build_skip_classes_processor
.. autofunction:: base_recursion_control_processor
.. autofunction:: debug_processor

Other PDF utilities
~~~~~~~~~~~~~~~~~~~

.. autofunction:: iter_pdf_ltpages
.. autofunction:: dump_pdf_structure
.. autofunction:: pdf2text

Text manipulation
~~~~~~~~~~~~~~~~~

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
.. autofunction:: last_word
.. autofunction:: colon_right
"""  # noqa

from __future__ import generator_stop

from collections import defaultdict
from datetime import date
from functools import update_wrapper, wraps
from io import BytesIO, TextIOWrapper
import logging
import sys

from pdfminer.high_level import extract_text_to_fp
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import (
    LAParams, LTAnno, LTChar, LTCurve, LTFigure, LTImage, LTLine, LTRect,
    LTText, LTTextBox, LTTextContainer, LTTextBoxHorizontal,
    LTTextLine, LTTextLineHorizontal)
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage


LOGGER = logging.getLogger('lowatt.pdfss')


def c_dmy_date(date_string):
    """Return a date formatted as string like 22/04/2018 to a class:`datetime.date`
    instance.

    >>> c_dmy_date('09/05/2018')
    datetime.date(2018, 5, 9)
    """
    return date(*(int(part) for part in reversed(date_string.split('/'))))


def c_amount_float(value):
    """
    >>> c_amount_float('25 028,80 €')
    25028.8
    >>> c_amount_float('25 028,80')
    25028.8
    >>> c_amount_float('4,326 c€ ')
    0.04326
    """
    value = value.strip().replace('€', '')
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
    (25028.0, 'kWh')
    """
    float_str, unit = value.rsplit(' ', 1)
    return c_str_float(float_str), unit.strip()


def c_str_float(value):
    """
    >>> c_str_float('25 028,80')
    25028.8
    """
    return float(value.replace(' ', '').replace(',', '.'))


def last_word(line):
    """
    >>> last_word('a few words')
    'words'
    """
    return line.rsplit(None, 1)[-1]


def colon_right(line):
    """
    >>> colon_right('colon separated : value')
    'value'
    """
    return line.split(':')[-1].strip()


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


def _ltobjs_generator(layout, state=None):
    """Root coroutine of the PDF parsing API, yielding `(state, ltobj)` tuple
    where:

    - `state` is the current state

    - `ltobj` is the current ltobj_ from PDFMiner.

    It's initialized by given `layout`, an instance of :class:!`PDFLayout`
    object, and an original `state`.

    Objects are yielded in depth first order of their appearance in the pdf
    file.  Subsequent coroutines may control traversal of the tree and state
    changes by sending a recursion boolean flag and a new state.

    When all the objects have been processed, a special 'end_of_page' state
    associated to None as ltobject is yielded, then the previous latest state in
    is returned (and may be catched using :exc:!`StopIteration` `value`
    attribute).

    .. _ltobj: https://euske.github.io/pdfminer/programming.html#layout
    """
    stack = list(reversed(layout._objs))
    while stack:
        ltobj = stack.pop()
        recurs, new_state = (yield state, ltobj)
        if recurs is None or recurs is True:
            try:
                stack += reversed(ltobj._objs)
            except AttributeError:
                pass  # no subobjects, eg ltobj is LTChar

        if new_state != state:
            LOGGER.debug('State change from %s to %s', state, new_state)
            state = new_state

    # inject special state to notify end of page
    previous_state = state
    recurs, state = (yield 'end_of_page', None)
    # if no one reacted to the end_of_page state, restore the previous one
    if state is None or state == 'end_of_page':
        state = previous_state

    return state


def debug_processor(ltobjs_generator, data):
    """Processor that print received state and *ltobj* from the generator.

    You may insert it anywhere in the chain to see what's hapening there.
    """
    state, ltobj = next(ltobjs_generator)
    while True:
        LOGGER.info('[{}] {!r}'.format(
            state, ltobj.lower_text if ltobj is not None else None))
        recurs, state = (yield state, ltobj)
        try:
            state, ltobj = ltobjs_generator.send((recurs, state))
        except StopIteration as exc:
            return exc.value


def simple_ltobj_processor(func):
    """Decorator to turn a function expecting current `state`, `ltobj` and `data`
    dictionary as argument and returning a boolean flag indicating whether the
    object has been processed, hence should not be propagated down, and the new
    state into a processor suitable for :func:`scrap_ltpage`.
    """
    @wraps(func)
    def wrapper(ltobjs_generator, data):
        state, ltobj = next(ltobjs_generator)
        while True:
            processed, state = func(state, ltobj, data)
            if processed:
                # ltobj has been processed by our inner function, don't recurs
                # nor propagate it down.
                recurs = False
            else:
                recurs, state = (yield state, ltobj)
            try:
                state, ltobj = ltobjs_generator.send((recurs, state))
            except StopIteration as exc:
                return exc.value

    return wrapper


def base_recursion_control_processor(ltobjs_generator, data):
    """Processor that will allow recursion on text containers, except if downwards
    processor send it back a 'no recurs' flag.

    This is usually the first processor in the chain.
    """
    state, ltobj = next(ltobjs_generator)
    while True:
        recurs, state = (yield state, ltobj)
        if recurs is None or recurs is True:
            recurs = type(ltobj) in (LTTextBox, LTTextLine, LTTextBoxHorizontal)
        try:
            state, ltobj = ltobjs_generator.send((recurs, state))
        except StopIteration as exc:
            return exc.value


def build_skip_classes_processor(classes):
    """Return a processor which will block propagation and recursion of given
    *ltobjects* `classes`.
    """
    @simple_ltobj_processor
    def skip_classes_processor(state, ltobj, data):
        return type(ltobj) in classes, state

    return skip_classes_processor


def build_skip_block_starting_with_processor(*skip):
    """Return a processor that will block propagation and recursion of
    *ltobjects* whose text starts with one of the string given as arguments.
    """

    @simple_ltobj_processor
    def skip_block_starting_with_processor(state, ltobj, data):
        return ltobj is not None and ltobj.lower_text.startswith(skip), state

    return skip_block_starting_with_processor


def build_store_tables_data_processor(initial_state, start_collect_text,
                                      on_collect_end):
    """Return a processor which will collect every *ltobject* which is not processed
    by a downward processor (i.e. whose `recurs` flag sent back is not `False`)
    into an intermediary structure, for handling once all the page has been
    processed. This is necessary for case where *ltobjects* may be found at
    random places in the PDF, which seems unfortunatly usual.

    :param initial_state: state or states from which we should start looking for
      the `start_collect_text`

    :param start_collect_text: text a *ltobject* should starts with to trigger
      the beginning of *ltobjects* collection

    :param on_collect_end: callback function that will be called once collect is
      finished (i.e. at page end, take care data may restart on the next page),
      given the state before 'end_of_page', a data dictionary and the collected
      data as `{y: {x: text, ...}, ...}` dictionary, describing text at Y and X
      coordinates in the page (0 being the bottom-left corner, but they are
      returned in reverse order to start from the top left corner). It must
      returns the next state.

    Collected data dictionary may be simplified using :func:`regroup_lines` and
    :func:`regroup_wrapped_headers` or similar.
    """
    if isinstance(initial_state, str):
        initial_states = (initial_state,)
    else:
        initial_states = initial_state

    def store_tables_data_processor(ltobjs_generator, data):
        tables_data = None
        state, ltobj = next(ltobjs_generator)
        while True:
            previous_state = state
            recurs, state = (yield state, ltobj)

            if recurs is False:
                # object has been processed by downwards processor
                state, ltobj = ltobjs_generator.send((recurs, state))
                continue

            if tables_data is None and state in initial_states \
               and ltobj is not None:
                if ltobj.lower_text.startswith(start_collect_text):
                    tables_data = defaultdict(dict)

            if tables_data is not None:
                if state == 'end_of_page':
                    # end of page, all the tables'data should now have been
                    # collected
                    state = on_collect_end(previous_state, data, tables_data) \
                        or state
                    tables_data = None

                elif type(ltobj) is LTTextLineHorizontal:
                    _save_ltobj(tables_data, ltobj)

            try:
                state, ltobj = ltobjs_generator.send((recurs, state))
            except StopIteration as exc:
                return exc.value

    return store_tables_data_processor


def _save_ltobj(tables_data, ltobj):
    """Collect `ltobj` indexed by their bbox coordinates into `tables_data` so we
    may get back table structure.
    """
    last = None
    parts = []
    for i, subltobj in enumerate(ltobj._objs):
        if last is None:
            last = subltobj
            parts.append([subltobj.x0, subltobj.x1, ''])

        if isinstance(subltobj, LTChar):
            parts[-1][1] = subltobj.x1
            parts[-1][2] += subltobj.lower_text
        elif isinstance(subltobj, LTAnno) and subltobj.get_text() == ' ':
            # if there is too much space betwwen two chars separated by a space,
            # split the word
            #
            # XXX "10" has been arbitrarily determined and should depends on the
            # font size
            if ltobj._objs[i+1].x1 - last.x1 > 10:
                parts.append([last.x1, None, ''])
            else:
                parts[-1][-1] += ' '
        elif isinstance(subltobj, LTAnno) and subltobj.lower_text == '\n':
            pass
        else:
            assert False, subltobj
        last = subltobj

    for x0, x1, text in parts:
        tables_data[ltobj.y0][(round(x0), round(x1))] = text


def regroup_lines(tables_data):
    """Return an iterator lines `(line y coordinate, line data dict)` extracted from
    raw `tables_data` dictionary.

    This is usually the first item in tables data processing chain, since it
    will regroup lines according to vertical spacing.
    """
    stacked = None
    for y, line_data in reversed(sorted(tables_data.items())):
        if stacked is None:
            stacked = (y, line_data)
        elif stacked[0] - y > 5:
            # new line, yield stacked one
            yield stacked
            stacked = (y, line_data)
        else:
            stacked[-1].update(line_data)
    if stacked is not None:
        yield stacked


def regroup_wrapped_headers(tables_data_it):
    """Iterator on `(line y coordinate, line data dict)`, folding lines
      detected as beeing wrapped part of the first column of the previous line.
    """
    stacked = None
    for y, line_data in tables_data_it:
        if stacked is None:
            stacked = (y, line_data)
        else:
            if len(line_data) == 1:
                x_index, text = next(iter(line_data.items()))
                x_index = x_index[0]
                # XXX 16 vertical spacing is arbitrary and may need adjustemnt
                # or configuration
                if x_index == min(stacked[1])[0] and (stacked[0] - y) < 16:
                    # this is the following of the previous line's
                    stacked[1][min(stacked[1])] += ' ' + text
                    continue

            yield stacked
            stacked = (y, line_data)
    if stacked is not None:
        yield stacked


def iter_tables_data_columns(tables_data_it):
    """Given an iterator on tables_data lines `(y, line_data)`, yield only columns
    as text for each line.
    """
    for x in tables_data_it:
        x = list(x)
        _, line_data = x
        yield [text for _, text in sorted(line_data.items())]


#: Base list of processors you'll usually want to use.
#:
#: It includes func:`base_recursion_control_processor` to only recurse on text
#: containers (`LTTextBox, LTTextLine, LTTextBoxHorizontal`) and another built
#: using :func:`build_skip_classes_processor` to skip instances of `LTChar`,
#: `LTCurve`, `LTFigure`, `LTImage`, `LTLine` and `LTRect`.
BASE_PROCESSORS = [
    base_recursion_control_processor,
    build_skip_classes_processor(
        set((LTChar, LTCurve, LTFigure, LTImage, LTLine, LTRect)))
]


def scrap_ltpage(ltpage, processors, data, state=None):
    """Entry point to extract data from some PDF stream.

    :param ltpage: the :class:!`pdfminer.layout.page` that should be scraped.

    :param processors: ordered list of processors to apply. You should consider
      :data:!`BASE_PROCESSORS` as a basis.

    :param data: dictionary into which scraped data should be stored.

    :param state: current state, default to None.

    :return: the new state
    """
    if len(ltpage._objs) == 1 and type(ltpage._objs[0]) is LTFigure:
        LOGGER.warning("Skip figure only page, is it a scanned document?")
        return state

    # initialize the processors chain with _ltobjs_generator on the top
    generator = _ltobjs_generator(ltpage, state)
    for processor in processors:
        generator = processor(generator, data)
    # exhaust it for this page
    try:
        state, ltobj = next(generator)
        while True:
            state, ltobj = generator.send((True, state))
    except StopIteration as exc:
        state = exc.value
    return state


# credits
# https://docs.pylonsproject.org/projects/pyramid/en/latest/_modules/pyramid/decorator.html#reify
class reify(object):
    """ Use as a class method decorator.  It operates almost exactly like the
    Python ``@property`` decorator, but it puts the result of the method it
    decorates into the instance dict after the first call, effectively
    replacing the function it decorates with an instance variable.  It is, in
    Python parlance, a non-data descriptor.  The following is an example and
    its usage:

    .. doctest::

        >>> class Foo(object):
        ...     @reify
        ...     def jammy(self):
        ...         print('jammy called')
        ...         return 1

        >>> f = Foo()
        >>> v = f.jammy
        jammy called
        >>> print(v)
        1
        >>> f.jammy
        1
        >>> # jammy func not called the second time; it replaced itself with 1
        >>> # Note: reassignment is possible
        >>> f.jammy = 2
        >>> f.jammy
        2
    """
    def __init__(self, wrapped):
        self.wrapped = wrapped
        update_wrapper(self, wrapped)

    def __get__(self, inst, objtype=None):
        if inst is None:
            return self
        val = self.wrapped(inst)
        setattr(inst, self.wrapped.__name__, val)
        return val


def _lower_text(self):
    return self.get_text().lower()


LTAnno.lower_text = property(_lower_text)
LTChar.lower_text = property(_lower_text)


def _container_lower_text(self):
    return ''.join(obj.lower_text for obj in self if isinstance(obj, LTText))


LTTextContainer.lower_text = reify(_container_lower_text)


if __name__ == '__main__':
    if len(sys.argv) >= 3:
        pages = [int(arg) for arg in sys.argv[2:]]
    else:
        pages = None
    dump_pdf_structure(sys.argv[1], pages=pages)
