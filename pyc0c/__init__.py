from importer import importer
importer("../../pyltr/pyltr", __file__)
importer("../../pycdb/pycdb", __file__)

from pathlib import Path
from pycdb.precedence import table

import pyltr

kinds = ["ident", "keyword", "nonterm", "nonterms", "builtin"]

def btypes():
	bt = ["float", "double", "int", "long", "void", "char", "bool"]
	for w in [8, 16, 32, 64]:
		bt.append(f"u{w}")
		bt.append(f"i{w}")
	return bt

builtins = {
	"type": set(btypes()),
	"op2": set(["+", "-", "*", "/", "%",
		"&", "|", "^", "&&", "||", "<<", ">>",
		">", ">=", "<", "<=", "==", "!=",
		".", ",", "->", "@"] + table[14]),
	"op1": set(["!", "~", "&p", "*p", "+n", "-n"]),
}

def mapliteral(term):
	assert isinstance(term, str)
	if term == "*":
		return f"special/*"
	if "/" not in term:
		return f"nonterm/{term}"
	return term

def ruletable():
	lines = []
	path = Path(__file__).parent / "syntax.txt"
	s = pyltr.striphash(open(path).read())
	rules = pyltr.parse_flat(s)
	rules2 = {}
	for rule in rules:
		rule2 = []
		for term in rule:
			if isinstance(term, list):
				result = []
				for subterm in term:
					result.append(mapliteral(subterm))
				rule2.append(result)
			else:
				rule2.append(mapliteral(term))
		rules2[(rule2[0], rule2[1])] = rule2
	return rules2
rules = ruletable()
