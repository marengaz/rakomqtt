import json

def _default_serialisation(obj):
    """Default JSON serializer."""
    import calendar, datetime

    if isinstance(obj, datetime.datetime):
        return obj.isoformat()

    raise TypeError('Not sure how to serialize %s' % (obj,))


class SerialisationError(Exception):

    def __init__(self, instance, errors):
        super().__init__(self, "Could not serialise {}, errors, {}".format(str(instance), str(json.dumps(errors))))


class DeserialisationError(Exception):

    def __init__(self, instance, errors):
        super().__init__(self, "Could not deserialise {}, errors, {}".format(str(instance), str(json.dumps(errors))))


def serialise(schema, cls_instance):
    """Uses marshellow schema to serialise class, if there is a problem throws a SerialisationError"""
    # the default serialiser is needed because we dont have a proper marshmellow schema for the event log which has datetime objects so marshmellow falls back to normal json serialisation.
    # when we update to v3 and improve the event log entry schema we can remove this hack
    result, errors = schema.dumps(cls_instance, default=_default_serialisation)

    if len(errors) > 0:
        raise SerialisationError(cls_instance, errors)

    return result


def deserialise(schema, string_or_dict):
    """Uses marshellow schema to serialise class, if there is a problem throws a SerialisationError"""

    if isinstance(string_or_dict, dict):
        result, errors = schema.load(string_or_dict)
    elif isinstance(string_or_dict, str):
        result, errors = schema.loads(string_or_dict)
    else:
        raise Exception('Unexpected arg type to deserialise {}'.format(str(type(string_or_dict))))

    if len(errors) > 0:
        raise DeserialisationError(string_or_dict, errors)

    return result
