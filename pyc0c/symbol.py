# symbol table analysis

from gid import gid2c
from pycdb import btypes, consts, opprec
from . import commands
from .symdb import resolve_external

# symbolman.analyze takes a list of blocks
# compute all the required symbol information(blockwise), stored in itself
class Symbolman:
	def __init__(self, gids): # gid[0] must be self
		self.gids = gids
		self.camels = [gid2c(g, "camel") for g in gids]
		self.snakes = [gid2c(g, "snake") for g in gids]
		self.parsing_public = False
		self.locals = []

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
	def gid_match(self, sym):
		if sym[0].isupper():
			for gid, camel in zip(self.gids, self.camels):
				if sym.startswith(camel):
					return gid
		else:
			for gid, snake in zip(self.gids, self.snakes):
				if sym.startswith(snake):
					return gid
		return None
	def add_symbol(self, sym, istype):
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
		if sym in consts:
			return
		ns = self.gid_match(sym)
		if ns != None:
			self.kjkj[sym] = ns
		else:
			ns = resolve_external(sym, istype)
			self.external[sym] = ns
		if self.parsing_public:
			self.header_includes.add(ns)
		else:
			self.src_includes.add(ns)
	def uniform(self, j, rule_name):
		assert rule_name.startswith("nonterm/")
		match rule_name.removeprefix("nonterm/"):
			case "declare":
				self.locals[-1].add(j[0])
			case "designated":
				pass
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
	def analyze(self, blocks):
		# first round
		for block in blocks:
			assert block[0] in ["fn", "struct", "union"]
			ret = self.gid_match(block[1])
			self.defined.append(block[1])
			self.isexports.append(ret != None)
		# second round
		for (isexport, block) in zip(self.isexports, blocks):
			self.parsing_public = isexport
			self.locals.append(set())
			self.analyze_rule(block, "nonterm/block")
			self.locals.pop()
