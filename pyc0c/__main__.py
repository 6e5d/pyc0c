from pyltr import parse_flat
from gid import path2gid
from .symbol import Symbolman
import sys
from pathlib import Path
j = parse_flat(sys.stdin.read())
sm = Symbolman([path2gid(Path(x).resolve()) for x in sys.argv[1:]])
sm.analyze(j)
for isexport, name in zip(sm.isexports, sm.defined):
	print(name, isexport)
print(sm.kjkj)
print(sm.external)
print(set(sm.kjkj.values()))
print(set(sm.external.values()))
print(sm.src_includes)
print(sm.header_includes)
