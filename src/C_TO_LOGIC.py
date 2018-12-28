#!/usr/bin/env python
import sys

import os
from pycparser import c_parser, c_ast, c_generator
import copy
import pickle
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import math
import hashlib

from subprocess import Popen, PIPE
from collections import OrderedDict

import VHDL
import SW_LIB
import SYN
import VHDL_INSERT


RETURN_WIRE_NAME = "return_output"
SUBMODULE_MARKER = "____" # Hacky, need to be something unlikely as wire name
REF_TOK_DELIM = "__REF__" # This is dumb, so am I
DUMB_STRUCT_THING = "_ARRAY_STRUCT" # C is dumb, so am I
DEFAULT_LIBRARY_NAME = "work"
CONST_PREFIX="CONST_"
MUX_LOGIC_NAME="MUX"
UNARY_OP_LOGIC_NAME_PREFIX="UNARY_OP"
BIN_OP_LOGIC_NAME_PREFIX="BIN_OP"
CONST_REF_RD_FUNC_NAME_PREFIX = "CONST_REF_RD"
VAR_REF_ASSIGN_FUNC_NAME_PREFIX="VAR_REF_ASSIGN"
VAR_REF_RD_FUNC_NAME_PREFIX = "VAR_REF_RD"
RAW_HDL_PREFIX = "RAW_HDL"
BOOL_C_TYPE = "uint1_t"

# Unary Operators
UNARY_OP_NOT_NAME = "NOT"

# Binary operators
BIN_OP_GT_NAME = "GT"
BIN_OP_GTE_NAME = "GTE"
BIN_OP_LT_NAME = "LT"
BIN_OP_LTE_NAME = "LTE"
BIN_OP_PLUS_NAME = "PLUS"
BIN_OP_MINUS_NAME = "MINUS"
BIN_OP_EQ_NAME = "EQ"
BIN_OP_AND_NAME = "AND" # Ampersand?
BIN_OP_OR_NAME="OR"
BIN_OP_XOR_NAME = "XOR"
BIN_OP_SL_NAME = "SL"
BIN_OP_SR_NAME = "SR"
BIN_OP_MULT_NAME = "MULT"
BIN_OP_DIV_NAME = "DIV"


# TAKEN FROM https://github.com/eliben/pycparser/blob/c5463bd43adef3206c79520812745b368cd6ab21/pycparser/__init__.py
def preprocess_file(filename, cpp_path='cpp', cpp_args=''):
    """ Preprocess a file using cpp.
        filename:
            Name of the file you want to preprocess.
        cpp_path:
        cpp_args:
            Refer to the documentation of parse_file for the meaning of these
            arguments.
        When successful, returns the preprocessed file's contents.
        Errors from cpp will be printed out.
    """
    path_list = [cpp_path]
    if isinstance(cpp_args, list):
        path_list += cpp_args
    elif cpp_args != '':
        path_list += [cpp_args]
    path_list += [filename]

    try:
        # Note the use of universal_newlines to treat all newlines
        # as \n for Python's purpose
        #
        pipe = Popen(   path_list,
                        stdout=PIPE,
                        universal_newlines=True)
        text = pipe.communicate()[0]
    except OSError as e:
        raise RuntimeError("Unable to invoke 'cpp'.  " +
            'Make sure its path was passed correctly\n' +
            ('Original error: %s' % e))
    except Exception as e:
		print "Something went wrong preprocessing:"
		print "File:",filename
		raise e

    return text
    

def preprocess_text(text, cpp_path='cpp'):
	""" Preprocess a file using cpp.
        filename:
            Name of the file you want to preprocess.
        cpp_path:
        cpp_args:
            Refer to the documentation of parse_file for the meaning of these
            arguments.
        When successful, returns the preprocessed file's contents.
        Errors from cpp will be printed out.
    """
    
	path_list = [cpp_path]
	path_list += ["-"] # TO read from std in

	try:
		# Note the use of universal_newlines to treat all newlines
		# as \n for Python's purpose
		#
		pipe = Popen(   path_list,
						stdout=PIPE,
						stdin=PIPE,
                        universal_newlines=True)
        # Send in C text and get output
		text = pipe.communicate(input=text)[0]
	except OSError as e:
		raise RuntimeError("Unable to invoke 'cpp'.  " +
			'Make sure its path was passed correctly\n' +
			('Original error: %s' % e))

	return text

def casthelp(arg):
	try:
		print arg
	except:
		pass;
	
	try:
		arg.show()
	except:
		pass;
	
	try:	
		print dir(arg)
	except:
		pass; 
		
def LIST_UNION(self_a,b):
	# Ummm?
	if self_a == b:
		return self_a
	
	#return list( set().union(*[a,b]) )
	# uhh faster?
	self_a.extend(b)
	return list(set(self_a))
	

def C_AST_VAL_UNIQUE_KEY_DICT_MERGE_old(d1_arg,d2_arg):
	d1 = d1_arg
	d2 = d2_arg
	rv = copy.deepcopy(d1)
	for key in d2:
		if key in d1:
			v1 = d1[key]
			v2 = d2[key]
			if C_AST_COORD_STR(v1.coord) != C_AST_COORD_STR(v2.coord):
				print "C_AST_VAL_UNIQUE_KEY_DICT_MERGE Dicts aren't unique:",d1,d2
				print "key", key
				print "v1",C_AST_COORD_STR(v1.coord)
				print "v2",C_AST_COORD_STR(v2.coord)
				print 0/0
				sys.exit(0)
			else:
				rv[key] = d2[key] # Dont need deep copy or copy since is c_ast node?
		else:
			# Key only in d2
			rv[key] = d2[key] # Dont need deep copy or copy since is c_ast node?
			
	return rv
	
def C_AST_VAL_UNIQUE_KEY_DICT_MERGE(self_d1,d2):
	# uh?
	if self_d1 == d2:
		return self_d1
	
	for key in d2:
		if key in self_d1:
			v1 = self_d1[key]
			v2 = d2[key]
			if C_AST_COORD_STR(v1.coord) != C_AST_COORD_STR(v2.coord):
				print "C_AST_VAL_UNIQUE_KEY_DICT_MERGE Dicts aren't unique:",self_d1,d2
				print "key", key
				print "v1",C_AST_COORD_STR(v1.coord)
				print "v2",C_AST_COORD_STR(v2.coord)
				print 0/0
				sys.exit(0)
	
	# Do merge with dict methods
	rv = self_d1
	#rv.update(copy.deepcopy(d2))
	rv.update(d2)
	
	return rv

def LIST_VAL_UNIQUE_KEY_DICT_MERGE_old(d1_arg,d2_arg):
	d1 = d1_arg 
	d2 = d2_arg
	rv = copy.deepcopy(d1)
	for key in d2:
		if key in d1:
			v1 = d1[key]
			v2 = d2[key]
			if str(v1) != str(v2):
				print "List val dicts aren't unique:",d1,d2
				print "key", key
				print "v1",v1
				print "v2",v2
				print 0/0
				sys.exit(0)
			else:
				rv[key] = d2[key][:]
		else:
			# Key only in d2
			rv[key] = d2[key][:]
			
	return rv
	
	
def LIST_VAL_UNIQUE_KEY_DICT_MERGE(self_d1,d2):
	# Uhhh?
	if self_d1 == d2:
		return self_d1
	
	for key in d2:
		if key in self_d1:
			v1 = self_d1[key]
			v2 = d2[key]
			if str(v1) != str(v2):
				print "List val dicts aren't unique:",self_d1,d2
				print "key", key
				print "v1",v1
				print "v2",v2
				print 0/0
				sys.exit(0)
				
				
	# Do merge with dict methods
	rv = self_d1
	#rv.update(copy.deepcopy(d2))
	rv.update(d2)
	
	return rv


def UNIQUE_KEY_DICT_MERGE(self_d1,d2):
	# Uhh?
	if self_d1 == d2:
		return self_d1
	
	# Check that are unique
	for key in d2:
		if key in self_d1:
			v1 = self_d1[key]
			v2 = d2[key]
			if v1 != v2:
				print "Dicts aren't unique:",self_d1,d2
				print "key", key
				print "v1",v1
				print "v2",v2
				print 0/0
				sys.exit(0)
		#except:
		#	pass
				
	# Do merge with dict methods
	rv = self_d1
	#rv.update(copy.deepcopy(d2))
	rv.update(d2)
	
	return rv


def UNIQUE_KEY_DICT_MERGE_old(d1_arg,d2_arg):
	d1 = d1_arg 
	d2 = d2_arg
	rv = copy.deepcopy(d1)
	for key in d2:
		if key in d1:
			v1 = d1[key]
			v2 = d2[key]
			if v1 != v2:
				print "Dicts aren't unique:",d1,d2
				print "key", key
				print "v1",v1
				print "v2",v2
				print 0/0
				sys.exit(0)
			else:
				rv[key] = copy.deepcopy(d2[key])
		else:
			# Key only in d2
			rv[key] = copy.deepcopy(d2[key])
			
	return rv
	
def DICT_LIST_VALUE_MERGE(self_d1,d2):
	rv = self_d1
	for key in d2:
		if key in self_d1:
			# Result is union of two lists
			rv[key] = LIST_UNION(self_d1[key],d2[key])
		else:
			#rv[key] = copy.deepcopy(d2[key])
			rv[key] = d2[key]
			
	return rv   
	
def STR_LIST_PREPEND(l,prepend_text):
	new_l = []
	for i in l:
		new_l.append(prepend_text+i)
	return new_l

def STR_DICT_KEY_PREPREND(d,prepend_text):
	new_d = dict()
	
	#print "d",d
	for key in d:
		new_d[prepend_text+key] = d[key]
	return new_d

def STR_DICT_KEY_AND_ALL_VALUES_PREPREND(d,prepend_text):
	new_d = dict()
	for key in d:
		value = d[key]
		if type(value) is list:
			new_d[prepend_text+key] = STR_LIST_PREPEND(value,prepend_text)
		else:
			new_d[prepend_text+key] = prepend_text + value
		
	return new_d


class Logic:
	def __init__(self):
		
		####### MODIFY DEEP COPY TOO
		#
		#
		#
		#
		#
		#	
		
		# FOR LOGIC IMPLEMENTED IN C THE STRINGS MUST BE C SAFE
		# (inst name adjust is after all the parsing so dont count SUBMODULE_MARKER)		
		
		self.func_name=None #function, operation
		self.inst_name=None
		self.variable_names=[] # List of original variable names  
		self.wires=[]  # ["a","b","return"] wire names (renamed variable regs), includes inputs+outputs
		self.inputs=[] #["a","b"] 
		self.outputs=[] #["return"]
		self.global_wires=[]
		self.volatile_global_wires=[]
		self.uses_globals = False
		self.submodule_instances = dict() # instance name -> logic func_name
		self.c_ast_node = None
		# Is this logic a c built in C function?
		self.is_c_built_in = False
		
		
		# Mostly for c built in C functions
		self.submodule_instance_to_c_ast_node = dict()
		self.submodule_instance_to_input_port_names = dict()
		self.ref_submodule_instance_to_input_port_driven_ref_toks = dict()
		self.ref_submodule_instance_to_ref_toks = dict()
		
		# Python graph example was dict() of strings so this
		# string based wire naming makes Pythonic sense.
		# I think pointers would work better.
		# Wire names with a dot means sub module connection
		# func0.a  is a port on the func0 instance
		# Connections are given as two lists "drives" and "driven by"
		self.wire_drives = dict() # wire_name -> [driven,wire,names]
		self.wire_driven_by = dict() # wire_name -> driving wire
		
		# To keep track of C execution over time in logic graph,
		# each assignment assigns to a renamed variable, renamed
		# variables keep execution order
		# Need to keep dicts for variable names
		self.wire_aliases_over_time = dict() # orig var name -> [list,of,renamed,wire,names] # Further in list is further in time
		self.alias_to_orig_var_name = dict() # alias -> orig var name
		self.alias_to_ref_toks = dict() # alias -> [ref,toks]
		
		# Need to look up types by wire name
		# wire_to_c_type[wire_name] -> c_type_str
		self.wire_to_c_type = dict()
		
		# For timing, levels of logic
		# this is populated by vendor tool
		self.total_logic_levels = None
		
		# Save C code text for later
		self.c_code_text = None
		
		# My containing inst? (name, string)
		self.containing_inst = None
	
	
	# Help!
	def DEEPCOPY(self):
		rv = Logic()
		rv.func_name = self.func_name
		rv.inst_name = self.inst_name
		rv.variable_names = self.variable_names[:] # List of original variable names
		rv.wires = self.wires[:]  # ["a","b","return"] wire names (renamed variable regs), includes inputs+outputs
		rv.inputs = self.inputs[:] #["a","b"]
		rv.outputs = self.outputs[:] #["return"]
		rv.global_wires = self.global_wires[:]
		rv.volatile_global_wires = self.volatile_global_wires[:]
		rv.uses_globals = self.uses_globals
		rv.submodule_instances = dict(self.submodule_instances) # instance name -> logic func_name all IMMUTABLE types?
		rv.c_ast_node = copy.copy(self.c_ast_node) # Uhhh seemed wrong ?
		rv.is_c_built_in = self.is_c_built_in
		rv.submodule_instance_to_c_ast_node = self.DEEPCOPY_DICT_COPY(self.submodule_instance_to_c_ast_node)  # dict(self.submodule_instance_to_c_ast_node) # IMMUTABLE types / dont care
		rv.submodule_instance_to_input_port_names = self.DEEPCOPY_DICT_LIST(self.submodule_instance_to_input_port_names)
		rv.wire_drives = self.DEEPCOPY_DICT_LIST(self.wire_drives)
		rv.wire_driven_by = dict(self.wire_driven_by) # wire_name -> driving wire #IMMUTABLE
		rv.wire_aliases_over_time = self.DEEPCOPY_DICT_LIST(self.wire_aliases_over_time)
		rv.alias_to_orig_var_name = dict(self.alias_to_orig_var_name) #IMMUTABLE
		rv.alias_to_ref_toks = self.DEEPCOPY_DICT_LIST(self.alias_to_ref_toks) # alias -> [ref,toks]
		rv.wire_to_c_type = dict(self.wire_to_c_type) #IMMUTABLE
		rv.total_logic_levels = self.total_logic_levels
		rv.c_code_text = self.c_code_text
		rv.containing_inst = self.containing_inst
		rv.ref_submodule_instance_to_input_port_driven_ref_toks = self.DEEPCOPY_DICT_LIST(self.ref_submodule_instance_to_input_port_driven_ref_toks)
		rv.ref_submodule_instance_to_ref_toks = self.DEEPCOPY_DICT_LIST(self.ref_submodule_instance_to_ref_toks)
		
		return rv
		
	# Really, help! # Replace with deep copy?
	def DEEPCOPY_DICT_LIST(self, d):
		rv = dict()
		for key in d:
			rv[key] = d[key][:]
		return rv
		
	def DEEPCOPY_DICT_COPY(self, d):
		rv = dict()
		for key in d:
			rv[key] = copy.copy(d[key])
		return rv
	
	
	# Modify self,
	# Returns none
	def INST_LOGIC_ADJUST_W_PREPEND(self, new_inst_name_prepend_text):

		# FUNC NAME STAYS SAME self.func_name=None #function, operation
		
		# NEW INST NAME IS USED TO RENAME EVERYTHING
		# MAIN INST NAME IS SPECIAL case
		if self.inst_name == "main":
			# Allow prepend if raw hdl
			if new_inst_name_prepend_text == (RAW_HDL_PREFIX + "_"):
				self.inst_name = new_inst_name_prepend_text + self.inst_name
			elif new_inst_name_prepend_text != "":
				print 'new_inst_name_prepend_text != ""', new_inst_name_prepend_text
				sys.exit(0)
			else:
				# All good to ignore prepend
				self.inst_name = self.inst_name
		else:
			'''
			# C built in has c ast coord already
			if self.is_c_built_in or (len(self.submodule_instances) <= 0):
				self.inst_name = new_inst_name_prepend_text + self.inst_name 
			else:
				self.inst_name = new_inst_name_prepend_text + self.inst_name + "_" + C_AST_COORD_STR(c_ast_node_when_used.coord)
			'''
			self.inst_name = new_inst_name_prepend_text + self.inst_name
			
			#print "GET_INST_NAME_ADJUSTED_LOGIC"
			#print "self.func_name",self.func_name
			#print "new_inst_name_prepend_text",new_inst_name_prepend_text
			#print "self.inst_name ",self.inst_name 
			#print "C_AST_COORD_STR", C_AST_COORD_STR(c_ast_node_when_used.coord)
			#print ""
			
				
		prepend_text = self.inst_name + SUBMODULE_MARKER
		
		# Then do regular prepend
		self.PREPEND_TEXT(prepend_text)
		
		return None
		
	# Merges logic_b into self
	# Returns none intentionally
	def MERGE_COMB_LOGIC(self,logic_b):		
		# Um...?
		if self == logic_b:
			return None
		
		# Func name must match if set
		if (self.func_name is not None) and (logic_b.func_name is not None):
			if self.func_name != logic_b.func_name:
				print "Cannot merge comb logic with mismatching func names!"
				print self.func_name
				print logic_b.func_name
			else:
				self.func_name = self.func_name
		# Otherwise use whichever is set
		elif self.func_name is not None:
			self.func_name = self.func_name
		else:
			self.func_name = logic_b.func_name
		
		# Inst must match if set
		if (self.inst_name is not None) and (logic_b.inst_name is not None):
			if self.inst_name != logic_b.inst_name:
				print "Cannot merge comb logic with mismatching instance names!"
				print self.inst_name
				print logic_b.inst_name
			else:
				self.inst_name = self.inst_name
		# Otherwise use whichever is set
		elif self.inst_name is not None:
			self.inst_name = self.inst_name
		else:
			self.inst_name = logic_b.inst_name
			
		# C built in status must match if set
		if (self.is_c_built_in is not None) and (logic_b.is_c_built_in is not None):
			if self.is_c_built_in != logic_b.is_c_built_in:
				print "Cannot merge comb logic with mismatching is_c_built_in !"
				print self.inst_name, self.is_c_built_in
				print logic_b.inst_name, logic_b.is_c_built_in
				sys.exit(0)
			else:
				self.is_c_built_in = self.is_c_built_in
		# Otherwise use whichever is set
		elif self.is_c_built_in is not None:
			self.is_c_built_in = self.is_c_built_in
		else:
			self.is_c_built_in = logic_b.is_c_built_in
			
		# Absorb true values of using globals
		self.uses_globals = self.uses_globals or logic_b.uses_globals
		
		# Merge lists
		self.wires = LIST_UNION(self.wires,logic_b.wires)
		self.global_wires = LIST_UNION(self.global_wires,logic_b.global_wires)
		self.volatile_global_wires = LIST_UNION(self.volatile_global_wires,logic_b.volatile_global_wires)
		self.variable_names = LIST_UNION(self.variable_names,logic_b.variable_names)
		
		# I/O order matters - check that
		# If one is empty then thats fine
		if len(self.inputs) > 0 and len(logic_b.inputs) > 0:
			# Check for equal
			if self.inputs != logic_b.inputs:
				print "Cannot merge comb logic with mismatching inputs !"
				print self.inst_name, self.inputs
				print logic_b.inst_name, logic_b.inputs
				print 0/0
				sys.exit(0)
			else:
				self.inputs = self.inputs[:]
		else:
			# Default a
			self.inputs = self.inputs[:]
			if len(self.inputs) <= 0:
				self.inputs = logic_b.inputs[:]
		
		if len(self.outputs) > 0 and len(logic_b.outputs) > 0:
			# Check for equal
			if self.outputs != logic_b.outputs:
				print "Cannot merge comb logic with mismatching outputs !"
				print self.inst_name, self.outputs
				print logic_b.inst_name, logic_b.outputs
				sys.exit(0)
			else:
				self.outputs = self.outputs[:]
		else:
			# Default a
			self.outputs = self.outputs[:]
			if len(self.outputs) <= 0:
				self.outputs = logic_b.outputs[:]
			
		
		# Merge dicts
		self.wire_to_c_type = UNIQUE_KEY_DICT_MERGE(self.wire_to_c_type,logic_b.wire_to_c_type)
		self.submodule_instances = UNIQUE_KEY_DICT_MERGE(self.submodule_instances,logic_b.submodule_instances)	
		self.wire_driven_by = UNIQUE_KEY_DICT_MERGE(self.wire_driven_by,logic_b.wire_driven_by)
		
		# WTF MERGE BUG?
		lens = len(self.wire_drives)+ len(logic_b.wire_drives)
		self.wire_drives = DICT_LIST_VALUE_MERGE(self.wire_drives,logic_b.wire_drives)
		if lens > 0 and len(self.wire_drives) == 0:
			print "self.wire_drives",self.wire_drives
			print "logic_b.wire_drives",logic_b.wire_drives
			print "Should have at least",lens, "entries..."
			print "MERGE COMB self.wire_drives",self.wire_drives
			print "WTF"
			sys.exit(0)
		
		# C ast node values wont be == , manual check with coord str
		self.submodule_instance_to_c_ast_node = C_AST_VAL_UNIQUE_KEY_DICT_MERGE(self.submodule_instance_to_c_ast_node,logic_b.submodule_instance_to_c_ast_node)
		self.submodule_instance_to_input_port_names = LIST_VAL_UNIQUE_KEY_DICT_MERGE(self.submodule_instance_to_input_port_names,logic_b.submodule_instance_to_input_port_names)
		self.ref_submodule_instance_to_input_port_driven_ref_toks = LIST_VAL_UNIQUE_KEY_DICT_MERGE(self.ref_submodule_instance_to_input_port_driven_ref_toks,logic_b.ref_submodule_instance_to_input_port_driven_ref_toks)
		self.ref_submodule_instance_to_ref_toks = LIST_VAL_UNIQUE_KEY_DICT_MERGE(self.ref_submodule_instance_to_ref_toks, logic_b.ref_submodule_instance_to_ref_toks)
		
		# Also for both wire drives and driven by, remove wire driving self:
		# wire_driven_by
		new_wire_driven_by = dict()
		for driven_wire in self.wire_driven_by:
			# Filter out self driving
			driving_wire = self.wire_driven_by[driven_wire]
			if driving_wire != driven_wire:
				new_wire_driven_by[driven_wire] = driving_wire
		
		#print "new_wire_driven_by",new_wire_driven_by
		self.wire_driven_by = new_wire_driven_by
		
		# wire_drives
		new_wire_drives = dict()
		for driving_wire in self.wire_drives:
			driven_wires = self.wire_drives[driving_wire]
			new_driven_wires = []
			for driven_wire in driven_wires:
				if driven_wire != driving_wire:
					new_driven_wires.append(driven_wire)	
			new_wire_drives[driving_wire] = new_driven_wires
		self.wire_drives=new_wire_drives
				
		'''		
		# If one node is null then use other
		if self.c_ast_node is None:
			self.c_ast_node = logic_b.c_ast_node
		if logic_b.c_ast_node is None:
			self.c_ast_node = self.c_ast_node
		'''
		# C ast must match if set
		if (self.c_ast_node is not None) and (logic_b.c_ast_node is not None):
			# For now its the same c ast node if its the same coord
			# If causes problems... abandon then
			if C_AST_COORD_STR(self.c_ast_node.coord) != C_AST_COORD_STR(logic_b.c_ast_node.coord):
				print "Cannot merge comb logic with mismatching c_ast_node!"
				print self.func_name
				print logic_b.func_name
				print self.c_ast_node
				print logic_b.c_ast_node
				print 0/0
				sys.exit(0)
			else:
				self.c_ast_node = self.c_ast_node
		# Otherwise use whichever is set
		elif self.c_ast_node is not None:
			self.c_ast_node = self.c_ast_node
		else:
			self.c_ast_node = logic_b.c_ast_node
		
		
		
		# Only way this makes sense with MERGE_SEQUENTIAL_LOGIC
		# is for dicts to be equal (checked python docs for eq syntax)
		# Uhhh.... seems wrong?
		if self.wire_aliases_over_time != logic_b.wire_aliases_over_time:
			# Only OK if one dict is completely empty
			if not(self.wire_aliases_over_time == dict() or logic_b.wire_aliases_over_time == dict()):		
				print "Aliases over time do not match in MERGE_COMB_LOGIC!"
				print self.wire_aliases_over_time
				print logic_b.wire_aliases_over_time
				sys.exit(0)

		if self.wire_aliases_over_time == dict():
			self.wire_aliases_over_time = logic_b.wire_aliases_over_time

		# Only one orig wire name per alias
		self.alias_to_orig_var_name = UNIQUE_KEY_DICT_MERGE(self.alias_to_orig_var_name,logic_b.alias_to_orig_var_name)
		self.alias_to_ref_toks = UNIQUE_KEY_DICT_MERGE(self.alias_to_ref_toks,logic_b.alias_to_ref_toks) 
		
		# Code text keep whichever is set
		if (self.c_code_text is not None) and (logic_b.c_code_text is not None):
			if self.c_code_text != logic_b.c_code_text:
				print "Cannot merge comb logic with mismatching c_code_text!"
				print self.c_code_text
				print logic_b.c_code_text
			else:
				self.c_code_text = self.c_code_text
		# Otherwise use whichever is set
		elif self.c_code_text is not None:
			self.c_code_text = self.c_code_text
		else:
			self.c_code_text = logic_b.c_code_text
		
		return None
			
	
	# Function to merge logic with implied execution order
	# Merges with self
	# Intentionally returns None
	def MERGE_SEQ_LOGIC(self, second_logic):		
		# Um...?
		if self == second_logic:
			return None
		
		#print "===="
		#print "self.wire_drives", self.wire_drives 
		#print "self.wire_driven_by", self.wire_driven_by 
		#print "second_logic.wire_drives", second_logic.wire_drives 
		#print "second_logic.wire_driven_by", second_logic.wire_driven_by 
		
		# Func name must match if set
		if (self.func_name is not None) and (second_logic.func_name is not None):
			if self.func_name != second_logic.func_name:
				print "Cannot merge comb logic with mismatching func names!"
				print self.func_name
				print second_logic.func_name
		# Otherwise use whichever is set
		if self.func_name is not None:
			self.func_name = self.func_name
		else:
			self.func_name = second_logic.func_name
		
		# Inst must match if set
		if (self.inst_name is not None) and (second_logic.inst_name is not None):
			if self.inst_name != second_logic.inst_name:
				print "Cannot merge comb logic with mismatching instance names!"
				print self.inst_name
				print second_logic.inst_name
		# Otherwise use whichever is set
		if self.inst_name is not None:
			self.inst_name = self.inst_name
		else:
			self.inst_name = second_logic.inst_name	
		
		# Merge lists
		self.wires = LIST_UNION(self.wires,second_logic.wires)
		self.global_wires = LIST_UNION(self.global_wires,second_logic.global_wires)
		self.volatile_global_wires = LIST_UNION(self.volatile_global_wires,second_logic.volatile_global_wires)
		self.variable_names = LIST_UNION(self.variable_names,second_logic.variable_names)
		
		# Absorb true values of using globals
		self.uses_globals = self.uses_globals or second_logic.uses_globals
		
		# I/O order matters - check that
		# If one is empty then thats fine
		if len(self.inputs) > 0 and len(second_logic.inputs) > 0:
			# Check for equal
			if self.inputs != second_logic.inputs:
				print "Cannot merge seq logic with mismatching inputs !"
				print self.inst_name, self.inputs
				print second_logic.inst_name, second_logic.inputs
				sys.exit(0)
			else:
				self.inputs = self.inputs[:]
		else:
			# Default self
			self.inputs = self.inputs
			if len(self.inputs) <= 0:
				self.outputs = second_logic.inputs[:]
		
		if len(self.outputs) > 0 and len(second_logic.outputs) > 0:
			# Check for equal
			if self.outputs != second_logic.outputs:
				print "Cannot merge seq logic with mismatching outputs !"
				print self.inst_name, self.outputs
				print second_logic.inst_name, second_logic.outputs
				sys.exit(0)
			else:
				self.outputs = self.outputs[:]
		else:
			# Default self
			self.outputs = self.outputs
			if len(self.outputs) <= 0:
				self.outputs = second_logic.outputs[:]
		
		
		
		self.wire_to_c_type = UNIQUE_KEY_DICT_MERGE(self.wire_to_c_type,second_logic.wire_to_c_type)
		
		# Merge dict
		self.submodule_instances = UNIQUE_KEY_DICT_MERGE(self.submodule_instances,second_logic.submodule_instances)
		self.submodule_instance_to_c_ast_node = C_AST_VAL_UNIQUE_KEY_DICT_MERGE(self.submodule_instance_to_c_ast_node,second_logic.submodule_instance_to_c_ast_node)
		self.submodule_instance_to_input_port_names = LIST_VAL_UNIQUE_KEY_DICT_MERGE(self.submodule_instance_to_input_port_names,second_logic.submodule_instance_to_input_port_names)
		
		
		# Driving wires need to reflect over time
		# Last alias from first logic replaces original wire name in second logic
		# self.wire_drives = dict() # wire_name -> [driven,wire,names]
		for orig_var in self.wire_aliases_over_time:
			# And the var drives second_logic 
			if orig_var in second_logic.wire_drives:
				# First logic has aliases for orig var
				# Second logic has record of the orig var driving things
				# Both first and second logic should have same driven wies
				first_driven_wires = []
				if orig_var in self.wire_drives:
					first_driven_wires = self.wire_drives[orig_var]
				second_driven_wires = []
				if orig_var in second_logic.wire_drives:
					second_driven_wires = second_logic.wire_drives[orig_var]
					
				sorted_first_driven_wires = sorted(first_driven_wires)
				sorted_second_driven_wires = sorted(second_driven_wires)
				# Was the second logic actually refering to something different?
				if sorted_first_driven_wires != sorted_second_driven_wires:	
					# If second just has extra then OK
					if len(sorted_first_driven_wires) < len(sorted_second_driven_wires):
						# Check for match, but not like a dummy?
						#for i in range(0, len(sorted_first_driven_wires)):
						#	if sorted_first_driven_wires[i] != sorted_second_driven_wires[i]:
						for sorted_first_driven_wire in sorted_first_driven_wires:
							if sorted_first_driven_wire not in sorted_second_driven_wires:
								print "first driven wire:", sorted_first_driven_wire,"was not in second logic driven wires? was removed? wtf?"
								print "first:",sorted_first_driven_wires
								print "second:", sorted_second_driven_wires
								#print 0/0
								sys.exit(0)
						# Got match, first is subset of second, update first to match second
						self.wire_drives[orig_var] = second_driven_wires
						for second_driven_wire in second_driven_wires:
							self.wire_driven_by[second_driven_wire] = second_logic.wire_driven_by[second_driven_wire]
						
					else:
						# First has same or more, cant match second at this point
						print "orig_var",orig_var
						aliases = self.wire_aliases_over_time[orig_var]
						print "first aliases",aliases
						last_alias = aliases[len(aliases)-1]
						print "first logic last_alias",last_alias
						print "self.wire_drives[orig_var]",first_driven_wires
						print "second_logic.wire_drives[orig_var]",second_driven_wires
						# Get the last alias for that var from first logic
						print "second aliases", second_logic.wire_aliases_over_time[orig_var]
						
						# If this last alias is not in the first logic 
						
						# If aliases over time already agree then no need 
						
						# And replace that wire in the 
						# second logic wire_drives key (not value)
						temp_value = copy.deepcopy(second_logic.wire_drives[orig_var])
						# Delete orig var key
						second_logic.wire_drives.pop(orig_var, None)
						# Replace with last alias
						second_logic.wire_drives[last_alias] = temp_value
						print last_alias," DRIVES ", temp_value
						sys.exit(0)
						
		
		
		# wire_driven_by can't have multiple drivers over time and
		# should error out in normal merge below
		
		# If one node is null then use other
		if self.c_ast_node is None:
			self.c_ast_node = second_logic.c_ast_node
		if second_logic.c_ast_node is None:
			self.c_ast_node = self.c_ast_node
		
		# wire_aliases_over_time	
		# Do first+second first
		# If first logic has aliases over time
		for var_name in self.wire_aliases_over_time:
			if var_name in second_logic.wire_aliases_over_time:
				# And so does second
				# Merged value is first plus second
				first = self.wire_aliases_over_time[var_name]
				second = second_logic.wire_aliases_over_time[var_name]
				# Start with including first
				self.wire_aliases_over_time[var_name] = first[:]
				
				# Check that the aliases over time are equal 
				# in the period of time they share (the first logic)
				for i in range(0, len(first)):
					if first[i] != second[i]:
						print "At time index", i,"for orig variable name =", var_name,"the first and second logic do not agree:"
						print "First logic aliases over time:", first
						print "Second logic aliases over time:", second
						print 0/0
						sys.exit(0)
				
				# Equal in shared time so only append not shared part of second
				for i in range(len(first), len(second)):
					self.wire_aliases_over_time[var_name].append(second[i])
				#print "self.wire_aliases_over_time",self.wire_aliases_over_time
					
			else:
				# First only alias (second does not have alias)
				# Merged value is first only
				self.wire_aliases_over_time[var_name] = self.wire_aliases_over_time[var_name][:]
		# Then include wire_aliases_over_time ONLY from second logic
		for var_name in second_logic.wire_aliases_over_time:
			# And first logic does not
			if not(var_name in self.wire_aliases_over_time):
				# Merged value is just from second logic
				second = second_logic.wire_aliases_over_time[var_name]
				self.wire_aliases_over_time[var_name] = second[:]
		
		# To not error in normal MERGE_LOGIC below, first and second logic must have same 
		# resulting wire_aliases_over_time
		#modified_first_logic = copy.deepcopy(self)
		
		#modified_second_logic = copy.deepcopy(second_logic) 
		modified_second_logic = second_logic
		
		#modified_first_logic.wire_aliases_over_time = self.wire_aliases_over_time
		modified_second_logic.wire_aliases_over_time = self.wire_aliases_over_time
		
		# orig_wire_name Only one orig wire name per alias, handled in MERGE_LOGIC
		
		
		#print "PRE_COMB self.wire_drives", modified_first_logic.wire_drives 
		#print "self.wire_driven_by", modified_first_logic.wire_driven_by 
		#print "second_logic.wire_drives", modified_second_logic.wire_drives 
		#print "second_logic.wire_driven_by", modified_second_logic.wire_driven_by 
		
		
		
		# Then merge logic as normal
		self.MERGE_COMB_LOGIC(modified_second_logic)
		
		#print "MID_COMB tmp.wire_drives", tmp.wire_drives 
		#print "tmp.wire_driven_by", tmp.wire_driven_by 
		
		#self.MERGE_COMB_LOGIC(modified_first_logic)
		
		
		#print "POS_COMB self.wire_drives", self.wire_drives 
		#print "self.wire_driven_by", self.wire_driven_by 
		
		return None
			
	# Modify self
	# Return None
	def PREPEND_TEXT(self, prepend_text):
		self.variable_names = STR_LIST_PREPEND(self.variable_names, prepend_text) #   # List of original variable names
		self.wires = STR_LIST_PREPEND(self.wires, prepend_text) # =[]  # ["a","b","return"] wire names (renamed variable regs), includes inputs+outputs
		self.inputs = STR_LIST_PREPEND(self.inputs, prepend_text) # =[] #["a","b"]
		self.outputs = STR_LIST_PREPEND(self.outputs, prepend_text) # =[] #["return"]
		self.global_wires = STR_LIST_PREPEND(self.global_wires, prepend_text)
		self.volatile_global_wires = STR_LIST_PREPEND(self.volatile_global_wires, prepend_text)
		self.submodule_instances = STR_DICT_KEY_PREPREND(self.submodule_instances, prepend_text) #  = dict() # instance name -> self func_name
		self.submodule_instance_to_c_ast_node = STR_DICT_KEY_PREPREND(self.submodule_instance_to_c_ast_node, prepend_text) #  = dict() # Mostly for c built in C functions
		self.submodule_instance_to_input_port_names = STR_DICT_KEY_AND_ALL_VALUES_PREPREND(self.submodule_instance_to_input_port_names, prepend_text)
		self.ref_submodule_instance_to_input_port_driven_ref_toks = STR_DICT_KEY_PREPREND(self.ref_submodule_instance_to_input_port_driven_ref_toks, prepend_text)
		self.ref_submodule_instance_to_ref_toks = STR_DICT_KEY_PREPREND(self.ref_submodule_instance_to_ref_toks, prepend_text)
		# self.c_ast_node = None
	
		# Python graph example was dict() of strings so this
		# string based wire naming makes Pythonic sense.
		# I think pointers would work better.
		# Wire names with a dot means sub module connection
		# func0.a  is a port on the func0 instance
		# Connections are given as two lists "drives" and "driven by"
		self.wire_drives = STR_DICT_KEY_AND_ALL_VALUES_PREPREND(self.wire_drives, prepend_text) #  = dict() # wire_name -> [driven,wire,names]
		self.wire_driven_by = STR_DICT_KEY_AND_ALL_VALUES_PREPREND(self.wire_driven_by, prepend_text) #  = dict() # wire_name -> driving wire
		
		# To keep track of C execution over time in self graph,
		# each assignment assigns to a renamed variable, renamed
		# variables keep execution order
		# Need to keep dicts for variable names
		self.wire_aliases_over_time = STR_DICT_KEY_AND_ALL_VALUES_PREPREND(self.wire_aliases_over_time, prepend_text) #  = dict() # orig var name -> [list,of,renamed,wire,names] # Further in list is further in time
		self.alias_to_orig_var_name = STR_DICT_KEY_AND_ALL_VALUES_PREPREND(self.alias_to_orig_var_name, prepend_text) #  = dict() # alias -> orig var name
		self.alias_to_ref_toks = STR_DICT_KEY_PREPREND(self.alias_to_ref_toks, prepend_text) 
		
		# Need to look up types by wire name
		self.wire_to_c_type = STR_DICT_KEY_PREPREND(self.wire_to_c_type, prepend_text) #  = dict() # wire_to_c_type[wire_name] -> c_type_str
		
		# For timing, levels of self
		# this is populated by vendor tool
		#self.total_logic_levels=None
		
		
		return None
		
		
			
	def SHOW(self):
		# Make adjency matrix out of all wires and submodule isnts and own 'wire'/node in network
		nodes = self.wires
		for submodule_inst in self.submodule_instances:
			nodes.append(submodule_inst)
		sorted_nodes = sorted(nodes)
		num_nodes = len(sorted_nodes)
		adjacency_matrix = np.zeros((num_nodes,num_nodes), dtype=np.int)
		# Build labels
		labels_dict = make_label_dict(sorted_nodes)
		rev_labels_dict = make_rev_label_dict(sorted_nodes)
		
		# Populate adjaceny matrix 
		for wire in self.wire_drives:
			driver_num = rev_labels_dict[wire]
			driven_wires = self.wire_drives[wire]
			
			# Get what a submodule inst form this wire would look like
			driving_submodule_inst_name = None
			if SUBMODULE_MARKER in wire:
				toks = wire.split(SUBMODULE_MARKER)
				inst_name = SUBMODULE_MARKER.join(toks[0:len(toks)-1])
				if inst_name in self.submodule_instances:
					driving_submodule_inst_name = inst_name
			
			# Do driven wires
			for driven_wire in driven_wires:
				driven_num = rev_labels_dict[driven_wire]
				adjacency_matrix[driver_num,driven_num] = 1
				
				# Get what a submodule inst form this driven wire would look like
				driven_submodule_inst_name = None
				if SUBMODULE_MARKER in driven_wire:
					toks = driven_wire.split(SUBMODULE_MARKER)
					inst_name = SUBMODULE_MARKER.join(toks[0:len(toks)-1])
					if inst_name in self.submodule_instances:
						driven_submodule_inst_name = inst_name
					
				# Assign IO for submodule insts
				if not(driving_submodule_inst_name is None):
					# Mus tbe output add common driver from submodule inst to output driver wire
					driving_submodule_node_num = rev_labels_dict[driving_submodule_inst_name]
					adjacency_matrix[driving_submodule_node_num,driver_num] = 1
				# Assign IO for submodule insts
				if not(driven_submodule_inst_name is None):
					# Msut be input
					# Add common inst driven by driver wire
					driven_submodule_node_num = rev_labels_dict[driven_submodule_inst_name]
					adjacency_matrix[driven_num,driven_submodule_node_num] = 1				
				
				
		show_graph_with_labels(adjacency_matrix, labels_dict)
			
			
		

# Thanks stack overflow
#https://stackoverflow.com/questions/29572623/plot-networkx-graph-from-adjacency-matrix-in-csv-file
def show_graph_with_labels(adjacency_matrix, mylabels):
    rows, cols = np.where(adjacency_matrix == 1)
    edges = zip(rows.tolist(), cols.tolist())
    gr = nx.Graph()
    gr.add_edges_from(edges)
    nx.draw(gr, node_size=500, labels=mylabels, with_labels=True)
    plt.show()
    
def make_label_dict(labels):
    l = {}
    for i, label in enumerate(labels):
        l[i] = label
    return l
def make_rev_label_dict(labels):
    l = {}
    for i, label in enumerate(labels):
        l[label] = i
    return l   

	
def WIRE_IS_CONSTANT(wire, logic_inst_name):
	if logic_inst_name is None:
		logic_inst_name = ""
		# Uhhhh?? ^^
	
	# Remove inst name
	new_wire = wire.replace(logic_inst_name+SUBMODULE_MARKER,"")
	
	# Also split on last submodule marker
	toks = new_wire.split(SUBMODULE_MARKER)
	last_tok = toks[len(toks)-1]
	
	rv = last_tok.startswith(CONST_PREFIX)
	
	if (CONST_PREFIX in wire) and not(rv) and not(CONST_REF_RD_FUNC_NAME_PREFIX in wire):
		print "WHJAT!?"
		print "logic_inst_name",logic_inst_name
		print "wire",wire
		print "new_wire", new_wire
		print "WIRE_IS_CONSTANT   but is not?"
		sys.exit(0)	
	
	return rv
	

def WIRE_IS_SUBMODULE_PORT(wire, logic):
	# Is everything but last item submodule in this logic?
	toks = wire.split(SUBMODULE_MARKER)
	possible_submodule_inst = SUBMODULE_MARKER.join(toks[0:len(toks)-1])
	
	# Check port name too?
	# No for now?
	return possible_submodule_inst in logic.submodule_instances
	
	
	

	

def BUILD_C_BUILT_IN_SUBMODULE_LOGIC_INST(containing_func_logic, new_inst_name_prepend_text, submodule_inst_name, parser_state):	
	#print "containing_func_logic.func_name, new_inst_name_prepend_text, submodule_inst_name"
	#print containing_func_logic.func_name, "|", new_inst_name_prepend_text, "|", submodule_inst_name
	#print "====================================================================================="
	# Construct a fake 'submodule_logic' with correct name, inputs, outputs
	submodule_logic = Logic()
	submodule_logic.is_c_built_in = True
	# Look up logic name for the submodule instance
	#print "containing_func_logic.func_name",containing_func_logic.func_name
	#print "containing_func_logic.submodule_instances",containing_func_logic.submodule_instances
	submodule_logic_name = containing_func_logic.submodule_instances[submodule_inst_name]
	#print "submodule_inst_name",submodule_inst_name
	#print "submodule_logic_name",submodule_logic_name
	submodule_logic.func_name = submodule_logic_name
	submodule_logic.inst_name = submodule_inst_name
	
	# Ports and types are specific to the submodule instance
	# Get data from c ast node
	c_ast_node = containing_func_logic.submodule_instance_to_c_ast_node[submodule_inst_name]
	submodule_logic.c_ast_node = c_ast_node
	
	# It looks like the c parser doesnt let you look up type from name...
	# Probably would be complicated
	# Lets manually do it.
	# 1) parse funtion param declartions in wire_to_c_type
	# 2) parse var decls to wire_to_c_type
	# 3) Look up driver of submodule to determine type
	
	# Assume children list is is order of args if not HDL INSERT
	input_names = []
	if submodule_logic.func_name.startswith(VHDL_INSERT.HDL_INSERT):
		print "What VHDL insert is like broken for this?"
		sys.exit(0)
	else:
		if submodule_inst_name in containing_func_logic.submodule_instance_to_input_port_names:
			input_names = containing_func_logic.submodule_instance_to_input_port_names[submodule_inst_name]
			submodule_logic.inputs += input_names
		else:
			for child in c_ast_node.children():
				name=child[0]
				input_names.append(name)
				submodule_logic.inputs.append(name)	
	
	# For each input wire look up type of driving wire
	input_types = []
	for input_name in input_names:	
		input_wire_name = submodule_inst_name + SUBMODULE_MARKER + input_name
		#print logic.wire_driven_by
		driving_wire = containing_func_logic.wire_driven_by[input_wire_name]
		c_type = containing_func_logic.wire_to_c_type[driving_wire]
		# If driving wire c type is enum and this is BIN OP == then replace with input port wire with uint
		if (c_type in parser_state.enum_to_ids_dict) and (submodule_logic_name.startswith(BIN_OP_LOGIC_NAME_PREFIX + "_" + BIN_OP_EQ_NAME)):
			#print "submodule_logic_name", submodule_logic_name, "BIN_OP_EQ_NAME ENUM"
			#print "right enum"
			num_ids = len(parser_state.enum_to_ids_dict[c_type])
			width = int(math.ceil(math.log(num_ids,2)))
			c_type = "uint" + str(width) + "_t"
		submodule_logic.wire_to_c_type[input_name] = c_type
		input_types.append(c_type)
		
	# Output wire is return wire and type is type of what is driven
	output_port_name = RETURN_WIRE_NAME
	submodule_logic.outputs.append(RETURN_WIRE_NAME)
	output_wire_name = submodule_inst_name + SUBMODULE_MARKER + output_port_name
	
	# Mux output type is that of inputs
	if submodule_logic.func_name.startswith(MUX_LOGIC_NAME):
		# Mux is cond is input[0], left is [1] and should be of same type as right
		submodule_logic.wire_to_c_type[output_port_name]=input_types[1]
			
	# By default assume type of driven wire
	elif output_wire_name in containing_func_logic.wire_drives:
		driven_wires = containing_func_logic.wire_drives[output_wire_name]
		if len(driven_wires)==0 :
			print "Built in submodule not driving anthying?",submodule_inst_name
			sys.exit(0)
		c_type = containing_func_logic.wire_to_c_type[driven_wires[0]]
		submodule_logic.wire_to_c_type[output_port_name]=c_type
		
	else:
		print "containing_func_logic.func_name",containing_func_logic.func_name
		print "output_wire_name",output_wire_name
		print "containing_func_logic.wire_drives",containing_func_logic.wire_drives
		print "Input type to output type mapping assumption for built in submodule output "
		print submodule_logic.func_name
		print submodule_logic.inst_name
		sys.exit(0)		
			
	
	# Also do submodule instances for built in logic that is not raw VHDL
	if VHDL.C_BUILT_IN_FUNC_IS_RAW_HDL(submodule_logic_name,input_types):	
		# IS RAW VHDL
		pass
	# NOT RAW VHDL (assumed to be built from C code then)
	else:
		submodule_logic = BUILD_LOGIC_AS_C_CODE(submodule_logic, parser_state, containing_func_logic)
	
	
	# Do here for early debug
	SYN.IS_BITWISE_OP(submodule_logic)
			
	return submodule_logic
	
_other_partial_logic_cache = dict()
def BUILD_LOGIC_AS_C_CODE(partially_complete_logic, parser_state, containing_func_logic):
	# The binary operators and their input types completely define the operator
	# So Cache the other partial logic
	cache_tok = partially_complete_logic.func_name
	for in_wire in partially_complete_logic.inputs:
		c_type = partially_complete_logic.wire_to_c_type[in_wire]
		cache_tok += "_" + c_type
		
	if cache_tok in _other_partial_logic_cache:
		other_partial_logic = _other_partial_logic_cache[cache_tok]
	else:
		out_dir = SYN.GET_OUTPUT_DIRECTORY(partially_complete_logic, implement=False)
		# Get C code depending on function
		#print "BUILD_LOGIC_AS_C_CODE"
		#print "partially_complete_logic.func_name",partially_complete_logic.func_name
		#print "partially_complete_logic.inst_name",partially_complete_logic.inst_name
		#print "containing_func_logic.func_name",containing_func_logic.func_name
		#print "containing_func_logic.inst_name",containing_func_logic.inst_name
		#print "=================================================================="
		if partially_complete_logic.func_name.startswith(VAR_REF_ASSIGN_FUNC_NAME_PREFIX + "_"):
			# Get the c code
			c_code_text = SW_LIB.GET_VAR_REF_ASSIGN_C_CODE(partially_complete_logic, containing_func_logic, out_dir, parser_state)
		elif partially_complete_logic.func_name.startswith(VAR_REF_RD_FUNC_NAME_PREFIX + "_"):
			# Get the c code
			c_code_text = SW_LIB.GET_VAR_REF_RD_C_CODE(partially_complete_logic, containing_func_logic, out_dir, parser_state)
		elif partially_complete_logic.func_name == (BIN_OP_LOGIC_NAME_PREFIX + "_" + BIN_OP_MULT_NAME):
			# Get the c code
			c_code_text = SW_LIB.GET_BIN_OP_MULT_C_CODE(partially_complete_logic, out_dir, parser_state)
		elif partially_complete_logic.func_name == (BIN_OP_LOGIC_NAME_PREFIX + "_" + BIN_OP_DIV_NAME):
			c_code_text = SW_LIB.GET_BIN_OP_DIV_C_CODE(partially_complete_logic, out_dir)
		elif partially_complete_logic.func_name == (BIN_OP_LOGIC_NAME_PREFIX + "_" + BIN_OP_GT_NAME):
			c_code_text = SW_LIB.GET_BIN_OP_GT_GTE_C_CODE(partially_complete_logic, out_dir, op_str=">")
		elif partially_complete_logic.func_name == (BIN_OP_LOGIC_NAME_PREFIX + "_" + BIN_OP_GTE_NAME):
			c_code_text = SW_LIB.GET_BIN_OP_GT_GTE_C_CODE(partially_complete_logic, out_dir, op_str=">=")
		elif partially_complete_logic.func_name == (BIN_OP_LOGIC_NAME_PREFIX + "_" + BIN_OP_PLUS_NAME):
			c_code_text = SW_LIB.GET_BIN_OP_PLUS_C_CODE(partially_complete_logic, out_dir)
		elif partially_complete_logic.func_name == (BIN_OP_LOGIC_NAME_PREFIX + "_" + BIN_OP_MINUS_NAME):
			c_code_text = SW_LIB.GET_BIN_OP_MINUS_C_CODE(partially_complete_logic, out_dir)
		elif partially_complete_logic.func_name == (BIN_OP_LOGIC_NAME_PREFIX + "_" + BIN_OP_SL_NAME):
			c_code_text = SW_LIB.GET_BIN_OP_SL_C_CODE(partially_complete_logic, out_dir, containing_func_logic, parser_state)
		elif partially_complete_logic.func_name == (BIN_OP_LOGIC_NAME_PREFIX + "_" + BIN_OP_SR_NAME):
			c_code_text = SW_LIB.GET_BIN_OP_SR_C_CODE(partially_complete_logic, out_dir, containing_func_logic, parser_state)
		else:
			print "How to BUILD_LOGIC_AS_C_CODE for",partially_complete_logic.func_name, "?"
			sys.exit(0)	
			
		# Use the c code to get the logic
		partially_complete_logic.c_code_text = c_code_text
		
		#print "c_code_text"
		#print c_code_text
		
		# And read logic
		#print "partially_complete_logic.
		fake_filename = VHDL.GET_INST_NAME(partially_complete_logic, use_leaf_name=True) + ".c"
		#print "fake_filename",fake_filename
		out_path = out_dir + "/" + fake_filename
			
		# Parse and return the only func def
		func_name = partially_complete_logic.func_name
		print "...",cache_tok.replace(partially_complete_logic.func_name+"_", partially_complete_logic.func_name + " : ")
		sw_func_name_2_logic = SW_LIB.GET_AUTO_GENERATED_FUNC_NAME_LOGIC_LOOKUP_FROM_CODE_TEXT(c_code_text, parser_state)
		# Merge into existing
		for sw_func_name in sw_func_name_2_logic:
			#print "sw_func_name",sw_func_name
			parser_state.FuncName2Logic[sw_func_name] = sw_func_name_2_logic[sw_func_name]
		
		FuncName2Logic = GET_FUNC_NAME_LOGIC_LOOKUP_TABLE_FROM_C_CODE_TEXT(c_code_text, fake_filename, parser_state, parse_body = True)
		
		# Get the other partial logic if it exists
		if not(func_name in FuncName2Logic ):
			print "I cant find func name",func_name,"in the C code so far"
			print "c_code_text"
			print c_code_text
			print "========="
			print "sw_func_name_2_logic"
			print sw_func_name_2_logic
			print "CHECK CODE PARSING autogenerated stuff?"
			sys.exit(0)
		other_partial_logic = FuncName2Logic[func_name].DEEPCOPY() #copy.deepcopy(FuncName2Logic[func_name]) #Deepcopy unneeded?
		# CACHE THIS
		_other_partial_logic_cache[cache_tok] = other_partial_logic
	
	#print "partially_complete_logic.func_name",partially_complete_logic.func_name
	#print "partially_complete_logic.inst_name",partially_complete_logic.inst_name
	#print "other_partial_logic.func_name", other_partial_logic.func_name
	#print "other_partial_logic.submodule_instances", other_partial_logic.submodule_instances
	#print "partially_complete_logic.inputs",partially_complete_logic.inputs
	#print "other_partial_logic.inputs", other_partial_logic.inputs
	if other_partial_logic.func_name in other_partial_logic.submodule_instances:
		print "other_partial_logic.func_name in other_partial_logic.submodule_instances"
		print "other_partial_logic.func_name",other_partial_logic.func_name
		sys.exit(0)
	
	# Func logic has wrong inst name
	other_partial_logic.inst_name = partially_complete_logic.inst_name
	#print "other_partial_logic.inst_name",other_partial_logic.inst_name
	# Also needs built in flag from partial logic
	other_partial_logic.is_c_built_in = partially_complete_logic.is_c_built_in
	# Fix cast ndoe too
	other_partial_logic.c_ast_node = partially_complete_logic.c_ast_node
	
	# Combine two partial logics
	#print "partially_complete_logic.c_ast_node.coord", partially_complete_logic.c_ast_node.coord
	#print "other_partial_logic.c_ast_node.coord", other_partial_logic.c_ast_node.coord
	partially_complete_logic.MERGE_COMB_LOGIC(other_partial_logic)
	#print "merged_logic.c_ast_node.coord", merged_logic.c_ast_node.coord
	
	#print "merged_logic.inst_name", merged_logic.inst_name
	#print "merged_logic.func_name", merged_logic.func_name
	
	return partially_complete_logic
		
# DOESNT SEEM TO HELP
#print "Keep _GET_FUNC_NAME_LOGIC_LOOKUP_TABLE_FROM_C_CODE_TEXT_cache? 849"
#_GET_FUNC_NAME_LOGIC_LOOKUP_TABLE_FROM_C_CODE_TEXT_cache = dict()
def GET_FUNC_NAME_LOGIC_LOOKUP_TABLE_FROM_C_CODE_TEXT(text, fake_filename, parser_state, parse_body):
	#print "GET_FUNC_NAME_LOGIC_LOOKUP_TABLE_FROM_C_CODE_TEXT"
	#print text
	#print fake_filename
	
	
	#global _GET_FUNC_NAME_LOGIC_LOOKUP_TABLE_FROM_C_CODE_TEXT_cache
	#cache_tok = text+fake_filename
	#try:
	#	return _GET_FUNC_NAME_LOGIC_LOOKUP_TABLE_FROM_C_CODE_TEXT_cache[cache_tok]
	#except:
	#	pass
	
	
	# Build function name to logic from func defs from files
	func_name_2_logic = copy.deepcopy(parser_state.FuncName2Logic) #copy.deepcopy(parser_state.FuncName2Logic)   #### Uh need this copy so bit manip/math funcs not directly in C text are accumulated over time wtf? TODO: Fix 
	#func_name_2_logic = dict()
	
	func_defs = GET_C_AST_FUNC_DEFS_FROM_C_CODE_TEXT(text, fake_filename)
	#print "== done parsing"
	
	
	for func_def in func_defs:
		#print "...func def"
		# Each func def produces a single logic item
		existing_logic=None
		driven_wire_names=[]
		prepend_text=""
		logic = C_AST_FUNC_DEF_TO_LOGIC(func_def, parser_state, parse_body)
		#logic = C_AST_NODE_TO_LOGIC(func_def,existing_logic, driven_wire_names, prepend_text, func_name_2_logic)
		
		#print "GET_FUNC_NAME_LOGIC_LOOKUP_TABLE_FROM_C_CODE_TEXT", logic.func_name, logic.wire_drives
		
		func_name_2_logic[logic.func_name] = logic
		func_name_2_logic[logic.func_name].inst_name = logic.func_name 
	
	#print "===================================================="
	
	#_GET_FUNC_NAME_LOGIC_LOOKUP_TABLE_FROM_C_CODE_TEXT_cache[cache_tok]=func_name_2_logic
	
	
	return func_name_2_logic
	
		
# WHY CAN I NEVER REMEMBER DICT() IS NOT IMMUTABLE (AKA needs copy operator)
# BECAUSE YOU ARE A PIECE OF SHIT	

# Node needs context for variable renaming over time, can give existing logic
def C_AST_NODE_TO_LOGIC(c_ast_node, driven_wire_names, prepend_text, parser_state):
	#func_name_2_logic = parser_state.FuncName2Logic
	
	#rv = Logic()
	
	#existing_logic_copy = Logic()
	#if parser_state.existing_logic is not None:
	#	existing_logic_copy = rv.MERGE_COMB_LOGIC(parser_state.existing_logic)
	
	# Cover logic as far up in c ast tree as possible
	# Each node will have function to deal with node type:
	# which may or may not recursively call this function.
	
	# C_AST nodes can represent pure structure logic
	if type(c_ast_node) == c_ast.FuncDef:
		if prepend_text!="":
			print "prepend for func def what?"
			sys.exit(0)
		return C_AST_FUNC_DEF_TO_LOGIC(c_ast_node, parser_state)
	elif type(c_ast_node) == c_ast.Compound:
		return C_AST_COMPOUND_TO_LOGIC(c_ast_node, prepend_text, parser_state)
	elif type(c_ast_node) == c_ast.Decl:
		return C_AST_DECL_TO_LOGIC(c_ast_node, prepend_text, parser_state)	
	elif type(c_ast_node) == c_ast.If:
		return C_AST_IF_TO_LOGIC(c_ast_node,prepend_text, parser_state)
	elif type(c_ast_node) == c_ast.Return:
		return C_AST_RETURN_TO_LOGIC(c_ast_node, prepend_text, parser_state)
	elif type(c_ast_node) == c_ast.FuncCall:
		return C_AST_FUNC_CALL_TO_LOGIC(c_ast_node,driven_wire_names, prepend_text, parser_state)
	elif type(c_ast_node) == c_ast.BinaryOp:
		return C_AST_BINARY_OP_TO_LOGIC(c_ast_node,driven_wire_names, prepend_text, parser_state)
	elif type(c_ast_node) == c_ast.UnaryOp:
		return C_AST_UNARY_OP_TO_LOGIC(c_ast_node,driven_wire_names, prepend_text, parser_state)
	elif type(c_ast_node) == c_ast.Constant:
		return C_AST_CONSTANT_TO_LOGIC(c_ast_node,driven_wire_names, prepend_text, parser_state)
	elif type(c_ast_node) == c_ast.ID:
		return C_AST_ID_TO_LOGIC(c_ast_node,driven_wire_names,prepend_text, parser_state)
		'''
	elif type(c_ast_node) == c_ast.StructRef:
		ret = C_AST_STRUCTREF_TO_LOGIC(c_ast_node,driven_wire_names,prepend_text, parser_state)
		return ret
		'''
	#elif type(c_ast_node) == c_ast.ID or type(c_ast_node) == c_ast.StructRef :
	#	return C_AST_ID_OR_STRUCTREF_TO_LOGIC(c_ast_node,driven_wire_names, prepend_text, parser_state)
	elif type(c_ast_node) == c_ast.StructRef or type(c_ast_node) == c_ast.ArrayRef:
		return C_AST_REF_TO_LOGIC(c_ast_node,driven_wire_names, prepend_text, parser_state)
	#elif type(c_ast_node) == c_ast.ArrayRef:
	#	return C_AST_ARRAYREF_TO_LOGIC(c_ast_node,driven_wire_names, prepend_text, parser_state)
	elif type(c_ast_node) == c_ast.Assignment:
		return C_AST_ASSIGNMENT_TO_LOGIC(c_ast_node,driven_wire_names,prepend_text, parser_state)
	elif type(c_ast_node) == c_ast.For:
		return C_AST_FOR_TO_LOGIC(c_ast_node,driven_wire_names,prepend_text, parser_state)
	else:
		#start here
		print "Cannot parse c ast node to logic: ",c_ast_node
		casthelp(c_ast_node)
		print "driven_wire_names=",driven_wire_names
		sys.exit(0)
		
	
	## Update parser state since merged in exsiting logic earlier
	#parser_state.existing_logic = rv
		
	#return rv
	
def C_AST_RETURN_TO_LOGIC(c_ast_return, prepend_text, parser_state):
	# Check for double return
	if RETURN_WIRE_NAME in parser_state.existing_logic.wire_driven_by:
		print "What, more than one return? Come on man don't make me sad...", str(c_ast_return.coord)
		sys.exit(0)	
	
	# Return is just connection to wire
	# Since each logic blob is a C function
	# only one return per function allowed
	# connect variable wire name to "return"
	driven_wire_names=[RETURN_WIRE_NAME]
	prepend_text=""
	return_logic = C_AST_NODE_TO_LOGIC(c_ast_return.expr, driven_wire_names, prepend_text, parser_state)
	

	##### Bleh do the easier hard coded for 0 clk way for now
	
	# Also tie all globals to global wire
	# Collpase struct ref hierarchy to get top most orig wire name nodes
	#print "global_orig_wire_names",global_orig_wire_names
	# Whooray
	for global_wire in parser_state.existing_logic.global_wires:
		# Read ref_toks takes care of it
		ref_toks = [global_wire]
		connect_logic = C_AST_REF_TOKS_TO_LOGIC(ref_toks, c_ast_return, [global_wire], prepend_text, parser_state)
		#connect_logic = READ_ORIG_WIRE_LOGIC(global_wire, [global_wire], c_ast_return, prepend_text, parser_state)
		return_logic.MERGE_COMB_LOGIC(connect_logic)
		
	# Same for volatile globals
	for volatile_global_wire in parser_state.existing_logic.volatile_global_wires:
		# Read ref_toks takes care of it
		ref_toks = [volatile_global_wire]
		connect_logic = C_AST_REF_TOKS_TO_LOGIC(ref_toks, c_ast_return, [volatile_global_wire], prepend_text, parser_state)
		#connect_logic = READ_ORIG_WIRE_LOGIC(global_wire, [global_wire], c_ast_return, prepend_text, parser_state)
		return_logic.MERGE_COMB_LOGIC(connect_logic)
	
	
	parser_state.existing_logic = return_logic
	# Connect the return logic node to this one
	return return_logic

	
def GET_NAMES_LIST_FROM_STRUCTREF(c_ast_structref):
	if type(c_ast_structref.name) == c_ast.StructRef:
		names_list = GET_NAMES_LIST_FROM_STRUCTREF(c_ast_structref.name)
		names_list = names_list + [c_ast_structref.field.name]
		return names_list
	elif type(c_ast_structref.name) == c_ast.ID:
		name_wire = str(c_ast_structref.name.name)
		names_list = [name_wire, c_ast_structref.field.name]
		return names_list
	elif type(c_ast_structref.name) == c_ast.ArrayRef:
		names_list = GET_NAMES_LIST_FROM_ARRAYREF(c_ast_structref.name)
		names_list = names_list + [c_ast_structref.field.name]
		return names_list
	else:
		print "Need entry in GET_NAMES_LIST_FROM_STRUCTREF", 
		casthelp(c_ast_structref.name)
		sys.exit(0)
	
	return rv


	
def GET_LEAF_FIELD_NAME_FROM_STRUCTREF(c_ast_structref):
	names_list = GET_NAMES_LIST_FROM_STRUCTREF(c_ast_structref)
	return names_list[len(names_list)-1]
	
	
def GET_BASE_VARIABLE_NAME_FROM_STRUCTREF(c_ast_structref):
	names_list = GET_NAMES_LIST_FROM_STRUCTREF(c_ast_structref)
	return names_list[0]
		
def ORIG_VAR_NAME_TO_MOST_RECENT_ALIAS(orig_var_name, existing_logic):
	if existing_logic is not None:
		most_recent_alias = GET_MOST_RECENT_ALIAS(existing_logic, orig_var_name)
		return most_recent_alias
	else:
		return orig_var_name	

def C_AST_REF_TOKS_ARE_CONST(ref_toks):
	for ref_tok in ref_toks:
		# Constant array ref
		if type(ref_tok) == int:
			pass
		# ID or struct ref
		elif type(ref_tok) == str:
			pass
		# Variable array ref
		elif isinstance(ref_tok, c_ast.Node):
			return False
		else:
			print "Whats this ref eh yo?", ref_tok, c_ast_node.coord
			sys.exit(0)
	return True
			
			
def C_AST_REF_TOKS_TO_NEXT_WIRE_ASSIGNMENT_ALIAS(ref_toks, c_ast_node, parser_state):
	existing_logic = parser_state.existing_logic
	orig_var_name = ref_toks[0]
	id_str = ""
	for i in range(0, len(ref_toks)):
		ref_tok = ref_toks[i]
		# Constant array ref
		if type(ref_tok) == int:
			id_str += "[" + str(ref_tok) + "]"
		# ID or struct ref
		elif type(ref_tok) == str:
			if i == 0:
				# Base ID
				id_str += ref_tok
			else:
				# Struct ref
				id_str += "." + ref_tok
		# Variable array ref
		elif isinstance(ref_tok, c_ast.Node):
			id_str += "[*]"
		else:
			print "Whats this ref eh?", ref_tok, c_ast_node.coord
			sys.exit(0)
			
	
	# Alias will include location in src
	coord_str = C_AST_COORD_STR(c_ast_node.coord)
	# Base name
	alias_base = id_str+"_"+coord_str
	
	# Return base without number appended?
	if orig_var_name in existing_logic.wire_aliases_over_time:
		aliases = existing_logic.wire_aliases_over_time[orig_var_name]
		if alias_base not in aliases:
			return alias_base
	
	# Check existing logic for alias
	# First one to try is "0"
	i=0
	alias = alias_base+str(i)
	if existing_logic is not None:
		if orig_var_name in existing_logic.wire_aliases_over_time:
			aliases = existing_logic.wire_aliases_over_time[orig_var_name]
			while alias in aliases:
				i=i+1
				alias = alias_base+"_" + str(i)
	
	return alias
	

def ORIG_WIRE_NAME_TO_NEXT_WIRE_ASSIGNMENT_ALIAS(orig_wire_name, c_ast_node,  existing_logic):
	# Alias will include location in src
	coord_str = C_AST_COORD_STR(c_ast_node.coord)
	# Base name
	alias_base = orig_wire_name+"_"+coord_str+"_"
	
	# Check existing logic for alias
	# First one to try is "0"
	i=0
	alias = alias_base+str(i)
	if existing_logic is not None:
		if orig_wire_name in existing_logic.wire_aliases_over_time:
			aliases = existing_logic.wire_aliases_over_time[orig_wire_name]
			while alias in aliases:
				i=i+1
				alias = alias_base+str(i)
	
	return alias

def C_AST_CONSTANT_TO_ORIG_WIRE_NAME(c_ast_node):
	return str(c_ast_node.value)
		
def GET_MOST_RECENT_ALIAS(logic,orig_var_name):
	if orig_var_name in logic.wire_aliases_over_time:
		aliases =  logic.wire_aliases_over_time[orig_var_name]
		last_alias = aliases[len(aliases)-1]
		return last_alias
	else:
		return orig_var_name
		
		
		
# Bleh this is useful for for loop
# Maybe if I keep it near the regular assignment I will remember to fix bugs here too
# Maybe
def FAKE_ASSIGNMENT_TO_LOGIC(lhs_orig_var_name, rhs, c_ast_node, driven_wire_names, prepend_text, parser_state):	
	lhs_ref_toks = [lhs_orig_var_name]
	# For now only do constant on RHS
	if type(rhs) is not int:
		print "Can't fake none constant assignment for now..."
		sys.exit(0)
	
	func_name_2_logic = parser_state.FuncName2Logic
	existing_logic = parser_state.existing_logic
	
	rv = Logic()
	if existing_logic is not None:
		rv.MERGE_COMB_LOGIC(existing_logic)
	# BOTH LHS and RHS CAN BE EXPRESSIONS!!!!!!
	# BUT LEFT SIDE MUST RESULT IN VARIABLE ADDRESS / wire?
	#^^^^^^^^^^^^^^^^^
	
	
	
	# Assignments are ordered over time with existing logic
	# Assigning to a variable creates an alias
	# future reads on this variable are done from the alias
	lhs_next_wire_assignment_alias = prepend_text+C_AST_REF_TOKS_TO_NEXT_WIRE_ASSIGNMENT_ALIAS(lhs_ref_toks, c_ast_node, parser_state)
	#print "lhs_next_wire_assignment_alias",lhs_next_wire_assignment_alias
		
	# /\
	# SET LHS TYPE
	parser_state.existing_logic = rv
	lhs_c_type = C_AST_REF_TOKS_TO_C_TYPE(lhs_ref_toks, c_ast_node, parser_state)
	if not(lhs_orig_var_name in rv.variable_names):
		rv.variable_names.append(lhs_orig_var_name)
	# Type of alias wire is same as original wire
	rv.wire_to_c_type[lhs_next_wire_assignment_alias] = lhs_c_type
	

	driven_wire_names=[lhs_next_wire_assignment_alias]
	# Do constant number RHS as driver 
	wire_name = CONST_PREFIX + str(rhs) + "_" + C_AST_COORD_STR(c_ast_node.coord)
	const_connect_logic = CONNECT_WIRES_LOGIC(wire_name, driven_wire_names)
	rv.MERGE_COMB_LOGIC(const_connect_logic)
	rv.wire_to_c_type[wire_name]=lhs_c_type


	# Add alias to list in existing logic
	existing_aliases = []
	if lhs_orig_var_name in rv.wire_aliases_over_time:
		existing_aliases = rv.wire_aliases_over_time[lhs_orig_var_name]
	new_aliases = existing_aliases
	
    # Dont double add aliases
	if not(lhs_next_wire_assignment_alias in new_aliases):
		new_aliases = new_aliases + [lhs_next_wire_assignment_alias]
	rv.wire_aliases_over_time[lhs_orig_var_name] = new_aliases
	rv.alias_to_ref_toks[lhs_next_wire_assignment_alias] = lhs_ref_toks
	rv.alias_to_orig_var_name[lhs_next_wire_assignment_alias] = lhs_orig_var_name
	

	
	# Update parser state since merged in exsiting logic earlier
	parser_state.existing_logic = rv
	
	
	return rv

def GET_VAR_REF_REF_TOK_INDICES_DIMS_ITER_TYPES(ref_toks, c_ast_node, parser_state):
	#print "=="
	#print "ref_toks",ref_toks
	var_dim_ref_tok_indices = []
	var_dims = []
	var_dim_iter_types = []
	curr_ref_toks = ref_toks[:]		
	# need at last 2 ref toks, array cant be in pos 0
	while len(curr_ref_toks) >= 2:
		#print "=="
		#print "curr_ref_toks",curr_ref_toks
		last_index = len(curr_ref_toks)-1
		last_tok = curr_ref_toks[last_index]
		if isinstance(last_tok, c_ast.Node):
			# is variable array dim
			# Pop off this entry
			curr_ref_toks.pop(last_index)
			# Get the array type
			c_array_type = C_AST_REF_TOKS_TO_C_TYPE(curr_ref_toks, c_ast_node, parser_state)
			# Sanity check
			if not C_TYPE_IS_ARRAY(c_array_type):
				print "Oh no not an array?", c_array_type
				sys.exit(0)
			# Get the dims from the array
			#print "c_array_type",c_array_type
			elem_type,dims = C_ARRAY_TYPE_TO_ELEM_TYPE_AND_DIMS(c_array_type)
			#print "elem_type",elem_type
			#print "dims",dims
			# Want last dim? 
			'''
			last_dim = dims[len(dims)-1]
			# Save
			var_dim_ref_tok_indices.append(last_index)
			var_dims.append(last_dim)		
			var_dim_iter_types.append("uint" + str(int(math.ceil(math.log(last_dim,2)))) + "_t")
			'''
			# Or wait want first dim?
			first_dim = dims[0]
			# Save
			var_dim_ref_tok_indices.append(last_index)
			var_dims.append(first_dim)		
			var_dim_iter_types.append("uint" + str(int(math.ceil(math.log(first_dim,2)))) + "_t")			
		else:
			# Pop off this entry
			curr_ref_toks.pop(last_index)
			# Thats it
	
	# Have been reversed
	var_dim_ref_tok_indices.reverse()
	var_dims.reverse()
	var_dim_iter_types.reverse()
	
	#print "var_dim_ref_tok_indices, var_dims, var_dim_iter_types",var_dim_ref_tok_indices, var_dims, var_dim_iter_types
	
	return var_dim_ref_tok_indices, var_dims, var_dim_iter_types



def MAYBE_GLOBAL_VAR_INFO_TO_LOGIC(maybe_global_var, parser_state):
	# Regular globals
	if maybe_global_var in parser_state.global_info:
		# Oh fucklles account for inst logic?\
		global_var_inst_name = maybe_global_var
		if parser_state.existing_logic.inst_name is not None:
			global_var_inst_name = parser_state.existing_logic.inst_name + SUBMODULE_MARKER + maybe_global_var
		
		# Copy info into existing_logic
		parser_state.existing_logic.wire_to_c_type[global_var_inst_name] = parser_state.global_info[maybe_global_var].type_name

		# Add as global_wrie 
		if global_var_inst_name not in parser_state.existing_logic.global_wires:
			parser_state.existing_logic.global_wires.append(global_var_inst_name)
			
		# Record using globals
		parser_state.existing_logic.uses_globals = True
		#print "rv.func_name",rv.func_name, rv.uses_globals
		
	# Volatile globals
	if maybe_global_var in parser_state.volatile_global_info:
		print "TODO volatile adjsuit for inst blah blahj fuck"
		# Copy info into existing_logic
		parser_state.existing_logic.wire_to_c_type[maybe_global_var] = parser_state.volatile_global_info[maybe_global_var].type_name
		
		# Add as volatile global_wrie
		if maybe_global_var not in parser_state.existing_logic.volatile_global_wires:
			parser_state.existing_logic.volatile_global_wires.append(maybe_global_var)


	return parser_state.existing_logic


# If this works great, if not ill be so sad
# Sadness forever

def C_AST_ASSIGNMENT_TO_LOGIC(c_ast_assignment,driven_wire_names,prepend_text, parser_state):
	# Assume lhs can be evaluated as ref?
	lhs_ref_toks = C_AST_REF_TO_TOKENS(c_ast_assignment.lvalue, parser_state)
	lhs_orig_var_name = lhs_ref_toks[0]	


	func_name_2_logic = parser_state.FuncName2Logic
	existing_logic = parser_state.existing_logic
	
	rv = Logic()
	if existing_logic is not None:
		rv = existing_logic
	# BOTH LHS and RHS CAN BE EXPRESSIONS!!!!!!
	# BUT LEFT SIDE MUST RESULT IN VARIABLE ADDRESS / wire?
	#^^^^^^^^^^^^^^^^^
	
	#### GLOBALS \/
	# This is the first place we should see a global reference in terms of this function/logic
	parser_state.existing_logic = MAYBE_GLOBAL_VAR_INFO_TO_LOGIC(lhs_orig_var_name, parser_state)
	
	lhs_base_type = parser_state.existing_logic.wire_to_c_type[lhs_orig_var_name]
	const_lhs = C_AST_REF_TOKS_ARE_CONST(lhs_ref_toks)

	if not const_lhs:
		# Variable references write to larger "sized" references then constant references
		# dims=A,B,C
		# x[i] = 0   writes the entire 'x' array  (aka reads from anywhere in 'x' depend on this)
		# x[0][i] writes all of x[0] which is of type array[B]
		# x[i][0] writes all of x[ ][0]?? which is of type array[A]  ???
		# x[0][1][i] writes all of x[0][1] which is of type array[C]
		# x[i][0][j] writes all of x[ ][0][ ] which is of type x_type[A][C] ?
		# y[k].x[i][0][j]  = rhs       
		#
		# The RHS value is 'written' by muxing it into that portion of the array
		# First ready the entire struct portion that could be written
		# The full range of references is a sum of reading a bunch of constants
		# Build list of ref toks
		# [y,0,x,0,0,0]
		# [y,0,x,0,0,1]
		# [y,0,x,1,0,0]
		# ...
		# Get list of variable dims
		var_dim_ref_tok_indices, var_dims, var_dim_iter_types = GET_VAR_REF_REF_TOK_INDICES_DIMS_ITER_TYPES(lhs_ref_toks, c_ast_assignment.lvalue, parser_state)

		#print "lhs_ref_toks",lhs_ref_toks
		#print "var_dims",var_dims
		#print "var_dim_ref_tok_indices",var_dim_ref_tok_indices
	
		# Do the nest loops to create all possible ref toks
		ref_toks_list = []
		
		for orig_ref_tok_i in range(0, len(lhs_ref_toks)):
			orig_ref_tok = lhs_ref_toks[orig_ref_tok_i]
			# Start a new return list
			new_ref_toks_list = []
			# Is this orig ref tok variable?
			if isinstance(orig_ref_tok, c_ast.Node):
				# Variable
				# What dimension is this variable
				# Sanity check
				if orig_ref_tok_i not in var_dim_ref_tok_indices:
					print "Wait this ref tok isnt variable?", orig_ref_tok
					sys.exit(0)
				# Get index of this var dim is list of var dims
				var_dim_i = var_dim_ref_tok_indices.index(orig_ref_tok_i)
				var_dim = var_dims[var_dim_i]
				# For each existing ref tok append that with all possible dim values
				for ref_toks in ref_toks_list:
					for dim_val in range(0, var_dim):
						new_ref_toks = ref_toks + [dim_val]
						new_ref_toks_list.append(new_ref_toks)
			else:
				# Constant just append this constant value to all ref toks in list
				for ref_toks in ref_toks_list:
					new_ref_toks = ref_toks + [orig_ref_tok]
					new_ref_toks_list.append(new_ref_toks)
				# Or add as base element
				if len(ref_toks_list) == 0:
					new_ref_toks_list.append([orig_ref_tok])
			
			# Next iteration save new ref toks
			ref_toks_list = new_ref_toks_list[:]
		
		
		#print "ref_toks_list",ref_toks_list
		# Reduce that list of refs
		reduced_ref_toks_list = REDUCE_REF_TOKS(ref_toks_list, c_ast_assignment.lvalue, parser_state)
		#print "reduced_ref_toks_list",reduced_ref_toks_list
		
		##########################################
		# These refs are input to write funciton
		# 	Do regular logic writing to 'base' variable (in C this time?)
		# Writing to this base variable is mux between different copies of base var?
		# ^^^^^^^^^^^^^^^^^^^^ NOOOOOOOO dont want to be muxing giant base var when only writing a portion
		#
		# IF
		# x[ ][0][ ] which is of type x_type[A][C] 
		# What is the type driven by y[k].name[i][0][j]   
		#			is it    y_name_type[A][B][D] ????
		# Assign all the ref toks into a type like y_name_type[A][B][D]
		# Make copyies of that val and make constant assingments into it
		# Then nmux the copies type based on values of k,i,j
		# Output of write function is like y_name_type[A][B][D]
		lhs_elem_c_type = C_AST_REF_TOKS_TO_C_TYPE(lhs_ref_toks, c_ast_assignment.lvalue, parser_state)
		
		# Build C array type using variable dimensions
		lhs_array_type = lhs_elem_c_type
		for var_dim in var_dims:
			lhs_array_type += "[" + str(var_dim) + "]"
			
			
		# FUCK FUCK C cant return array blah blah 
		lhs_struct_array_type = lhs_elem_c_type + DUMB_STRUCT_THING
		for var_dim in var_dims:
			lhs_struct_array_type += "_" + str(var_dim)
		
		#print "lhs_struct_array_type",lhs_struct_array_type
		#sys.exit(0)
		
		
		# This is going to be implemented in as C so func name needs to be unique
		func_name = VAR_REF_ASSIGN_FUNC_NAME_PREFIX
	
		# Cant cache all refs?
		# Fuck it just make names that wont be wrong/overlap
		# Are there built in structs?
		# output/elem type
		func_name += "_" + lhs_elem_c_type.replace("[","").replace("]","")
		# Base type
		lhs_base_var_type_c_name = lhs_base_type.replace("[","_").replace("]","")
		func_name += "_" +lhs_base_var_type_c_name
		# output ref toks --dont include base var name
		for ref_tok in lhs_ref_toks[1:]:
			if type(ref_tok) == int:
				func_name += "_" + str(ref_tok)
			elif type(ref_tok) == str:
				func_name += "_" + ref_tok
			elif isinstance(ref_tok, c_ast.Node):
				func_name += "_" + "VAR"
			else:
				print "What is lhs ref tok?", ref_tok
				sys.exit(0)
		# input ref toks  --dont include base var name
		for ref_toks in reduced_ref_toks_list:
			for ref_tok in ref_toks[1:]:
				if type(ref_tok) == int:
					func_name += "_" + str(ref_tok)
				elif type(ref_tok) == str:
					func_name += "_" + ref_tok
				elif isinstance(ref_tok, c_ast.Node):
					func_name += "_" + "VAR"
				else:
					print "What is lhs ref tok?", ref_tok
					sys.exit(0)
		
		# NEED HASH to account for reduced ref toks as name
		input_ref_toks_str = ""
		for ref_toks in ref_toks_list:
			for ref_tok in ref_toks[1:]: # Skip base var name
				if type(ref_tok) == int:
					input_ref_toks_str += "_" + str(ref_tok)
				elif type(ref_tok) == str:
					input_ref_toks_str += "_" + ref_tok
				elif isinstance(ref_tok, c_ast.Node):
					input_ref_toks_str += "_" + "VAR"
				else:
					print "What is ref tok bleh????", ref_tok
					sys.exit(0)
		# Hash the string
		hash_ext = "_" + ((hashlib.md5(input_ref_toks_str).hexdigest())[0:4]) #4 chars enough?
		func_name += hash_ext
		
		
		'''
		# Variable dimensions
		for var_dim in var_dims:
			# uint width is log2
			width = int(math.ceil(math.log(var_dim,2)))
			var_dim_type = "uint" + str(width) + "_t"
			func_name += "_" + var_dim_type

		# Sanitize func name single is C
		func_name = func_name.replace("[","_").replace("]","_").replace("__","_")
		'''
		
		
		
		
		# get inst name
		func_inst_name = BUILD_INST_NAME(prepend_text,func_name, c_ast_assignment.lvalue)
		output_wire_name = func_inst_name+SUBMODULE_MARKER+RETURN_WIRE_NAME
		# Save ref toks for this ref submodule
		parser_state.existing_logic.ref_submodule_instance_to_ref_toks[func_inst_name] = lhs_ref_toks
		
		
		# DO INPUT WIRES
		# (elem_val, ref_tok0, ref_tok1, ..., var_dim0, var_dim1, ...)
		c_ast_node_2_driven_input_wire_names = OrderedDict()
		# KEY will be input port driving wire name
		use_input_nodes_fuck_it = False
		
		
		# Elem val is from rhs
		input_port_name = "elem_val"
		input_wire = func_inst_name+SUBMODULE_MARKER+input_port_name
		# Make the c_ast node drive the input wire
		input_connect_logic = C_AST_NODE_TO_LOGIC(c_ast_assignment.rvalue, [input_wire], prepend_text, parser_state)
		# Merge this connect logic
		rv.MERGE_SEQ_LOGIC(input_connect_logic)
		parser_state.existing_logic = rv
		# What drives the input port?
		driving_wire = rv.wire_driven_by[input_wire]
		# Save this
		c_ast_node_2_driven_input_wire_names[driving_wire] = [input_wire]
		
		# Do C_AST_REF_TOKS_TO_LOGIC
		# For all the ref toks
		# DONT INCLUDE VAR NAMES IN ports
		# Dont want to encode ref toks?
		# Var assign is implemented in C, then must be C safe
		ref_toks_i = 0
		parser_state.existing_logic.ref_submodule_instance_to_input_port_driven_ref_toks[func_inst_name] = []
		for ref_toks in reduced_ref_toks_list:
			input_port_name = "ref_toks_" + str(ref_toks_i)
			ref_toks_i += 1
			
			## if base variable then call it base
			#if len(ref_toks) == 1:
			#	input_port_name = "base_var"			
			input_wire = func_inst_name+SUBMODULE_MARKER+input_port_name
			
			# Make the ref toks drive the input wire
			input_connect_logic = C_AST_REF_TOKS_TO_LOGIC(ref_toks, c_ast_assignment.lvalue, [input_wire], prepend_text, parser_state)
			# Merge this connect logic
			rv.MERGE_SEQ_LOGIC(input_connect_logic)
			parser_state.existing_logic = rv
			
			# What drives the input port?
			driving_wire = rv.wire_driven_by[input_wire]
			
			# Save this
			c_ast_node_2_driven_input_wire_names[driving_wire] = [input_wire]
			
			# SET ref_submodule_instance_to_input_port_driven_ref_toks
			parser_state.existing_logic.ref_submodule_instance_to_input_port_driven_ref_toks[func_inst_name].append(ref_toks)
			
			
			
		# Do C_AST_NODE_TO_LOGIC for var_dim c_ast_nodes
		for var_dim_i in range(0, len(var_dims)):
			ref_tok_index = var_dim_ref_tok_indices[var_dim_i]
			ref_tok_c_ast_node = lhs_ref_toks[ref_tok_index]
			# Sanity check
			if not isinstance(ref_tok_c_ast_node, c_ast.Node):
				print "Not a variable ref tok?", ref_tok_c_ast_node
				sys.exit(0)
				
			# Cant use hacky str encode sinc eis just "*"
			# Say which variable index this is
			input_port_name = "var_dim_" + str(var_dim_i)
			input_wire = func_inst_name+SUBMODULE_MARKER+input_port_name
			
			# Set type of input wire
			parser_state.existing_logic.wire_to_c_type[input_wire] = var_dim_iter_types[var_dim_i]
			
			# Make the c_ast node drive the input wire
			input_connect_logic = C_AST_NODE_TO_LOGIC(ref_tok_c_ast_node, [input_wire], prepend_text, parser_state)
			# Merge this connect logic
			rv.MERGE_SEQ_LOGIC(input_connect_logic)
			parser_state.existing_logic = rv
			
			# What drives the input port?
			driving_wire = rv.wire_driven_by[input_wire]
			
			# Save this
			c_ast_node_2_driven_input_wire_names[driving_wire] = [input_wire]
			
			
		# OK, got all the input wires connected
	
		# VERY SIMILAR TO CONST
		###########################################
		# RECORD NEW ALIAS FOR THIS ASSIGNMENT!!!
		
		# Assignments are ordered over time with existing logic
		# Assigning to a variable creates an alias
		# future reads on this variable are done from the alias
		lhs_next_wire_assignment_alias = prepend_text+C_AST_REF_TOKS_TO_NEXT_WIRE_ASSIGNMENT_ALIAS(lhs_ref_toks, c_ast_assignment.lvalue, parser_state)
		#print "lhs_next_wire_assignment_alias",lhs_next_wire_assignment_alias
			
		# /\
		# SET LHS TYPE
		# Type of alias wire is "larger" sized array type
		#rv.wire_to_c_type[lhs_next_wire_assignment_alias] = lhs_array_type
		rv.wire_to_c_type[lhs_next_wire_assignment_alias] = lhs_struct_array_type
		
		
		# Save orig var name
		parser_state.existing_logic = rv
		if not(lhs_orig_var_name in rv.variable_names):
			rv.variable_names.append(lhs_orig_var_name)
		
		#print "lhs_next_wire_assignment_alias",lhs_next_wire_assignment_alias
		

		#print "c_ast_assignment.rvalue"
		#casthelp(c_ast_assignment.rvalue)
		driven_wire_names=[lhs_next_wire_assignment_alias]
		parser_state.existing_logic = rv
		
		# Get func logic
		rhs_to_lhs_logic = C_AST_N_ARG_FUNC_INST_TO_LOGIC(func_name, c_ast_node_2_driven_input_wire_names, output_wire_name, driven_wire_names, prepend_text, c_ast_assignment.lvalue, parser_state, use_input_nodes_fuck_it)	
		
		
		
		#print "after 'rv' in rv.wire_to_c_type", "rv" in rv.wire_to_c_type
		
		# Set type of RHS wire as LHS type if not known
		rhs_driver = rhs_to_lhs_logic.wire_driven_by[lhs_next_wire_assignment_alias]
		if rhs_driver not in rhs_to_lhs_logic.wire_to_c_type:
			#rhs_to_lhs_logic.wire_to_c_type[rhs_driver] = lhs_array_type	
			rhs_to_lhs_logic.wire_to_c_type[rhs_driver] = lhs_struct_array_type
			

		
		# Merge existing and rhs logic
		rv.MERGE_SEQ_LOGIC(rhs_to_lhs_logic)	

		# Add alias to list in existing logic
		existing_aliases = []
		if lhs_orig_var_name in rv.wire_aliases_over_time:
			existing_aliases = rv.wire_aliases_over_time[lhs_orig_var_name]
		new_aliases = existing_aliases
		
		# Dont double add aliases
		if not(lhs_next_wire_assignment_alias in new_aliases):
			new_aliases = new_aliases + [lhs_next_wire_assignment_alias]
		rv.wire_aliases_over_time[lhs_orig_var_name] = new_aliases
		rv.alias_to_ref_toks[lhs_next_wire_assignment_alias] = lhs_ref_toks
		rv.alias_to_orig_var_name[lhs_next_wire_assignment_alias] = lhs_orig_var_name
		

		
		# Update parser state since merged in exsiting logic earlier
		parser_state.existing_logic = rv
		
		
		return rv
	
	
	
	else:
		# CONSTANT ~~~~~~~~~~~~~~
		###########################################
		# RECORD NEW ALIAS FOR THIS ASSIGNMENT!!!
		
		# Assignments are ordered over time with existing logic
		# Assigning to a variable creates an alias
		# future reads on this variable are done from the alias
		lhs_next_wire_assignment_alias = prepend_text+C_AST_REF_TOKS_TO_NEXT_WIRE_ASSIGNMENT_ALIAS(lhs_ref_toks, c_ast_assignment.lvalue, parser_state)
		#print "lhs_next_wire_assignment_alias",lhs_next_wire_assignment_alias
			
		# /\
		# SET LHS TYPE
		parser_state.existing_logic = rv
		lhs_c_type = C_AST_REF_TOKS_TO_C_TYPE(lhs_ref_toks, c_ast_assignment.lvalue, parser_state)
		if not(lhs_orig_var_name in rv.variable_names):
			rv.variable_names.append(lhs_orig_var_name)
		# Type of alias wire is same as original wire
		rv.wire_to_c_type[lhs_next_wire_assignment_alias] = lhs_c_type
		
		
		#print "lhs_c_type",lhs_c_type
		#print "lhs_next_wire_assignment_alias",lhs_next_wire_assignment_alias
		

		#print "c_ast_assignment.rvalue"
		#casthelp(c_ast_assignment.rvalue)
		driven_wire_names=[lhs_next_wire_assignment_alias]
		parser_state.existing_logic = rv
		rhs_to_lhs_logic = C_AST_NODE_TO_LOGIC(c_ast_assignment.rvalue, driven_wire_names, prepend_text, parser_state)
		#print "after 'rv' in rv.wire_to_c_type", "rv" in rv.wire_to_c_type
		
		# Set type of RHS wire as LHS type if not known
		rhs_driver = rhs_to_lhs_logic.wire_driven_by[lhs_next_wire_assignment_alias]
		if rhs_driver not in rhs_to_lhs_logic.wire_to_c_type:
			rhs_to_lhs_logic.wire_to_c_type[rhs_driver] = lhs_c_type	
		

		
		# Merge existing and rhs logic
		rv.MERGE_SEQ_LOGIC(rhs_to_lhs_logic)	

		# Add alias to list in existing logic
		existing_aliases = []
		if lhs_orig_var_name in rv.wire_aliases_over_time:
			existing_aliases = rv.wire_aliases_over_time[lhs_orig_var_name]
		new_aliases = existing_aliases
		
		# Dont double add aliases
		if not(lhs_next_wire_assignment_alias in new_aliases):
			new_aliases = new_aliases + [lhs_next_wire_assignment_alias]
		rv.wire_aliases_over_time[lhs_orig_var_name] = new_aliases
		rv.alias_to_ref_toks[lhs_next_wire_assignment_alias] = lhs_ref_toks
		rv.alias_to_orig_var_name[lhs_next_wire_assignment_alias] = lhs_orig_var_name
		

		
		# Update parser state since merged in exsiting logic earlier
		parser_state.existing_logic = rv
		
		
		return rv
	
	
def C_AST_NODE_TO_ORIG_VAR_NAME(c_ast_node):
	if type(c_ast_node) == c_ast.ID:
		return C_AST_ID_TO_ORIG_WIRE_NAME(c_ast_node)
	elif type(c_ast_node) == c_ast.StructRef:
		return GET_BASE_VARIABLE_NAME_FROM_STRUCTREF(c_ast_node)
	else:
		print "WHat C_AST_NODE_TO_ORIG_VAR_NAME", c_ast_node
		sys.exit(0)
	
def EXPAND_REF_TOKS_OR_STRS(ref_toks_or_strs, c_ast_ref, parser_state):
	#print "EXPAND:",ref_toks_or_strs
	
	# Get list of variable dims
	var_dim_ref_tok_indices = []
	var_dims = []
	curr_ref_toks = ref_toks_or_strs[:]		
	# need at last 2 ref toks, array cant be in pos 0
	while len(curr_ref_toks) >= 2:
		last_index = len(curr_ref_toks)-1
		last_tok = curr_ref_toks[last_index]
		if last_tok == "*" or isinstance(last_tok, c_ast.Node):
			# is variable array dim
			# Pop off this entry
			curr_ref_toks.pop(last_index)
			
			# need to fake c_ast node for is this is strs
			curr_ref_toks_faked = []
			for curr_ref_tok in curr_ref_toks:
				if curr_ref_tok == "*":
					curr_ref_toks_faked.append(c_ast.Node())
				else:
					curr_ref_toks_faked.append(curr_ref_tok)
			
			# Get the array type
			c_array_type = C_AST_REF_TOKS_TO_C_TYPE(curr_ref_toks_faked, c_ast_ref, parser_state)
			# Sanity check
			if not C_TYPE_IS_ARRAY(c_array_type):
				print "Oh no not an array?2", c_array_type
				sys.exit(0)
			# Get the dims from the array
			elem_type,dims = C_ARRAY_TYPE_TO_ELEM_TYPE_AND_DIMS(c_array_type)
			# Want last dim
			#last_dim = dims[len(dims)-1]
			# First dim?
			first_dim = dims[0];
			# Save
			var_dim_ref_tok_indices.append(last_index)
			var_dims.append(first_dim)				
		else:
			# Pop off this entry
			curr_ref_toks.pop(last_index)
			# Thats it
	
	# Do the nest loops to create all possible ref toks
	ref_toks_list = []
	
	for orig_ref_tok_i in range(0, len(ref_toks_or_strs)):
		orig_ref_tok = ref_toks_or_strs[orig_ref_tok_i]
		# Start a new return list
		new_ref_toks_list = []
		# Is this orig ref tok variable?
		if orig_ref_tok =="*" or isinstance(orig_ref_tok, c_ast.Node):
			# Variable
			# What dimension is this variable
			# Sanity check
			if orig_ref_tok_i not in var_dim_ref_tok_indices:
				print "Wait this ref tok isnt variable?2", orig_ref_tok
				sys.exit(0)
			# Get index of this var dim is list of var dims
			var_dim_i = var_dim_ref_tok_indices.index(orig_ref_tok_i)
			var_dim = var_dims[var_dim_i]
			# For each existing ref tok append that with all possible dim values
			for ref_toks in ref_toks_list:
				for dim_val in range(0, var_dim):
					new_ref_toks = ref_toks + [dim_val]
					new_ref_toks_list.append(new_ref_toks)
		else:
			# Fix string digits to be ints
			if type(orig_ref_tok) == str and orig_ref_tok.isdigit():
				orig_ref_tok = int(orig_ref_tok)
			# Constant just append this constant value to all ref toks in list
			for ref_toks in ref_toks_list:
				new_ref_toks = ref_toks + [orig_ref_tok]
				new_ref_toks_list.append(new_ref_toks)				
			# Or add as base element
			if len(ref_toks_list) == 0:
				new_ref_toks_list.append([orig_ref_tok])
		
		# Next iteration save new ref toks
		ref_toks_list = new_ref_toks_list[:]
	
	
	#print "EXPANDED:", ref_toks_list
	#if "*" in ref_toks_or_strs:
	#	sys.exit(0)
	
	return ref_toks_list
		
_REF_TOKS_TO_ALL_BRANCH_REF_TOKS_cache = dict()
# For now stick with string wires instead of toks list
def REF_TOKS_TO_ALL_BRANCH_REF_TOKS(ref_toks, c_ast_ref, parser_state):
	debug = False
	debug = ("VAR_REF_ASSIGN_uint8_t_uint8_t_8_VAR_a1a4" in parser_state.existing_logic.func_name) and (ref_toks[0] == "rv")
	
	
	# Try to get cache
	# Build key
	ref_toks_str = parser_state.existing_logic.func_name[:]
	for ref_tok in ref_toks:
		if type(ref_tok) == int:
			ref_toks_str += "_" + str(ref_tok)
		elif type(ref_tok) == str:
			ref_toks_str += "_" + ref_tok
		elif isinstance(ref_tok, c_ast.Node):
			ref_toks_str += "_" + "VAR"
		else:
			print "What is ref tok bleh?sdkhjgsd???", ref_tok
			sys.exit(0)
	# Try for cache
	try:
		return _REF_TOKS_TO_ALL_BRANCH_REF_TOKS_cache[ref_toks_str]
	except:
		pass
	
	# Current c type
	c_type = C_AST_REF_TOKS_TO_C_TYPE(ref_toks, c_ast_ref, parser_state)

	#print ref_toks, c_type
	
	rv = []

	# Struct?
	if C_TYPE_IS_STRUCT(c_type, parser_state):
		# Child branches are struct field names
		field_type_dict = parser_state.struct_to_field_type_dict[c_type]
		for field in field_type_dict:
			new_toks = ref_toks[:]
			new_toks.append(field)
			rv.append(new_toks)
			# Recurse on new toks
			rv += REF_TOKS_TO_ALL_BRANCH_REF_TOKS(new_toks, c_ast_ref, parser_state)
	
	# Array?
	elif C_TYPE_IS_ARRAY(c_type):
		# One dimension at a time works?
		base_elem_type, dims = C_ARRAY_TYPE_TO_ELEM_TYPE_AND_DIMS(c_type)
		current_dim = dims[0]
		inner_type = GET_ARRAYREF_OUTPUT_TYPE_FROM_C_TYPE(c_type)
		for i in range(0, current_dim):
			new_toks = ref_toks[:]
			new_toks.append(i)
			rv.append(new_toks)
			# Recurse on new toks
			rv += REF_TOKS_TO_ALL_BRANCH_REF_TOKS(new_toks, c_ast_ref, parser_state)
	else:
		# Not composite type 
		# Only branch is self?
		rv = [ref_toks]
		
	

	# Expand all varaible ref toks
	# variable_ref_toks_exist
	variable_ref_toks_exist = False
	for ref_toks_i in rv:
		for tok in ref_toks_i:
			if isinstance(tok, c_ast.Node):
				variable_ref_toks_exist = True
				break
		if variable_ref_toks_exist:
			break
			
	while variable_ref_toks_exist:
		# Find a variable ref tok
		for i in range(0, len(rv)):
			ref_toks_i = rv[i]
			made_change = False
			for j in range(0, len(ref_toks_i)):
				tok = ref_toks_i[j]
				if isinstance(tok, c_ast.Node):
					# Remove this ref tok from list
					rv.remove(ref_toks_i)
					# Replace it with all the possible dimensions of this variable ref array
					# What is the type of the array represented by this type
					included_toks = ref_toks_i[0:j]
					#print "included_toks",included_toks
					c_type = C_AST_REF_TOKS_TO_C_TYPE(included_toks, c_ast_ref, parser_state)
					# Sanity check
					if not C_TYPE_IS_ARRAY(c_type):
						print "Wtf not an array type?"
						sys.exit(0)
					# Get dims
					elem_type, dims = C_ARRAY_TYPE_TO_ELEM_TYPE_AND_DIMS(c_type)
					#last_dim = dims[len(dims)-1]
					# Want first dim?
					first_dim = dims[0]
					
					# The last dim is our variable ref
					for dim_val in range(0, first_dim):
						net_ref_toks = ref_toks_i[:]
						net_ref_toks[j] = dim_val
						rv.append(net_ref_toks)
					# Done
					made_change = True
					break
			if made_change:
				break
		
		# variable_ref_toks_exist
		variable_ref_toks_exist = False
		for ref_toks_i in rv:
			for tok in ref_toks_i:
				if isinstance(tok, c_ast.Node):
					variable_ref_toks_exist = True
					break
			if variable_ref_toks_exist:
				break
				
			
			
	# Update cache
	_REF_TOKS_TO_ALL_BRANCH_REF_TOKS_cache[ref_toks_str] = rv
				
	return rv
	
	

def REDUCE_REF_TOKS(ref_toks_list, c_ast_node, parser_state):
	# Collpase ex. [ [struct,pointa,x] , [struct,pointa,y], [struct,pointb,x] ]
	# collpases down to [ [struct,pointa], [struct,pointb,x] ] since sub elements of point are all driven
	
	rv_ref_toks_list = ref_toks_list[:]
	still_removing_elements = True
	while still_removing_elements:
		# Assume stoping now
		still_removing_elements = False
		
		#print "====="
		#print "rv_ref_toks_list",rv_ref_toks_list
		
		# Loop over all ref toks
		loop_copy_rv_ref_toks_list = rv_ref_toks_list[:]
		for ref_toks in loop_copy_rv_ref_toks_list:
			# IF removing elements then back to outermost loop
			if still_removing_elements:
				break
			
			# Remove children of this ref_tok
			for maybe_child_ref_tok in loop_copy_rv_ref_toks_list:
				if maybe_child_ref_tok != ref_toks:
					if REF_TOKS_STARTS_WITH(maybe_child_ref_tok, ref_toks, parser_state):
						rv_ref_toks_list.remove(maybe_child_ref_tok)
						
			# Record if change was made and jump to next iteration
			if rv_ref_toks_list != loop_copy_rv_ref_toks_list:
				still_removing_elements = True
				break
				
			
			#c_type = C_AST_REF_TOKS_TO_C_TYPE(ref_toks, c_ast_node, parser_state)
			## If not a struct ref then no more collpasing possible
			#if not C_TYPE_IS_STRUCT(c_type, parser_state)  "." not in orig_wire_name:
			#	continue					
			
			# Check if these ref_toks are a leaf with all sibling leafs driven
			if len(ref_toks) < 2:
				continue

			# Get root struct for this struct ref
			root_ref_toks = ref_toks[0:len(ref_toks)-1]
			# Check if all fields of this root struct ref are in this list
			root_c_type = C_AST_REF_TOKS_TO_C_TYPE(root_ref_toks, c_ast_node, parser_state)
			all_fields_present = True
			if C_TYPE_IS_STRUCT(root_c_type,parser_state):
				field_types_dict = parser_state.struct_to_field_type_dict[root_c_type]
				for field_name in field_types_dict:
					possible_ref_toks = root_ref_toks + [field_name]
					if not REF_TOKS_IN_REF_TOKS_LIST(possible_ref_toks, rv_ref_toks_list):
						all_fields_present = False
							
				# If all there then remove them all
				if all_fields_present:
					still_removing_elements = True
					for field_name in field_types_dict:
						possible_ref_toks = root_ref_toks + [field_name]
						rv_ref_toks_list.remove(possible_ref_toks)
					# And replace with root
					rv_ref_toks_list.append(root_ref_toks)
					# Next iteration
					break
						
			elif C_TYPE_IS_ARRAY(root_c_type):
				#print "!~~~"
				#print "root_ref_toks",root_ref_toks
				#print "root_c_type",root_c_type
				elem_type, dims = C_ARRAY_TYPE_TO_ELEM_TYPE_AND_DIMS(root_c_type)
				#last_dim = dims[len(dims)-1]
				# No want first dim?
				first_dim = dims[0]
				
				for i in range(0, first_dim):
					possible_ref_toks = root_ref_toks + [i]
					#print "	possible_ref_toks",possible_ref_toks
					#print "in"
					#print rv_ref_toks_list
					if not REF_TOKS_IN_REF_TOKS_LIST(possible_ref_toks, rv_ref_toks_list):
						#print "NO"
						all_fields_present = False
						
						
				# If all there then remove them all
				if all_fields_present:
					#print "all_fields_present", root_ref_toks
					still_removing_elements = True
					for i in range(0, first_dim):
						possible_ref_toks = root_ref_toks + [i]
						#print "	REMOVING possible_ref_toks",possible_ref_toks
						rv_ref_toks_list.remove(possible_ref_toks)
					# And replace with root
					rv_ref_toks_list.append(root_ref_toks)
					# Next iteration
					break
			else:
				# Is not a composite type?
				pass
			 
			
	#print "rv_ref_toks_list",rv_ref_toks_list
	#sys.exit(0)
	return rv_ref_toks_list


def REF_TOKS_STARTS_WITH(ref_toks, starting_ref_toks, parser_state):
	for ref_tok_i in range(0, len(starting_ref_toks)):
		if ref_tok_i > len(ref_toks) - 1:
			return False
		ref_tok = ref_toks[ref_tok_i]
		# Variable c_ast node matches anything
		if isinstance(ref_tok, c_ast.Node) or isinstance(starting_ref_toks[ref_tok_i], c_ast.Node):
			pass
		else:
			# Do compare
			#print ref_tok, "!=?",starting_ref_toks[ref_tok_i]
			if ref_tok != starting_ref_toks[ref_tok_i]:
				return False
	return True

	#return ref_toks[:len(starting_ref_toks)] == starting_ref_toks

def REF_TOKS_IN_REF_TOKS_LIST(ref_toks, ref_toks_list):
	return ref_toks in ref_toks_list


def WIRE_TO_REF_TOKS(wire, parser_state):
	# Get ref toks for this alias
	if wire in parser_state.existing_logic.alias_to_ref_toks:
		driven_ref_toks = parser_state.existing_logic.alias_to_ref_toks[wire]
	else:
		# Must be orig variable name
		if wire in parser_state.existing_logic.variable_names:
			driven_ref_toks=[wire]
		# Or input
		elif wire in parser_state.existing_logic.inputs:
			driven_ref_toks=[wire]
		# Or global ~
		elif wire in parser_state.global_info:
			driven_ref_toks=[wire]
		# Or volatile global
		elif wire in parser_state.volatile_global_info:
			driven_ref_toks=[wire]
		else:
			print "wire:",wire
			print "var name?:",parser_state.existing_logic.variable_names
			print "does not have associatated ref toks", parser_state.existing_logic.alias_to_ref_toks
			print 0/0
			sys.exit(0)
			
	return driven_ref_toks

# THIS IS DIFFERENT FROM REDUCE DONE ABOVE
def REMOVE_COVERED_REF_TOK_BRANCHES(remaining_ref_toks, alias, c_ast_node, parser_state):
	
	#if "rv.structs[*].a[*][*]_main_c_l24_c2" in alias:
	#print "~~~~"
	#print "alias", alias
	#print "remaining_ref_toks",remaining_ref_toks
		
	driven_ref_toks = WIRE_TO_REF_TOKS(alias, parser_state)
		
	
	new_remaining_ref_toks = []
	# First loop for obvious coverage 
	# Given alias wire a.b.c , it covers any remaining wire a.b.c.x, a.b.c.y
	for ref_toks in remaining_ref_toks:
		if not REF_TOKS_STARTS_WITH(ref_toks, driven_ref_toks, parser_state):
			# Save this ref toks
			new_remaining_ref_toks.append(ref_toks)
			
	#if "rv.structs[*].a[*][*]_main_c_l24_c2" in alias:
	#print "driven_ref_toks", driven_ref_toks
	#print "new_remaining_ref_toks",new_remaining_ref_toks	
	
	
	#print "===="
	#print "alias",alias
	#print "driven_ref_toks",driven_ref_toks
	#print "remaining_ref_toks",remaining_ref_toks
	#print "new_remaining_ref_toks",new_remaining_ref_toks
	#print "===="
	
	# Then remove any ref toks with no remaining branches in list
	removing_elems = True
	rv = new_remaining_ref_toks[:]
	while removing_elems:
		removing_elems = False
		new_remaining_ref_toks = rv[:]
		rv = []
		for ref_toks in new_remaining_ref_toks:
			all_branch_ref_toks = REF_TOKS_TO_ALL_BRANCH_REF_TOKS(ref_toks, c_ast_node, parser_state)	
			
			# Does this ref tok even have branches?
			has_remaining_branch = True # default has self branch
			if len(all_branch_ref_toks) > 1:
				# Any of those branches (that arent self) left in list?
				has_remaining_branch = False
				for branch_ref_toks in all_branch_ref_toks:
					# Dont look for self in list? Needed?
					if (branch_ref_toks != ref_toks) and REF_TOKS_IN_REF_TOKS_LIST(branch_ref_toks, new_remaining_ref_toks):
						#if "rv.structs[*].a[*][*]_main_c_l24_c2" in alias:
						#	print "branch_ref_toks in branch_ref_toks",branch_ref_toks
						has_remaining_branch = True
						break
			if not has_remaining_branch:
				# No remaining branches so elminate this wire
				removing_elems = True
				continue
					
			# Save this ref toks
			rv.append(ref_toks)
		
	
	
	
	#if "rv.structs[*].a[*][*]_main_c_l24_c2" in alias:
	#print "rv",rv
	
	
	return rv
	
	

# Struct read is different from array read since:
# At the time of struct read it is possible to narrow down the 
# renamed intermediate wires that of what the struct ref is referreing
# for an array reference the "struct locations in memory / memory addrs" cannot be known ahead of time
# Always need to input entire array unless constant, when constant do like struct ref?

'''
DID you do struct ref wrong?
CANT PROCESS AS single x.y.z expression
Need to recursively get X, with .y  ... then get output of that DOT z
fuck

ONly diff between constant array and dynamic is where the "branches" start in the structref/array search
# Since arrays are written to like structs, COPY ON READ
Structref and constant array look very similar
'''
	
# ID could be a struct ID which needs struct read logic
# ID could also be an array ID which needs array read logic


# x[i][1][k]
# First need to select the i'th [n][n] array from 'x'
# Then select the 1st [n] array from output of above
# Then select k'th element from output of above
# So out of all x only these elements are needed
# 
# x 0 0 0    
# x 0 0 1
# x 0 1 0     X
# x 0 1 1     X 
# x 1 0 0 
# x 1 0 1
# x 1 1 0     X
# x 1 1 1     X

# Need to expand struct, array to all branches?
# Then evaluate  s.x[i][1] to be  s[x,i,1]
#	s.x[0][0]   
#	s.x[0][1]   X
#	s.x[1][0]
#	s.x[1][1]   X
#	s.y[0][0]
#	s.y[0][1]
#	s.y[1][0]
#	s.y[1][1]

def C_TYPE_IS_STRUCT(c_type_str, parser_state):
	if parser_state is None:
		print 0/0
	return (c_type_str in parser_state.struct_to_field_type_dict) or (DUMB_STRUCT_THING in c_type_str)
	
def C_TYPE_IS_ENUM(c_type_str, parser_state):
	if parser_state is None:
		print 0/0
	return c_type_str in parser_state.enum_to_ids_dict
	
def C_TYPE_IS_ARRAY(c_type):
	return "[" in c_type and c_type.endswith("]")
	
#def C_TYPE_IS_BUILT_IN(c_type):
	
#def C_TYPES_ARE_BUILT_IN(input_types):
	

	
# Returns None if ID is not driven by constant
def RESOLVE_CONST_ID(c_ast_id, parser_state):
	orig_var_name = str(c_ast_id.name)
	# Get most recent alias
	mra = GET_MOST_RECENT_ALIAS(parser_state.existing_logic, orig_var_name)
	# See if this is directly driven by constant
	const_driving_wire = FIND_CONST_DRIVING_WIRE(mra, parser_state.existing_logic)
	if const_driving_wire is None:
		return None
	
	# Get value from this constant
	maybe_digit = GET_MAYBE_DIGIT_FROM_CONST_WIRE(const_driving_wire, parser_state.existing_logic, parser_state)
	if not maybe_digit.isdigit():
		return None
	
	return int(maybe_digit)
	
	
# Returns None if not resolved
def RESOLVE_CONST_ARRAY_REF(c_ast_array_ref, parser_state):
	if type(c_ast_array_ref.subscript) == c_ast.Constant:
		const = int(c_ast_array_ref.subscript.value)
		return const
	elif type(c_ast_array_ref.subscript) == c_ast.ID:
		return RESOLVE_CONST_ID(c_ast_array_ref.subscript,parser_state)
	else:	
		print "I don't know how to resolve the array ref at", c_ast_ref.subscript.coord
		sys.exit(0)

# ONLY USE THIS WITH REF C AST NODES
def C_AST_REF_TO_TOKENS(c_ast_ref, parser_state):
	toks = []
	if type(c_ast_ref) == c_ast.ID:
		toks += [str(c_ast_ref.name)]
	elif type(c_ast_ref) == c_ast.ArrayRef:
		new_tok = None
		# Only constant array ref right now	
		const = RESOLVE_CONST_ARRAY_REF(c_ast_ref, parser_state)
		if const is None:
			new_tok = c_ast_ref.subscript
		else:
			new_tok = const
		# Name is a ref node
		toks += C_AST_REF_TO_TOKENS(c_ast_ref.name, parser_state)
		toks += [new_tok]
	elif type(c_ast_ref) == c_ast.StructRef:
		# Name is a ref node
		toks += C_AST_REF_TO_TOKENS(c_ast_ref.name, parser_state)
		toks += [str(c_ast_ref.field.name)]
	else:
		print "Uh what node in C_AST_REF_TO_TOKENS?",c_ast_ref
		print 0/0
		sys.exit(0)
		
	# Reverse reverse
	#toks = toks[::-1]
		
	return toks
	
_C_AST_REF_TOKS_TO_C_TYPE_cache = dict()	
def C_AST_REF_TOKS_TO_C_TYPE(ref_toks, c_ast_ref, parser_state):
	
	# Try to get cache
	# Build key
	ref_toks_str = parser_state.existing_logic.func_name[:]
	for ref_tok in ref_toks:
		if type(ref_tok) == int:
			ref_toks_str += "_" + str(ref_tok)
		elif type(ref_tok) == str:
			ref_toks_str += "_" + ref_tok
		elif isinstance(ref_tok, c_ast.Node):
			ref_toks_str += "_" + "VAR"
		else:
			print "What is ref tok bleh?sdsd???", ref_tok
			sys.exit(0)
	# Try for cache
	try:
		return _C_AST_REF_TOKS_TO_C_TYPE_cache[ref_toks_str]
	except:
		pass
	
	
	# Get base variable name
	#print "ref_toks",ref_toks
	var_name = ref_toks[0]
	
	#if var_name == "bs":
	#	print "C_AST_REF_TOKS_TO_C_TYPE ref_toks",ref_toks
	
	# This is the first place we should see a global reference in terms of this function/logic
	parser_state.existing_logic = MAYBE_GLOBAL_VAR_INFO_TO_LOGIC(var_name, parser_state)
		
	# Get the type of this base name
	inst_adj_var_name = var_name
	if parser_state.existing_logic.inst_name is not None:
		inst_adj_var_name = parser_state.existing_logic.inst_name + SUBMODULE_MARKER + var_name
	if var_name in parser_state.existing_logic.wire_to_c_type:
		base_type = parser_state.existing_logic.wire_to_c_type[var_name]
	elif inst_adj_var_name in parser_state.existing_logic.wire_to_c_type:
		base_type = parser_state.existing_logic.wire_to_c_type[inst_adj_var_name]
	else:
		print "parser_state.existing_logic.inst_name",parser_state.existing_logic.inst_name
		print "It looks like variable", var_name, "is not defined?",c_ast_ref.coord
		print "parser_state.existing_logic.wire_to_c_type",parser_state.existing_logic.wire_to_c_type
		print 0/0
		sys.exit(0)
		
	# Is this base type an ID, array or struct ref?
	if len(ref_toks) == 1:
		# Just an ID
		return base_type
	
	#if var_name == "bs":	
	#	print "var_name",var_name
	#	print "base_type",base_type
		
	# Is a struct ref and/or array ref
	remaining_toks = ref_toks[1:]
	
	# While we have a reminaing tok
	current_c_type = base_type
	while len(remaining_toks) > 0:
		#if var_name == "bs":
		#	print "current_c_type",current_c_type
		#	print "remaining_toks",remaining_toks
			
		next_tok = remaining_toks[0]
		if type(next_tok) == int:
			# Constant array ref
			# Sanity check
			if not C_TYPE_IS_ARRAY(current_c_type):
				print "Arrayref tok but not array type?", current_c_type, remaining_toks,c_ast_ref.coord
				sys.exit(0)
			# Go to next tok			
			remaining_toks = remaining_toks[1:]
			# Remove inner subscript to form output type
			current_c_type = GET_ARRAYREF_OUTPUT_TYPE_FROM_C_TYPE(current_c_type)
		elif type(next_tok) == str:
			# Struct
			# Sanity check
			if not C_TYPE_IS_STRUCT(current_c_type, parser_state):
				print "Struct ref tok but not struct type?", remaining_toks,c_ast_ref.coord
				sys.exit(0)
			field_type_dict = parser_state.struct_to_field_type_dict[current_c_type]
			if next_tok not in field_type_dict:
				print next_tok, "is not a member field of",current_c_type, c_ast_ref.coord
				print 0/0
				sys.exit(0)
			# Go to next tok			
			remaining_toks = remaining_toks[1:]
			current_c_type = field_type_dict[next_tok]			
		elif isinstance(next_tok, c_ast.Node):
			# Variable array ref
			# Sanity check
			if not C_TYPE_IS_ARRAY(current_c_type):
				print "Arrayref tok but not array type?2", current_c_type, remaining_toks,c_ast_ref.coord
				sys.exit(0)
			# Go to next tok			
			remaining_toks = remaining_toks[1:]
			# Remove inner subscript to form output type
			current_c_type = GET_ARRAYREF_OUTPUT_TYPE_FROM_C_TYPE(current_c_type)		
		else:
			casthelp(next_tok)
			print "What kind of reference is this?", c_ast_ref.coord
			sys.exit(0)
			
			
	# Write cache	
	_C_AST_REF_TOKS_TO_C_TYPE_cache[ref_toks_str] = current_c_type
			
	return current_c_type
	

def C_AST_ID_TO_LOGIC(c_ast_node, driven_wire_names, prepend_text, parser_state):	
	# Is the ID an ENUM constant?
	is_enum_const = ID_IS_ENUM_CONST(c_ast_node, parser_state.existing_logic, parser_state)
	
	#print c_ast_node
	#print "is_enum_const",is_enum_const
	
	if is_enum_const:
		return C_AST_ENUM_CONST_TO_LOGIC(c_ast_node,driven_wire_names, prepend_text, parser_state)
	else:
		return C_AST_REF_TO_LOGIC(c_ast_node, driven_wire_names, prepend_text, parser_state)

def C_AST_REF_TO_LOGIC(c_ast_ref, driven_wire_names, prepend_text, parser_state):
	if type(c_ast_ref) == c_ast.ArrayRef:
		pass
	elif type(c_ast_ref) == c_ast.StructRef:
		pass
	elif type(c_ast_ref) == c_ast.ID:
		pass
	else:
		print "What type of ref is this?", c_ast_ref
		sys.exit(0)
		
	# Get tokens to identify the reference
	# x.y[5].z.q[i]   is [x,y,5,z,q,<c_ast_node>]
	ref_toks = C_AST_REF_TO_TOKENS(c_ast_ref, parser_state)
	
	return C_AST_REF_TOKS_TO_LOGIC(ref_toks, c_ast_ref, driven_wire_names, prepend_text, parser_state)
	
def C_AST_REF_TOKS_TO_LOGIC(ref_toks, c_ast_ref, driven_wire_names, prepend_text, parser_state):				
	
	# FUCK
	debug = False
	#debug = (len(driven_wire_names)==1) and (driven_wire_names[0]==RETURN_WIRE_NAME) and (ref_toks[0] == "rv") and ("VAR_REF_ASSIGN_uint8_t_uint8_t_8_VAR_a1a4" in parser_state.existing_logic.func_name)
	
		
	# The original variable name is the first tok
	base_var_name = ref_toks[0]
	# What type is this reference?
	c_type = C_AST_REF_TOKS_TO_C_TYPE(ref_toks, c_ast_ref, parser_state)

	# This is the first place we should see a global reference in terms of this function/logic
	parser_state.existing_logic = MAYBE_GLOBAL_VAR_INFO_TO_LOGIC(base_var_name, parser_state)
	
	# Use base var (NOT ORIG WIRE SINCE structs) to look up alias list
	driving_aliases_over_time = []
	# Base variable is only driven if an input, global, volatile global, or in wire driven by
	if ( (base_var_name in parser_state.existing_logic.inputs) or
	     (base_var_name in parser_state.existing_logic.global_wires) or
	     (base_var_name in parser_state.existing_logic.volatile_global_wires) or
	     (base_var_name in parser_state.existing_logic.wire_driven_by) ):
		driving_aliases_over_time += [base_var_name]
	aliases_over_time = []
	if base_var_name in parser_state.existing_logic.wire_aliases_over_time:
		aliases_over_time = parser_state.existing_logic.wire_aliases_over_time[base_var_name]
	driving_aliases_over_time += aliases_over_time
	
	
	#sys.exit(0)
	
	# Does most recent alias cover entire wire?
	# Break orig wire name to all branches
	#print "ref_toks",ref_toks
	all_ref_toks = REF_TOKS_TO_ALL_BRANCH_REF_TOKS(ref_toks, c_ast_ref, parser_state)
	#sys.exit(0)
	
	
	debug = len(driving_aliases_over_time)==0
	
	
	if debug:
		print "=="
		print "inst name",parser_state.existing_logic.inst_name
		print "ref_toks",ref_toks
		print "driving_aliases_over_time",driving_aliases_over_time
		print "all_ref_toks",all_ref_toks

	
	# Find the first alias (IN REVERSE ORDER) that elminates some branches
	remaining_ref_toks = all_ref_toks[:]
	i = len(driving_aliases_over_time)-1
	first_driving_alias = None
	while len(remaining_ref_toks) == len(all_ref_toks):
		if i < 0:
			print "Ran out of aliases?"
			print "inst name",parser_state.existing_logic.inst_name
			print "ref_toks",ref_toks
			print "driving_aliases_over_time",driving_aliases_over_time
			print "all_ref_toks",all_ref_toks
			sys.exit(0)
		
		
		alias = driving_aliases_over_time[i]
		alias_c_type = parser_state.existing_logic.wire_to_c_type[alias]
		remaining_ref_toks = REMOVE_COVERED_REF_TOK_BRANCHES(remaining_ref_toks, alias, c_ast_ref, parser_state)
		# Next alias working backwards
		i = i - 1
	
	# At this point alias is first driver
	first_driving_alias = alias
	first_driving_alias_c_type = alias_c_type
	# If all wires elminated because was exact type match then do simple wire assignment
	first_driving_alias_type_match = first_driving_alias_c_type==c_type	
	

	
	if len(remaining_ref_toks) == 0 and first_driving_alias_type_match:
		'''
		if not first_driving_alias_type_match:
			print "A simple connect with mismatching types?"
			print "c_type",c_type
			print "first_driving_alias_c_type",first_driving_alias_c_type
			print "all_ref_toks",all_ref_toks
			print "first_driving_alias",first_driving_alias
			sys.exit(0)
		'''			
		return GET_SIMPLE_CONNECT_LOGIC(first_driving_alias, driven_wire_names, c_ast_ref, prepend_text, parser_state)		
	else:
		######
		# TODO: Replace 1 input functions (not first alias or type match) with VHDL insert?
		#
		#######
		
		'''
		print "ref_toks",ref_toks
		
		print "c_type",c_type
		print "first_driving_alias_c_type",first_driving_alias_c_type
		print "all_ref_toks",all_ref_toks
		'''
		#print "first_driving_alias",first_driving_alias
		#print "remaining_ref_toks",remaining_ref_toks
		

		# Create list of driving aliases
		driving_aliases = []
		#if len(remaining_wires) < len_pre_drive:
		driving_aliases += [first_driving_alias]
		
		
		#print "remaining_wires after first alias",remaining_wires

		# Work backwards in alias list starting with next wire
		i = len(driving_aliases_over_time)-2
		while len(remaining_ref_toks) > 0:
			alias = driving_aliases_over_time[i]

			# Then remove all branch wires covered by this driver
			len_pre_drive = len(remaining_ref_toks)
			#if c_type == "big_struct_t":
			remaining_ref_toks = REMOVE_COVERED_REF_TOK_BRANCHES(remaining_ref_toks, alias, c_ast_ref, parser_state)
			
			# Record this alias as driver if it drove wires
			if len(remaining_ref_toks) < len_pre_drive:
				driving_aliases += [alias]
			
			# Next alias working backwards
			i = i - 1	
		
		# Reverse order of drivers
		driving_aliases = driving_aliases[::-1]
	
		
		#print "func_inst_name",func_inst_name
		#print "driving_aliases_over_time",driving_aliases_over_time
		#print "first_driving_alias",first_driving_alias
		#print "ref driving aliases",driving_aliases
		
		
		#if func_name == "CONST_REF_RD_big_struct_t_big_struct_t_structs_VAR_a_VAR_VAR":
		#if driving_aliases[0] == "rv" and len(driving_aliases) == 2 and C_AST_REF_TOKS_ARE_CONST(ref_toks):
		'''
		if c_type == "big_struct_t":
			print "driving_aliases",driving_aliases
			print "all_ref_toks",all_ref_toks
			print "driving_aliases_over_time",driving_aliases_over_time
			print "first_driving_alias",first_driving_alias
			print "first_driving_alias_c_type",first_driving_alias_c_type
			print "remaining_ref_toks",remaining_ref_toks
			print "driven_wire_names",driven_wire_names
			print "first_driving_alias_type_match",first_driving_alias_type_match
			print c_ast_ref.coord
			#sys.exit(0)
		'''
		
		# Needs ref read function
		# Name needs ot include the ref being done
		
		# Constant ref ?
			
		prefix = CONST_REF_RD_FUNC_NAME_PREFIX
		if not C_AST_REF_TOKS_ARE_CONST(ref_toks):
			prefix = VAR_REF_RD_FUNC_NAME_PREFIX
				
		
		# NEEDS TO BE LEGIT C FUNC NAME
		func_name = prefix
		# Cant cache all refs?
		# Fuck it just make names that wont be wrong/overlap
		# Are there built in structs?
		# output type
		# Base type
		# output ref toks --dont include base var name
		# input ref toks  --dont include base var name
		# # ?? not needed, included in output ref toks?  variable dims (If not const)		 
		
		# Output type of the ref
		func_name += "_" + c_type
		
		# Base type of the ref
		base_var_type = parser_state.existing_logic.wire_to_c_type[base_var_name]
		base_var_type_c_name = base_var_type.replace("[","_").replace("]","")
		func_name += "_" + base_var_type_c_name
		
		# Output ref toks
		for ref_tok in ref_toks[1:]: # Skip base var name
			if type(ref_tok) == int:
				func_name += "_" + str(ref_tok)
			elif type(ref_tok) == str:
				func_name += "_" + ref_tok
			elif isinstance(ref_tok, c_ast.Node):
				func_name += "_" + "VAR"
			else:
				print "What is ref tok?", ref_tok
				sys.exit(0)
		
		
		# Need to condense c_ast_ref in function name since too big for file name?
		# Bleh? TODO later and solve for bigger reasons?
		# Damnit cant postpone
		# Build list of driven ref toks and reduce
		driven_ref_toks_list = []
		for driving_alias in driving_aliases:
			driven_ref_toks = WIRE_TO_REF_TOKS(driving_alias, parser_state)
			driven_ref_toks_list.append(driven_ref_toks)
		# Reduce
		#print "driven_ref_toks_list",driven_ref_toks_list
		reduced_driven_ref_toks_list = REDUCE_REF_TOKS(driven_ref_toks_list, c_ast_ref , parser_state)
		#print "reduced_driven_ref_toks_list",reduced_driven_ref_toks_list
		
		# Func name built with reduced list
		for driven_ref_toks in reduced_driven_ref_toks_list:
			for ref_tok in driven_ref_toks[1:]: # Skip base var name
				if type(ref_tok) == int:
					func_name += "_" + str(ref_tok)
				elif type(ref_tok) == str:
					func_name += "_" + ref_tok
				elif isinstance(ref_tok, c_ast.Node):
					func_name += "_" + "VAR"
				else:
					print "What is ref tok bleh?", ref_tok
					sys.exit(0)
					
					
		# STILL NEED TO APPEND HASH!
		# BLAGH
		# Ref toks driven by aliases
		input_ref_toks_str = ""
		for driven_ref_toks in driven_ref_toks_list:
			for ref_tok in driven_ref_toks[1:]: # Skip base var name
				if type(ref_tok) == int:
					input_ref_toks_str += "_" + str(ref_tok)
				elif type(ref_tok) == str:
					input_ref_toks_str += "_" + ref_tok
				elif isinstance(ref_tok, c_ast.Node):
					input_ref_toks_str += "_" + "VAR"
				else:
					print "What is ref tok bleh????", ref_tok
					sys.exit(0)
		# Hash the string
		hash_ext = "_" + ((hashlib.md5(input_ref_toks_str).hexdigest())[0:4]) #4 chars enough?
		func_name += hash_ext
		
		
		# VAR DIMS HANDLED IN output ref toks?
		'''
		# Variable dimensions
		var_dim_ref_tok_indices, var_dims, var_dim_iter_types = GET_VAR_REF_REF_TOK_INDICES_DIMS_ITER_TYPES(ref_toks, c_ast_ref, parser_state)
		for var_dim in var_dims:
			# uint width is log2
			width = int(math.ceil(math.log(var_dim,2)))
			var_dim_type = "uint" + str(width) + "_t"
			func_name += "_" + var_dim_type
		'''
		
		
		# Get inst name
		func_inst_name = BUILD_INST_NAME(prepend_text,func_name, c_ast_ref)
		# Save ref toks for this ref submodule
		parser_state.existing_logic.ref_submodule_instance_to_ref_toks[func_inst_name] = ref_toks
		
		
		# Input wire is most recent copy of input ID node 
		c_ast_node_2_driven_input_wire_names = OrderedDict()
			
		# N input port names named by their arg name
		# Decompose inputs to N ARG FUNCTION
		# Dont use input nodes
		use_input_nodes_fuck_it = False
	
		
		# Each of those aliases drives an input port
		# Var ref is implemented in C, then must be C safe (just do same for const ref too , why not)
		ref_toks_i = 0
		parser_state.existing_logic.ref_submodule_instance_to_input_port_driven_ref_toks[func_inst_name] = []
		for driving_alias in driving_aliases:
			#print "driving_alias",driving_alias
			# Build an input port name based off the tokens this alias drives?
			driven_ref_toks = WIRE_TO_REF_TOKS(driving_alias, parser_state)
			
			# dont get input ref toks from input names
			
			# if base variable then call it base
			#if len(driven_ref_toks) == 1:
			#	input_port_name = "base_var"
			input_port_name = "ref_toks_" + str(ref_toks_i)
			ref_toks_i += 1
			input_port_wire = func_inst_name+SUBMODULE_MARKER+input_port_name
			# Remember using driving wire not c ast node  (since doing use_input_nodes_fuck_it = False)
			#print "driving_alias",driving_alias
			#print "drives:"
			#print "input_port_wire",input_port_wire
			c_ast_node_2_driven_input_wire_names[driving_alias] = [input_port_wire]
			
			# SET ref_submodule_instance_to_input_port_driven_ref_toks
			parser_state.existing_logic.ref_submodule_instance_to_input_port_driven_ref_toks[func_inst_name].append(driven_ref_toks)

			
		# Variable dimensions come after
		var_dim_ref_tok_indices, var_dims, var_dim_iter_types = GET_VAR_REF_REF_TOK_INDICES_DIMS_ITER_TYPES(ref_toks, c_ast_ref, parser_state)
		for var_dim_i in range(0, len(var_dims)):
			ref_tok_index = var_dim_ref_tok_indices[var_dim_i]
			ref_tok_c_ast_node = ref_toks[ref_tok_index]
			# Sanity check
			if not isinstance(ref_tok_c_ast_node, c_ast.Node):
				print "Not a variable ref tok?2", ref_tok_c_ast_node
				sys.exit(0)
				
			# Cant use hacky str encode sinc eis just "*"
			# Say which variable index this is
			input_port_name = "var_dim_" + str(var_dim_i)
			input_wire = func_inst_name+SUBMODULE_MARKER+input_port_name
			
			# Set type of input wire
			parser_state.existing_logic.wire_to_c_type[input_wire] = var_dim_iter_types[var_dim_i]
			
			# Make the c_ast node drive the input wire
			input_connect_logic = C_AST_NODE_TO_LOGIC(ref_tok_c_ast_node, [input_wire], prepend_text, parser_state)
			# Merge this connect logic
			parser_state.existing_logic.MERGE_SEQ_LOGIC(input_connect_logic)
			
			# What drives the input port?
			driving_wire = parser_state.existing_logic.wire_driven_by[input_wire]
			
			# Save this
			c_ast_node_2_driven_input_wire_names[driving_wire] = [input_wire]
		
		
		
		# Before evaluating input nodes make sure type of port is there so constants can be evaluated
		# Get type from driving aliases (since doing use_input_nodes_fuck_it = False)
		for driving_alias in c_ast_node_2_driven_input_wire_names:
			input_port_wires = c_ast_node_2_driven_input_wire_names[driving_alias]
			for input_port_wire in input_port_wires:
				if input_port_wire not in parser_state.existing_logic.wire_to_c_type:
					parser_state.existing_logic.wire_to_c_type[input_port_wire] = parser_state.existing_logic.wire_to_c_type[driving_alias]

		
		#print "c_ast_node_2_driven_input_wire_names"
		#for x,y in c_ast_node_2_driven_input_wire_names.iteritems():
		#	print x,y
			
		# Output wire is the type of the struct ref
		output_port_name = RETURN_WIRE_NAME
		# If we know type of output then use that
		if driven_wire_names[0] in parser_state.existing_logic.wire_to_c_type:
			output_c_type = parser_state.existing_logic.wire_to_c_type[driven_wire_names[0]]
		else:
			# Otherwise output wire is the type of the ref rd
			output_c_type = c_type
			# Set type of output wire too
			parser_state.existing_logic.wire_to_c_type[driven_wire_names[0]] = output_c_type
			
		output_wire = func_inst_name+SUBMODULE_MARKER+output_port_name
		parser_state.existing_logic.wire_to_c_type[output_wire] = output_c_type
		

		
		
		# DO THE N ARG FUNCTION
		func_logic = C_AST_N_ARG_FUNC_INST_TO_LOGIC(func_name, c_ast_node_2_driven_input_wire_names, output_wire, driven_wire_names,prepend_text,c_ast_ref,parser_state,use_input_nodes_fuck_it)
		parser_state.existing_logic = func_logic
			
		
		return func_logic
	
def C_ARRAY_TYPE_TO_ELEM_TYPE_AND_DIMS(input_array_type):
	toks = input_array_type.split("[")
	#print toks
	elem_type = toks[0]
	dims = []
	for tok_i in range(1,len(toks)):
		tok = toks[tok_i]
		dim = int(tok.replace("]",""))
		dims.append(dim)
	return elem_type, dims
	
def GET_ARRAYREF_OUTPUT_TYPE_FROM_C_TYPE(input_array_type):
	elem_type, dims = C_ARRAY_TYPE_TO_ELEM_TYPE_AND_DIMS(input_array_type)
	output_dims = dims[1:]
	output_type = elem_type
	for output_dim in output_dims:
		output_type = output_type + "[" + str(output_dim) + "]"
		
	return output_type
		

def GET_SIMPLE_CONNECT_LOGIC(driving_wire, driven_wire_names, c_ast_node, prepend_text, parser_state):
	existing_logic = parser_state.existing_logic
	
	# Connect driving wire to driven wires	
	connect_logic = CONNECT_WIRES_LOGIC(driving_wire, driven_wire_names)
	
	
	# Technically the existing logic is before this SEQ merge
	if not(existing_logic is None):
		first_logic = existing_logic
		second_logic = connect_logic
		first_logic.MERGE_SEQ_LOGIC(second_logic)
		seq_merged_logic = first_logic

		# Look up that type and make sure if the driven wire names have types that they match	
		#print c_ast_id.coord
		if not(driving_wire in seq_merged_logic.wire_to_c_type):
			print "Looks like wire'",driving_wire,"'isn't declared?"
			print C_AST_COORD_STR(c_ast_node.coord)
			sys.exit(0)
		rhs_type = seq_merged_logic.wire_to_c_type[driving_wire]
		
		
		for driven_wire_name in driven_wire_names:
			if driven_wire_name in seq_merged_logic.wire_to_c_type:
				driven_wire_type = seq_merged_logic.wire_to_c_type[driven_wire_name]
				if driven_wire_type != rhs_type:
					
					# Integer promotion / slash supported truncation in C lets this be OK
					if ( ( VHDL.WIRES_ARE_INT_N([driven_wire_name],seq_merged_logic) or VHDL.WIRES_ARE_UINT_N([driven_wire_name],seq_merged_logic))
						and 
						 ( VHDL.C_TYPE_IS_INT_N(rhs_type) or VHDL.C_TYPE_IS_UINT_N(rhs_type) )   ):
							 continue
					# Enum driving UINT is fine
					elif VHDL.WIRES_ARE_UINT_N([driven_wire_name],seq_merged_logic) and WIRE_IS_ENUM(driving_wire, parser_state.existing_logic, parser_state):
						continue
					
					# Otherwise bah!
					#print "VHDL.WIRES_ARE_UINT_N([driven_wire_name],seq_merged_logic)",VHDL.WIRES_ARE_UINT_N([driven_wire_name],seq_merged_logic)
					#print "WIRE_IS_ENUM(driving_wire, parser_state.existing_logic, parser_state)",WIRE_IS_ENUM(driving_wire, parser_state.existing_logic, parser_state)
					print "RHS",driving_wire,"drives",driven_wire_name,"with different types?"
					print driven_wire_type, rhs_type
					sys.exit(0)
			else:
				# Driven wire type isnt set, set it
				seq_merged_logic.wire_to_c_type[driven_wire_name] = rhs_type
		
				
		#print "seq_merged_logic.wire_drives", seq_merged_logic.wire_drives 
		#print "seq_merged_logic.wire_driven_by", seq_merged_logic.wire_driven_by 
				
		# Update parser state since merged in exsiting logic earlier
		parser_state.existing_logic = seq_merged_logic
				
		return seq_merged_logic
	else:
		# No existing logic just return connect logic
		return connect_logic	


	
def WIRE_IS_ENUM(maybe_not_enum_wire, existing_logic, parser_state):	
	# Will not be:
	#	(this is dumb)
	#   known to enum
	#	input
	#	global
	#   volatile global
	#	variable
	# 	output
	#
	# Then must be ENUM
	if (maybe_not_enum_wire in existing_logic.wire_to_c_type) and (existing_logic.wire_to_c_type[maybe_not_enum_wire] in parser_state.enum_to_ids_dict):
		return True
	elif ORIG_WIRE_NAME_TO_ORIG_VAR_NAME(maybe_not_enum_wire) in existing_logic.inputs:
		return False
	elif (maybe_not_enum_wire in existing_logic.global_wires) or (ORIG_WIRE_NAME_TO_ORIG_VAR_NAME(maybe_not_enum_wire) in parser_state.global_info):
		return False
	elif (maybe_not_enum_wire in existing_logic.volatile_global_wires) or (ORIG_WIRE_NAME_TO_ORIG_VAR_NAME(maybe_not_enum_wire) in parser_state.volatile_global_info):
		return False
	elif ORIG_WIRE_NAME_TO_ORIG_VAR_NAME(maybe_not_enum_wire) in existing_logic.variable_names:
		return False
	elif ORIG_WIRE_NAME_TO_ORIG_VAR_NAME(maybe_not_enum_wire) in existing_logic.outputs:
		return False
	else:
		#print "ENUM:",maybe_not_enum_wire
		return True
		
def ID_IS_ENUM_CONST(c_ast_id, existing_logic, parser_state):	
	
	# Get ref tokens
	ref_toks = C_AST_REF_TO_TOKENS(c_ast_id,parser_state)
	if len(ref_toks) > 1:
		return False
		
	base_name = ref_toks[0]
		
	# Will not be:
	#	(this is dumb)
	#   known to enum const
	#	input
	#	global
	#   volatile global
	#	variable
	# 	output
	#
	# Then must be ENUM
	inst_name = ""
	if existing_logic.inst_name is not None:
		inst_name = existing_logic.inst_name
	
	
	if (base_name in existing_logic.wire_to_c_type) and (existing_logic.wire_to_c_type[base_name] in parser_state.enum_to_ids_dict) and WIRE_IS_CONSTANT(base_name, inst_name):
		return True
	elif base_name in existing_logic.inputs:
		return False
	elif (base_name in existing_logic.global_wires) or (base_name in parser_state.global_info):
		return False
	elif (base_name in existing_logic.volatile_global_wires) or (base_name in parser_state.volatile_global_info):
		return False
	elif base_name in existing_logic.variable_names:
		return False
	elif base_name in existing_logic.outputs:
		return False
	else:
		# Check that is one of the enum consts available at least :(
		for enum_type in parser_state.enum_to_ids_dict:
			ids = parser_state.enum_to_ids_dict[enum_type]
			for id_str in ids:
				if id_str == base_name:
					return True
		return False
	
# ENUM is like constant
def C_AST_ENUM_CONST_TO_LOGIC(c_ast_node,driven_wire_names,prepend_text, parser_state):
	existing_logic = parser_state.existing_logic
	
	# Create wire for this constant
	#wire_name = prepend_text+"CONST_" + str(c_ast_node.type)+ "_"+ str(c_ast_node.value) + "_" + C_AST_COORD_STR(c_ast_node.coord)
	#wire_name =  CONST_PREFIX + str(c_ast_node.type)+ "_"+ str(c_ast_node.value)
	value = str(c_ast_node.name)
	#casthelp(c_ast_node)
	#print "value",value
	#print "==="
	# Hacky use $ for enum only oh sad
	wire_name =  CONST_PREFIX + str(value) + "$" + C_AST_COORD_STR(c_ast_node.coord)
	rv = CONNECT_WIRES_LOGIC(wire_name, driven_wire_names)
	
	rv.MERGE_COMB_LOGIC(existing_logic)
	

	### FUCK CAN'T DO ENUM TYPE CHECKING SINCE OPERATORS IMPLEMENTED AS unsigned compare (not num type compare, for pipelining...)
	# Hey yeah this sucks
	'''
	# Use type of driven wire if available
	c_type_str = None
	for driven_wire_name in driven_wire_names:
		if driven_wire_name in existing_logic.wire_to_c_type:
			print "driven_wire_name",driven_wire_name
			type_str = existing_logic.wire_to_c_type[driven_wire_name]
			if not(c_type_str is None):
				if type_str != c_type_str:
					print "Constant driving a wire with multiple types!?"
					sys.exit(0)
			c_type_str = type_str
	if not(c_type_str is None):
		# Check that this enum const exists for this type
		ids = parser_state.enum_to_ids_dict[c_type_str]
		if not(value in ids):
			print "Enum:",value, "is not part of the enum type:", c_type_str,C_AST_COORD_STR(c_ast_node.coord)
			sys.exit(0)	
	'''
	
	parser_state.existing_logic = rv
		 
	return rv
	
def GET_MAYBE_DIGIT_FROM_CONST_WIRE(wire_name, Logic, parser_state):
	inst_name = ""
	if Logic.inst_name is not None:
		inst_name = Logic.inst_name
	local_name = wire_name.replace(inst_name+SUBMODULE_MARKER,"")
	
	# Ge tlast submodule tok
	toks = local_name.split(SUBMODULE_MARKER)
	last_tok = toks[len(toks)-1]
	local_name = last_tok	
	
	# What type of const
	# Strip off CONST_
	stripped_wire_name = local_name
	if local_name.startswith(CONST_PREFIX):
		stripped_wire_name = local_name[len(CONST_PREFIX):]
	#print "stripped_wire_name",stripped_wire_name
	# Split on under
	toks = stripped_wire_name.split("_")
	
	ami_digit = toks[0]

	return ami_digit

# Const jsut makes wire with CONST name
def C_AST_CONSTANT_TO_LOGIC(c_ast_node,driven_wire_names, prepend_text, parser_state, is_negated=False):
	existing_logic = parser_state.existing_logic
	
	# Since constants are constants... dont add prepend text or line location info
	# Create wire for this constant
	#wire_name = prepend_text+"CONST_" + str(c_ast_node.type)+ "_"+ str(c_ast_node.value) + "_" + C_AST_COORD_STR(c_ast_node.coord)
	#wire_name =  CONST_PREFIX + str(c_ast_node.type)+ "_"+ str(c_ast_node.value)
	value = int(c_ast_node.value)
	if is_negated:
		value = value * -1
	#casthelp(c_ast_node)
	#print "value",value
	#print "==="
	wire_name =  CONST_PREFIX + str(value) + "_" + C_AST_COORD_STR(c_ast_node.coord)
	rv = CONNECT_WIRES_LOGIC(wire_name, driven_wire_names)
	
	rv.MERGE_COMB_LOGIC(existing_logic)
	
	# Use type of driven wire if available
	c_type_str = None
	for driven_wire_name in driven_wire_names:
		if driven_wire_name in existing_logic.wire_to_c_type:
			type_str = existing_logic.wire_to_c_type[driven_wire_name]
			if not(c_type_str is None):
				if type_str != c_type_str:
					print "Constant with multiple types!?"
					sys.exit(0)
			c_type_str = type_str
	if not(c_type_str is None):
		rv.wire_to_c_type[wire_name]=c_type_str		
		
	parser_state.existing_logic = rv
		 
	return rv
	
def C_AST_ARRAYDECL_TO_LOGIC(c_ast_array_decl, prepend_text, parser_state):
	existing_logic = parser_state.existing_logic
	# All we need is wire name right now
	rv = Logic()
	if not(existing_logic is None):
		rv = existing_logic
	
	#c_ast_array_decl.show()
	name, elem_type, dim = C_AST_ARRAYDECL_TO_NAME_ELEM_TYPE_DIM(c_ast_array_decl)
	#print "elem_type",elem_type
	#print "dim",dim
	
	#casthelp(c_ast_array_decl.type.declname)
	#print c_ast_array_decl.type.declname.children()
	
	
	wire_name = name
	#print "DECL", wire_name
	
	#sys.exit(0)
	#casthelp(c_ast_decl)
	#casthelp(c_ast_decl.init)
	#sys.exit(0)
	rv.wires.append(wire_name)
	rv.wire_to_c_type[wire_name] = elem_type + "[" + str(dim) + "]"
	## Orig wire var here too
	
	# This is a variable declaration
	rv.variable_names.append(wire_name)
	
	# If has init value then is also assignment
	#if not(c_ast_array_decl.init is None):
	#	print "No array declarations with intialziations yet..."
	#	casthelp(c_ast_array_decl)
	#	sys.exit(0)
		
	# Update parser state since merged in existing logic earlier
	parser_state.existing_logic = rv
	
	return rv

def C_AST_DECL_TO_LOGIC(c_ast_decl, prepend_text, parser_state):
	if type(c_ast_decl.type) == c_ast.ArrayDecl:
		return C_AST_ARRAYDECL_TO_LOGIC(c_ast_decl.type, prepend_text, parser_state)
	elif type(c_ast_decl.type) == c_ast.TypeDecl:
		return C_AST_TYPEDECL_TO_LOGIC(c_ast_decl.type, prepend_text, parser_state, c_ast_decl)
	else:
		print "C_AST_DECL_TO_LOGIC",c_ast_decl.type
		sys.exit(0)
	
def C_AST_TYPEDECL_TO_LOGIC(c_ast_typedecl, prepend_text, parser_state, parent_c_ast_decl):
	existing_logic = parser_state.existing_logic
	# Only encountered as variable decl right now
	# All we need is wire name right now
	rv = Logic()
	if not(existing_logic is None):
		rv = existing_logic
	
	# Dont use prepend text for decl since cant decl twice?
	# TODO check this if it does work and I forget about it
	#prepend_text+
	wire_name = parent_c_ast_decl.name
	#print "DECL", wire_name
	#casthelp(parent_c_ast_decl)
	#casthelp(parent_c_ast_decl.init)
	#sys.exit(0)
	c_type = c_ast_typedecl.type.names[0]
	#print "c_type",c_type
	#sys.exit(0)
	rv.wires.append(wire_name)
	rv.wire_to_c_type[wire_name] = c_type
	# Orig wire var here too
	
	# This is a variable declaration
	rv.variable_names.append(wire_name)
	
	# If has init value then is also assignment
	if not(parent_c_ast_decl.init is None):
		print "No variable declarations with intialziations yet..."
		casthelp(parent_c_ast_decl)
		sys.exit(0)
		
	# Update parser state since merged in exsiting logic earlier
	parser_state.existing_logic = rv
	
	return rv

	
def C_AST_COMPOUND_TO_LOGIC(c_ast_compound, prepend_text, parser_state):
	existing_logic = parser_state.existing_logic
	
	# How to handle assignment over time?
	# Use function that merges logic over time
	# MERGE_SEQUENTIAL_LOGIC
	# TODO: Do this every place merge logic is used? probabhly not
	# Assumption: Compound logic block items imply execution order
	rv = Logic()
	if existing_logic is not None:
		rv = existing_logic
		
	if not(c_ast_compound.block_items is None):
		for block_item in c_ast_compound.block_items:
			#print "block_item in c_ast_compound.block_items"
			#casthelp(block_item)
			#print '"leading_zeros" in rv.wire_to_c_type', ("leading_zeros" in rv.wire_to_c_type)
			#print "block_item",block_item
			parser_state.existing_logic = rv
			driven_wire_names=[]
			item_logic = C_AST_NODE_TO_LOGIC(block_item, driven_wire_names, prepend_text, parser_state)
			prev_logic = rv
			next_logic = item_logic
			
			#print "MERGING block item sequentially"
			#print "PRE SEQ MERGE rv.wire_drives", rv.wire_drives 
			#print "PRE SEQ MERGE rv.wire_driven_by", rv.wire_driven_by 
			
			prev_logic.MERGE_SEQ_LOGIC(next_logic)
			rv = prev_logic
			
			# Update parser state since merged in exsiting logic
			parser_state.existing_logic = rv
			
			#print str(block_item)
			#print "rv.wire_drives", rv.wire_drives 
			#print "rv.wire_driven_by", rv.wire_driven_by 
			
		
			
	return rv
	
#_C_AST_COORD_STR_cache = dict()
#print "Keep _C_AST_COORD_STR_cache?"
def C_AST_COORD_STR(c_ast_node_cord):
	'''
	global _C_AST_COORD_STR_cache
	try:
		return _C_AST_COORD_STR_cache[str(c_ast_node_cord)]
	except:
		pass
	'''
	
	file_coord_str = str(c_ast_node_cord.file) + "_l" + str(c_ast_node_cord.line) + "_c" + str(c_ast_node_cord.column)
	# Get leaf name (just stem file name of file hierarcy)
	file_coord_str = LEAF_NAME(file_coord_str)
	#file_coord_str = file_coord_str.replace(".","_").replace(":","_")
	#file_coord_str = file_coord_str.replace(":","_")
	# Lose readability for sake of having DOTs mean struct ref in wire names
	file_coord_str = file_coord_str.replace(".","_")
	
	
	'''
	_C_AST_COORD_STR_cache[str(c_ast_node_cord)] = file_coord_str
	'''
	
	return file_coord_str



def GET_FOR_LOOP_VAR_AND_INIT_VAL(c_ast_for_init, parser_state):
	# Only support simple assignment right now
	if type(c_ast_for_init) == c_ast.Assignment:
		# Left node must be id
		# Right node must be constant
		if (type(c_ast_for_init.lvalue) == c_ast.ID) and (type(c_ast_for_init.rvalue) == c_ast.Constant):
			# Left node must is assumed to be loop variable
			loop_var = str(c_ast_for_init.lvalue.name)
			# Right node is assumed to be value
			init_val = int(c_ast_for_init.rvalue.value)			
		else:
			return None
	else:
		return None
	
	return loop_var, init_val

def EVAL_FOR_NEXT(i_value, loop_var, c_ast_for_next, parser_state):	
	if type(c_ast_for_next) == c_ast.Assignment:
		if str(c_ast_for_next.op) == "=":
			#print "here1"
			# Left must be loop var
			# Right must be binary op
			if (c_ast_for_next.lvalue.name == loop_var) and (type(c_ast_for_next.rvalue) == c_ast.BinaryOp):
				#print "here2"
				# bin op  must be add or sub
				op_str = str(c_ast_for_next.rvalue.op)
				if op_str == "+" or op_str == "-":
					#print "here3"
					# One of the sides of the bin op must be loop var, the other constant
					if (type(c_ast_for_next.rvalue.right) == c_ast.ID) and (type(c_ast_for_next.rvalue.left) == c_ast.Constant):
						# Left is constant
						value = int(c_ast_for_next.rvalue.left.value)
					elif (type(c_ast_for_next.rvalue.right) == c_ast.Constant) and (type(c_ast_for_next.rvalue.left) == c_ast.ID):	
						# Right is constant
						value = int(c_ast_for_next.rvalue.right.value)
					else:
						return None
					
					# DO op
					if op_str == "+":
						return i_value + value
					elif op_str == "-":
						return i_value - value
			

	return None

	
	
def EVAL_FOR_COND(i_value, loop_var, c_ast_for_cond, parser_state):
	if type(c_ast_for_cond) == c_ast.BinaryOp:
		#print "here2"
		# bin op  must be add or sub
		op_str = str(c_ast_for_cond.op)
		if op_str == "<" or op_str == "<=" or op_str == ">" or op_str == ">=":
			#print "here3"
			# One of the sides of the bin op must be loop var, the other constant
			if (type(c_ast_for_cond.right) == c_ast.ID) and (type(c_ast_for_cond.left) == c_ast.Constant):
				# Left is constant
				value = int(c_ast_for_cond.left.value)
			elif (type(c_ast_for_cond.right) == c_ast.Constant) and (type(c_ast_for_cond.left) == c_ast.ID):	
				# Right is constant
				value = int(c_ast_for_cond.right.value)
			else:
				return None
			
			# DO op
			if op_str == "<":
				return i_value < value
			elif op_str == "<=":
				return i_value <= value
			elif op_str == ">":
				return i_value > value
			elif op_str == ">=":
				return i_value >= value

	return None

def GET_FOR_LOOP_VAR_AND_RANGE(c_ast_for, parser_state):
	# Use the init, cond, next  to figure out
	# 	Loop variable
	#   Constant range
	#print "TODO: GET_FOR_LOOP_VAR_AND_RANGE"
	
	# Init gives loop var and starting value
	loop_var_AND_init_value = GET_FOR_LOOP_VAR_AND_INIT_VAL(c_ast_for.init, parser_state)
	if loop_var_AND_init_value is None:
		print "I dont know how to handle what you are doing in the for loop initializer at", c_ast_for.init.coord
		sys.exit(0)
	loop_var, init_value = loop_var_AND_init_value
	
	# Only simple cond and next handled
	
	# OK lets do this the weird way
	val_range = [init_value]
	i_value = init_value
	while True:
		# Do 
		# {
		
		# Next
		next_i_value = EVAL_FOR_NEXT(i_value, loop_var, c_ast_for.next, parser_state)
		if next_i_value is None:
			print "I dont know how to handle what you are doing in the for loop next statement at", c_ast_for.next.coord
			sys.exit(0)
		# Cond
		cond_eval = EVAL_FOR_COND(next_i_value, loop_var, c_ast_for.cond, parser_state) 
		if cond_eval is None:
			print "I dont know how to handle what you are doing in the for loop condition at", c_ast_for.cond.coord
			sys.exit(0)
		if cond_eval:
			val_range.append(next_i_value)
		i_value = next_i_value

		# }
		# While (         )
		if not  (cond_eval):
			break

	return loop_var, val_range
	
def C_AST_FOR_TO_LOGIC(c_ast_node,driven_wire_names,prepend_text, parser_state):
	existing_logic = parser_state.existing_logic
	rv = existing_logic
	
	# Do init first
	#init_logic = C_AST_NODE_TO_LOGIC(c_ast_node.init, [], prepend_text, parser_state)
	#rv = rv.MERGE_SEQ_LOGIC(init_logic)
	
	# Not actually evaluating the "variable" part of the loop
	# We are unrolling it
	
	# Use the init, cond, next  to figure out
	# 	Loop variable
	#   Constant range
	loop_var, loop_range = GET_FOR_LOOP_VAR_AND_RANGE(c_ast_node, parser_state)
	
	# Do the 'statement' N times
	# Actually involves doing
	#   loop var = i
	#   'statement'
	for i in loop_range:
		# Set loop var equal to i
		# Like an assignment
		loop_prepend_text = prepend_text + "FOR_" + loop_var + "_" + str(i).replace("-","neg") + "_"
		iter_assign_logic = FAKE_ASSIGNMENT_TO_LOGIC(loop_var, i, c_ast_node, driven_wire_names, loop_prepend_text, parser_state)
		rv.MERGE_SEQ_LOGIC(iter_assign_logic)
		# Do the statement
		statement_logic = C_AST_NODE_TO_LOGIC(c_ast_node.stmt, [], loop_prepend_text, parser_state)
		rv.MERGE_SEQ_LOGIC(statement_logic)
		
	
	# Done?
	parser_state.existing_logic = rv
	return rv
	
def C_AST_IF_REF_TOKS_TO_STR(ref_toks, c_ast_ref):
	rv = ""
	# For now only deal with constant
	for i in range(0,len(ref_toks)):
		ref_tok = ref_toks[i]
		if type(ref_tok) == int:
			# Array ref
			rv += "_" + str(ref_tok)
		elif type(ref_tok) == str:
			if i == 0:
				# Base var
				rv += ref_tok
			else:
				# Struct ref
				rv += "_" + ref_tok
		elif isinstance(ref_tok, c_ast.Node):
			rv += "_" + "VAR"
		else:
			print "What kind of ref is this?", ref_toks, c_ast_ref.coord
			sys.exit(0)
	return rv


def C_AST_IF_TO_LOGIC(c_ast_node,prepend_text, parser_state):
	existing_logic = parser_state.existing_logic
	func_name_2_logic = parser_state.FuncName2Logic
	
	# Each if is just an IF ELSE (no explicit logic for "else if")
	# If logic is MUX with SEL, TRUE, and FALSE logic connected
	rv = existing_logic
		
	# One submodule MUX instance per variable contains in the if at this location
	# Name comes from location in file
	file_coord_str = C_AST_COORD_STR(c_ast_node.coord)
		
	# Helpful check for now
	#if len(c_ast_node.children()) < 3:
	#	print "All ifs must have else statements for now."
	#	sys.exit(0)
	
	# Port names from c_ast
	
	
	
	# Mux select is driven by intermediate shared wire without variable name
	mux_cond_port_name = c_ast_node.children()[0][0]
	mux_intermediate_cond_wire_wo_var_name = prepend_text + MUX_LOGIC_NAME + "_" + file_coord_str + "_interm_" + mux_cond_port_name
	rv.wires.append(mux_intermediate_cond_wire_wo_var_name)
	rv.wire_to_c_type[mux_intermediate_cond_wire_wo_var_name] = BOOL_C_TYPE		
	# Get logic for this if condition with it driving the shared condition wire
	parser_state.existing_logic = rv
	cond_logic = C_AST_NODE_TO_LOGIC(c_ast_node.cond, [mux_intermediate_cond_wire_wo_var_name], prepend_text, parser_state)
	first = rv
	second = cond_logic
	first.MERGE_SEQ_LOGIC(second)
	rv = first
	parser_state.existing_logic = rv
	
	
	# Get true/false logic
	# Add prepend text to seperate the two branches into paralel combinational logic
	# Rename each driven wire with inst name and _true or _false
	prepend_text_true = ""#prepend_text+MUX_LOGIC_NAME+"_"+file_coord_str+"_true"+"/"   # Line numbers should be enough?
	prepend_text_false = ""#prepend_text+MUX_LOGIC_NAME+"_"+file_coord_str+"_false"+"/" # Line numbers should be enough?
	driven_wire_names=[] 
	#
	parser_state_for_true = copy.copy(parser_state) # copy.deepcopy(parser_state) 
	parser_state_for_true.existing_logic = rv.DEEPCOPY() #copy.deepcopy(rv); #rv
	mux_true_port_name = c_ast_node.children()[1][0]
	true_logic = C_AST_NODE_TO_LOGIC(c_ast_node.iftrue, driven_wire_names, prepend_text_true, parser_state_for_true)
	#
	if len(c_ast_node.children()) >= 3:
		# Do false branch
		parser_state_for_false = copy.copy(parser_state) # copy.deepcopy(parser_state)
		parser_state_for_false.existing_logic = rv.DEEPCOPY() #copy.deepcopy(rv); #rv
		mux_false_port_name = c_ast_node.children()[2][0]
		false_logic = C_AST_NODE_TO_LOGIC(c_ast_node.iffalse, driven_wire_names, prepend_text_false, parser_state_for_false)
	else:
		# No false branch false logic if identical to existing logic
		false_logic = parser_state.existing_logic.DEEPCOPY() #copy.deepcopy(parser_state.existing_logic) 
		mux_false_port_name = "iffalse" # Will this work?
	
	# Var names cant be mixed type per C spec
	merge_var_names = LIST_UNION(true_logic.variable_names,false_logic.variable_names)
		
	# Find out which ref toks rv, p.x, p.y etc are driven inside this IF
	# Driving is recorded with aliases over time
	# True and false can share some existing drivings we dont want to consider
	# Loop over each variable
	var_name_2_all_ref_toks_list = dict()
	#print "==== IF",file_coord_str,"======="
	for var_name in merge_var_names:		
		# vars declared inside and IF cannot be used outside that if so cannot/should not have MUX inputs+outputs
		declared_in_this_if = not(var_name in existing_logic.variable_names) and (var_name not in parser_state.global_info) and (var_name not in parser_state.volatile_global_info)
		if declared_in_this_if:
			#print var_name, "declared_in_this_if"
			continue
		
		# Get aliases over time
		# original
		original_aliases= []
		if var_name in existing_logic.wire_aliases_over_time:
			original_aliases = existing_logic.wire_aliases_over_time[var_name]
		# true
		true_aliases = []
		if var_name in true_logic.wire_aliases_over_time:
			true_aliases = true_logic.wire_aliases_over_time[var_name]
		# false
		false_aliases = []
		if var_name in  false_logic.wire_aliases_over_time:
			false_aliases = false_logic.wire_aliases_over_time[var_name]
		# Max len
		max_aliases_len = max(len(true_aliases),len(false_aliases))
	
		#print var_name, "original_aliases:", original_aliases
		#print var_name, "true_aliases",true_aliases
		#print var_name, "false_aliases",false_aliases
	
		# Find where the differences start in the wire aliases over time
		diff_start_i = None
		for i in range(0, max_aliases_len):
			# If no element here then difference starts here
			if (i > len(true_aliases)-1) or (i > len(false_aliases)-1):
				diff_start_i = i
				break
			
			# Both have elements, same?
			if true_aliases[i] != false_aliases[i]:
				diff_start_i = i
				break
				
		# If no difference then this var was not driven inside this IF
		if diff_start_i is None:
			#print var_name, "NO DIFFERENT ALIASES = NOT DRIVEN" 
			continue
		
		# Collect all the ref toks from aliases - whatever order
		all_ref_toks_list = []
		for i in range(diff_start_i, max_aliases_len):
			if (i < len(true_aliases)):
				true_ref_toks = true_logic.alias_to_ref_toks[true_aliases[i]]
				if true_ref_toks not in all_ref_toks_list:
					all_ref_toks_list.append(true_ref_toks)
			if (i < len(false_aliases)):
				false_ref_toks = false_logic.alias_to_ref_toks[false_aliases[i]]
				if false_ref_toks not in all_ref_toks_list:
					all_ref_toks_list.append(false_ref_toks)
		
		# Collpase hierarchy to get top most orig wire name nodes	
		#print var_name, "all_ref_toks_list",all_ref_toks_list
		all_ref_toks_list = REDUCE_REF_TOKS(all_ref_toks_list, c_ast_node, parser_state)
		#print var_name, "reduced all_ref_toks_list",all_ref_toks_list
		#sys.exit(0)
		# Ok now have collpased list of ref toks that needed MUXes for this IF
		# Save this for later too
		var_name_2_all_ref_toks_list[var_name] = all_ref_toks_list[:]
		
	

		# Now do MUX inst logic		
		for ref_toks in all_ref_toks_list:
			##### SHARE COND WIRE DRIVEN drives SUBMODULE INST COND PORT
			##### NOT TRUE FALSE SPECIFIC  ######
			# indivudal mux submodule per orig wire
			ref_tok_id_str = C_AST_IF_REF_TOKS_TO_STR(ref_toks, c_ast_node)
			mux_inst_name = prepend_text+MUX_LOGIC_NAME+"_"+ref_tok_id_str+"_"+file_coord_str
			# Instance per variable cond port is driven by intermediate wire with var name	
			mux_inst_cond_wire = mux_inst_name + SUBMODULE_MARKER + mux_cond_port_name
			connect_logic = CONNECT_WIRES_LOGIC(mux_intermediate_cond_wire_wo_var_name,[mux_inst_cond_wire])
			connect_logic.wire_to_c_type[mux_inst_cond_wire] = BOOL_C_TYPE
			# Set submodule instance
			# TODO: USE N ARG FUNC INST
			connect_logic.submodule_instances[mux_inst_name]=MUX_LOGIC_NAME
			connect_logic.submodule_instance_to_c_ast_node[mux_inst_name]=c_ast_node
			connect_logic.submodule_instance_to_input_port_names[mux_inst_name]=[mux_cond_port_name,mux_true_port_name,mux_false_port_name]
			# Apply to both branches here?
			true_logic.MERGE_COMB_LOGIC(connect_logic)
			false_logic.MERGE_COMB_LOGIC(connect_logic)
			
			# Connect true and false wires using id_or_structref read logic
			mux_true_connection_wire_name = mux_inst_name + SUBMODULE_MARKER + mux_true_port_name
			mux_false_connection_wire_name = mux_inst_name + SUBMODULE_MARKER + mux_false_port_name
			
			# Type of true and false ports are the same
			c_type = C_AST_REF_TOKS_TO_C_TYPE(ref_toks, c_ast_node, parser_state)
		
			# Add C type for input ports based on connecting wire
			true_logic.wire_to_c_type[mux_true_connection_wire_name]=c_type
			false_logic.wire_to_c_type[mux_false_connection_wire_name]=c_type

			# Using each branches logic use id_or_structref logic to form read wire driving T/F ports
			# TRUE
			parser_state_for_true = copy.copy(parser_state) # copy.deepcopy(parser_state)
			parser_state_for_true.existing_logic = true_logic
			true_read_logic = C_AST_REF_TOKS_TO_LOGIC(ref_toks, c_ast_node, [mux_true_connection_wire_name], "TRUE_INPUT_"+MUX_LOGIC_NAME+"_"+ref_tok_id_str+"_", parser_state_for_true)
			# Merge in read
			true_logic.MERGE_COMB_LOGIC(true_read_logic)
			
			# FALSE
			parser_state_for_false = copy.copy(parser_state) # copy.deepcopy(parser_state)
			parser_state_for_false.existing_logic = false_logic
			false_read_logic = C_AST_REF_TOKS_TO_LOGIC(ref_toks, c_ast_node, [mux_false_connection_wire_name], "FALSE_INPUT_"+MUX_LOGIC_NAME+"_"+ref_tok_id_str+"_", parser_state_for_false)
			# Merge in read
			false_logic.MERGE_COMB_LOGIC(false_read_logic)
			
			# Cant handle outputs here since outputs are added as last alias
			# But can add alias to single list yet since havent merged true and false
			# So merge TF first
			
	
	
	# Merge T/F branches
	# Wire aliases over time from the true and false branches CANT be merged  
	# since selection of final alias from either true or false branch is what THIS MUX DOES
	# Loop over and remove branch-only aliases over time
	# RV contains logic before T/F logic so orig aliases
	new_true_false_logic_wire_aliases_over_time = dict()
	for orig_var in merge_var_names:		
		# Filtered aliases contains orig from RV logic
		filtered_aliases = []
		original_aliases = []
		if orig_var in rv.wire_aliases_over_time:
			original_aliases = rv.wire_aliases_over_time[orig_var]
		filtered_aliases += original_aliases
			
		# Remove aliases not in original
		if orig_var in true_logic.wire_aliases_over_time:
			for alias in true_logic.wire_aliases_over_time[orig_var]:
				if alias in original_aliases:
					# Is in orig, keep if not in list already
					if not(alias in filtered_aliases):
						filtered_aliases.append(alias)
				
		if orig_var in false_logic.wire_aliases_over_time:
			for alias in false_logic.wire_aliases_over_time[orig_var]:
				if alias in original_aliases:
					# Is in orig, keep if not in list already
					if not(alias in filtered_aliases):
						filtered_aliases.append(alias)
			
		if len(filtered_aliases) > 0:
			new_true_false_logic_wire_aliases_over_time[orig_var] = filtered_aliases
						
	# Shared comb mergeable wire aliases over time
	true_logic.wire_aliases_over_time = new_true_false_logic_wire_aliases_over_time
	false_logic.wire_aliases_over_time = new_true_false_logic_wire_aliases_over_time
	# Merge the true and false logic as parallel COMB logic since aliases over time fixed above
	true_logic.MERGE_COMB_LOGIC(false_logic)
	true_false_merged = true_logic
	

	# After TF merge we can have correct alias list include the mux output
	# Alias list for struct variable may be appended to multiple times
	# But since by def those drivings dont overlap then order doesnt really matter
	for variable in merge_var_names:
		# vars declared inside and IF cannot be used outside that if so cannot/should not have MUX inputs+outputs
		declared_in_this_if = not(variable in existing_logic.variable_names) and (variable not in parser_state.global_info) and (variable not in parser_state.volatile_global_info)
		if declared_in_this_if:
			continue
			
		# If not driven then skip
		if variable not in var_name_2_all_ref_toks_list:
			continue
		# Otherwise get drive orig wire names (already collapsed)
		all_if_ref_toks_list = var_name_2_all_ref_toks_list[variable]
		
		# Add mux output as alias for this var
		aliases = []
		if variable in true_false_merged.wire_aliases_over_time:
			aliases = true_false_merged.wire_aliases_over_time[variable]
			# Remove and re add after
			true_false_merged.wire_aliases_over_time.pop(variable)
		
		# Ok to add to same list multiple times for each orig_wire
		for ref_toks in all_if_ref_toks_list:
			ref_tok_id_str = C_AST_IF_REF_TOKS_TO_STR(ref_toks, c_ast_node)
			mux_inst_name = prepend_text+MUX_LOGIC_NAME+"_"+ref_tok_id_str+"_"+file_coord_str
			mux_connection_wire_name = mux_inst_name + SUBMODULE_MARKER + RETURN_WIRE_NAME
			true_false_merged.alias_to_orig_var_name[mux_connection_wire_name] = variable
			true_false_merged.alias_to_ref_toks[mux_connection_wire_name] = ref_toks
			# set the C type for output connection based on orig var name
			c_type = C_AST_REF_TOKS_TO_C_TYPE(ref_toks, c_ast_node, parser_state)
			true_false_merged.wire_to_c_type[mux_connection_wire_name] = c_type
			# Mux output just adds an alias over time to the original variable
			# So that the next read of the variable uses the mux output
			if not(mux_connection_wire_name in aliases):
				aliases.append(mux_connection_wire_name)
		
		# Re add if not empty list
		if len(aliases) > 0:
			true_false_merged.wire_aliases_over_time[variable] = aliases

	
	# Update parser state since merged in exsiting logic earlier
	parser_state.existing_logic = true_false_merged
	
	return true_false_merged
	

	
def LEAF_NAME(name, do_submodule_split=False):
	new_name = name
	
	# Pick last submodule item 
	if (SUBMODULE_MARKER in name) and do_submodule_split:
		toks = new_name.split(SUBMODULE_MARKER)
		toks.reverse()
		new_name = toks[0]	
	
	# And last leaf item
	if "/" in new_name:
		toks = new_name.split("/")
		toks.reverse()
		new_name = toks[0]
		
	return new_name

# Function instance is module connection
# Connect certain input nodes to certain lists of wire names
# dict[c_ast_node] => [list of driven wire names]
def SEQ_C_AST_NODES_TO_LOGIC(c_ast_node_2_driven_wire_names, prepend_text, parser_state):
	rv = parser_state.existing_logic
	

	# Get logic for each connection and merge
	for c_ast_node in c_ast_node_2_driven_wire_names:
		driven_wire_names = c_ast_node_2_driven_wire_names[c_ast_node]
		#rv.wires = rv.wires + driven_wire_names
		parser_state.existing_logic = rv
		l = C_AST_NODE_TO_LOGIC(c_ast_node, driven_wire_names, prepend_text, parser_state)
		first = rv
		second = l
		first.MERGE_SEQ_LOGIC(second)
		rv = first
		parser_state.existing_logic = rv		
	
	return rv

# ORDER OF ARGS MATTERS
def C_AST_N_ARG_FUNC_INST_TO_LOGIC(func_name, c_ast_node_2_driven_input_wire_names, output_wire_name, output_wire_driven_wire_names, prepend_text, func_c_ast_node, parser_state, use_input_nodes_fuck_it=True):
	func_name_2_logic = parser_state.FuncName2Logic
	existing_logic = parser_state.existing_logic
	rv = existing_logic
	func_inst_name = BUILD_INST_NAME(prepend_text,func_name, func_c_ast_node)
	# Sub module inst
	rv.submodule_instances[func_inst_name] = func_name
	# C ast node
	rv.submodule_instance_to_c_ast_node[func_inst_name]=func_c_ast_node
	
	if use_input_nodes_fuck_it:
		# Inputs
		#print "c_ast_node_2_driven_input_wire_names",c_ast_node_2_driven_input_wire_names
		# The order of evaluation of the postfix expression and the argument expression list is unspecified.
		#  ... All arguments are evaluated. Order not defined (as per standard). But all implementations of C/C++ (that I know of) evaluate function arguments from right to left. <<<<<<<<<<<<<<<<TTODO: Fix me? baaaaaaaaahhh
		parser_state.existing_logic = rv
		in_logic = SEQ_C_AST_NODES_TO_LOGIC(c_ast_node_2_driven_input_wire_names, prepend_text, parser_state)
		rv.MERGE_COMB_LOGIC(in_logic)		
	else:
		# The nodes are jsut the connections driving wire names, loop doing CONNECT_WIRES_LOGIC
		for driving_wire in c_ast_node_2_driven_input_wire_names:
			driven_input_port_wires = c_ast_node_2_driven_input_wire_names[driving_wire]
			# Assume only one for now
			if len(driven_input_port_wires) != 1:
				print driven_input_port_wires
				assert len(driven_input_port_wires) == 1
			driven_input_port_wire = driven_input_port_wires[0]
			#if type(driving_wire) == type(driven_input_port_wire): #Both must be wires
			rv = APPLY_CONNECT_WIRES_LOGIC(rv, driving_wire,[driven_input_port_wire])
				
	# Get list of input port names in order
	input_port_names = []
	for thing in c_ast_node_2_driven_input_wire_names:
		driven_input_port_wires = c_ast_node_2_driven_input_wire_names[thing]
		assert len(driven_input_port_wires) == 1
		driven_input_port_wire = driven_input_port_wires[0]
		# Get last leaf
		toks = driven_input_port_wire.split(SUBMODULE_MARKER)
		last_tok = toks[len(toks)-1]
		input_port_names.append(last_tok)
	rv.submodule_instance_to_input_port_names[func_inst_name] = input_port_names[:]
	
	# IF use_input_nodes_fuck_it the keys are all fucked, their jsut strings
	for c_ast_node in c_ast_node_2_driven_input_wire_names:
		driven_input_wire_names = c_ast_node_2_driven_input_wire_names[c_ast_node]
		for driven_input_wire_name in driven_input_wire_names:
			# Get type for inputs based on func_name if possible
			if func_name in func_name_2_logic:
				func_def_logic_object = func_name_2_logic[func_name]
				# Get port name from driven wire
				toks = driven_input_wire_name.split(SUBMODULE_MARKER)
				port_name = toks[len(toks)-1]
				driving_wire_c_type = func_def_logic_object.wire_to_c_type[port_name]
				if driven_input_wire_name not in rv.wire_to_c_type:
					rv.wire_to_c_type[driven_input_wire_name] = driving_wire_c_type
			else:
				# Set type for this wire by type of wire that drives this
				driving_wire = rv.wire_driven_by[driven_input_wire_name]
				# Type of driving wire
				#if driving_wire not in rv.wire_to_c_type
				driving_wire_c_type = rv.wire_to_c_type[driving_wire]
				
				
				if driven_input_wire_name not in rv.wire_to_c_type:
					rv.wire_to_c_type[driven_input_wire_name] = driving_wire_c_type
			
	# Set type for outputs based on func_name if possible
	if func_name in func_name_2_logic:
		func_def_logic_object = func_name_2_logic[func_name]
		# Get type of output
		output_type = func_def_logic_object.wire_to_c_type[RETURN_WIRE_NAME]
		# Set this type for the output if not set already? # This seems really hacky
		for output_wire_driven_wire_name in output_wire_driven_wire_names:
			if(not(output_wire_driven_wire_name in rv.wire_to_c_type)):
				rv.wire_to_c_type[output_wire_driven_wire_name] = output_type	
	
	
	#print "C_AST_N_ARG_FUNC_INST_TO_LOGIC rv.wires",rv.wires
	# Outputs
	# Finally connect the output of DO_THROUGHPUT_SWEEPthis operation to each of the driven wires
	out_logic = CONNECT_WIRES_LOGIC(output_wire_name, output_wire_driven_wire_names)	
	rv.MERGE_COMB_LOGIC(out_logic)
	# Update parser state since merged in exsiting logic earlier
	parser_state.existing_logic = rv

	
	#print "C_AST_N_ARG_FUNC_INST rv.wire_driven_by", rv.wire_driven_by
	
	return rv	
	
def BUILD_INST_NAME(prepend_text,func_name, c_ast_node):
	file_coord_str = C_AST_COORD_STR(c_ast_node.coord)
	inst_name = prepend_text+ func_name + "[" + file_coord_str + "]"
	return inst_name
	
def C_AST_FUNC_CALL_TO_LOGIC(c_ast_func_call,driven_wire_names,prepend_text,parser_state):
	func_name_2_logic = parser_state.FuncName2Logic
	func_name = str(c_ast_func_call.name.name)
	file_coord_str = C_AST_COORD_STR(c_ast_func_call.coord)
	func_inst_name = BUILD_INST_NAME(prepend_text,func_name, c_ast_func_call)
	if not(func_name in func_name_2_logic):
		print "C_AST_FUNC_CALL_TO_LOGIC Havent parsed func name '", func_name, "' yet. Where does that function come from?"
		print c_ast_func_call.coord
		sys.exit(0)
	not_inst_func_logic = func_name_2_logic[func_name]
		
	# N input port names named by their arg name
	# Decompose inputs to N ARG FUNCTION
	# dict[c_ast_input_node] => [list of driven wire names]
	c_ast_node_2_driven_input_wire_names = OrderedDict()
	
	# Helpful check
	if len(c_ast_func_call.args.exprs) != len(not_inst_func_logic.inputs): #<
		print "The function definition for",func_name,"has",len(c_ast_func_call.args.exprs), "arguments."
		print "as used at", c_ast_func_call.coord, "it has", len(not_inst_func_logic.inputs), "arguments."
		sys.exit(0)
	
	# Assume inputs are in arg order
	for i in range(0, len(not_inst_func_logic.inputs)):
		input_port_name = not_inst_func_logic.inputs[i]
		input_port_wire = func_inst_name+SUBMODULE_MARKER+input_port_name
		input_c_ast_node = c_ast_func_call.args.exprs[i]
		c_ast_node_2_driven_input_wire_names[input_c_ast_node] = [input_port_wire]
		
	# Output is type of logic not_inst_func_logic output wire
	if len(not_inst_func_logic.outputs) != 1:
		print "Whats going on here multiple outputs??"
		sys.exit(0)
	output_port_name = not_inst_func_logic.outputs[0]
	output_c_type = not_inst_func_logic.wire_to_c_type[output_port_name]
	output_wire = func_inst_name+SUBMODULE_MARKER+output_port_name
	parser_state.existing_logic.wire_to_c_type[output_wire] = output_c_type
	
	# Before evaluating input nodes make sure type of port is there so constants can be evaluated
	# Get types from func defs
	func_def_logic_object = func_name_2_logic[func_name]
	for input_port in func_def_logic_object.inputs:
		input_port_wire = func_inst_name + SUBMODULE_MARKER + input_port
		parser_state.existing_logic.wire_to_c_type[input_port_wire] = func_def_logic_object.wire_to_c_type[input_port]	

	# Decompose inputs to N ARG FUNCTION
	func_logic = C_AST_N_ARG_FUNC_INST_TO_LOGIC(func_name, c_ast_node_2_driven_input_wire_names, output_wire, driven_wire_names,prepend_text,c_ast_func_call,parser_state)	
	
	# Sanity check?
	if not(output_wire in func_logic.wire_to_c_type):
		print "444444444444   output_wire in func_logic.wire_to_c_type", bin_op_output in func_logic.wire_to_c_type
		sys.exit(0)
		
	
	# Update state
	parser_state.existing_logic = func_logic
		
	
	# Check input types match
	for input_port in func_def_logic_object.inputs:
		input_port_wire = func_inst_name + SUBMODULE_MARKER + input_port
		input_type = parser_state.existing_logic.wire_to_c_type[input_port_wire]
		driving_wire = parser_state.existing_logic.wire_driven_by[input_port_wire]
		driving_type = parser_state.existing_logic.wire_to_c_type[driving_wire]
		#if input_type != driving_type and (not VHDL.C_TYPES_ARE_INTEGERS([input_type,driving_type]) or C_TYPE_IS_ARRAY(input_type)):
		#	print "Mismatching input types for function",func_name,"at", c_ast_func_call.coord
		#	sys.exit(0)
	
	
	return func_logic
	
def C_AST_UNARY_OP_TO_LOGIC(c_ast_unary_op,driven_wire_names, prepend_text, parser_state):
	existing_logic = parser_state.existing_logic
	# Decompose to C_AST_N_ARG_FUNC_INST_TO_LOGIC
	c_ast_unary_op_str = str(c_ast_unary_op.op)
	
	# Is this UNARY op negating a constant?
	if (c_ast_unary_op_str=="-") and (type(c_ast_unary_op.expr) == c_ast.Constant):
		# THis is just a constant wire with negative value
		return C_AST_CONSTANT_TO_LOGIC(c_ast_unary_op.expr,driven_wire_names, prepend_text, parser_state, is_negated=True)
	
	# Determine op string to use in func name
	if c_ast_unary_op_str == "!":
		c_ast_op_str = UNARY_OP_NOT_NAME
	else:
		print "UNARY_OP name for c_ast_unary_op_str '" + c_ast_unary_op_str + "'?"
		sys.exit(0)
		
	# Set port names based on func name
	func_name = UNARY_OP_LOGIC_NAME_PREFIX + "_" + c_ast_op_str
	
	file_coord_str = C_AST_COORD_STR(c_ast_unary_op.coord)
	func_inst_name = BUILD_INST_NAME(prepend_text,func_name, c_ast_unary_op)
		
	unary_op_input_port_name = c_ast_unary_op.children()[0][0]
	unary_op_input = func_inst_name+SUBMODULE_MARKER+unary_op_input_port_name
	unary_op_output=func_inst_name+SUBMODULE_MARKER+RETURN_WIRE_NAME
	
	# Determine output type based on operator or driving wire type
	driven_c_type_str = GET_C_TYPE_FROM_WIRE_NAMES(driven_wire_names, parser_state.existing_logic, allow_fail=True)
	if driven_c_type_str is not None:
		# Most unary ops use the type of the driven wire
		if c_ast_unary_op_str == "!":
			output_c_type = driven_c_type_str
		else:
			print "Output C type for c_ast_unary_op_str '" + c_ast_unary_op_str + "'?"
			sys.exit(0)	
		# Set type for output wire
		parser_state.existing_logic.wire_to_c_type[unary_op_output] = output_c_type
	
	
	# Inputs
	# Decompose inputs to N ARG FUNCTION
	# dict[c_ast_input_node] => [list of driven wire names]
	c_ast_node_2_driven_input_wire_names = OrderedDict()
	c_ast_node_2_driven_input_wire_names[c_ast_unary_op.expr] = [unary_op_input]
	
	# Before evaluating input nodes make sure type of port is there so constants can be evaluated
	# Input must be non const or wtf guys
	in_logic = SEQ_C_AST_NODES_TO_LOGIC(c_ast_node_2_driven_input_wire_names, prepend_text, parser_state)
	if unary_op_input in in_logic.wire_to_c_type:
		input_type = in_logic.wire_to_c_type[unary_op_input]
	else:
		print func_inst_name, "looks like a constant unary op, what's going on?"
		print "in_logic.wire_to_c_type"
		print in_logic.wire_to_c_type
		sys.exit(0)
		
	in_logic.wire_to_c_type[unary_op_input] = input_type
	if unary_op_output not in in_logic.wire_to_c_type:
		in_logic.wire_to_c_type[unary_op_output] = input_type
	
	# In logic exists before funciton
	parser_state.existing_logic = in_logic
	
	
	func_logic = C_AST_N_ARG_FUNC_INST_TO_LOGIC(func_name, c_ast_node_2_driven_input_wire_names, unary_op_output,  driven_wire_names,prepend_text,c_ast_unary_op, parser_state)	

	parser_state.existing_logic = func_logic
	

	return func_logic

def C_AST_BINARY_OP_TO_LOGIC(c_ast_binary_op,driven_wire_names,prepend_text, parser_state):
	# Decompose to C_AST_N_ARG_FUNC_INST_TO_LOGIC
	c_ast_bin_op_str = str(c_ast_binary_op.op)
	
	# Determine op string to use in func name
	if c_ast_bin_op_str == ">":
		c_ast_op_str = BIN_OP_GT_NAME
	elif c_ast_bin_op_str == ">=":
		c_ast_op_str = BIN_OP_GTE_NAME
	elif c_ast_bin_op_str == "<":
		c_ast_op_str = BIN_OP_LT_NAME
	elif c_ast_bin_op_str == "<=":
		c_ast_op_str = BIN_OP_LTE_NAME
	elif c_ast_bin_op_str == "+":
		c_ast_op_str = BIN_OP_PLUS_NAME
	elif c_ast_bin_op_str == "-":
		c_ast_op_str = BIN_OP_MINUS_NAME
	elif c_ast_bin_op_str == "*":
		c_ast_op_str = BIN_OP_MULT_NAME
	elif c_ast_bin_op_str == "/":
		c_ast_op_str = BIN_OP_DIV_NAME
	elif c_ast_bin_op_str == "==":
		c_ast_op_str = BIN_OP_EQ_NAME
	elif c_ast_bin_op_str == "&":
		c_ast_op_str = BIN_OP_AND_NAME
	elif c_ast_bin_op_str == "|":
		c_ast_op_str = BIN_OP_OR_NAME
	elif c_ast_bin_op_str == "^":
		c_ast_op_str = BIN_OP_XOR_NAME
	elif c_ast_bin_op_str == "<<":
		c_ast_op_str = BIN_OP_SL_NAME
	elif c_ast_bin_op_str == ">>":
		c_ast_op_str = BIN_OP_SR_NAME
	else:
		print "BIN_OP name for c_ast_bin_op_str '" + c_ast_bin_op_str + "'?"
		sys.exit(0)
		
	# Set port names based on func name
	func_name = BIN_OP_LOGIC_NAME_PREFIX + "_" + c_ast_op_str
	
	file_coord_str = C_AST_COORD_STR(c_ast_binary_op.coord)
	func_inst_name = BUILD_INST_NAME(prepend_text,func_name, c_ast_binary_op)
		
	bin_op_left_input_port_name = c_ast_binary_op.children()[0][0]
	bin_op_right_input_port_name = c_ast_binary_op.children()[1][0]
	
	bin_op_left_input = func_inst_name+SUBMODULE_MARKER+bin_op_left_input_port_name
	bin_op_right_input = func_inst_name+SUBMODULE_MARKER+bin_op_right_input_port_name
	bin_op_output=func_inst_name+SUBMODULE_MARKER+RETURN_WIRE_NAME
	
	# Determine output type based on operator or driving wire type
	driven_c_type_str = GET_C_TYPE_FROM_WIRE_NAMES(driven_wire_names, parser_state.existing_logic)
	# Most binary ops use the type of the driven wire
	
	if c_ast_bin_op_str == ">":
		output_c_type = BOOL_C_TYPE
	elif c_ast_bin_op_str == ">=":
		output_c_type = BOOL_C_TYPE
	elif c_ast_bin_op_str == "<":
		output_c_type = BOOL_C_TYPE
	elif c_ast_bin_op_str == "<=":
		output_c_type = BOOL_C_TYPE
	elif c_ast_bin_op_str == "==":
		output_c_type = BOOL_C_TYPE
	elif c_ast_bin_op_str == "+":
		output_c_type = driven_c_type_str
	elif c_ast_bin_op_str == "-":
		output_c_type = driven_c_type_str
	elif c_ast_bin_op_str == "*":
		output_c_type = driven_c_type_str
	elif c_ast_bin_op_str == "/":
		output_c_type = driven_c_type_str
	elif c_ast_bin_op_str == "&":
		output_c_type = driven_c_type_str
	elif c_ast_bin_op_str == "|":
		output_c_type = driven_c_type_str
	elif c_ast_bin_op_str == "^":
		output_c_type = driven_c_type_str
	elif c_ast_bin_op_str == "<<":
		output_c_type = driven_c_type_str
	elif c_ast_bin_op_str == ">>":
		output_c_type = driven_c_type_str
	else:
		print "Output C type for '" + c_ast_bin_op_str + "'?"
		sys.exit(0)
	
	
	# Set type for output wire
	parser_state.existing_logic.wire_to_c_type[bin_op_output] = output_c_type
	#print " ----- ", bin_op_output, output_c_type
	
	rv = parser_state.existing_logic
	
	
	# Inputs
	# Decompose inputs to N ARG FUNCTION
	# dict[c_ast_input_node] => [list of driven wire names]
	c_ast_node_2_driven_input_wire_names = OrderedDict()
	c_ast_node_2_driven_input_wire_names[c_ast_binary_op.left] = [bin_op_left_input]
	c_ast_node_2_driven_input_wire_names[c_ast_binary_op.right] = [bin_op_right_input]
	
	# FIRST PROCESS THE INPUT CONNECTIONS ALONE
	in_logic = SEQ_C_AST_NODES_TO_LOGIC(c_ast_node_2_driven_input_wire_names, prepend_text, parser_state)
	parser_state.existing_logic.MERGE_COMB_LOGIC(in_logic)
	left_type = None
	# Was either input type evaluated?
	if bin_op_left_input in in_logic.wire_to_c_type:
		left_type = in_logic.wire_to_c_type[bin_op_left_input]
	right_type = None
	if bin_op_right_input in in_logic.wire_to_c_type:
		right_type = in_logic.wire_to_c_type[bin_op_right_input]
	# Which ones to use?
	if (left_type is None) and (right_type is None):
		print func_inst_name, "doesn't have type information for either input? What's going on?"
		print "in_logic.wire_to_c_type"
		print "bin_op_left_input",bin_op_left_input
		print "bin_op_right_input",bin_op_right_input
		print "Know types:"
		print in_logic.wire_to_c_type
		sys.exit(0)
	elif not(left_type is None) and (right_type is None):
		# Use left
		parser_state.existing_logic.wire_to_c_type[bin_op_left_input] = left_type
		parser_state.existing_logic.wire_to_c_type[bin_op_right_input] = left_type
	elif (left_type is None) and not(right_type is None):
		# Use Right
		parser_state.existing_logic.wire_to_c_type[bin_op_left_input] = right_type
		parser_state.existing_logic.wire_to_c_type[bin_op_right_input] = right_type
	else:
		# Different types set for each input
		parser_state.existing_logic.wire_to_c_type[bin_op_left_input] = left_type
		parser_state.existing_logic.wire_to_c_type[bin_op_right_input] = right_type
		
	#print "left_type",left_type
	#print "right_type",right_type
		
	# Replace ENUM with INT type of input wire so cast happens? :/?
	# Left
	if parser_state.existing_logic.wire_to_c_type[bin_op_left_input] in parser_state.enum_to_ids_dict:
		#print "left enum"
		# Set BIN OP input wire as UINT
		enum_type = parser_state.existing_logic.wire_to_c_type[bin_op_left_input]
		num_ids = len(parser_state.enum_to_ids_dict[enum_type])
		left_width = int(math.ceil(math.log(num_ids,2)))
		parser_state.existing_logic.wire_to_c_type[bin_op_left_input] = "uint" + str(left_width) + "_t"
		# Set driver of input as ENUM
		driving_wire = parser_state.existing_logic.wire_driven_by[bin_op_left_input]
		parser_state.existing_logic.wire_to_c_type[driving_wire] = enum_type
		#print "driving_wire",driving_wire,enum_type
		
	# Right
	if parser_state.existing_logic.wire_to_c_type[bin_op_right_input] in parser_state.enum_to_ids_dict:
		# Set BIN OP input wire as UINT
		enum_type = parser_state.existing_logic.wire_to_c_type[bin_op_right_input]
		num_ids = len(parser_state.enum_to_ids_dict[enum_type])
		right_width = int(math.ceil(math.log(num_ids,2)))
		parser_state.existing_logic.wire_to_c_type[bin_op_right_input] = "uint" + str(right_width) + "_t"
		# Set driver of input as ENUM
		driving_wire = parser_state.existing_logic.wire_driven_by[bin_op_right_input]
		parser_state.existing_logic.wire_to_c_type[driving_wire] = enum_type
		#print "driving_wire",driving_wire,enum_type
	
	#print "parser_state.existing_logic.wire_to_c_type[bin_op_left_input]",parser_state.existing_logic.wire_to_c_type[bin_op_left_input]
	#print "parser_state.existing_logic.wire_to_c_type[bin_op_right_input]",parser_state.existing_logic.wire_to_c_type[bin_op_right_input]
	
	
	func_logic = C_AST_N_ARG_FUNC_INST_TO_LOGIC(func_name, c_ast_node_2_driven_input_wire_names, bin_op_output, driven_wire_names,prepend_text,c_ast_binary_op, parser_state)	
	
	# Save c ast node of binary op
	
	
	parser_state.existing_logic = func_logic
	#print "AFTER:"
	#print "parser_state.existing_logic.wire_to_c_type[bin_op_left_input]",parser_state.existing_logic.wire_to_c_type[bin_op_left_input]
	#print "parser_state.existing_logic.wire_to_c_type[bin_op_right_input]",parser_state.existing_logic.wire_to_c_type[bin_op_right_input]
	return func_logic

	
def GET_C_TYPE_FROM_WIRE_NAMES(wire_names, logic, allow_fail=False):
	rv = None
	for wire_name in wire_names:
		if not(wire_name in logic.wire_to_c_type):
			if allow_fail:
				return None
			else:
				print "Cant GET_C_TYPE_FROM_WIRE_NAMES since", wire_name,"not in logic.wire_to_c_type"
				print "logic.wire_to_c_type",logic.wire_to_c_type
				print 0/0
				sys.exit(0)
		c_type_str = logic.wire_to_c_type[wire_name]
		if rv is None:
			rv = c_type_str
		else:
			if rv != c_type_str:
				print "GET_C_TYPE_FROM_WIRE_NAMES multilpe types?"
				print "wire_name",wire_name
				print rv, c_type_str
				print 0/0
				sys.exit(0)
			
	return rv

# Return None if wire is not driven by const (or anything)
def FIND_CONST_DRIVING_WIRE(wire, logic):
	if WIRE_IS_CONSTANT(wire,logic.inst_name):
		return wire
	else:
		if wire in logic.wire_driven_by:
			driving_wire = logic.wire_driven_by[wire]
			return FIND_CONST_DRIVING_WIRE(driving_wire, logic)
		else:
			return None		
			
def CONNECT_WIRES_LOGIC(driving_wire, driven_wire_names):	
	return APPLY_CONNECT_WIRES_LOGIC(Logic(), driving_wire, driven_wire_names)
	
def APPLY_CONNECT_WIRES_LOGIC(logic, driving_wire, driven_wire_names):
	# Add wires if not there
	if driving_wire not in logic.wires:
		logic.wires.append(driving_wire)	
	for driven_wire_name in driven_wire_names:
		if driven_wire_name not in logic.wires:
			logic.wires.append(driven_wire_name)
		
	# Record wire_drives
	all_driven_wire_names = []
	# Start with existing driven wires
	if driving_wire in logic.wire_drives:
		all_driven_wire_names = logic.wire_drives[driving_wire]
	# Append the new wires
	for driven_wire_name in driven_wire_names:
		if driven_wire_name not in all_driven_wire_names:
			all_driven_wire_names.append(driven_wire_name)
	# Save
	logic.wire_drives[driving_wire] = all_driven_wire_names
	# Record wire_driven_by
	for driven_wire_name in driven_wire_names:
		logic.wire_driven_by[driven_wire_name] = driving_wire
		
	return logic
	
# int x[2]     returns "x", "int", 2
# int x[2][2]  returns "x", "int[2]", 2
def C_AST_ARRAYDECL_TO_NAME_ELEM_TYPE_DIM(array_decl):
	#casthelp(array_decl)
	#print 
	#sys.exit(0)
	
	# Will be N nested ArrayDecls with dimensions folowed by the element type
	children = array_decl.children()
	dims = []
	while len(children)>1 and children[1][0]=='dim':
		# Get the dimension
		dim = int(children[1][1].value)
		dims.append(dim)
		array_decl = children[0][1]
		children = array_decl.children()
		
	# Reverse order from parsing
	#dims = dims[::-1]
	
	# Get base type
	# Array decl is now holding the inner type
	type_decl = array_decl
	type_name = type_decl.type.names[0]
	#casthelp(type_decl)
	#print "type_decl^"
	
	 
	
	# Append everything but last dim
	elem_type = type_name
	for dim_i in range(0, len(dims)-1):
		elem_type = elem_type + "[" + str(dims[dim_i]) + "]"
	
	dim = dims[len(dims)-1]
	#print elem_type
	#print dim
	#sys.exit(0)
	return type_decl.declname, elem_type,dim
	
	
	
def C_AST_PARAM_DECL_OR_GLOBAL_DEF_TO_C_TYPE(param_decl):
	# Need to get array type differently 
	if type(param_decl.type) == c_ast.ArrayDecl:
		name, elem_type, dim = C_AST_ARRAYDECL_TO_NAME_ELEM_TYPE_DIM(param_decl.type)
		array_type = elem_type + "[" + str(dim) + "]"
		#print "array_type",array_type
		return array_type			
	else:
		# Non array decl
		#print "Non array decl", param_decl
		return param_decl.type.type.names[0]
	
def C_AST_FUNC_DEF_TO_LOGIC(c_ast_funcdef, parser_state, parse_body = True):
	rv = Logic()
	# Save the c_ast node
	rv.c_ast_node = c_ast_funcdef
	
	# All func def logic has an output wire called "return"
	return_wire_name = RETURN_WIRE_NAME
	rv.outputs.append(return_wire_name)
	rv.wires.append(return_wire_name)
	rv.wire_to_c_type[return_wire_name] = c_ast_funcdef.decl.type.type.type.names[0]

	# First get name of function from the declaration
	rv.func_name = c_ast_funcdef.decl.name
	
	# Then get input wire names from the function def
	for param_decl in c_ast_funcdef.decl.type.args.params:
		input_wire_name = param_decl.name
		rv.inputs.append(input_wire_name)
		rv.wires.append(input_wire_name)
		c_type = C_AST_PARAM_DECL_OR_GLOBAL_DEF_TO_C_TYPE(param_decl)
		rv.wire_to_c_type[input_wire_name] = c_type
	
	# Merge with logic from the body of the func def
	existing_logic=rv
	driven_wire_names=[]
	prepend_text=""
	if parse_body:
		parser_state.existing_logic = rv
		body_logic = C_AST_NODE_TO_LOGIC(c_ast_funcdef.body, driven_wire_names, prepend_text, parser_state)
		
		#print "C_AST_FUNC_DEF_TO_LOGIC", rv.func_name, "body_logic.wire_drives",body_logic.wire_drives
		
		rv.MERGE_COMB_LOGIC(body_logic)
				
	# Sanity check for return
	if RETURN_WIRE_NAME not in rv.wire_driven_by and not SW_LIB.IS_BIT_MANIP(rv):
		print "No return statement in function:", rv.func_name
		sys.exit(0)
	
	return rv

def RECURSIVE_GET_ALL_SUBMODULE_INSTANCES(main_logic, LogicInstLookupTable):
	all_submodule_instances = []
	for submodule_inst in main_logic.submodule_instances:
		all_submodule_instances.append(submodule_inst)
		if submodule_inst in LogicInstLookupTable:
			submodule_logic = LogicInstLookupTable[submodule_inst]
			all_sub_submodule_instances = RECURSIVE_GET_ALL_SUBMODULE_INSTANCES(submodule_logic, LogicInstLookupTable)
			all_submodule_instances = all_submodule_instances + all_sub_submodule_instances
	
	#print "all_submodule_instances",all_submodule_instances
	return all_submodule_instances

def GET_LOGIC_INST_LOOKUP_CACHE_FILEPATH(Logic):
	key = Logic.inst_name
	key = key.replace("/","_");
	output_directory = SYN.GET_OUTPUT_DIRECTORY(Logic, implement=False)
	filepath = output_directory + "/" + key + ".logic"
	return filepath

def WRITE_LOGIC_INST_LOOKUP_CACHE(Logic, logic_lookup_table):
	filepath = GET_LOGIC_INST_LOOKUP_CACHE_FILEPATH(Logic)
	output_directory = SYN.GET_OUTPUT_DIRECTORY(Logic, implement=False)
	# Write dir first if needed
	if not os.path.exists(output_directory):
		os.makedirs(output_directory)
		
	# Write file
	with open(filepath, 'w') as output:
		pickle.dump(logic_lookup_table, output, pickle.HIGHEST_PROTOCOL)

def GET_CACHED_LOGIC_INST_LOOKUP(Logic):
	filepath = GET_LOGIC_INST_LOOKUP_CACHE_FILEPATH(Logic)
	if os.path.exists(filepath):
		with open(filepath, 'rb') as input:
			logic_lookup_table = pickle.load(input)
			return logic_lookup_table
	return None	

def GET_SUBMODULE_INPUT_PORT_DRIVING_WIRE(logic, submodule_inst_name, input_port_name):
	#print "logic.func_name", logic.func_name
	name = input_port_name #  submodule_inst_name + C_TO_LOGIC.SUBMODULE_MARKER + input_port_name
	#print " logic.wire_driven_by"
	#print logic.wire_driven_by
	driving_wire = logic.wire_driven_by[name]
	return driving_wire
	
def PRINT_DRIVER_WIRE_TRACE(start, logic, wires_driven_so_far=None):
	text = ""
	while not(start is None):
		if wires_driven_so_far is None:
			text += start.replace(logic.inst_name + SUBMODULE_MARKER,"") + " <= "
		else:
			text += start.replace(logic.inst_name + SUBMODULE_MARKER,"") + "(driven? " +  str(start in wires_driven_so_far) + ") <= "
			
		if start in logic.wire_driven_by:
			start = logic.wire_driven_by[start]
		else:
			text += "has no driver!!!!?"
			start = None
	print text
	return start

def GET_CONTAINER_LOGIC_FOR_SUBMODULE_INST(submodule_inst, LogicInstLookupTable):
	rv = None
	submodule_logic = LogicInstLookupTable[submodule_inst]
	if submodule_logic.containing_inst in LogicInstLookupTable:
		containing_logic = LogicInstLookupTable[submodule_logic.containing_inst]
		rv = containing_logic
	return rv
	
	
	
# This class hold all the state obtained by parsing a single C file
class ParserState:
	def __init__(self):
		self.FuncName2Logic=dict() #dict[func_name]=Logic() instance with just func info
		self.LogicInstLookupTable=dict() #dict[inst_name]=Logic() instance in full
		self.existing_logic = None # Temp working copy of logic ? idk it should work
		self.struct_to_field_type_dict = dict()
		self.enum_to_ids_dict = dict()
		self.global_info = dict()
		self.volatile_global_info = dict()
		self.global_mhz_limit = None
		
		
import sys
from numbers import Number
from collections import Set, Mapping, deque

try: # Python 2
    zero_depth_bases = (basestring, Number, xrange, bytearray)
    iteritems = 'iteritems'
except NameError: # Python 3
    zero_depth_bases = (str, bytes, Number, range, bytearray)
    iteritems = 'items'

def getsize(obj_0):
    """Recursively iterate to sum size of object & members."""
    _seen_ids = set()
    def inner(obj):
        obj_id = id(obj)
        if obj_id in _seen_ids:
            return 0
        _seen_ids.add(obj_id)
        size = sys.getsizeof(obj)
        if isinstance(obj, zero_depth_bases):
            pass # bypass remaining control flow and return
        elif isinstance(obj, (tuple, list, Set, deque)):
            size += sum(inner(i) for i in obj)
        elif isinstance(obj, Mapping) or hasattr(obj, iteritems):
            size += sum(inner(k) + inner(v) for k, v in getattr(obj, iteritems)())
        # Check for custom object instances - may subclass above too
        if hasattr(obj, '__dict__'):
            size += inner(vars(obj))
        if hasattr(obj, '__slots__'): # can have __slots__ with __dict__
            size += sum(inner(getattr(obj, s)) for s in obj.__slots__ if hasattr(obj, s))
        return size
    return inner(obj_0)
    
	
# Returns ParserState
def PARSE_FILE(top_level_func_name, c_file):
	# Catch pycparser exceptions
	try:
		parser_state = ParserState()
		print "Parsing PipelinedC code..."
		# Get the parsed struct def info
		parser_state.struct_to_field_type_dict = GET_STRUCT_FIELD_TYPE_DICT(c_file)
		#for struct_type in parser_state.struct_to_field_type_dict :
		#	print struct_type,parser_state.struct_to_field_type_dict[struct_type]
		# Get global variable info
		parser_state = GET_GLOBAL_INFO(parser_state, c_file)
		# Get volatile globals
		parser_state = GET_VOLATILE_GLOBAL_INFO(parser_state, c_file)
		# Get the parsed enum info
		parser_state.enum_to_ids_dict = GET_ENUM_IDS_DICT(c_file)
		# Get SW existing logic for this c file
		parser_state.FuncName2Logic = SW_LIB.GET_AUTO_GENERATED_FUNC_NAME_LOGIC_LOOKUP(c_file, parser_state)
		#print "parser_state.struct_to_field_type_dict",parser_state.struct_to_field_type_dict
		# Get the function definitions
		parser_state.FuncName2Logic = GET_FUNC_NAME_LOGIC_LOOKUP_TABLE([c_file], parser_state)
		# Fuck me add struct info for array wrapper
		parser_state = APPEND_ARRAY_STRUCT_INFO(parser_state)
		
		
		# cHECK FOR EXPECTED FUNC NAME
		if top_level_func_name not in parser_state.FuncName2Logic:
			print "There doesnt seem to be as function called '", top_level_func_name,"' in the file '",c_file,"'"
			sys.exit(0)
			
		# Check for double use of globals+volatiles the dumb way to print useful info
		for func_name1 in parser_state.FuncName2Logic:
			func1_logic = parser_state.FuncName2Logic[func_name1]
			for func_name2 in parser_state.FuncName2Logic:
				if func_name2 == func_name1:
					continue
				func2_logic = parser_state.FuncName2Logic[func_name2]
				for func1_global in (func1_logic.global_wires + func1_logic.volatile_global_wires):
					if func1_global in (func2_logic.global_wires + func2_logic.volatile_global_wires):
						print "Heyo can't use globals in more than one function!"
						print func1_global, "used in", func_name1, "and", func_name2
						sys.exit(0)
			
		
		c_ast_node_when_used = parser_state.FuncName2Logic[top_level_func_name].c_ast_node
		unadjusted_logic_lookup_table_so_far = None
		adjusted_containing_logic_inst_name=""		
		parser_state.LogicInstLookupTable = None
		# First check if is cached
		top_level_logic = parser_state.FuncName2Logic[top_level_func_name]
		logic_lookup_table_cache = GET_CACHED_LOGIC_INST_LOOKUP(top_level_logic)
		if not(logic_lookup_table_cache is None):
			print "Using cached hierarchy elaboration for '",top_level_func_name,"'"
			parser_state.LogicInstLookupTable = logic_lookup_table_cache
		else:
			
			main_func_logic = parser_state.FuncName2Logic["main"]
			first_sub = main_func_logic.submodule_instances.keys()[0]
			if SUBMODULE_MARKER in first_sub:
				print "Main func logic submodule inst has submodule marker?"
				print first_sub
				sys.exit(0)
			
			print "Elaborating hierarchy down to raw HDL logic..."	
			parser_state.LogicInstLookupTable = RECURSIVE_CREATE_LOGIC_INST_LOOKUP_TABLE(top_level_func_name, top_level_func_name, parser_state, unadjusted_logic_lookup_table_so_far, adjusted_containing_logic_inst_name, c_ast_node_when_used)
		
		
		# Write cache
		# top_level_func_name = main = inst name
		top_level_logic = parser_state.LogicInstLookupTable[top_level_func_name]

		
		print "Writing generated pipelined C code to output directories..."
		WRITE_LOGIC_INST_LOOKUP_CACHE(top_level_logic, parser_state.LogicInstLookupTable)
		
		for inst_name in parser_state.LogicInstLookupTable:
			logic = parser_state.LogicInstLookupTable[inst_name]
			if not(logic.c_code_text is None):
				# Fake name
				fake_filename = LEAF_NAME(logic.inst_name, True) + ".c"
				out_dir = SYN.GET_OUTPUT_DIRECTORY(logic, implement=False)
				outpath = out_dir + "/" + fake_filename
				if not os.path.exists(out_dir):
					os.makedirs(out_dir)
				f=open(outpath,"w")
				f.write(logic.c_code_text)
				f.close()		
				
		print "Doing that dumb loop to find containing submodules for everyone..."
		for inst_name in parser_state.LogicInstLookupTable:
			logic = parser_state.LogicInstLookupTable[inst_name]
			for submodule_inst in logic.submodule_instances:
				submodule_logic = parser_state.LogicInstLookupTable[submodule_inst]
				# Adjust listing containing inst
				submodule_logic.containing_inst = inst_name
				# Write back - this is bad python probably not required cuz im bad at python ok
				parser_state.LogicInstLookupTable[submodule_inst] = submodule_logic
				
		print
		
		
		return parser_state

	except c_parser.ParseError as pe:
		print "Top level:",top_level_func_name
		print 
		print "pycparser says you messed up here:",pe
		sys.exit(0)
		
class GlobalInfo:
	def __init__(self):
		self.name = None
		self.type_name = None
		
def GET_GLOBAL_INFO(parser_state, c_file):
	# Read in file with C parser and get function def nodes
	parser_state.global_info = dict()
	
	global_defs = GET_C_AST_GLOBALS(c_file)
	
	for global_def in global_defs:
		#casthelp(global_def.type.type.names[0])
		global_info = GlobalInfo()
		global_info.name = str(global_def.name)
		c_type = C_AST_PARAM_DECL_OR_GLOBAL_DEF_TO_C_TYPE(global_def)
		#print global_info.name, c_type
		global_info.type_name = c_type
		
		# Check for multiple types!
		if global_info.name in parser_state.global_info:
			if parser_state.global_info[global_info.name].type_name != global_info.type_name:
				print "Global variable with multiple types?", global_info.name
				sys.exit(0)
				
		# Save info
		parser_state.global_info[global_info.name] = global_info
			
	return parser_state
	
def GET_VOLATILE_GLOBAL_INFO(parser_state, c_file):
	# Read in file with C parser and get function def nodes
	parser_state.volatile_global_info = dict()
	
	volatile_global_defs = GET_C_AST_VOLATILE_GLOBALS(c_file)
	
	for volatile_global_def in volatile_global_defs:
		global_info = GlobalInfo()
		global_info.name = str(volatile_global_def.name)
		c_type = C_AST_PARAM_DECL_OR_GLOBAL_DEF_TO_C_TYPE(volatile_global_def)
		global_info.type_name = c_type
		
		# Check for multiple types!
		if global_info.name in parser_state.volatile_global_info:
			if parser_state.volatile_global_info[global_info.name].type_name != global_info.type_name:
				print "Volatile global variable with multiple types?", global_info.name
				sys.exit(0)
				
		# Save info
		parser_state.volatile_global_info[global_info.name] = global_info
			
	return parser_state

# Fuck me add struct info for array wrapper
def APPEND_ARRAY_STRUCT_INFO(parser_state):
	# Loop over all C types and find the array structs
	for func_name in parser_state.FuncName2Logic:
		func_logic = parser_state.FuncName2Logic[func_name]
		for wire in func_logic.wire_to_c_type:
			c_type  = func_logic.wire_to_c_type[wire]
			if DUMB_STRUCT_THING in c_type:
				# BReak apart
				toks = c_type.split(DUMB_STRUCT_THING+"_")
				# uint8_t_ARRAY_STRUCT_2_2
				elem_type = toks[0]
				dim_strs = toks[1].split("_")
				data_array_type = elem_type
				for dim_str in dim_strs:
					data_array_type += "[" + dim_str + "]"
				
				# Append to dict
				field_type_dict = dict()
				field_type_dict["data"] = data_array_type 
				parser_state.struct_to_field_type_dict[c_type] = field_type_dict
				
	return parser_state
				
				

def GET_ENUM_IDS_DICT(c_file):
	# Read in file with C parser and get function def nodes
	rv = dict()
	enum_defs = GET_C_AST_ENUM_DEFS(c_file)
	for enum_def in enum_defs:
		#casthelp(enum_def)
		#sys.exit(0)
		enum_name = str(enum_def.name)
		#print "struct_name",struct_name
		rv[enum_name] = []
		#casthelp(enum_def.values)
		#sys.exit(0)
		for child in enum_def.values.enumerators:
			if len(child.children()) > 0:
				child.show()
				print "Don't assign enums values for now OK?"
				sys.exit(0)			
			
			#sys.exit(0)
			id_str = str(child.name)
			#print id_str
			rv[enum_name].append(id_str)
			
			'''
			type_name = str(child.children()[0][1].children()[0][1].names[0])
			rv[struct_name][field_name] = type_name
			
			if struct_def.name is None:
				sys.exit(0)
			'''
	#print rv
	#sys.exit(0)
	return rv

_printed_GET_STRUCT_FIELD_TYPE_DICT = False
def GET_STRUCT_FIELD_TYPE_DICT(c_file):
	# Read in file with C parser and get function def nodes
	rv = dict()
	struct_defs = GET_C_AST_STRUCT_DEFS(c_file)
	for struct_def in struct_defs:
		if struct_def.name is None:
			global _printed_GET_STRUCT_FIELD_TYPE_DICT
			if not _printed_GET_STRUCT_FIELD_TYPE_DICT:
				print "WARNING: Must use tag_name and struct_alias in struct definitions... for now... Ex."
				print '''typedef struct tag_name {
	type member1;
	type member2;
} struct_alias;'''
				_printed_GET_STRUCT_FIELD_TYPE_DICT = True
			continue
					
		#casthelp(struct_def)
		struct_name = str(struct_def.name)
		#print "struct_name",struct_name
		rv[struct_name] = dict()
		for child in struct_def.decls:
			# Assume type decl	
			field_name = str(child.name)
			if type(child.type) == c_ast.ArrayDecl:
				field_name, base_type, dim = C_AST_ARRAYDECL_TO_NAME_ELEM_TYPE_DIM(child.type)
				#dim = int(child.type.dim.value)
				#base_type = child.type.type.type.names[0]
				type_name = base_type + "[" + str(dim) + "]"	
			else:
				# Non array
				type_name = str(child.children()[0][1].children()[0][1].names[0])
			rv[struct_name][field_name] = type_name
			
	return rv
	

# This will likely be called multiple times when loading multiple C files
def GET_FUNC_NAME_LOGIC_LOOKUP_TABLE(c_files, parser_state, parse_body = True):
	existing_func_name_2_logic = parser_state.FuncName2Logic
	
	# Build function name to logic from func defs from files
	func_name_2_logic = copy.deepcopy(existing_func_name_2_logic) #copy.deepcopy(existing_func_name_2_logic)  # Needed?
	
	# Loop over C files in order and collect func logic (not instance) from func defs
	# Each func def needs existing logic func name lookup
	for c_filename in c_files:
		# Read in file with C parser and get function def nodes
		func_defs = GET_C_AST_FUNC_DEFS(c_filename)
		for func_def in func_defs:
			# Each func def produces a single logic item
			parser_state.existing_logic=None
			driven_wire_names=[]
			prepend_text=""
			logic = C_AST_FUNC_DEF_TO_LOGIC(func_def, parser_state, parse_body)
			func_name_2_logic[logic.func_name] = logic
			func_name_2_logic[logic.func_name].inst_name = logic.func_name 
			
			parser_state.FuncName2Logic = func_name_2_logic
			
			
	'''
	# Remove unused instances
	if remove_unused:
		print "Removing unused function definitions..."
		new_func_name_2_logic = dict()
		for func_name in func_name_2_logic:
			found_as_submodule = False
			# Find func name in some other logic
			for being_searched_func_name in func_name_2_logic:
				being_searched_func_logic = func_name_2_logic[being_searched_func_name]
				for submodule_instance in being_searched_func_logic.submodule_instances:
					submodule_func_name = being_searched_func_logic.submodule_instances[submodule_instance]
					# Found func name as submodule?
					if submodule_func_name == func_name:
						new_func_name_2_logic[func_name] = func_name_2_logic[func_name]
						found_as_submodule = True
						break
				if found_as_submodule:
					break
						
		print "new_func_name_2_logic",new_func_name_2_logic
	'''
			
	return func_name_2_logic
	
			
def RECURSIVE_CREATE_LOGIC_INST_LOOKUP_TABLE(orig_logic_func_name, orig_logic_inst_name, parser_state, unadjusted_logic_lookup_table_so_far=None, adjusted_containing_logic_inst_name="", c_ast_node_when_used=None, recursion_level=0):	
	#if recursion_level==0:
	#print "=="
	#print "...Recursing from instance: '",orig_logic_inst_name,"'"
	#print "...orig_logic_func_name:",orig_logic_func_name
	#print "...adjusted_containing_logic_inst_name:",adjusted_containing_logic_inst_name
	#print "Recursing from:", adjusted_containing_logic_inst_name + SUBMODULE_MARKER + orig_logic_inst_name
	
	new_inst_name_prepend_text = adjusted_containing_logic_inst_name + SUBMODULE_MARKER
	if orig_logic_func_name == "main":
		# Main never gets prepend text
		if adjusted_containing_logic_inst_name != "":
			print "Wtf main never has container?",adjusted_containing_logic_inst_name
			sys.exit(0) 
		# Override
		new_inst_name_prepend_text = ""	
	
	func_name_2_logic = parser_state.FuncName2Logic
	logic_lookup_table_so_far = parser_state.LogicInstLookupTable
	
	# Adjust none input args for main
	if func_name_2_logic is None:
		func_name_2_logic = dict()
	
	if logic_lookup_table_so_far is None:
		new_logic_lookup_table_so_far = dict()
	else:
		new_logic_lookup_table_so_far = logic_lookup_table_so_far 
		
	if unadjusted_logic_lookup_table_so_far is None:
		unadjusted_logic_lookup_table_so_far = dict()
		
		
	# Does this speed things up?
	# NO AS IT SHOULD NOT (not doing unecessary recursive calls)
	#new_inst_name = new_inst_name_prepend_text + orig_logic_inst_name
	#if new_inst_name in unadjusted_logic_lookup_table_so_far:
	#	# Nothing to do
	#	return new_logic_lookup_table_so_far

	
	#print ""
	#print "RECURSIVE_CREATE_LOGIC_INST_LOOKUP_TABLE"
	#print "len(new_logic_lookup_table_so_far)",len(new_logic_lookup_table_so_far)	
	#print "orig_logic_func_name",orig_logic_func_name
	#print "orig_logic_inst_name",orig_logic_inst_name
	#print "new_inst_name_prepend_text",new_inst_name_prepend_text
	#print "orig_logic_inst_name in unadjusted_logic_lookup_table_so_far",orig_logic_inst_name in unadjusted_logic_lookup_table_so_far
	#print "orig_logic_func_name in func_name_2_logic",orig_logic_func_name in func_name_2_logic
	
	'''
	# Set instance for thsi submodule in lookup table	
	if (adjusted_containing_logic_inst_name,orig_logic_inst_name) in unadjusted_logic_lookup_table_so_far:
		#orig_inst_logic = copy.deepcopy(unadjusted_logic_lookup_table_so_far[(adjusted_containing_logic_inst_name,orig_logic_inst_name)])
		
		# THIS SERVES AS CHECK ON RECURSIVE LOOP?
		
		# Nothing to change?
		return new_logic_lookup_table_so_far
	'''
	
	# Is this a function parsed from C code?
	if orig_logic_func_name in func_name_2_logic:
		# Logic parsed from C files
		orig_func_logic = func_name_2_logic[orig_logic_func_name].DEEPCOPY() #copy.deepcopy(func_name_2_logic[orig_logic_func_name])
		# Create artificial inst logic with inst name from func arg
		orig_inst_logic = orig_func_logic
		orig_inst_logic.inst_name = orig_logic_inst_name
	else:
		# C built in logic (not parsed from function definitions)
		
		# Look up containing func logic for this submodule isnt
		containing_func_logic = None
		
		# Try to use full inst name of containing module
		adjusted_containing_logic_inst = new_logic_lookup_table_so_far[adjusted_containing_logic_inst_name]
		containing_logic_func_name = adjusted_containing_logic_inst.func_name
		if containing_logic_func_name in func_name_2_logic:
			containing_func_logic = func_name_2_logic[containing_logic_func_name]
			#print "1 containing_func_logic.func_name",containing_func_logic.func_name 
		
		
		
		# Containing module must not be in parsed C code
		if containing_func_logic is None:
			# Break apart the adjusted_containing_logic_inst_name
			# To find just func name 
			# Lookup containing_func_logic by name in func_name_2_logic
			#print "orig_logic_func_name",orig_logic_func_name
			#print "orig_logic_inst_name",orig_logic_inst_name
			#print "adjusted_containing_logic_inst_name",adjusted_containing_logic_inst_name
			#print "containing_logic_func_name",containing_logic_func_name
			
			# Because recursive, the upper level modules should be in lookup
			#in_dict = adjusted_containing_logic_inst_name in unadjusted_logic_lookup_table_so_far
			#print "in_dict",in_dict
			
			#sys.exit(0)
		
			containing_func_logic = unadjusted_logic_lookup_table_so_far[adjusted_containing_logic_inst_name]
		
		if containing_func_logic is not None:			
			orig_inst_logic = BUILD_C_BUILT_IN_SUBMODULE_LOGIC_INST(containing_func_logic,new_inst_name_prepend_text, orig_logic_inst_name, parser_state)
						
		else:
			# NONE contining logic>?		
			print "!!!!!!!!!!!!!!!!!"
			print "BAH! Cant find logic that contains orig_logic_inst_name",orig_logic_inst_name
			print "orig_logic_func_name",orig_logic_func_name
			print "containing inst:",adjusted_containing_logic_inst_name
			print "=== ALL NON_RAW_HDL func_name_2_logic ===="
			for func_name in func_name_2_logic:
				func_logic = func_name_2_logic[func_name]
				if len(func_logic.submodule_instances) > 0:
					print "func_name",func_name
					for submodule_inst in func_logic.submodule_instances:
						print "	submodule_inst ",submodule_inst
						
			print "=== ALL NON_RAW_HDL new_logic_lookup_table_so_far ===="
			for inst_name in new_logic_lookup_table_so_far:
				inst_logic = new_logic_lookup_table_so_far[inst_name]
				if len(inst_logic.submodule_instances) > 0:
					print "inst_name",inst_name
					for submodule_inst in inst_logic.submodule_instances:
						print "	submodule_inst ",submodule_inst
			
			sys.exit(0)
		
		
	# Save copy of orig_inst_logic before prepend
	orig_inst_logic_no_prepend = orig_inst_logic.DEEPCOPY() #copy.deepcopy(orig_inst_logic)	
	inst_logic = orig_inst_logic
	inst_logic.INST_LOGIC_ADJUST_W_PREPEND(new_inst_name_prepend_text)

	# Save this in rv
	new_logic_lookup_table_so_far[inst_logic.inst_name] = inst_logic
	

	# Since the original unadjusted instance name is not unique enough
	# Ex. A use of uint23_mux23 has a submodule MUX_layer0_node0 exactly as uint24_mux24 does so can store MUX_layer0_node0 as the inst name alone
	# Need to store containing inst too
	#unadjusted_logic_lookup_table_so_far[(adjusted_containing_logic_inst_name,orig_inst_logic_no_prepend.inst_name)] = orig_inst_logic_no_prepend
	unadjusted_logic_lookup_table_so_far[inst_logic.inst_name] = orig_inst_logic_no_prepend
	
	
	# Then recursively do submodules
	# USING local names from orig_inst_logic_no_prepend
	for orig_submodule_logic_inst_name in orig_inst_logic_no_prepend.submodule_instances:
		orig_submodule_logic_func_name = orig_inst_logic_no_prepend.submodule_instances[orig_submodule_logic_inst_name]
		submodule_c_ast_node_when_used = orig_inst_logic_no_prepend.submodule_instance_to_c_ast_node[orig_submodule_logic_inst_name]
		#print ""
		#print "RECURSIVELY DOING RECURSIVE_CREATE_LOGIC_INST_LOOKUP_TABLE"
		#submodule_new_inst_name_prepend_text = inst_logic.inst_name + SUBMODULE_MARKER
		submodule_adjusted_containing_logic_inst_name = inst_logic.inst_name
		#print "orig_submodule_logic_inst_name", orig_submodule_logic_inst_name
		#print "orig_submodule_logic_inst_name used at", C_AST_COORD_STR(submodule_c_ast_node_when_used.coord)
		#print "orig_submodule_logic_func_name",orig_submodule_logic_func_name
		#print "submodule_new_inst_name_prepend_text", submodule_new_inst_name_prepend_text
		
		parser_state.LogicInstLookupTable = new_logic_lookup_table_so_far
		
		new_logic_lookup_table_so_far = RECURSIVE_CREATE_LOGIC_INST_LOOKUP_TABLE(orig_submodule_logic_func_name, orig_submodule_logic_inst_name, parser_state, unadjusted_logic_lookup_table_so_far, submodule_adjusted_containing_logic_inst_name, submodule_c_ast_node_when_used, recursion_level)

		parser_state.LogicInstLookupTable = new_logic_lookup_table_so_far

	return new_logic_lookup_table_so_far



def GET_C_AST_FUNC_DEFS_FROM_C_CODE_TEXT(text, fake_filename):
	# Use C parser to do some lifting
	# See https://github.com/eliben/pycparser/blob/master/examples/explore_ast.py
	try:
		parser = c_parser.CParser()
		# Use preprocessor function
		c_text = preprocess_text(text)
		#print "========="
		#print "fake_filename",fake_filename
		#print "preprocessed text",c_text
		
		# Hacky because somehow parser.parse() getting filename from cpp output?
		c_text = c_text.replace("<stdin>",fake_filename)
		
		ast = parser.parse(c_text,filename=fake_filename)
		#ast.show()
	except c_parser.ParseError as pe:
		print "Parsed fake file name:",fake_filename
		print "Parsed text:"
		print c_text
		print "pycparser says you messed up here:",pe
		sys.exit(0)
	
	
	
	func_defs = GET_TYPE_FROM_LIST(c_ast.FuncDef, ast.ext)
	#if len(func_defs) > 0:
	#	print "Coord of func def", func_defs[0].coord
		
	#print "========="
	return func_defs

def GET_C_AST_FUNC_DEFS(c_filename):
	c_file_ast = GET_C_FILE_AST(c_filename)
	#c_file_ast.show()
	# children are "external declarations",
	# and are stored in a list called ext[]
	func_defs = GET_TYPE_FROM_LIST(c_ast.FuncDef, c_file_ast.ext)
	return func_defs
	
def GET_C_AST_STRUCT_DEFS(c_filename):
	c_file_ast = GET_C_FILE_AST(c_filename)

	# Get type defs
	type_defs = GET_TYPE_FROM_LIST(c_ast.Typedef, c_file_ast.ext)
	struct_defs = []
	for type_def in type_defs:
		#casthelp(type_def)
		thing = type_def.children()[0][1].children()[0][1]
		if type(thing) == c_ast.Struct:
			struct_defs.append(thing)
			
	return struct_defs
	
def GET_C_AST_ENUM_DEFS(c_filename):
	c_file_ast = GET_C_FILE_AST(c_filename)

	# Get type defs
	type_defs = GET_TYPE_FROM_LIST(c_ast.Typedef, c_file_ast.ext)
	enum_defs = []
	for type_def in type_defs:
		#casthelp(type_def)
		thing = type_def.children()[0][1].children()[0][1]
		if type(thing) == c_ast.Enum:
			enum_defs.append(thing)
	#print enum_defs
	#sys.exit(0)		
	return enum_defs
	
def GET_C_AST_GLOBALS(c_filename):
	c_file_ast = GET_C_FILE_AST(c_filename)
	#c_file_ast.show()
	
	# Get type defs
	variable_defs = GET_TYPE_FROM_LIST(c_ast.Decl, c_file_ast.ext)
	
	# Filter OUT volatile
	non_volatile_global_defs = []
	for variable_def in variable_defs:
		#print variable_def
		#print variable_def.quals
		if 'volatile' not in variable_def.quals:
			non_volatile_global_defs.append(variable_def)
	
	#print variable_defs
	#sys.exit(0)
		
	return non_volatile_global_defs
	
def GET_C_AST_VOLATILE_GLOBALS(c_filename):
	c_file_ast = GET_C_FILE_AST(c_filename)
	#c_file_ast.show()
	#print c_file_ast.ext
	#sys.exit(0)
	# Get type defs
	variable_defs = GET_TYPE_FROM_LIST(c_ast.Decl, c_file_ast.ext)
	
	# Filter TO volatile
	volatile_global_defs = []
	for variable_def in variable_defs:
		#print variable_def
		#print variable_def.quals
		if 'volatile' in variable_def.quals:
			volatile_global_defs.append(variable_def)
		
	#sys.exit(0)
	
	#print variable_defs
	#sys.exit(0)
		
	return volatile_global_defs

# Filter out a certain type from a list
# Im dumb at python
def GET_TYPE_FROM_LIST(py_type, l):
	rv = []
	for i in l:
		if type(i) == py_type:
			rv.append(i)
	return rv
	
	
def GET_C_FILE_AST(c_filename):
	try:
		# Use C parser to do A WHOLE LOT OF lifting
		# See https://github.com/eliben/pycparser/blob/master/examples/explore_ast.py
		parser = c_parser.CParser()
		# Use preprocessor function
		c_text = preprocess_file(c_filename)
		
		# Hacky because somehow parser.parse() getting filename from cpp output?
		c_text = c_text.replace("<stdin>",c_filename)
		
		#print "PREPROCESSED:"
		#print c_text
		# Catch pycparser exceptions
		ast = parser.parse(c_text,filename=c_filename)
	except c_parser.ParseError as pe:
		print "Parsed file:",c_filename
		print "Parsed text:"
		print c_text
		print "pycparser says you messed up here:",pe
		sys.exit(0)
	#ast.show()
	return ast

	
	
		
	
