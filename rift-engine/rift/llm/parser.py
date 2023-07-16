from typing import Literal, List, Tuple
from tree_sitter import Language as TreeLanguage, Parser, Tree, Node
from dataclasses import dataclass
from textwrap import dedent

TreeLanguage.build_library(
  'build/my-languages.so',
  [ 'vendor/tree-sitter-c', 'vendor/tree-sitter-javascript', 'vendor/tree-sitter-python', 'vendor/tree-sitter-typescript/typescript']
)

Language = Literal["c", "javascript", "python", "typescript"]

Pos = Tuple[int, int]
Range = Tuple[Pos, Pos] # ((start_line, start_column), (end_line, end_column))

@dataclass
class FunctionDeclaration:
    name: str
    range: Range
    substring: Tuple[int, int] # (start_byte, end_byte)
    
def find_function_declarations(code: str, node: Node) -> List[FunctionDeclaration]:
    declarations: List[FunctionDeclaration] = []
    if node.type in ['function_definition', 'function_declaration']:
        for child in node.children:
            if child.type == 'function_declarator':
                id = child.children[0]
                if id.type == 'identifier':
                    declarations.append(FunctionDeclaration(
                        name=code[id.start_byte:id.end_byte],
                        range=(node.start_point, node.end_point),
                        substring=(node.start_byte, node.end_byte)
                    ))
        func_name = None
        # Iterate over the children of the function definition node and find the identifier
        for child in node.children:
            if child.type == 'identifier':
                func_name = code[child.start_byte:child.end_byte]
                break
        if func_name is not None:
            declarations.append(FunctionDeclaration(
                name=func_name,
                range=(node.start_point, node.end_point),
                substring=(node.start_byte, node.end_byte)
            ))
    elif node.type == 'lexical_declaration':
        # look for variable_declaration
        for child in node.children:
            if child.type == 'variable_declarator':
                # look for identifier and arrow_function
                is_arrow_function = False
                var_name = None
                for grandchild in child.children:
                    if grandchild.type == 'identifier':
                        var_name = code[grandchild.start_byte:grandchild.end_byte]
                    elif grandchild.type == 'arrow_function':
                        is_arrow_function = True
                if is_arrow_function and var_name is not None:
                    declarations.append(FunctionDeclaration(
                        name=var_name,
                        range=(node.start_point, node.end_point),
                        substring=(node.start_byte, node.end_byte)
                    ))
    return declarations

def get_tree_language(language: Language) -> TreeLanguage:
    if language == 'c':
        return TreeLanguage('build/my-languages.so', 'c')
    elif language == 'javascript':
        return TreeLanguage('build/my-languages.so', 'javascript')
    elif language == 'python':
        return TreeLanguage('build/my-languages.so', 'python')
    elif language == 'typescript':
        return TreeLanguage('build/my-languages.so', 'typescript')
    else:
        raise ValueError(f"Unknown language: {language}")
    
def parse_functions(code: str, language: Language) -> List[FunctionDeclaration]:
    parser = Parser()
    parser.set_language(get_tree_language(language))
    tree = parser.parse(code.encode())
    declarations: List[FunctionDeclaration] = []
    for node in tree.root_node.children:
        declarations += find_function_declarations(code, node)
    return declarations

if __name__ == "__main__":
    code = dedent("""
        int aa() {
          return 0;
        }

        void foo(int **x) {
          *x = 0;
        }

        int bb() {
          return 0;
        }

        int main() {
          int *x;
          foo(&x);
          *x = 1;
          return 0;
        }
    """).lstrip()
    declarations = parse_functions(code, 'c')
    print(f"Code:\n-----\n{code}\n----\n")
    for d in declarations:
        print(f"Found function: {d.name} at {d.range} substring: {d.substring}")
