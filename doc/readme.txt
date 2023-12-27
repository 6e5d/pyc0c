# syntax(parsing) design

* program is a tree.

* there are 3 types of node: tuple, list, literal. Leaf = literal.

* list must contain arbitrary number of objects of same type.

* list must be child of tuple.

* list are not parsed, they are parsed during parsing their parent.

* when parsing a tuple,
the only context needed is the type(a string) of current tuple.

* type, such as `stmt`, `expr`, is known as "non-terminal" in production rules.

* the head(first child) of a tuple must be a literal.

* the syntax rule of current tuple can be determined by checking type
and the head only.

* a struct must match a syntax rule,
which define a fixed number of children of fixed types.
E.g. `[begin stmt1 stmt2 ...]` is invalid.

* Applying the rule and all children node get their type,
and the type is passed downward to do parsing recursively.
