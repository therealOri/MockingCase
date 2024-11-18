import beaupy
import ast
import os
import tokenize
from enum import Enum
from typing import Dict, Set, Optional, List, Tuple
from dataclasses import dataclass
from io import BytesIO
import token
from pystyle import Colors, Colorate


def clear():
    os.system("clear||cls")


def banner():
    banner="""

            ::::    ::::   ::::::::   ::::::::  :::    ::: :::::::::: :::::::::
            +:+:+: :+:+:+ :+:    :+: :+:    :+: :+:   :+:  :+:        :+:    :+:
            +:+ +:+:+ +:+ +:+    +:+ +:+        +:+  +:+   +:+        +:+    +:+
            +#+  +:+  +#+ +#+    +:+ +#+        +#++:++    +#++:++#   +#++:++#:
            +#+       +#+ +#+    +#+ +#+        +#+  +#+   +#+        +#+    +#+
            #+#       #+# #+#    #+# #+#    #+# #+#   #+#  #+#        #+#    #+#
            ###       ###  ########   ########  ###    ### ########## ###    ###


    -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
                            Made by: https://github.com/therealOri

"""
    colored_banner = Colorate.Horizontal(Colors.purple_to_blue, banner, 1)
    return colored_banner


class CaseStyle(Enum):
    MOCKING = "mocking"  # hElLo_WoRlD
    SNAKE = "snake"      # hello_world
    CAMEL = "camel"     # helloWorld
    PASCAL = "pascal"   # HelloWorld

@dataclass
class TransformConfig:
    """Configuration for the name transformer."""
    case_style: CaseStyle
    whitelist: Set[str]
    preserve_strings: bool
    dry_run: bool

# Set of built-in methods and attributes to ignore | may need to be updated with time.
PYTHON_BUILTINS = {
    # Built-in functions
    'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'breakpoint', 'bytearray',
    'bytes', 'callable', 'chr', 'classmethod', 'compile', 'complex', 'delattr',
    'dict', 'dir', 'divmod', 'enumerate', 'eval', 'exec', 'filter', 'float',
    'format', 'frozenset', 'getattr', 'globals', 'hasattr', 'hash', 'help',
    'hex', 'id', 'input', 'int', 'isinstance', 'issubclass', 'iter', 'len',
    'list', 'locals', 'map', 'max', 'memoryview', 'min', 'next', 'object',
    'oct', 'open', 'ord', 'pow', 'print', 'property', 'range', 'repr',
    'reversed', 'round', 'set', 'setattr', 'slice', 'sorted', 'staticmethod',
    'str', 'sum', 'super', 'tuple', 'type', 'vars', 'zip',

    # Common methods of built-in types
    'append', 'extend', 'insert', 'remove', 'pop', 'clear', 'index', 'count',
    'sort', 'reverse', 'copy', 'join', 'split', 'strip', 'lstrip', 'rstrip',
    'upper', 'lower', 'replace', 'startswith', 'endswith', 'find', 'rfind',
    'items', 'keys', 'values', 'get', 'update', 'add', 'remove', 'discard',

    # Special methods
    '__init__', '__str__', '__repr__', '__len__', '__getitem__', '__setitem__',
    '__delitem__', '__iter__', '__next__', '__contains__', '__call__', '__add__',
    '__sub__', '__mul__', '__div__', '__mod__', '__pow__', '__eq__', '__ne__',
    '__lt__', '__gt__', '__le__', '__ge__', '__name__'
}


def transform_with_tokens(source: str, name_map: Dict[str, str]) -> str:
    """Transform the code while preserving original formatting."""
    result = []
    prev_row = 1
    prev_col = 0
    source_bytes = source.encode('utf-8')
    tokens = list(tokenize.tokenize(BytesIO(source_bytes).readline))
    for token_info in tokens:
        token_type = token_info.type
        token_string = token_info.string
        start_row, start_col = token_info.start
        end_row, end_col = token_info.end

        if token_type == tokenize.ENCODING:
            continue

        # Add spaces n stuff to preserve formatting.
        if start_row > prev_row:
            result.append('' * (start_row - prev_row))
            prev_col = 0
        if start_col > prev_col:
            result.append(' ' * (start_col - prev_col))

        # Transform the token if it's in our name map.
        if token_type == token.NAME and token_string in name_map:
            result.append(name_map[token_string])
        else:
            result.append(token_string)

        prev_row, prev_col = end_row, end_col

    return ''.join(result)



class ImportTracker(ast.NodeVisitor):
    """Tracks imports and their usages."""
    def __init__(self):
        self.direct_imports = set()  # example | 'os' from 'import os'
        self.import_aliases = {}     # example | {'np': 'numpy'} from 'import numpy as np'
        self.from_imports = set()    # example | 'system' from 'from os import system'

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            if alias.asname:
                # Track aliased imports.
                self.import_aliases[alias.asname] = alias.name
            else:
                # Track direct imports.
                self.direct_imports.add(alias.name)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        for alias in node.names:
            if alias.asname:
                # Track aliased from-imports.
                self.import_aliases[alias.asname] = f"{node.module}.{alias.name}"
            else:
                # Track direct from-imports.
                self.from_imports.add(alias.name)
                if node.module:
                    self.direct_imports.add(node.module)



class StringPreservingTransformer(ast.NodeTransformer):
    """Preserves string literals during transformation."""
    def __init__(self):
        self.string_map: Dict[str, str] = {}
        self.counter = 0

    def visit_Str(self, node: ast.Constant):
        placeholder = f"__SPH_{self.counter}__" #SPH -> String Placeholder
        self.string_map[placeholder] = node.s
        self.counter += 1
        return ast.Str(s=placeholder)

    def restore_strings(self, code: str) -> str:
        """Restores original strings from placeholders."""
        for placeholder, original in self.string_map.items():
            code = code.replace(f"'{placeholder}'", f"'{original}'")
            code = code.replace(f'"{placeholder}"', f'"{original}"')
        return code



class NameCollector(ast.NodeVisitor):
    """Collects all names from Python code while respecting imports."""
    def __init__(self, whitelist: Set[str]):
        self.names: Set[str] = set()
        self.whitelist = whitelist
        self.import_tracker = ImportTracker()

    def should_collect(self, name: str) -> bool:
        return (name != 'self' and
                name not in PYTHON_BUILTINS and
                name not in self.whitelist and
                name not in self.import_tracker.direct_imports and
                name not in self.import_tracker.from_imports)

    def visit_Module(self, node: ast.Module):
        """First collect all imports, then process other names."""
        self.import_tracker.visit(node)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        if self.should_collect(node.id):
            self.names.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        if isinstance(node.value, ast.Name):
            value_id = node.value.id
            # If this is an aliased import, collect the alias name.
            if value_id in self.import_tracker.import_aliases:
                if self.should_collect(value_id):
                    self.names.add(value_id)
            elif value_id not in self.import_tracker.direct_imports:
                if value_id != 'self' and self.should_collect(value_id):
                    self.names.add(value_id)
                if self.should_collect(node.attr):
                    self.names.add(node.attr)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if self.should_collect(node.name):
            self.names.add(node.name)
        for arg in node.args.args:
            if self.should_collect(arg.arg):
                self.names.add(arg.arg)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        if self.should_collect(node.name):
            self.names.add(node.name)
        self.generic_visit(node)



class NameTransformer(ast.NodeTransformer):
    """Transforms names in python code according to a mapping."""
    def __init__(self, name_map: Dict[str, str], whitelist: Set[str], import_tracker: ImportTracker):
        self.name_map = name_map
        self.whitelist = whitelist
        self.import_tracker = import_tracker

    def should_transform(self, name: str) -> bool:
        return (name not in PYTHON_BUILTINS and
                name not in self.whitelist and
                name in self.name_map)

    def visit_Name(self, node: ast.Name):
        if node.id != 'self' and self.should_transform(node.id):
            node.id = self.name_map[node.id]
        return node

    def visit_Attribute(self, node: ast.Attribute):
        if isinstance(node.value, ast.Name):
            value_id = node.value.id
            if value_id not in self.import_tracker.direct_imports:
                if value_id != 'self' and self.should_transform(value_id):
                    node.value.id = self.name_map[value_id]
                if self.should_transform(node.attr):
                    node.attr = self.name_map[node.attr]
        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if self.should_transform(node.name):
            node.name = self.name_map[node.name]
        for arg in node.args.args:
            if arg.arg != 'self' and self.should_transform(arg.arg):
                arg.arg = self.name_map[arg.arg]
        self.generic_visit(node)
        return node

    def visit_ClassDef(self, node: ast.ClassDef):
        if self.should_transform(node.name):
            node.name = self.name_map[node.name]
        self.generic_visit(node)
        return node




def to_mocking_case(text: str) -> str:
    """Convert text to mOcKiNg_CaSe while preserving numbers and symbols."""
    result = []
    should_upper = False

    for char in text:
        if char.isalpha():
            result.append(char.upper() if should_upper else char.lower())
            should_upper = not should_upper
        else:
            result.append(char)

    return ''.join(result)

def to_snake_case(text: str) -> str:
    """Convert text to snake_case."""
    result = []
    for i, char in enumerate(text):
        if i > 0 and char.isupper():
            result.append('_')
        result.append(char.lower())
    return ''.join(result)

def to_camel_case(text: str) -> str:
    """Convert text to camelCase."""
    words = text.replace('-', '_').split('_')
    return words[0].lower() + ''.join(word.capitalize() for word in words[1:])

def to_pascal_case(text: str) -> str:
    """Convert text to PascalCase."""
    return ''.join(word.capitalize() for word in text.replace('-', '_').split('_'))




def transform_name(text: str, case_style: CaseStyle) -> str:
    """Transform text to the specified case style."""
    transform_functions = {
        CaseStyle.MOCKING: to_mocking_case,
        CaseStyle.SNAKE: to_snake_case,
        CaseStyle.CAMEL: to_camel_case,
        CaseStyle.PASCAL: to_pascal_case,
    }
    return transform_functions[case_style](text)


def transform_code(source_code: str, config: TransformConfig) -> Tuple[str, Dict[str, str]]:
    """Transform the code according to the configuration while respecting imports."""
    tree = ast.parse(source_code)
    collector = NameCollector(config.whitelist)
    collector.visit(tree)
    names = collector.names
    name_map = {name: transform_name(name, config.case_style) for name in names}
    transformed_code = transform_with_tokens(source_code, name_map)
    return transformed_code, name_map




if __name__ == '__main__':
    clear()
    print(f'{banner()}\n\n\n')
    file_path = beaupy.prompt("Path to the file you want to format - (drag & drop):")
    if not file_path:
        clear()
        quit()
    file_path = file_path.replace('\\', '').strip()

    # Get case style
    case_styles = [style.value for style in CaseStyle]
    style_choice = beaupy.select(case_styles, cursor_style="#ffa533")
    if not style_choice:
        clear()
        case_style = CaseStyle('snake')

    elif case_styles[0] in style_choice:
        case_style = CaseStyle('mocking')

    elif case_styles[1] in style_choice:
        case_style = CaseStyle('snake')

    elif case_styles[2] in style_choice:
        case_style = CaseStyle('camel')

    elif case_styles[3] in style_choice:
        case_style = CaseStyle('pascal')

    #Words you don't want to be modified.
    whitelist_input = beaupy.prompt('Provide names to whitelist (comma-separated) or press "enter" to skip:')
    whitelist = set(name.strip() for name in whitelist_input.split(',')) if whitelist_input else set()

    preserve_strings = beaupy.confirm("Preserve string literals?")
    dry_run = beaupy.confirm("Perform a dry run (preview changes)?")

    config = TransformConfig(
        case_style=case_style,
        whitelist=whitelist,
        preserve_strings=preserve_strings,
        dry_run=dry_run
    )

    with open(file_path, 'r') as fr:
        code = fr.read()

    transformed_code, name_map = transform_code(code, config)
    clear()
    print("\nName transformations:")
    for original, transformed in name_map.items():
        print(f"{original} -> {transformed}")

    print("\nTransformed code:")
    print(transformed_code)

    if not dry_run:
        output_file = 'transformed_code.py'
        with open(output_file, 'w') as fw:
            fw.write(transformed_code)
        print(f"\nCode written to {output_file}")
    else:
        print("\nDry run completed - no files were modified.")
