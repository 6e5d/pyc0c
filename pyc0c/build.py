from subprocess import run as prun
from buildc.cc import cc
from gid import path2gid
from .step2 import step2

def get_deps(proj):
	pgid = path2gid(proj)
	gids = [pgid]
	depfile = proj / ".lpat/deps.txt"
	if depfile.exists():
		for line in open(depfile):
			if "_" in line:
				# not c/ccc ns
				continue
			path = (proj.parent / line.strip()).resolve()
			gids.append(path2gid(path))
	sysfile = proj / ".lpat/syslib.txt"
	if sysfile.exists():
		for line in open(sysfile):
			gids.append(["com", "6e5d", "syslib"] +\
				line.strip().split("_"))
	return gids

def step3(proj, hasmain, links):
	stem = proj.stem
	d = proj / "build"
	cmd = cc()
	if hasmain:
		cmd += ["-fPIE", "-o", d / f"{stem}.elf"]
	else:
		cmd += ["-fPIC", "-shared", "-o", d / f"lib{stem}.so"]
	cmd += links
	cmd.append(d / f"{stem}.c")
	prun(cmd, check = True)

def buildc0c(proj):
	gids = get_deps(proj)
	hasmain, links, header_only = step2(proj, gids)
	if not header_only:
		step3(proj, hasmain, links)
