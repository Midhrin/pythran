'''
This modules contains OpenMP-related stuff.
    * OMPDirective is used to represent OpenMP annotations in the AST
    * GatherOMPData turns OpenMP-like string annotations into metadata
'''

import metadata
from ast import AST
import ast
import re
from passmanager import Transformation

keywords = {
        'atomic',
        'barrier',
        'collapse',
        'copyin',
        'copyprivate',
        'default',
        'firstprivate',
        'final',
        'flush',
        'for',
        'if',
        'lastprivate',
        'none',
        'nowait',
        'num_threads',
        'omp',
        'ordered',
        'parallel',
        'private',
        'reduction',
        'schedule',
        'section',
        'sections',
        'shared',
        'single',
        'task',
        'taskwait',
        'taskyield',
        'threadprivate',
        'untied',
        }

reserved_contex = {
        'default',
        'schedule',
        }


class OMPDirective(AST):
    '''
    Turn a string into a context-dependent metadata.
    '''

    def __init__(self, s):

        self.deps = []

        def tokenize(s):
            # not completely satisfying if there are strings in if expressions
            out = ''
            par_count = 0
            curr_index = 0
            in_reserved_context = False
            while curr_index < len(s):
                m = re.match('^([a-zA-Z_]\w*)', s[curr_index:])
                if m:
                    word = m.group(0)
                    curr_index += len(word)
                    if (in_reserved_context
                            or (par_count == 0 and word in keywords)):
                        out += word
                        in_reserved_context = word in reserved_contex
                    else:
                        v = '{}'
                        self.deps.append(ast.Name(word, ast.Param()))
                        out += v
                elif s[curr_index] == '(':
                    par_count += 1
                    curr_index += 1
                    out += '('
                elif s[curr_index] == ')':
                    par_count -= 1
                    curr_index += 1
                    out += ')'
                    if par_count == 0:
                        in_reserved_context = False
                else:
                    if s[curr_index] == ',':
                        in_reserved_context = False
                    out += s[curr_index]
                    curr_index += 1
            return out

        self.s = tokenize(s)
        self._fields = ('deps',)

    def __str__(self):
        return self.s.format(*[n.id for n in self.deps])


##
class GatherOMPData(Transformation):
    '''
    Walks node and collect string comments looking for OpenMP directives.
    '''

    # there is a special handling for If and Expr, so not listed here
    statements = ("FunctionDef", "Return", "Delete", "Assign", "AugAssign",
            "Print", "For", "While", "Raise", "TryExcept", "TryFinally",
            "Assert", "Import", "ImportFrom", "Pass", "Break",)

    # these fields hold statement lists
    statement_lists = ("body", "orelse", "finalbody",)

    def __init__(self):
        Transformation.__init__(self)
        for s in GatherOMPData.statements:
            setattr(self, "visit_" + s, lambda node_: self.attach_data(node_))
        self.current = list()

    def isompdirective(self, node):
        return isinstance(node, ast.Str) and node.s.startswith("omp ")

    def visit_Expr(self, node):
        if self.isompdirective(node.value):
            self.current.append(node.value.s)
            return None
        else:
            self.attach_data(node)
        return node

    def visit_If(self, node):
        if self.isompdirective(node.test):
            self.visit(ast.Expr(node.test))
            return self.visit(ast.If(ast.Num(1), node.body, node.orelse))
        else:
            return self.attach_data(node)

    def attach_data(self, node):
        if self.current:
            for curr in self.current:
                md = OMPDirective(curr)
                metadata.add(node, md)
            self.current = list()
        # add a Pass to hold some directives
        for field_name, field in ast.iter_fields(node):
            if field_name in GatherOMPData.statement_lists:
                if (field
                        and isinstance(field[-1], ast.Expr)
                        and self.isompdirective(field[-1].value)):
                    field.append(ast.Pass())
        self.generic_visit(node)
        return node
