#!/usr/bin/env python3
import json, os
from google.protobuf import json_format
from itertools import chain
import protob.types_pb2 as types

HEADER_TEMPLATE = """
// This file is automatically generated by nem_mosaics.py -- DO NOT EDIT!

#ifndef __NEM_MOSAICS_H__
#define __NEM_MOSAICS_H__

#include "types.pb.h"

#define NEM_MOSAIC_DEFINITIONS_COUNT ({count})

extern const NEMMosaicDefinition NEM_MOSAIC_DEFINITIONS[NEM_MOSAIC_DEFINITIONS_COUNT];
extern const NEMMosaicDefinition *NEM_MOSAIC_DEFINITION_XEM;

#endif
""".lstrip()

CODE_TEMPLATE = """
// This file is automatically generated by nem_mosaics.py -- DO NOT EDIT!

#include "nem_mosaics.h"

const NEMMosaicDefinition NEM_MOSAIC_DEFINITIONS[NEM_MOSAIC_DEFINITIONS_COUNT] = {code};

const NEMMosaicDefinition *NEM_MOSAIC_DEFINITION_XEM = NEM_MOSAIC_DEFINITIONS;
""".lstrip()

def format_primitive(value):
    if type(value) is bool:
        return ("false", "true")[value]
    elif type(value) in (int, float):
        return str(value)
    elif type(value) is str:
        return json.dumps(value)
    elif type(value) is list:
        return "{ " + ", ".join(
            format_primitive(item) for item in value
        ) + " }"
    else:
        raise TypeError

def format_struct(struct):
    return "{\n" + "\n".join(
        "\t.{0} = {1},".format(member, value) for member, value in struct.items()
    ) + "\n}"


def format_field(field, value):
    if field.message_type is not None:
        raise TypeError
    elif field.enum_type:
        return "{0}_{1}".format(field.enum_type.name, field.enum_type.values_by_number[value].name)
    elif hasattr(value, "_values"):
        return format_primitive(value._values)
    else:
        return format_primitive(value)

def field_to_meta(field, value):
    if hasattr(value, "_values"):
        return ("{}_count".format(field.name), format_primitive(len(value._values)))
    else:
        return ("has_{}".format(field.name), format_primitive(True))

def message_to_struct(_message, proto):
    message = json_format.ParseDict(_message, proto())
    return dict(chain.from_iterable(
        (
            field_to_meta(field, value),
            (field.name, format_field(field, value)),
        ) for field, value in message.ListFields()
    ))

def format_message(message, proto):
    return format_struct(message_to_struct(message, proto))

def format_messages(messages, proto):
    return "{" + ",\n".join(
        format_message(message, proto) for message in messages
    ) + "}"

if __name__ == "__main__":
    os.chdir(os.path.abspath(os.path.dirname(__file__)))

    messages = json.load(open("nem_mosaics.json"))

    with open("nem_mosaics.h", "w+") as f:
        f.write(HEADER_TEMPLATE.format(count=format_primitive(len(messages))))

    with open("nem_mosaics.c", "w+") as f:
        f.write(CODE_TEMPLATE.format(code=format_messages(messages, types.NEMMosaicDefinition)))