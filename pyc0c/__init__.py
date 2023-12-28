from importer import importer
importer("../../pyltr/pyltr", __file__)
importer("../../pycdb/pycdb", __file__)
importer("../../gid/gid", __file__)

from pathlib import Path
from pycdb.precedence import prectable

import pyltr

def btypes():
	bt = ["float", "double", "int", "long", "void", "char", "bool"]
	for w in [8, 16, 32, 64]:
		bt.append(f"u{w}")
		bt.append(f"i{w}")
	return bt

builtins = {
	"type": set(btypes()),
	"op2": set(sum([prectable[idx] for idx in
		[1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]], [])),
	"op1": set(prectable[2]),
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
	commands = {}
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
		if rule[1].startswith("keyword/"):
			commands[rule2[1].removeprefix("keyword/")] = rule2
	return commands
commands = ruletable()
