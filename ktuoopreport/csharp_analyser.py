"""
    Copyright (C) 2022 - Rokas Puzonas <rokas.puz@gmail.com>

    This file is part of KTU OOP Report Generator.

    KTU OOP Report Generator is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    KTU OOP Report Generator is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with KTU OOP Report Generator. If not, see <https://www.gnu.org/licenses/>.
"""
from typing import Iterable, Optional
from lark.lark import Lark
from lark.lexer import Token
from lark.tree import ParseTree, Tree
from .class_diagram import EnumDiagram, VisibilityEnum, ParameterDirection, ClassAttribute, ClassMethodParameter, ClassMethod, ClassDiagram

# NOTE: This parser assumes that the c# file has not syntax errors.
# Because I am not validating if something looks logical or not.

# BUG: Methods only support strings and numbers as default parameter values

# BUG: Doesn't support partial classess

l = Lark(r"""
    start: namespace_import* namespace_definition

    IDENTIFIER_NAME: /[a-zA-Z0-9_\.]+/
    !type_name: IDENTIFIER_NAME
             | IDENTIFIER_NAME "[" ","* "]"
             | IDENTIFIER_NAME "<" (type_name ",")* type_name ">"

    SIGNED_INTEGER: /[+-]?(0|[1-9][0-9]*)/

    ANY_VALUE: /.+/

    namespace_import: "using" IDENTIFIER_NAME ";"

    namespace_definition: "namespace" IDENTIFIER_NAME "{" namespace_block "}"
    namespace_block: (class_definition | enum_definition)*

    VISIBILITY: "private" | "public" | "protected"
    modifier: (VISIBILITY | "static")~1..2

    enum_definition.2: modifier? "enum" IDENTIFIER_NAME [":" IDENTIFIER_NAME] "{" enum_block? "}"
    enum_block: (IDENTIFIER_NAME ",")* IDENTIFIER_NAME

    class_definition.2: modifier? "partial"? "class" IDENTIFIER_NAME [":" IDENTIFIER_NAME] "{" class_block "}"
    class_block: (method | attribute)*

    attribute.2: modifier? type_name IDENTIFIER_NAME (("=" ATTRIBUTE_VALUE) | ";")
             | modifier type_name IDENTIFIER_NAME "{ " VISIBILITY? "get;" VISIBILITY? "set; }" ["=" ATTRIBUTE_VALUE]
    ATTRIBUTE_VALUE: /.+/ ";"

    method.2: modifier? "override"? return_type? IDENTIFIER_NAME "(" method_parameters? ")" "{" _METHOD_BLOCK* "}"
    !return_type: "void" | type_name
    method_parameters.2: (method_parameter ",")* method_parameter
    method_parameter: METHOD_DIRECTION? type_name IDENTIFIER_NAME ["=" METHOD_PARAMETER_DEFAULT]
    METHOD_DIRECTION: "ref" | "out"
    METHOD_PARAMETER_DEFAULT: SIGNED_INTEGER | STRING
    _METHOD_BLOCK: ANY_VALUE

    %import common.WS
    %import common.C_COMMENT
    %import common.CPP_COMMENT
    %import common.ESCAPED_STRING -> STRING
    %ignore C_COMMENT
    %ignore CPP_COMMENT
    %ignore WS
""")

def find_direct_child_token(tree: ParseTree, token: str) -> Optional[Token]:
    for child in tree.children:
        if isinstance(child, Token) and child.type == token:
            return child

def find_direct_child_rule(tree: ParseTree, token: str) -> Optional[ParseTree]:
    for child in tree.children:
        if isinstance(child, Tree) and child.data == token:
            return child

def find_namespace_names(tree: ParseTree) -> Iterable[tuple[ParseTree, str]]:
    for namespace_node in tree.find_data("namespace_definition"):
        name = find_direct_child_token(namespace_node, "IDENTIFIER_NAME")
        assert name
        yield (namespace_node, name.value)

def find_class_names(tree: ParseTree) -> Iterable[tuple[ParseTree, str]]:
    for class_node in tree.find_data("class_definition"):
        name = find_direct_child_token(class_node, "IDENTIFIER_NAME")
        assert name
        yield (class_node, name.value)

def find_visibility(tree: ParseTree) -> Optional[VisibilityEnum]:
    modifier = find_direct_child_rule(tree, "modifier")
    if not modifier:
        return VisibilityEnum.Private

    visibility = find_direct_child_token(modifier, "VISIBILITY")
    if not visibility:
        return VisibilityEnum.Private

    if visibility.value == "public":
        return VisibilityEnum.Public
    elif visibility.value == "private":
        return VisibilityEnum.Private
    elif visibility.value == "protected":
        return VisibilityEnum.Protected
    else:
        return VisibilityEnum.Private

def find_type_name(tree: ParseTree, token: str = "type_name") -> Optional[str]:
    type_name = find_direct_child_rule(tree, token)
    if not type_name:
        return None

    return "".join(type_name.scan_values(lambda v: isinstance(v, Token)))

def find_attributes(tree: ParseTree) -> Iterable[ClassAttribute]:
    for attr_node in tree.find_data("attribute"):
        name = find_direct_child_token(attr_node, "IDENTIFIER_NAME")
        assert name
        attr_type = find_type_name(attr_node)
        assert attr_type
        visibility = find_visibility(attr_node)
        assert visibility
        initial_value = find_direct_child_token(attr_node, "ATTRIBUTE_VALUE")
        if initial_value:
            initial_value = initial_value.value[:-1].strip()
        yield ClassAttribute(name.value, attr_type, visibility, initial_value)

def find_method_parameters(tree: ParseTree) -> list[ClassMethodParameter]:
    parameters_node = find_direct_child_rule(tree, "method_parameters")
    if not parameters_node:
        return []

    parameters = []
    for parameter_node in parameters_node.find_data("method_parameter"):
        parameter_name = find_direct_child_token(parameter_node, "IDENTIFIER_NAME")
        assert parameter_name

        parameter_type = find_type_name(parameter_node, "type_name")
        assert parameter_type

        parameter_default = find_direct_child_token(parameter_node, "METHOD_PARAMETER_DEFAULT")
        if parameter_default:
            parameter_default = parameter_default.value

        direction = ParameterDirection.In
        direction_node = find_direct_child_token(parameter_node, "METHOD_DIRECTION")
        if direction_node:
            if direction_node.value == "ref":
                direction = ParameterDirection.InOut
            elif direction_node.value == "out":
                direction = ParameterDirection.Out

        parameters.append(ClassMethodParameter(
            name = parameter_name.value,
            type = parameter_type,
            direction = direction,
            default = parameter_default
        ))

    return parameters

def find_methods(tree: ParseTree) -> Iterable[ClassMethod]:
    for method_node in tree.find_data("method"):
        name = find_direct_child_token(method_node, "IDENTIFIER_NAME")
        assert name

        return_type = find_type_name(method_node, "return_type")

        visibility = find_visibility(method_node)
        assert visibility

        parameters = find_method_parameters(method_node)

        yield ClassMethod(name.value, return_type, visibility, parameters)

def find_class_diagrams(tree: ParseTree) -> Iterable[ClassDiagram]:
    for (namespace_node, namespace_name) in find_namespace_names(tree):
        for (class_node, class_name) in find_class_names(namespace_node):
            yield ClassDiagram(
                namespace = namespace_name,
                name = class_name,
                attributes = list(find_attributes(class_node)),
                methods = list(find_methods(class_node))
            )

def find_enum_names(tree: ParseTree) -> Iterable[tuple[ParseTree, str]]:
    for enum_node in tree.find_data("enum_definition"):
        name = find_direct_child_token(enum_node, "IDENTIFIER_NAME")
        assert name
        yield (enum_node, name.value)

def find_enum_diagrams(tree: ParseTree) -> Iterable[EnumDiagram]:
    for (namespace_node, namespace_name) in find_namespace_names(tree):
        for (enum_node, enum_name) in find_enum_names(namespace_node):
            enum_block = find_direct_child_rule(enum_node, "enum_block")
            assert enum_block

            values = []
            for value_node in enum_block.children:
                assert isinstance(value_node, Token)
                values.append(value_node.value)

            yield EnumDiagram(
                namespace = namespace_name,
                name = enum_name,
                values = values
            )

def extract_diagrams(filename: str) -> list[ClassDiagram | EnumDiagram]:
    contents = None
    with open(filename, "r", encoding="utf-8-sig") as f:
        contents = f.read()
    assert contents

    tree = l.parse(contents)
    diagrams = []
    diagrams.extend(find_class_diagrams(tree))
    diagrams.extend(find_enum_diagrams(tree))
    return diagrams
