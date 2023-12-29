from . import builtins
from pycdb import opprec

class Translator:
	def __init__(self):
		self.output = []
		self.indent = 0
	def newline(self):
		self.add("\n" + "\t" * self.indent)
	def scopein(self):
		self.add("{")
		self.indent += 1
	def scopeout(self):
		self.indent -= 1
		self.newline()
		self.add("}")
	def add(self, *args):
		self.output += args
	def declare2(self, var, ty):
		l = []
		while isinstance(ty, list):
			l.append(ty)
			ty = ty[1]
		assert isinstance(ty, str)
		build = f"{var}"
		for ll in l:
			match ll[0]:
				case "Array":
					build += f"[{ll[2]}]"
				case "Arg":
					at = self.argtype(ll[2])
					build += at
				case "Argbind":
					at = self.argbind(ll[2])
					build += at
				case "Ptr":
					build = f"(*{build})"
				case "Struct":
					ty = f"struct {ty}"
				case "Union":
					ty = f"union {ty}"
				case x:
					raise Exception(ty, ll)
		return ty + " " + build
	def declare(self, var, ty):
		s = self.declare2(var, ty)
		self.add(s)
	def op1(self, r, prec):
		if prec <= 1:
			self.add("(")
		if r[0] == "*p":
			self.add("*")
		elif r[0] == "&p":
			self.add("&")
		elif r[0] == "+n":
			self.add("+")
		elif r[0] == "-n":
			self.add("-")
		else:
			self.add(r[0])
		self.expr(r[1], 2)
		if prec <= 1:
			self.add(")")
	def op2(self, r, prec):
		prec2 = opprec(r[0])
		assert prec2 != None
		if prec2 >= prec:
			self.add("(")
		self.expr(r[1], prec2)
		self.add(r[0])
		self.expr(r[2], prec2)
		if prec2 >= prec:
			self.add(")")
	def sval(self, sv):
		self.scopein()
		for var, val in sv:
			self.newline()
			self.add(".")
			self.add(var)
			self.add(" = ")
			self.expr(val, 15)
			self.add(",")
		self.scopeout();
	def aval(self, av):
		self.scopein()
		self.newline()
		for val in av:
			self.expr(val, 15)
			self.add(",")
		self.scopeout();
	def expr(self, r, prec):
		match r[0]:
			case "begin":
				self.scopein()
				for rr in r[1:]:
					self.newline()
					if self.expr(rr, 16) not in [
						"begin",
						"cond",
						"case",
						"while",
						"for",
					]:
						self.add(";")
				self.scopeout()
				return r[0]
			case "set" | "var":
				self.declare(r[1], r[2])
				if r[0] == "set":
					self.add(" = ")
					self.expr(r[3], 14)
				return
			case "sval":
				self.sval(r[1:])
				return
			case "aval":
				self.aval(r[1:])
				return
			case "continue":
				self.add("continue")
				return
			case "break":
				self.add("break")
				return
			case "nop":
				return
			case "return":
				self.add("return ")
				self.expr(r[1], 16)
				return
			case "returnvoid":
				self.add("return")
				return
			case "sizeof":
				self.add("sizeof(")
				self.declare("", r[1])
				self.add(")")
				return
			case "cond":
				for idx, branch in enumerate(r[1:]):
					if idx > 0:
						self.add("else ")
					self.add("if")
					self.add("(")
					self.expr(branch[0], 16)
					self.add(")")
					self.expr(branch[1], 16)
				return r[0]
			case "while":
				self.add("while")
				self.add("(")
				self.expr(r[1], 16)
				self.add(")")
				self.expr(r[2], 16)
				return r[0]
			case "for":
				self.add("for")
				self.add("(")
				self.expr(r[1], 16)
				self.add(";")
				self.expr(r[2], 16)
				self.add(";")
				self.expr(r[3], 16)
				self.add(")")
				self.expr(r[4], 16)
				return r[0]
			case "goto":
				assert isinstance(r[1], str)
				self.add("goto ")
				self.add(r[1])
				return
			case "label":
				self.add(r[1])
				self.add(":;")
				return
			case "@":
				self.expr(r[1], 1)
				self.add("[")
				self.expr(r[2], 1)
				self.add("]")
				return
			case "lit":
				if r[1] == "char":
					self.add(f"'{r[2]}'")
				elif r[1] == "str":
					self.add(f'"{r[2]}"')
				else:
					self.add(r[2])
				return
			case "cast":
				if prec <= 1:
					self.add("(")
				self.add("(")
				self.declare("", r[1])
				self.add(")")
				self.expr(r[2], 2)
				if prec <= 1:
					self.add(")")
				return
			case "sizeof":
				self.add("sizeof(")
				self.declare("", r[1])
				self.add(")")
				return
		# the above cases are in op1/op2 but needs special handling
		if isinstance(r, str):
			# expr = single var
			self.add(r)
			return
		if isinstance(r[0], str):
			if r[0] in builtins["op2"]:
				self.op2(r, prec)
				return
			elif r[0] in builtins["op1"]:
				self.op1(r, prec)
				return
		# call
		self.expr(r[0], 1)
		self.argval(r[1:])
	def argtype(self, r):
		result = ["("]
		first = True
		for ty in r:
			if first:
				first = False
			else:
				result.append(",")
			result.append(self.declare2("", ty))
		if first:
			result.append("void")
		result.append(")")
		return "".join(result)
	def fields(self, r):
		self.scopein()
		for var, ty in r:
			self.newline()
			self.add(self.declare2(var, ty))
			self.add(";")
		self.scopeout()
	def argbind(self, r):
		syms = "(,)"
		result = "("
		first = True
		for var, ty in r:
			if first:
				first = False
			else:
				result += ", "
			result += self.declare2(var, ty)
		if first:
			result += "void"
		result += ")"
		return result
	def argval(self, r):
		self.add("(")
		first = True
		for var in r:
			if first:
				first = False
			else:
				self.add(",")
			self.expr(var, 15)
		self.add(")")
	def translate_su(self, r, header):
		if header:
			self.add(f"typedef {r[0]} {r[1]} {r[1]}")
		else:
			self.add(f"{r[0]} {r[1]}")
			self.fields(r[2])
		self.add(";")
	def translate(self, r, header):
		match r[0]:
			case "fn":
				self.declare(r[1], ["Argbind", r[3], r[2]])
				if header:
					self.add(";")
				else:
					self.expr(r[4], 16)
			case "struct" | "union":
				self.translate_su(r, header)
			case x:
				raise Exception(x)
		output = self.output
		self.output = []
		return output
