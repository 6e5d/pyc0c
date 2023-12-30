from pyltr import parse_slit
from pyc0parse.symbol import Symbolman
from pyc0c.translate import Translator
from pycdb.gid2file import gid2file

debug = False

def build_files(sm):
	src_includes = []
	header_includes = []
	links = []
	for gid in sm.header_includes:
		incls2, links2 = gid2file(gid)
		header_includes += incls2
		links += links2
	for gid in sm.src_includes:
		incls2, links2 = gid2file(gid)
		src_includes += incls2
		links += links2
	return set(src_includes), set(header_includes), set(links)

def step2(proj, gids):
	stem = proj.stem
	ltr = parse_slit(open(proj / "build" / f"{stem}.c0").read())
	sm = Symbolman(gids)
	sm.analyze(ltr)
	if debug:
		print("reexports:", [x[-1] for x in sm.header_includes])
		print("dependencies:", [x[-1] for x in sm.src_includes])
	d = proj / "build"
	main = False
	src_includes, header_includes, links = build_files(sm)
	header_only = True
	with (
		open(d / f"{stem}.c", "w") as fc,
		open(d / f"{stem}.h", "w") as fh,
	):
		print(f'#include "{stem}.h"', file = fc)
		print(f"#pragma once", file = fh)
		for incl in set(header_includes):
			print(f"#include {incl}", file = fh)
		for incl in set(src_includes):
			print(f"#include {incl}", file = fc)
		t = Translator()
		# fn and struct declarations
		for idx, b in enumerate(ltr):
			if b[1] == "main":
				main = True
			code = t.translate(b, True)
			if sm.isexports[idx]:
				print("".join(code), file = fh)
			else:
				print("".join(code), file = fc)
		# struct definitions
		for idx, b in enumerate(ltr):
			if b[0] == "fn":
				continue
			code = t.translate(b, False)
			if sm.isexports[idx]:
				print("".join(code), file = fh)
			else:
				print("".join(code), file = fc)
		# function definitions
		for idx, b in enumerate(ltr):
			if b[0] != "fn":
				continue
			code = t.translate(b, False)
			header_only = False
			print("".join(code), file = fc)
	return main, links, header_only
