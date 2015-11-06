'''Module that provides helpful classes and functions.
'''

__all__ = ('to_bool', 'ConfigPropertyList', 'ConfigPropertyDict', 'StringList',
           'String2DList', 'StringDict')

from re import compile, split
from copy import deepcopy
from functools import partial
from io import StringIO
from csv import reader, writer

try:
    from ConfigParser import RawConfigParser
    boolean_states = RawConfigParser._boolean_states
except ImportError:
    from configparser import RawConfigParser
    boolean_states = RawConfigParser.BOOLEAN_STATES

from kivy.properties import ConfigParserProperty

to_list_pat = compile('(?:, *)?\\n?')
to_dict_pat = compile('(?:: *)?\\n?')


def to_bool(val):
    '''Takes anything and converts it to a bool type. Similar to Phyton's
    RawConfigParser `getboolean` method, which is case insensitively defined as
    0, false, no, off for False, and 1, true, yes, on for True.

    :Parameters:

        `val`: object
            A value which represents True/False.

    :Returns:
        bool. `val`, evalutaed to a boolean.
    '''
    if val.lower() not in boolean_states:
        raise ValueError('Not a boolean: %s' % val)
    return boolean_states[val.lower()]


class StringList(list):
    ''':class:`StringList` is a list class which when converted to a string,
    returns the list elements as a comma separated string, with strings quoted.

    ::

        >>> l = StringList([0, None, 'apples', 55.7])
        >>> l
        0, None, apples, 55.7
    '''

    autofill = False

    def __init__(self, iterable=[], autofill=False, *largs, **kwargs):
        super(StringList, self).__init__(iterable, *largs, **kwargs)
        self.autofill = autofill

    def __getitem__(self, key):
        if isinstance(key, slice):
            vals = super(StringList, self).__getitem__(key)  # validate key
            if not self:  # nothing to pad by or extract
                return StringList(autofill=self.autofill)

            if not self.autofill:
                return StringList(vals, False)

            start, stop, step = key.start, key.stop, key.step
            count = (stop - start) if start else stop
            if step is not None and step > 1:
                rem = count % step
                count = (count - rem) // step + (1 if rem else 0)

            n = len(vals)
            assert n <= count
            if n == count:
                return StringList(vals, True)

            val = super(StringList, self).__getitem__(-1)
            vals.extend([val] * (count - n))
            return StringList(vals, True)

        else:
            try:
                return super(StringList, self).__getitem__(key)
            except IndexError:
                if not self.autofill or key <= 0 or not len(self):
                    raise
                return super(StringList, self).__getitem__(-1)

    def __str__(self):
        return ', '.join(map(str, self))

    def __repr__(self):
        return self.__str__()


class String2DList(list):
    ''':class:`String2DList` is similar to :class:`StringList`, but instead
    represents a 2D list as a string. Each inner list is converted to a comma
    separated string. These lists, are then separated by newlines.

    ::

        >>> l = String2DList([range(4), ['apples', 'wine']])
        >>> l
        0, 1, 2, 3
        apples, wine
    '''

    def __str__(self):
        return '\n'.join([', '.join(map(str, item)) for item in self])

    def __repr__(self):
        return self.__str__()


def to_string_list(val_type, val, autofill=True):
    if isinstance(val, list):
        vals = StringList(autofill, val)
    elif isinstance(val, basestring):
        vals = StringList(autofill, split(to_list_pat, val.strip(' []()')))
    else:
        vals = StringList(autofill, [val])
    for i, v in enumerate(vals):
        vals[i] = val_type(v)
    return vals


def ConfigPropertyList(
        val, section, key, config, val_type, inner_list=False, autofill=True,
        **kwargs):
    '''A list implementation of :kivy:class:`ConfigParserProperty`. Other than
    `val_type`, and `inner_list`, the parameters are the same.

    :Parameters:

        `val_type`: callable
            In a normal :kivy:class:`ConfigParserProperty`, `val_type` is used
            to convert the string value to a particular type for every change
            in value. Here, `val_type` is instead applied to each element in
            the list.
        `inner_list`: bool
            Whether the list is a 1D (False) or 2D (True) list. The lists are
            represented in the config file using the string output of
            :class:`StringList` and :class:`String2DList` respectively.
        `autofille`: bool
            Only for inner list in 2DList.

    :Returns:
        A :kivy:class:`ConfigParserProperty`.

    One can set the value to either the lists themselves, or to a string
    representing the lists similarly to how it appears in the config file (see
    examples). In addition, the config file and the string representation is
    allowed to have the list symbols, which get stripped (see below).

    When setting the property to a list it'll be converted to a
    :class:`StringList` or :class:`String2DList`, unless it's already in
    this format. Reading the property will also always return such a list.
    This is required, because these list classes have a special string
    representation required when writing to the config file.

    .. note::
        In the config file, after the first line, any additional line is
        started with a single tab character. The tab is not used when
        setting the property to a string.

        Also, spaces after the commas will be stripped.

        For a 1D list, newlines will act similarly to a comma.

    ::

        >>> from kivy.uix.widget import Widget
        >>> from kivy.config import ConfigParser
        >>> config = ConfigParser(name='my_app')
        >>> config.read('my_confg.ini')

        >>> class MyWidget(Widget):
            >>> vals = ConfigPropertyList(range(5), 'Attrs', 'vals', 'my_app',\
 val_type=int)
            >>> vals2D = ConfigPropertyList([range(5), range(3)], 'Attrs', \
'vals2d', 'my_app', val_type=float, inner_list=True)
            >>> vals_str = ConfigPropertyList(['apple', 'wine', 'cheese and \
fruit'], 'Attrs', 'vals_str', 'my_app', val_type=str)

        >>> wid = MyWidget()
        >>> print wid.vals
        0, 1, 2, 3, 4
        >>> print wid.vals2D
        0.0, 1.0, 2.0, 3.0, 4.0
        0.0, 1.0, 2.0
        >>> print type(wid.vals), type(wid.vals2D)
        <class 'moa.utils.StringList'> <class 'moa.utils.String2DList'>
        >>> wid.vals = '1'
        >>> print type(wid.vals), wid.vals
        <class 'moa.utils.StringList'> 1
        >>> wid.vals = '1, 2, 3, 4'
        >>> print type(wid.vals), wid.vals
        <class 'moa.utils.StringList'> 1, 2, 3, 4
        >>> print wid.vals_str
        apple, wine, cheese and fruit
        >>> wid.vals2D = '1, 2, 3\n6, 7, 8'
        >>> print wid.vals2D
        1.0, 2.0, 3.0
        6.0, 7.0, 8.0

    At the end, the `my_confg.ini` file looks like::

        [Attrs]
        vals2d = 1.0, 2.0, 3.0
        \t6.0, 7.0, 8.0
        vals = 1, 2, 3, 4
        vals_str = apple, wine, cheese and fruit
    '''
    def to_2d_list(val):
        if isinstance(val, list):
            vals = String2DList(
                [StringList(autofill, l) for l in deepcopy(val)])
        elif isinstance(val, basestring):
            vals = String2DList(
                [StringList(autofill, split(to_list_pat, line.strip(' []()')))
                 for line in val.strip(' []()').splitlines()])
        else:
            vals = String2DList([StringList(autofill, [val])])
        for i, line in enumerate(vals):
            for j, v in enumerate(line):
                vals[i][j] = val_type(v)
        return vals

    v_type = to_2d_list if inner_list else partial(
        to_string_list, val_type, autofill=autofill)
    val = v_type(val)
    return ConfigParserProperty(val, section, key, config, val_type=v_type,
                                **kwargs)


class StringDict(dict):
    ''':class:`StringDict` is a dict class which when converted to a string,
    returns the dict key,vals/elements as a colon/newline separated string.

    ::

        >>> d = StringDict({'q': 55, 'a': 33})
        >>> d
        a: 33
        q: 55
    '''

    def __str__(self):
        return '\n'.join(['{}: {}'.format(k, v) for k, v in
                          sorted(self.items(), key=lambda x: x[0])])

    def __repr__(self):
        return self.__str__()


def ConfigPropertyDict(val, section, key, config, val_type, key_type,
                       **kwargs):
    '''Similar to :class:`ConfigPropertyList`, but instead represents a dict
    as a config item.  Other than `val_type`, and `key_type`, the parameters
    are the same as a :kivy:class:`ConfigParserProperty`.

    :Parameters:

        `val_type`: callable
            In a normal :kivy:class:`ConfigParserProperty`, `val_type` is used
            to convert the string value to a particular type for every change
            in value. Here, `val_type` is instead applied to each value in the
            dict.
        `key_type`: callable
            A callable applied to each key of the dict to convert it from the
            string when reading.

    :Returns:
        A :kivy:class:`ConfigParserProperty`.

    One can set the value to either a dicts, or to a string representing the
    dict similarly to how it appears in the config file (see
    examples). In addition, the config file and the string representation is
    allowed to have the dict symbols (`{`, `}`), which get stripped.

    When setting the property to a dict it'll be converted to a
    :class:`StringDict`, unless it's already in this format. Reading the
    property will also always return such a dict. This is required, because
    these dict classes have a special string representation required when
    writing to the config file.

    .. note::
        In the config file, after the first line, any additional line is
        started with a single tab character. The tab is not used when
        setting the property to a string.

        Also, spaces after the colon will be stripped.

    ::

        >>> from kivy.uix.widget import Widget
        >>> from kivy.config import ConfigParser
        >>> config = ConfigParser(name='my_app')
        >>> config.read('my_confg.ini')

        >>> class MyWidget(Widget):
            >>> vals = ConfigPropertyDict({1: 55, 12: 88}, 'Attrs', 'vals', \
'my_app', key_type=int, val_type=float)

        >>> wid = MyWidget()
        >>> print wid.vals
        1: 55.0
        2: 66.0
        >>> print type(wid.vals)
        <class 'moa.utils.StringDict'>
        >>> wid.vals = '1: 55'
        >>> print type(wid.vals), wid.vals
        <class 'moa.utils.StringDict'> 1: 55.0
        >>> wid.vals = '1: 55 \n2: 66'
        >>> print type(wid.vals), wid.vals
        <class 'moa.utils.StringDict'> 1: 55.0
        2: 66.0

    At the end, the `my_confg.ini` file looks like::

    ::

        [Attrs]
        vals = 1: 55.0
        \t2: 66.0
    '''
    def to_dict(val):
        if isinstance(val, dict):
            vals = StringDict(val)
        else:
            vals = [split(to_dict_pat, line.strip(' '), maxsplit=1)
                    for line in val.strip(' }{').splitlines()]
            vals = StringDict({k: v for k, v in vals})

        return StringDict({key_type(k): val_type(v) for k, v in vals.items()})

    val = to_dict(val)
    return ConfigParserProperty(val, section, key, config, val_type=to_dict,
                                **kwargs)
