from importer import importer
importer("../../pyltr/pyltr", __file__)
importer("../../pycdb/pycdb", __file__)
importer("../../syslib/syslib", __file__)
importer("../../pyc0parse/pyc0parse", __file__)
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
