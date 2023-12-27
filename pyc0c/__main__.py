from pyltr import parse_flat
from .translate import Translator
import sys
j = parse_flat(sys.stdin.read())
t = Translator()
for jj in j:
	td = t.translate(jj, False)
	print("".join(td))
