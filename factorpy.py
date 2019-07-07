import operator as op
import math, re,time, importlib
import standard_lib, utils
#Big todo's

#Make labels for when the same factory is called twice but under different circumstances
	#Make it assume that if a single input factory is called twice that it should be given a seperate label

#Make the system for defining factories, im thinking that to add a function call to a user defined factory it should work like this
	#User defines the factory
	#Gets parsed as normal, with special storage placeholders for inputs
	#Storage+Factories gets stored somewhere
	#When that factory gets called it pulls out the list of factories, shifts the storage array to make it fit (or just have multiple seperate storages since the factory is completely seperate)
	#And then it adds the factories from the def into the current list of running factories

#Comment the code properly, since the first pass was super quick and jank, especially setup_for_eval

#Get multiple output functions working, should be a mirror of how I got multiple inputs working

#Small Todo's
#make 1-> special()[0] ->print() possible??

DEBUG = True

def section(lines):
	cons_section = []
	rule_section = []
	imports = []
	factory_defs = {} #key = factory name, value = standard sections list
	current_factory_name = None
	in_factory_def = False
	for line in lines:
		if in_factory_def:
			line = line.strip()
			if line[:3] == "let":
				factory_defs[current_factory_name][0].append(line)
			elif line[:6] == "import":
				factory_defs[current_factory_name][2].append(line)
			elif line == "}":
				in_factory_def = False
			else:
				factory_defs[current_factory_name][1].append(line)
		else:
			if line[:3] == "let":
				cons_section.append(line)
			elif line[:6] == "import":
				imports.append(line)
			elif line[:7] == "factory":
				parts = line.split()
				current_factory_name = parts[1][:-3]
				factory_defs[current_factory_name] = [[],[],[]]
				in_factory_def = True
			else:
				rule_section.append(line)
	return (cons_section,rule_section,imports), factory_defs

def parse_constants(c_lines, in_factory_def = False):
	cons_dict = {}
	#print(v_lines)
	for line in c_lines:
		line = line[3:]
		name, value = line.split("=")
		if not in_factory_def:
			value = atom(value,cons_dict)
		else:
			value = atom_for_factory_defs(value,cons_dict)
		cons_dict[name.strip()] = value
	#print(var_dict)
	return cons_dict

def parse_rules(lines,in_factory_def=False):
	rules = []
	for line in lines:
		parts  = line.split("->")
		for i in range(len(parts)-1):
			if parts[i] == "in":
				parts[i] = utils.in_identifier
			if parts[i+1] == "out":
				parts[i+1] = utils.out_identifier 
			rule = {
				'from':parts[i],
				'to':parts[i+1]
			}
			rules.append(rule)
	return rules

def standard_env():
	env = {}
	env.update({
	    'print':(print,1,False),
	    '+':(op.add,2,False),
	})
	return env

def import_special(env,i_lines):
	utils.update_env(env, importlib.import_module("standard_lib")) #always import the standard_lib first because things get overwritten
	for line in i_lines:
		filename = line.replace("import","").replace(".py","").strip()
		if DEBUG:
			print("importing:",filename)
		f = importlib.import_module(filename)
		env = utils.update_env(env,f)
	return env

def generate_factory(fact_str):
	fact_str = fact_str.strip()
	fact_str,label = fact_str.split("()")
	#fact_str+="()" #maybe, not sure
	try:
		#if DEBUG:
			#print("Generating factory for name=",fact_str,"info in env=",env[fact_str])
		fn, number_of_inputs, is_factory = env[fact_str]
		return fn, number_of_inputs,label, is_factory
	except KeyError:
		raise SyntaxError("No function in current env called:"+fact_str)

def atom_for_factory_defs(x, constants):
	if x.strip() == "in":
		return utils.in_identifier
	if x.strip() == "out":
		return utils.out_identifier
	else:
		return atom(x,constants)
#Whistles nervously
def atom(x, constants):
	try: 
		val = int(x)
	except ValueError:
		try: val = float(x)
		except ValueError:
			try: val = constants[x]
			except KeyError: 
				try: val = utils.parse_list(x)
				except ValueError:
					s = re.search("\"*\"",x)
					if s == None:
						raise SyntaxError("No variable found with name, "+x)
					else:
						val = x.replace("\"","").replace("'","") #String, get rid of the quotes
	return val

#Converts a list of rules to a list of factories and it's associated storage
def setup_for_eval(rules,constants, encaped_facts, in_factory_def=False):
	factories = []
	input_id = 0
	cur_storage_size = 256
	storage = [0]*cur_storage_size #where the inputs are going to be stored, current storage size is 256
	output_id = 50 # this has gotta be big, need a system for dynamically increasing output_id and storage size for when things get big
	in_out_ports = {
		'in':[],
		'out':[]
	}
	for rule in rules:
		if input_id >= 256 or output_id >=256:
			raise Exception("Not enough storage space, calm down with all those pipes")
		r_from = rule['from'].strip()
		r_to = rule['to'].strip()

		#Setup/update the destination factory
		if r_to.find("()") != -1:
			fixed_fact_str = r_to
			in_num = None #This stays as nonetype if the function call did not specify which input it wanted to go to
			#check if r_to has [factory_input] syntax
			x = re.search("\[*\]",r_to)
			if x != None:
				fixed_fact_str = r_to[0:x.span()[0]-2]
				in_num = int(r_to[x.span()[0]-1:x.span()[1]-1])
				#if DEBUG:
					#print("weirdo, fixed=",fixed_fact_str,"in_num=",in_num)

			#check if the factory alredy exists
			l = [x if x['name'] == fixed_fact_str else None  for x in factories]
			i=0
			exists = False
			#updated_factory = None
			for x in l:
				if x != None:
					#Match, append on the input_id
					x['in_id'].append(input_id)
					x['id_to_in_num'].append(in_num)
					#factories[i] = x
					data = x
					exists = True
					#if DEBUG:
						#print("adding input to factory "+x['name']+ " new in_id = ",input_id)
					break
				i+=1

			skip = False
			if not exists:
				factory, input_num, label, is_factory = generate_factory(fixed_fact_str)
				if is_factory:
					internal_facts, internal_storage, in_out_ports = factory

					#Append the storage from the factory info onto the current storage
					storage = storage + internal_storage
					for fact in internal_facts:
						fact['in_id'] = [x + cur_storage_size for x in fact['in_id']]
						fact['out_id'] += cur_storage_size
					factories +=internal_facts
					data = {
						'in_id':[x + cur_storage_size for x in in_out_ports['in']],
						'out_id':in_out_ports['out']+cur_storage_size,
					}
					skip = True
				else:
					input_list = [input_id]
					data = {
						'name':fixed_fact_str,
						'fact': factory,
						'in_id': input_list, #the port it is waiting on 
						'out_id': output_id, #the port it outputs on
						'status':'waiting',
						'in_num':input_num, #the number of inputs it's expecting
						'id_to_in_num':[in_num],
						'num_waiting':input_num
						#Todo: Implement labels for the different factories
						#TODO: Add a number that represents the number of input's it's currently waiting for
					}
			input_id+=1
			output_id+=1
		else:
			if in_factory_def and r_to == "out":
				in_out_ports['out'] = data['out_id'] #when defining an internal factory we also return a dict of the in/out ports which we use for when we use the internal fact later
			else:
				raise SyntaxError("error, cannot pipe into non-function")

		#Setup the from_factory/atom
		if r_from.find("()") == -1:
			#If r_from is a constant

			#Is this an internal factory def?
			if in_factory_def:

				val = atom_for_factory_defs(r_from,constants)
				#print("internal val",val)

				if val == utils.in_identifier: #We want to keep track of which ports the factory wants to in and out to for later
					in_out_ports['in'].append(data['in_id'][-1])

				elif val == utils.out_identifier:
					raise SyntaxError("Can't pipe in from an outwards port")
				else:
					storage[data['in_id'][-1]] = val
					data['num_waiting']-=1

			#if not then:
			else:
				val = atom(r_from,constants)

				#Are we dealing with an input going into an internal factory?
				if skip:
					new_inputs = []
					for in_id in data['in_id']:
						storage[in_id] = val
						new_inputs.append(in_id)

					#Set all the factories that were waiting for those values to gogogo
					for i in range(len(internal_facts)):
						fact = factories[-1*(i+1)] #this loops through all the new factories that were added as part of the new internal one
						for in_id in fact['in_id']:
							if in_id in new_inputs:
								fact['num_waiting']-=1
							if fact['num_waiting'] <= 0:
								fact['status']= 'ready'

				#if not
				else:
					storage[data['in_id'][-1]] = val
					data['num_waiting']-=1
					if data['num_waiting'] <= 0:
						data['status'] = 'ready' 
		else:
			try:
				r_from = r_from.strip()
				waiting_for = None
				for fact in factories:
					if fact['name'] == r_from:
						waiting_for = fact
				data['in_id'][-1] = waiting_for['out_id']

			except TypeError:
				good = False
				for i_fact in encaped_facts:
					#print("COMAPRE THESE",i_fact['name'],r_from)
					if i_fact['name'] == r_from:
						data['in_id'][-1] = i_fact['out_id']
						good = True
				if not good:
					raise SyntaxError("Cannot wait for input from non-existant factory")
		if not skip:
			if not exists:
				factories.append(data)
			else:
				factories[i] = data
	if in_factory_def:
		return factories, storage, in_out_ports
	else:
		return factories, storage

#TODO: make this multithreaded!! that is the main point of the language after all
def eval(facts,storage):
	new_outputs = []
	while True:
		if DEBUG:
			utils.pretty_print(facts,storage)

		if utils.all_waiting(facts):
			print("All factories have stopped, halting evaluation")
			break
		else:
			for factory in facts:
				if factory['status'] == 'ready':
					going_in = [storage[i] for i in factory['in_id']]
					if len(going_in) != factory['in_num']:
						raise SyntaxError("Number of inputs does not match number of inputs required by factory")
					if factory['id_to_in_num'][0] != None:
						#print("reordering going_in")
						new_going_in = [0]*factory['in_num']
						count = 0
						try:
							for index in factory['id_to_in_num']:
								new_going_in[index] = going_in[count]
								count+=1
						except TypeError:
							raise SyntaxError("If one input is specified, then they all need to be specified")
						except IndexError:
							raise SyntaxError("Are you sure you specified the right inputs? Remember that inputs start from 0")
						going_in = new_going_in
					res = factory['fact'](*going_in)
					if DEBUG:
						print(factory['name'],"res=",res)
					storage[factory['out_id']] = res
					factory['status'] = 'waiting'
					new_outputs.append(factory['out_id'])

			for factory in facts:
				for potential in new_outputs: #TODO: make this work for when it's waiting for multiple inputs
					if potential in factory['in_id']:
						factory['num_waiting']-=1
						if factory['num_waiting'] == 0:
							factory['status'] = 'ready'
			new_outputs = []
			#time.sleep(10) #ITS GOING TOOO FAST, SLOW IT DOWN

f = open("test_encap.fl")
sections,factory_defs = section(f.readlines())

if DEBUG:
	print("sections=",sections)
	print("factory defs=",factory_defs)

global_constants = parse_constants(sections[0])
global_rules = parse_rules(sections[1])
env = standard_env()
env = import_special(env,sections[2])

internal_facts = []
if DEBUG:
	print("global rules =",global_rules)
	print("global constants = ",global_constants)

for f_name, (f_constants,f_rules,f_imports)in zip(factory_defs.keys(),factory_defs.values()):
	const = parse_constants(f_constants,True)
	#print(f_constants)
	rules = parse_rules(f_rules,True)
	#env = utils.add_factory(env,f_name)
	if DEBUG:
		print("factory constants",const)
		print("factory rules",rules)
	#uhh not sure what to do about the env right now...
	#probably just don't allow local only imports?

	#create the portable factory
	facts, storage, in_out_ports = setup_for_eval(rules,const, internal_facts, True) #FUCK IT CAN'T RECURSE IF I DO IT LIKE THIS FUCK FUCKFUCKITY FUCK
	print("list of internal factories",facts)
	if DEBUG:
		print("previewing internal factory, name=",f_name)
		utils.pretty_print(facts,storage)
		print("internal factory is waiting for ",in_out_ports['in'])
		print("internal factory is sending to ",in_out_ports['out'])

	internal_fact = {
		'name':f_name+"()",
		'in_id':in_out_ports['in'],
		'out_id':in_out_ports['out']
	}
	internal_facts.append(internal_fact)

	env[f_name] = (facts,storage,in_out_ports),1,True

print("list of internal facts:",internal_facts)

global_facts,global_storage = setup_for_eval(global_rules,global_constants, internal_facts)

print("-"*10+"starting evalutation"+"-"*10)
eval(global_facts,global_storage)

