from typing import List
from rift.llm.parser import Language, Range, parse_functions
from dataclasses import dataclass

@dataclass
class TextEdit:
    range: Range
    newText: str

def extract_code_blocks(msg: str) -> List[str]:
    """Extract code blocks from a message."""
    code_blocks = []
    code_block = ""
    in_code_block = False
    for line in msg.splitlines():
        if line.startswith("```"):
            if in_code_block:
                code_blocks.append(code_block)
                code_block = ""
                in_code_block = False
            else:
                in_code_block = True
        elif in_code_block:
            code_block += line + "\n"
    return code_blocks

def text_edits_from_code_blocks(code_blocks: List[str], document: str, language: Language) -> List[TextEdit]:
    """Generate a list of text edits from a list of code blocks.

    This function takes a list of code blocks, a document containing the original code, and the language of the code.
    It extracts the functions present in the document and compares them with the functions in each code block.
    If a function with the same name is found, the corresponding text edit is generated.

    Args:
        code_blocks (List[str]): A list of code blocks.
        document (str): The document containing the code.
        language (Language): The language of the code.

    Returns:
        List[TextEdit]: A list of TextEdit objects representing the required changes.

    """

    functions_in_document = parse_functions(document, language)
    text_edits: List[TextEdit] = []
    for block in code_blocks:
        functions_in_block = parse_functions(block, language)
        for bf in functions_in_block:
            # find if there is a function declaration with the same name in the file
            for df in functions_in_document:
                if bf.name == df.name:
                    newText = block[bf.substring[0]:bf.substring[1]]
                    text_edit = TextEdit(range=df.range, newText=newText)
                    text_edits.append(text_edit)
    return text_edits

from textwrap import dedent
    
class Test:
    document = dedent("""
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

    response = dedent("""
        To fix the error reported in the `main` function, you need to make the following changes:

        1. Modify the `foo` function to validate the pointer passed to it and assign it a value only if it is not null.
        2. Update the `main` function to handle the case where the pointer returned by `foo` is null.

        Here are the required changes:

        1. In the `foo` function, add a null check before assigning a value to `*x`:
        ```c
        void foo(int **x) {
          if (x != NULL) {
            *x = 0;
          }
        }
        ```

        2. In the `main` function, add a null check after calling `foo` and before dereferencing `x`:
        ```c
        int main() {
          int *x;
          foo(&x);

          if (x != NULL) {
            *x = 1;
          }

          return 0;
        }
        ```
    """).lstrip()
    
if __name__ == "__main__":
    language : Language = "c"
    code_blocks = extract_code_blocks(Test.response)
    text_edits = text_edits_from_code_blocks(code_blocks=code_blocks, document=Test.document, language=language)
    print(f"text edits: {text_edits}")
