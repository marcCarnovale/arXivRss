# -*- coding: utf-8 -*-
"""
boolean_parser.py

Implements parsing of boolean expressions into a tree structure and
reconstructing them back to string form.
"""

import re
from enum import Enum, auto
from typing import Dict, List, Optional, Union


class Conjunction(Enum):
    """
    Represents the type of logical conjunction between nodes.
    """
    MISSING = auto()
    AND = auto()
    OR = auto()
    NOT = auto()


class Node:
    """
    A node in the boolean expression parse tree.

    - 'delimiter': one of '(', '"' or None if this node isn't delimited.
    - 'data': text content for this node (e.g. "Bergelson", "Austin", etc.).
    - 'child': references a child node (for nested expressions).
    - 'next': references the sibling node in the same "row" or expression level.
    - 'parent': reference to the node's parent.
    - 'conjunction': relationship to the next node (AND, OR, NOT, or MISSING).
    """

    def __init__(self,
                 data: Optional[Union[str, int]] = None,
                 delimiter: Optional[str] = None):
        self.data = data
        self.delimiter = delimiter
        self.child: Optional[Node] = None
        self.next: Optional[Node] = None
        self.parent: Optional[Node] = None
        self.conjunction: Conjunction = Conjunction.MISSING

    def __repr__(self):
        return (f"Node(data={self.data}, delim={self.delimiter}, "
                f"conj={self.conjunction})")

    def set_child(self, child: "Node"):
        self.child = child
        child.parent = self

    def set_next(self, sibling: "Node"):
        self.next = sibling
        sibling.parent = self.parent


def parse_boolean_expression(expression: str,
                             delimiters: Dict[str, str] = {'(' : ')', '"' : '"'},
                             *,
                             AND: str = '&',
                             OR: str = '|',
                             NOT: str = '-') -> Node:
    """
    Parses a boolean expression into a tree structure.

    Examples of valid expressions:
      - "alpha & beta"
      - "(gamma | delta) & - (epsilon)"
      - '"quoted text" & (another)'
      - Nested parentheses, quotes, etc.

    :param expression: The input string containing the boolean expression.
    :param delimiters: A dict mapping a left delimiter to its matching right delimiter.
    :param AND:        The textual operator that denotes logical AND.
    :param OR:         The textual operator that denotes logical OR.
    :param NOT:        The textual operator that denotes logical NOT.
    :return:           The root Node of the parse tree.
    """
    # Escape the operator tokens for safe regex matching
    AND_esc = re.escape(AND)
    OR_esc  = re.escape(OR)
    NOT_esc = re.escape(NOT)

    # The stack will hold Node objects for each open delimiter context
    stack: List[Node] = []
    root: Optional[Node] = None

    i = 0
    length = len(expression)

    # We'll keep track of the 'current' node. On encountering a left delimiter,
    # we create a new node, push it on the stack, and set current to it.
    # On encountering a right delimiter, we pop from the stack, so that we move up.
    current: Optional[Node] = None

    while i < length:
        ch = expression[i]

        # Skip whitespace
        if ch.isspace():
            i += 1
            continue

        # -----------------------------------------
        # 1) LEFT DELIMITER DETECTED
        # -----------------------------------------
        if ch in delimiters:
            new_node = Node(delimiter=ch)  ### CHANGED

            # If we have no root, this becomes root
            if not root:
                root = new_node
            else:
                # If there's a current node, link as child or sibling
                if current:
                    # If current has no child, set it
                    if not current.child:
                        current.set_child(new_node)
                    else:
                        # Find the last sibling in the child list
                        sib = current.child
                        while sib.next:
                            sib = sib.next
                        sib.set_next(new_node)
                else:
                    # If there's a root but no current, it means
                    # we finished parsing something, and now see '(' again.
                    # We'll just treat this new node as a sibling of root (or root's siblings).
                    temp = root
                    while temp.next:
                        temp = temp.next
                    temp.set_next(new_node)

            stack.append(new_node)   # push
            current = new_node       # move 'current' down
            i += 1
            continue

        # -----------------------------------------
        # 2) RIGHT DELIMITER DETECTED
        # -----------------------------------------
        if stack and ch == delimiters.get(stack[-1].delimiter, None):
            # We found a matching right delimiter
            closed_node = stack.pop()
            # After closing, 'current' should be the node that was popped's parent
            # (or the top of the stack, if any remain)
            if stack:
                current = stack[-1]
            else:
                current = closed_node  # we've closed the root-level delimiter

            i += 1
            continue

        # -----------------------------------------
        # 3) OPERATORS: NOT, AND, OR
        # -----------------------------------------
        # We check if the substring from i matches NOT, AND, or OR in that order
        if expression[i:].startswith(NOT):
            # If there's no 'current', create a new Node for it
            if not current:
                current = Node()
                if not root:
                    root = current
            current.conjunction = Conjunction.NOT
            i += len(NOT)
            continue
        elif expression[i:].startswith(AND):
            if not current:
                current = Node()
                if not root:
                    root = current
            current.conjunction = Conjunction.AND
            i += len(AND)
            continue
        elif expression[i:].startswith(OR):
            if not current:
                current = Node()
                if not root:
                    root = current
            current.conjunction = Conjunction.OR
            i += len(OR)
            continue

        # -----------------------------------------
        # 4) PLAIN TEXT (DATA)
        # -----------------------------------------
        # If we are here, it's presumably text (keyword, author name, etc.)
        match = re.match(r'[^\s()"]+', expression[i:])
        if match:
            text = match.group(0)
            new_node = Node(data=text)

            if not root:
                # This data node is the root if nothing else
                root = new_node
                current = new_node
            else:
                if current:
                    # If current node is a delimiter with no child => set child
                    if not current.child:
                        current.set_child(new_node)
                    else:
                        # Otherwise, attach as a sibling to the last child
                        sib = current.child
                        while sib.next:
                            sib = sib.next
                        sib.set_next(new_node)
                    current = new_node
                else:
                    # If there's a root but current is None, attach as sibling of root
                    temp = root
                    while temp.next:
                        temp = temp.next
                    temp.set_next(new_node)
                    current = new_node
            i += len(text)
        else:
            # If we get here, there's a character that doesn't match any known pattern
            raise SyntaxError(f"Unexpected character '{ch}' at position {i} in expression:\n{expression}")

    # If the expression was entirely empty or had only whitespace
    if not root:
        root = Node(data="")

    return root


def process_tree(node: Node,
                 delimiters: Dict[str, str] = {'(' : ')', '"' : '"'}) -> str:
    """
    Reconstructs the boolean expression from the parse tree.

    :param node:       The starting node (root of the parse tree).
    :param delimiters: The dictionary mapping left delimiters to right.
    :return:           A string representing the reconstructed expression.
    """
    if not node:
        return ""

    result = ""

    # If node has a delimiter (e.g. '(' or '"'), append it
    if node.delimiter:
        result += node.delimiter

    # If node.data is present (i.e. plain text), append it
    if isinstance(node.data, str) and node.data.strip():
        # you might choose to ensure spacing if needed
        result += node.data

    # Recursively process the child node
    if node.child:
        result += process_tree(node.child, delimiters)

    # If node has a delimiter, close it
    if node.delimiter:
        right_delim = delimiters[node.delimiter]
        result += right_delim

    # Based on node's conjunction, add an operator string
    if node.conjunction != Conjunction.MISSING:
        # In many use-cases, you'd want a symbol like ' & ' or ' OR ' or ' NOT '
        # Here we just use node.conjunction.name for demonstration
        result += f" {node.conjunction.name} "

    # If the node has a sibling, process that
    if node.next:
        result += process_tree(node.next, delimiters)

    return result
