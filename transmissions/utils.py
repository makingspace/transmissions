from six import with_metaclass


class EnumDictType(type):
    @property
    def values(cls, *args, **kwargs):
        """ Create enum values from all uppercase class attributes and store them in a dict"""
        attributes = [k_v for k_v in list(cls.__dict__.items()) if k_v[0].isupper()]
        labels = cls.__dict__.get('labels', {})

        values = {}
        for attribute in attributes:
            values[attribute[1]] = labels.get(attribute[1])
        return values

class EnumDict(with_metaclass(EnumDictType)):
    pass


