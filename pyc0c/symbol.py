# symbol table analysis

from gid import gid2c
from pycdb import btypes, consts, opprec
from syslib import symtable
from . import commands

# symbolman.analyze takes a list of blocks
# compute all the required symbol information(blockwise), stored in itself
class Symbolman:
	def __init__(self, gids): # gid[0] must be self
		self.gids = gids
		self.camels = []
		self.snakes = []
		self.parsing_public = False
		self.locals = []
		self.missing = []

		externals = []
		for gid in gids:
			if gid[:3] == ["com", "6e5d", "syslib"]:
				externals.append(gid)
			else:
				self.camels.append(gid2c(gid, "camel"))
				self.snakes.append(gid2c(gid, "snake"))
		self.symtable = symtable(externals)

		# defined symbol name, corresponding to block
		self.defined = []
		# zipped with defined, whether it is statis/exported
		self.isexports = []

		# sym -> namespace
		self.kjkj = dict()
		# sym -> libname
		self.external = dict()

		self.src_includes = set()
		self.header_includes = set()
	def gid_match_ty(self, sym):
		for gid, camel in zip(self.gids, self.camels):
			if sym.startswith(camel):
				remain = sym.removeprefix(camel)
				if not remain or remain[0] == "_"\
					or remain[0].isupper():
					return gid
		return None
	def gid_match_fn(self, sym):
		for gid, snake in zip(self.gids, self.snakes):
			if sym.startswith(snake):
				remain = sym.removeprefix(snake)
				if not remain or remain[0] == "_":
					return gid
		return None
	def gid_match(self, sym):
		if sym[0].isupper():
			return self.gid_match_ty(sym)
		else:
			return self.gid_match_fn(sym)
	def add_symbol(self, sym, _istype):
		if not isinstance(sym, str):
			raise Exception(sym)
		if sym[0].isdigit():
			return
		if opprec(sym) != None:
			return
		if sym in btypes:
			return
		if sym in self.defined:
			return
		for l in self.locals:
			if sym in l:
				return
		# print(sym)
		if sym in consts:
			return
		ns = self.gid_match(sym)
		if ns != None:
			self.kjkj[sym] = ns
		else:
			if sym not in self.symtable:
				self.missing.append(sym)
				return
			ns = self.symtable[sym]
			self.external[sym] = ns
		if self.parsing_public:
			self.header_includes.add(tuple(ns))
		else:
			self.src_includes.add(tuple(ns))
	def uniform(self, j, rule_name):
		assert rule_name.startswith("nonterm/")
		match rule_name.removeprefix("nonterm/"):
			case "declare":
				self.locals[-1].add(j[0])
				self.analyze_rule(j[1], "nonterm/type")
			case "designated":
				self.analyze_rule(j[1], "nonterm/expr")
			case "branch":
				self.analyze_rule(j[0], "nonterm/expr")
				self.analyze_rule(j[1], "nonterm/expr")
			case "fields":
				self.analyze_rule(j[1], "nonterm/type")
			case x:
				raise Exception(x)
	def align(self, j, rule):
		if isinstance(j, str):
			if rule == "nonterm/type":
				self.add_symbol(j, True)
				return
			raise Exception(j, rule)
		if len(j) != len(rule):
			if rule[-1] != "special/*":
				raise Exception(j, rule)
		for idx, jj in enumerate(j):
			if idx >= len(rule) - 1 and rule[-1] == "special/*":
				rr = rule[-2]
			else:
				rr = rule[idx]
			if isinstance(rr, list):
				assert isinstance(jj, list)
				assert rr[1] == "special/*"
				for jjj in jj:
					self.uniform(jjj, rr[0])
				continue
			if isinstance(jj, list):
				self.analyze_rule(jj, rr)
			if rr.startswith("nonterm/"):
				self.analyze_rule(jj, rr)
				continue
			if rr == "ident/var":
				self.add_symbol(jj, False)
				continue
			if rr == "ident/field":
				continue
			if rr == "ident/type":
				self.add_symbol(jj, True)
				continue
			if rr == "ident/local":
				self.locals[-1].add(jj)
				continue
			if rr.startswith("keyword/"):
				assert rr.removeprefix("keyword/") == jj
				continue
			if rr == "builtin/type":
				continue
			raise Exception(rr)
	def analyze_rule(self, j, parent):
		# handle special(single definition sections)
		match parent:
			case "nonterm/branch":
				self.analyze_rule(j[0], "nonterm/expr")
				self.analyze_rule(j[1], "nonterm/expr")
				return
			case "nonterm/designated":
				self.analyze_rule(j[1], "nonterm/expr")
				return
			case "nonterm/fields":
				raise Exception("fields only in uniform")
			case "nonterm/declare":
				raise Exception("declares only in uniform")
		if isinstance(j, str):
			match parent:
				case "nonterm/type":
					self.add_symbol(j, True)
				case "nonterm/literal":
					pass
				case "nonterm/expr":
					self.add_symbol(j, False)
				case x:
					raise Exception(j, x)
			return
		if isinstance(j[0], str) and j[0] in commands:
			if j[0] == "begin":
				self.locals.append(set())
			self.align(j, commands[j[0]][1:])
			if j[0] == "begin":
				self.locals.pop()
			return
		if isinstance(j, list): # function call
			for jj in j:
				self.analyze_rule(jj, "nonterm/expr")
			return
	# toplevel: param types/return types/fields types
	# if the declaration itself is public(parsing_public == True)
	# if these types used external type, we have to reexport headers
	def analyze_toplevel(self, block):
		match block[0]:
			case "fn":
				for j in block[2]:
					self.uniform(j, "nonterm/declare")
				self.analyze_rule(block[3], "nonterm/type")
				self.parsing_public = False
				self.analyze_rule(block[4], "nonterm/expr")
			case "struct" | "union":
				for j in block[2]:
					self.uniform(j, "nonterm/fields")
			case x:
				raise Exception(x)
	def analyze(self, blocks):
		# first round
		for block in blocks:
			ret = self.gid_match(block[1])
			self.defined.append(block[1])
			self.isexports.append(ret != None)
		# second round
		for (isexport, block) in zip(self.isexports, blocks):
			self.parsing_public = isexport
			self.locals.append(set())
			self.analyze_toplevel(block)
			self.locals.pop()
		missing = set(self.missing)
		if missing:
			for sym in missing:
				print(sym)
			raise Exception("missing", len(missing), "symbols")
