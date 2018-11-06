def dict2xml(d, root_node=None, level=0, indent=2):
    wrap          =  False if None == root_node or isinstance(d, list) else True
    root          = 'objects' if None == root_node else root_node
    root_singular = root[:-1] if 's' == root[-1] and None == root_node else root
    xml           = ''
    attr          = ''
    children      = []
    indents       = level
    space_char    = ' ' * indent
    tabs = space_char*indents
    key = ''

    if isinstance(d, dict):
        for key, value in dict.items(d):
            if isinstance(value, dict):
                children.append(dict2xml(value, key, level=indents+1, indent=indent))
            elif isinstance(value, list) and not False in \
                [isinstance(item, dict) for item in value]:
                children.append(dict2xml(value, key, level=indents+1, indent=indent))
            elif key.startswith('@'):
                attr = attr + ' ' + key[1::] + '="' + str(value) + '"'
            elif isinstance(value, list) and not key.startswith("#"):
                if isinstance(value[0], list):
                    value = value[0]
                value = ' '.join(map(str, value))
                xml = tabs + '<' + key + ">" + str(value) + '</' + key + '>\n' 
                children.append(xml)
            else:
                if key.startswith('#'):
                    assert(isinstance(value, list))
                    assert(isinstance(value[0], dict))
                    key = key[1:]
                    value = value[0]['value']
                    value = ' '.join(map(str, value))
                xml = tabs + '<' + key + ">" + str(value) + '</' + key + '>' 
                children.append(xml)

    else:
        #if list
        if not False in [isinstance(item, dict) for item in d]:
            for value in d:
                children.append(dict2xml(value, root_singular, level=indents+1, indent=indent))

    end_tag = '>\n' if 0 < len(children) else '/>\n'

    if wrap or isinstance(d, dict):
        xml = tabs + '<' + root + attr + end_tag

    if 0 < len(children):
        for child in children:
            xml = xml + child

        if wrap or isinstance(d, dict):
            xml = xml + tabs + '</' + root + '>\n'

    return xml