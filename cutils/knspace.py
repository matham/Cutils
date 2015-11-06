from kivy.event import EventDispatcher
from kivy.properties import (
    StringProperty, DictProperty, ObjectProperty, AliasProperty)

knspace = None
'''Default root namespace.
'''

class KNSpace(EventDispatcher):
    '''
    '''

    parent = None
    __has_applied = None

    def __init__(self, parent=None, **kwargs):
        super(KNSpace, self).__init__(**kwargs)
        self.parent = parent
        self.__has_applied = set()

    def __setattr__(self, name, value):
        prop = super(KNSpace, self).property(name, quiet=True)
        has_applied = self.__has_applied
        if prop is None:
            if hasattr(self, name):
                super(KNSpace, self).__setattr__(name, value)
            else:
                value = getattr(value, 'proxy_ref', value)
                self.apply_property(
                    **{name:
                       ObjectProperty(value, rebind=True, allownone=True)}
                )
                has_applied.add(name)
        elif name not in has_applied:
            self.apply_property(**{name: prop})
            has_applied.add(name)
            value = getattr(value, 'proxy_ref', value)
            super(KNSpace, self).__setattr__(name, value)
        else:
            value = getattr(value, 'proxy_ref', value)
            super(KNSpace, self).__setattr__(name, value)

    def __getattr__(self, name):
        parent = self.parent
        if parent is None:
            raise AttributeError(name)
        return getattr(parent, name)

    def property(self, name, quiet=False):
        prop = super(KNSpace, self).property(name, quiet=quiet)
        if prop is not None:
            return prop

        prop = ObjectProperty(None, rebind=True, allownone=True)
        self.apply_property(**{name: prop})
        self.__has_applied.add(name)
        return prop

    def clone(self):
        return KNSpace(parent=self)


class KNSpaceBehavior(object):

    _knspace = ObjectProperty(None, allownone=True)
    _name = StringProperty('')
    __last_knspace = None
    __callbacks = None

    def __init__(self, knspace=None, **kwargs):
        self.knspace = knspace
        super(KNSpaceBehavior, self).__init__(**kwargs)

    def __exchange_nspace(self, new_knspace):
        last = self.__last_knspace
        if last is new_knspace:
            return
        self.__last_knspace = new_knspace

        name = self.name
        if not name:
            return

        if new_knspace:
            setattr(new_knspace, name, self)

        if self == getattr(last, name):
            setattr(last, name, None)

    def __knspace_change_callback(self, *largs):
        for obj, name, uid in self.__callbacks:
            obj.unbind_uid(name, uid)

    def _get_knspace(self):
        _knspace = self._knspace
        if _knspace is not None:
            return _knspace

        parent_key = self.knspace_key
        if not parent_key:
            self.__last_knspace = knspace
            return knspace

        parent = getattr(self, parent_key, None)
        while parent is not None:
            parent_knspace = getattr(parent, 'knspace', 0)
            if parent_knspace is not 0:
                self.__last_knspace = parent_knspace
                return parent_knspace
            parent = getattr(parent, parent_key, None)
        self.__last_knspace = knspace
        return knspace

    def _set_knspace(self, value):
        knspace = self.knspace
        name = self.name
        if name and knspace:
            setattr(knspace, name, None)  # reset old namespace

        if value == 'clone':
            if knspace:
                value = knspace.clone()
            else:
                raise ValueError('Cannot clone with no namesapce')
        self.__last_knspace = self._knspace = value

        if name:
            knspace = self.knspace
            if not knspace:
                raise ValueError('Object has name "{}", but no namespace'.
                                 format(name))
            else:
                setattr(knspace, name, self)

    knspace = AliasProperty(
        _get_knspace, _set_knspace, bind=('_knspace', ), cache=False,
        rebind=True, allownone=True)
    '''.. warning::
        Changing the :attr:`knspace` value will clear the name association of
        the previous :attr:`knspace`, if named. However, the named objects
        who were in the namespace of the previous :attr:`knspace` value
        due to their :attr:`knspacce_key` pointing here will not change their
        association. I.e. the previous :attr:`knspace` will still point to
        them.
    '''

    knspace_key = StringProperty('parent', allownone=True)

    def _get_name(self):
        return self._name

    def _set_name(self, value):
        old_name = self._name
        knspace = self.knspace
        if old_name and knspace:
            setattr(knspace, old_name, None)

        self._name = value
        if value:
            if knspace:
                setattr(knspace, value, self)
            else:
                raise ValueError('Object has name "{}", but no namespace'.
                                 format(value))

    name = AliasProperty(_get_name, _set_name, bind=('_name', ), cache=False)

knspace = KNSpace()
