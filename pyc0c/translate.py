from . import builtins
from pycdb.precedence import opprec

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
	def declare2(self, ty, var, before, after):
		if isinstance(ty, str):
			self.add(ty, " ")
			self.add(before)
			self.add(var)
			self.add(after)
		match ty[0]:
			case "array":
				self.declare2(ty[1], var,
					before + "(", after)
				self.add("[", ty[2], "]", ")")
			case "arg":
				self.declare2(ty[1], var,
					before + "(", after)
				self.argtype(ty[2])
				self.add(")")
			case "ptr":
				self.declare2(ty[1], var,
					before + "*", after)
	def declare(self, ty, var):
		self.declare2(ty, var, "", "")
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
		if r[0] == "@":
			self.expr(r[1], 1)
			self.add("[")
			self.expr(r[2], 1)
			self.add("]")
			return
		prec2 = opprec(r[0])
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
	def expr(self, r, prec):
		if r[0] in builtins["op2"]:
			self.op2(r, prec)
		elif r[0] == "lit":
			if r[1] == "char":
				self.add(f"'{r[2]}'")
			elif r[1] == "str":
				self.add(f'"{r[2]}"')
			else:
				self.add(r[2])
		elif r[0] in builtins["op1"]:
			self.op1(r, prec)
		elif r[0] == "cast":
			if prec <= 1:
				self.add("(")
			self.add("(")
			self.declare(r[1], "")
			self.add(")")
			self.expr(r[2], 2)
			if prec <= 1:
				self.add(")")
		elif r[0] == "casts":
			if prec <= 1:
				self.add("(")
			self.add("(")
			self.declare(r[1], "")
			self.add(")")
			self.sval(r[2])
			if prec <= 1:
				self.add(")")
		elif r[0] == "sizeof":
			self.add("sizeof(")
			self.declare(r[1], "")
			self.add(")")
		elif isinstance(r, str):
			self.add(r)
		else:
			# call
			self.expr(r[0], 1)
			self.argval(r[1:])
	def stmt(self, r):
		match r[0]:
			case "begin":
				self.scopein()
				for rr in r[1:]:
					self.newline()
					self.stmt(rr)
				self.scopeout()
			case "set" | "sets" | "var":
				self.declare(r[2], r[1])
				if r[0] == "set":
					self.add(" = ")
					self.expr(r[3], 14)
				elif r[0] == "sets":
					self.add(" = ")
					self.sval(r[3], 14)
				self.add(";")
			case "return":
				self.add("return ")
				self.expr(r[1], 16)
				self.add(";")
			case "sizeof":
				self.add("sizeof ")
				self.declare(r[1], "")
				self.add(";")
			case "cond":
				for idx, branch in enumerate(r[1:]):
					if idx > 0:
						self.add("else ")
					self.add("if")
					self.add("(")
					self.expr(branch[0], 16)
					self.add(")")
					self.stmt(branch[1])
			case "while":
				self.add("while")
				self.add("(")
				self.expr(r[1], 16)
				self.add(")")
				self.stmt(r[2])
			case "for":
				self.add("for")
				self.add("(")
				self.stmt(r[1])
				self.expr(r[2], 16)
				self.add(";")
				self.expr(r[3], 16)
				self.add(")")
				self.stmt(r[4])
			case "goto":
				assert isinstance(r[1], str)
				self.add("goto ")
				self.add(r[1])
				self.add(";")
			case "label":
				self.add(r[1])
				self.add(":;")
			case "expr":
				self.expr(r[1], 16)
				self.add(";")
			case x:
				raise Exception(x)
	def argtype(self, r):
		self.add("(")
		first = True
		for ty in r:
			if first:
				first = False
			else:
				self.add(",")
			self.declare(ty, "")
		if first:
			self.add("void")
		self.add(")")
	def argbind(self, r, struct_style):
		if struct_style:
			syms = "{;}"
		else:
			syms = "(,)"
		self.add(syms[0])
		first = True
		for var, ty in r:
			if first:
				first = False
			else:
				self.add(syms[1])
			self.declare(ty, var)
		if first:
			if struct_style:
				raise Exception("empty struct not allowed")
			self.add("void")
		if struct_style:
			self.add(syms[1])
		self.add(syms[2])
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
	def translate(self, r, header):
		match r[0]:
			case "fn":
				self.declare(r[3], r[1])
				self.argbind(r[2], False)
				if header:
					self.add(";")
				else:
					self.stmt(r[4])
			case "struct":
				self.add("typedef ", "struct")
				self.argbind(r[2], True)
				self.add(r[1])
				self.add(";")
			case x:
				raise Exception(x)
		output = self.output
		self.output = []
		return output
