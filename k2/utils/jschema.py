#!/usr/bin/env python3


def apply(obj, scheme, key=None):
    """
        obj - some object
        scheme - jschema
        key is name of top-level object (or None) ; (for log)
        scheme ::= type of this object : list/dict/str/int/float or "const"
          OR
        scheme ::= dict - {
          type       : type of this object : "list/dict/str/int/float or "const"
          value      : scheme - need for
                         - list/dict - pointer to scheme for child
                         - const - list or set (or iterable) of allowed values
          default    : default value if this object does not exists (if callable will be called)
          filter     : function value -> bool - if false then raise error
          pre_call   : function value -> value - will be called before cheking filter and value
          post_call  : function value -> value - will be called after cheking filter and value
          blank      : raise error if value is blank
          max_length : extra check of length (len)
          min_length : extra check of length (len)
          unexpected : allow unexpected keys (for dict)
        }
    """
    def default(value):
        return value() if callable(value) else value

    _key = key if key else 'Top-level'
    extra = ''.join(['for ', key]) if key else ''
    if not isinstance(scheme, (dict, type)) and scheme != 'const':
        raise ValueError(f'scheme must be type, dict or "const" {extra}')
    elif scheme == 'const':
        return obj
    elif isinstance(scheme, type):
        if isinstance(obj, scheme):
            return  obj
        raise ValueError(f'"{obj}" is not type of "{scheme}" {extra}')

    if 'pre_call' in scheme:
        obj = scheme['pre_call'](obj)

    if scheme['type'] == 'const':
        if obj not in scheme['value']:
            raise ValueError(
                f'"{obj}" is not allowed as "{key}"'
            )
    elif isinstance(scheme['type'], type):
        if not isinstance(obj, scheme['type']):
            raise ValueError(f'''expected type "{scheme['type']}" {extra} ; got {type(obj)}''')
        if 'filter' in scheme and not scheme['filter'](obj):
            raise ValueError(f'"{key}" not passed filter')
        if scheme.get('blank') is False and not obj:
            raise ValueError(f'"{key}" is blank')
        if 'max_length' in scheme and len(obj) > scheme['max_length']:
            raise ValueError(f'"{key}" > max_length')
        if 'min_length' in scheme and len(obj) < scheme['min_length']:
            raise ValueError(f'"{key}" < min_length')

        if issubclass(scheme['type'], list):
            if 'value' in scheme:
                obj = [apply(i, scheme['value'], key=_key) for i in obj]
        elif issubclass(scheme['type'], dict):
            if 'value' in scheme:
                new_obj = {}
                unex = {i for i in obj if i not in scheme['value']}
                if unex:
                    if scheme.get('unexpected', False):
                        new_obj.update(
                            {
                                i: obj[i]
                                for i in unex
                            }
                        )
                    else:
                        raise ValueError(f'''Got unexpected keys: "{'", "'.join([str(i) for i in unex])}" {extra};''')
                if missed := {i for i in scheme['value'] if i not in obj and 'default' not in scheme['value'][i]}:
                    raise ValueError(f'''expected keys "{'", "'.join([str(i) for i in missed])}" {extra}''')

                new_obj.update(
                    {
                        i:
                        default(scheme['value'][i]['default'])
                        if i not in obj else
                        apply(
                            obj=obj[i],
                            scheme=scheme['value'][i],
                            key=i,
                        )
                        for i in scheme['value']
                    }
                )
                obj = new_obj
            elif 'anykey' in scheme:
                obj = {
                    i: apply(
                        obj=obj[i],
                        scheme=scheme['anykey'],
                        key=i,
                    )
                    for i in obj
                }
    else:
        raise ValueError(f'''Scheme has unknown type "{scheme['type']}"''')

    if 'post_call' in scheme:
        obj = scheme['post_call'](obj)
    return obj
