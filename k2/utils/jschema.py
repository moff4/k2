
from typing import Any, Dict


def _apply(obj: Any, schema: Dict[Any, Any], key: str) -> Any:
    """
        obj - some object
        schema - jschema
        key is name of top-level object (or None) ; (for log)
        schema ::= type of this object : list/dict/str/int/float or "const"
          OR
        schema ::= dict - {
          type         : type of this object : "list/dict/str/int/float or "const"
          "value"      : schema - need for
                           - list/dict - pointer to schema for child
                           - const - list or set (or iterable) of allowed values
          "default"    : default value if this object does not exists (if callable will be called)
          "filter"     : function value -> bool - if false then raise error
          "pre_call"   : function value -> value - will be called before cheking filter and value
          "post_call"  : function value -> value - will be called after cheking filter and value
          "blank"      : raise error if value is blank
          "max_length" : extra check of length (len)
          "min_length" : extra check of length (len)
          "unexpected" : allow unexpected keys (for dict)
        }
    """
    def get_type(sch) -> Any:
        return sch[type if type in sch else 'type']

    def default(value) -> Any:
        return value() if callable(value) else value

    extra = ''.join(['for ', key]) if key else ''
    if not isinstance(schema, (dict, type)) and schema != 'const':
        raise ValueError(f'schema must be type, dict or "const" {extra}')
    elif schema == 'const':
        return obj
    elif isinstance(schema, type):
        if isinstance(obj, schema):
            return obj
        raise ValueError(f'"{obj}" is not type of "{schema}" {extra}')

    if 'pre_call' in schema:
        obj = schema['pre_call'](obj)

    if (schema_type := get_type(schema)) == 'const':
        if obj not in schema['value']:
            raise ValueError(f'"{obj}" is not allowed as "{key}"')
    elif isinstance(schema_type, type):
        if not isinstance(obj, schema_type):
            raise ValueError(f'''expected type "{schema_type}" {extra} ; got {type(obj)}''')
        if 'filter' in schema and not schema['filter'](obj):
            raise ValueError(f'"{key}" not passed filter')
        if schema.get('blank') is False and not obj:
            raise ValueError(f'"{key}" is blank')
        if 'max_length' in schema and len(obj) > schema['max_length']:
            raise ValueError(f'"{key}" > max_length')
        if 'min_length' in schema and len(obj) < schema['min_length']:
            raise ValueError(f'"{key}" < min_length')

        if issubclass(schema_type, list):
            if 'value' in schema:
                obj = [_apply(i, schema['value'], key=key) for i in obj]
        elif issubclass(schema_type, dict):
            if 'value' in schema:
                new_obj = {}
                if unex := {i for i in obj if i not in schema['value']}:
                    if schema.get('unexpected', False):
                        new_obj.update(
                            {
                                i: obj[i]
                                for i in unex
                            }
                        )
                    else:
                        raise ValueError(f'''Got unexpected keys: "{'", "'.join([str(i) for i in unex])}" {extra};''')
                if missed := {i for i in schema['value'] if i not in obj and 'default' not in schema['value'][i]}:
                    raise ValueError(f'''expected keys "{'", "'.join([str(i) for i in missed])}" {extra}''')

                new_obj.update(
                    {
                        i:
                        default(schema['value'][i]['default'])
                        if i not in obj else
                        _apply(
                            obj=obj[i],
                            schema=schema['value'][i],
                            key=i,
                        )
                        for i in schema['value']
                    }
                )
                obj = new_obj
            elif 'anykey' in schema:
                obj = {i: _apply(obj[i], schema['anykey'], i) for i in obj}
    else:
        raise ValueError(f'''schema has unknown type "{schema_type}"''')

    if 'post_call' in schema:
        obj = schema['post_call'](obj)
    return obj


def apply(obj: Any, schema: Dict[Any, Any]) -> Any:
    return _apply(obj, schema, 'Top-level')