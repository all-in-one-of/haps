import re, sys, os
from copy import deepcopy

def split_shader_to_body_and_args(shader_string):
    block = re.compile(
    ur"(shader)(.*?)(\{)", re.IGNORECASE | re.DOTALL | re.MULTILINE)
    data = [result[1] for result in re.findall(block, shader_string)]
    body = shader_string.replace(data[0], "")
    return data[0].replace("", ""), body.replace("shader", "")



def find_metadata(shader_string):
    block = re.compile(
    ur"(\[\[)(.*?)(\]\])", re.IGNORECASE | re.DOTALL | re.MULTILINE)
    data = [result[1] for result in re.findall(block, shader_string)]
    code = deepcopy(shader_string)
    for d in data:
        code = code.replace(d, "")
    code = code.replace("[[]]", "")
    data = [[line.strip() for line in result.split("\n") if line] for result in data]
    return data, code

def process_metadata(meta):
    parms = []
    for parm_group in meta:
        group = {}
        for line in parm_group:
            parm = {}
            if not line:
                continue
            fields = line.split(" ")
            fields = [field.strip() for field in fields if field]
            fields = [field.strip(",") for field in fields if field]
            fields = [field.strip('"') for field in fields if field]
            tokens = fields

            assert(len(tokens) >= 4)
            parm['type'] = tokens[0]
            parm['name'] = tokens[1]
            if parm['name'] != "help":
                parm['value'] = tokens[3]
            else:
                parm['value'] = " ".join(tokens[3:])
            group[parm['name']] = deepcopy(parm)
        parms += [group]

    return parms

def create_ds_string(metas):

    node = """ {sb}
         name appleseed
        label "Appleseed"

    {parms}\n{eb}
    """

    parm = """parm {sb}
        name    "{name_}"
        label   "{label_}"
        type    {type_}
        default {sb} {default_} {eb}
        range   {sb} {min_} {max_} {eb}
        help    "{help_}"
        parmtag {sb} {tag_} {eb}
    {eb}\n"""

    name = 'parm'
    label = 'parm'
    type_ = 'float'
    default = '0.0'
    _min  = '0.0'
    _max  = '1.0'
    help = ""
    tag = ""
    output = ""
    parms = ""

    for meta in metas:
        # print meta.keys()
        if 'as_maya_attribute_name' in meta:
            name = meta['as_maya_attribute_name']['value']
        if 'label' in meta:
            label = meta['label']['value']
        if 'min' in meta:
            _min = meta['min']['value']
        if 'max' in meta:
            _max = meta['max']['value']
        if 'help' in meta:
            help = meta['help']['value']
        ds = parm.format(name_=name, label_=label, type_=type_, 
            default_=default, min_=_min, max_=_max, help_=help, 
            tag_=tag, sb="{", eb="}")
        parms += ds

    output = node.format(parms=parms, sb='{', eb='}')
    return output


def main():
    import os
    if len(sys.argv) < 2:
        return 1

    filename = sys.argv[1]
    basename = os.path.splitext(filename)[0]
    dsfilename = basename + ".ds"
    codefilename = basename + ".code"
    parms = ""

    with open(filename) as file:
        shader = file.read()
        metas, code  = find_metadata(shader)
        metas  = process_metadata(metas)
        param  = create_ds_string(metas)
        args, body = split_shader_to_body_and_args(code)
        print "SHADER ARGUMENTS: "
        print args
        print "SHADER BODY:"
        print body

    with open(dsfilename, 'w') as file:
        file.write(param)

    with open(codefilename, 'w') as file:
        file.write(str(code))



if __name__=="__main__":main()

"""
    - glob into folder -> [files] (appleseed/shaders/*.osl)
    - for every file in files:
        - read file to shader_string
        - extract meta data end shader's (args, body)
        - generate *.ds file from meta data (create_ds_string())
        - generate hda from *.ds (ds2hda.py)
        - edit hda definition (definition = hou.hdaDefinition(filename.hda, assetname):
            - put code into code tab
            - create inputs (based on args)
            - create output (based on args)
            - create node help from metadata 
        - save HDA


"""