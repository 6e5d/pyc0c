from gid import gid2c
std = ["free", "assert"]

def resolve_external(sym, istype):
	if not istype:
		if sym.startswith("mem"):
			return "std"
		if sym.startswith("str"):
			return "std"
		if sym.startswith("std"):
			return "std"
		if sym.endswith("alloc"):
			return "std"
		if sym.endswith("printf"):
			return "std"
		if sym in std:
			return "std"
		if sym.endswith("scanf"):
			return "std"
	if sym.startswith("Vk"):
		return "vulkan"
	if sym.startswith("Wl"):
		return "wayland"
	raise Exception(sym)
