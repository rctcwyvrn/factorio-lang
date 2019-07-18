import operator as op
import math, re,time, importlib
import standard_lib, utils

#Big todo's

#Make labels for when the same factory is called twice but under different circumstances
	#Make it assume that if a single input factory is called twice that it should be given a seperate label

#Make the system for defining factories is readable and not a buggy mess
	#because that's what it is right now
	#Currently not working: multiple inputs, recursion, multiple outputs in general

#Comment the code properly, since the first pass was super quick and jank, especially generate_IR

#Get multiple output functions working, should be a mirror of how I got multiple inputs working

#Make special in/out functions that pipe into everything that is waiting on an identifier
	#Makes the rule checking for later so much easier

#Figure out where I'm supposed to be stripping the values, because holy fuck why are they everywhere

DEBUG = False #Show whats happening behind the scenes during evaluation
DETAILED_DEBUG = False #Show whats happening behind the scenes during parsing and setup

def section(lines):
	cons_section = []
	rule_section = []
	imports = []
	factory_defs = {} #key = factory name, value = standard list of sections
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
		line = line[3:].strip() #get rid of the let
		name, value = line.split("=")
		if not in_factory_def:
			value = atom(value,cons_dict)
		else:
			value = atom_for_factory_defs(value,cons_dict) #the only thing that is different is that this will return the in_identifier and out_identifier functions for "in" and "out"
		cons_dict[name.strip()] = value
	#print(var_dict)
	return cons_dict

def parse_rules(lines,in_factory_def=False):
	rules = []
	for line in lines:
		parts  = line.split("->")
		for i in range(len(parts)-1):
			if parts[i].strip() == "in" and in_factory_def:
				parts[i] = utils.in_identifier
			if parts[i+1].strip() == "out" and in_factory_def: #Replace "in"/"out" in functions with the identifiers
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
		if DETAILED_DEBUG:
			print("generate_factory(): For name=",fact_str)
		fn, number_of_inputs, is_factory = env[fact_str]
		return fn, number_of_inputs,label, is_factory
	except KeyError:
		raise SyntaxError("No function in current env called:"+fact_str)

def atom_for_factory_defs(x, constants):
	if x == utils.in_identifier or x == utils.out_identifier:
		return x
	x = x.strip()
	if x == "in":
		return utils.in_identifier
	if x == "out":
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

def check_input_syntax(r_to):
	fixed_fact_str = r_to
	in_num = None
	x = re.search("\[*\]",r_to)
	if x != None:
		fixed_fact_str = r_to[0:x.span()[0]-2]
		in_num = int(r_to[x.span()[0]-1:x.span()[1]-1]) #in_num specifies which port
		if DETAILED_DEBUG:
			print("generate_IR(): input port specified, fixed=",fixed_fact_str,"in_num=",in_num,'\n')
	return fixed_fact_str, in_num

def search_and_add_id(factories, fixed_fact_str, input_id, in_num):
	factory_names = [x if x['name'] == fixed_fact_str else None for x in factories]
	factory_match_index=0
	exists = False
	data = None
	for x in factory_names:
		if x != None:
			#Found a match, append on the input_id
			x['in_id'].append(input_id)
			x['id_to_in_num'].append(in_num)

			data = x
			exists = True

			if DETAILED_DEBUG:
				print("generate_IR(): adding input to factory "+x['name']+ " new in_id = ",input_id,'\n')

			break
		factory_match_index+=1
	return exists, data, factory_match_index

def make_new_factory(input_id, output_id, fixed_fact_str, factories, storage, input_port):
	going_to_factory = False
	factory, input_num, label, is_factory = generate_factory(fixed_fact_str) #is_factory if the r_to is a user defined factory

	num_new_factories = 0
	#if it is a user defined factory
	if is_factory:
		internal_facts, internal_storage, in_out_ports = factory

		#Append the storage from the factory info onto the current storage
		storage = storage + internal_storage
		for fact in internal_facts:
			#Shift the in_id and out_id to match
			fact['in_id'] = [x + cur_storage_size for x in fact['in_id']]
			if not fact['out_id'] == in_out_ports['out']: #except for the out_port, i don't know what to do about that yet
				fact['out_id'] += cur_storage_size

		#Append on the factories
		factories +=internal_facts

		#Make a dummy data value to use for r_from and specify that it should NOT be appended to the list of factories at the end
		data = {
			'in_id':[x + cur_storage_size for x in in_out_ports['in']],
			'out_id':in_out_ports['out']+cur_storage_size,
		}
		going_to_factory = True
		num_new_factories = len(internal_facts)

	#If it is not a user defined factory and does exist
	else:
		input_list = [input_id]
		data = {
			'name':fixed_fact_str,
			'fact': factory,
			'in_id': input_list, #the port it is waiting on 
			'out_id': output_id, #the port it outputs on
			'status':'waiting',
			'in_num':input_num, #the number of inputs it's expecting
			'id_to_in_num':[input_port],
			'num_waiting':input_num
		}
	return data, going_to_factory, num_new_factories, factories, storage

def send_const_to_new_factories(val, factories, storage, num_new_factories, dummy_data):
		#TODO: Make this work with [] notation to allow factories to take different inputs and stuff, because right now it can only ever take one
	new_inputs = []
	for in_id in dummy_data['in_id']:
		storage[in_id] = val #add val to storage for every spot that the internal factory was waiting for inputs
		new_inputs.append(in_id)

	#Set all the factories that were waiting for those values to gogogo
	for i in range(num_new_factories):
		fact = factories[-1*(i+1)] #this loops through all the new factories that were added as part of the new internal one (i hope)
		for in_id in fact['in_id']:

			if in_id in new_inputs:
				fact['num_waiting']-=1

			if fact['num_waiting'] <= 0:
				fact['status']= 'ready'
		factories[-1*(i+1)] = fact 
	return factories, storage

cur_storage_size = 256
def generate_encap_IR(rules,constants,encaped_facts):
	factories = []
	input_id = 0
	storage = [0]*cur_storage_size #where the inputs are going to be stored, current storage size is 256
	output_id = 50 # this has gotta be big, need a system for dynamically increasing output_id and storage size for when things get big

	in_out_ports = {
		'in':[],
		'out':[]
	}
	if DETAILED_DEBUG:
		print("ENCAP RULES: ",rules)
	for rule in rules:
		if DETAILED_DEBUG:
			print("RULE: ",rule)
		if input_id >= 256 or output_id >=256:
			raise Exception("Not enough storage space, calm down with all those pipes")

		r_from = rule['from']#.strip()
		r_to = rule['to']#.strip()

		#Setup/update the destination factory
		if DETAILED_DEBUG:
			print("generate_encap_IR(): setting up r_to=",r_to,'\n')

		sending_to_encap_out = False
		if not callable(r_to) and r_to.find("()") != -1:

			r_to = r_to.strip()

			#check if r_to has [factory_input] syntax
			fixed_fact_str, in_port_number = check_input_syntax(r_to)

			#check if the factory alredy exists, add the current in id if so
			#return a dummy new_factory with in_id/out_id values only and a match index if it exists
			exists, new_factory, factory_match_index = search_and_add_id(factories, fixed_fact_str, input_id, in_port_number)

			#If the factory does not yet exist
			if not exists:
				new_factory, going_to_factory, num_new_factories, factories, storage = make_new_factory(input_id, output_id, fixed_fact_str, factories, storage, in_port_number)

			input_id+=1 #make sure the id's remain unique
			output_id+=1

		else: #r_to was either an identifier or didn't have ()
			if r_to == utils.out_identifier:
				sending_to_encap_out = True #sending to the out pipe of the encapsulated factory
			else:
				raise SyntaxError("error, cannot pipe into non-function r_to = "+r_to)

		if DETAILED_DEBUG:
			print("generate_encap_IR(): setting up r_from=",r_from)

		#Setup the r_from factory/atom
		if callable(r_from) or r_from.find("()") == -1:
			#If r_from is a constant or is an identifier
			val = atom_for_factory_defs(r_from,constants)

			if val == utils.in_identifier: #We want to keep track of which ports the factory wants to in and out to for later
				in_out_ports['in'].append(new_factory['in_id'][-1]) #in_id represents the shifted port that the newly added factories are waiting for
				val = None #wipe the value

			elif val == utils.out_identifier:
				raise SyntaxError("Can't pipe in from an outwards port")

			
			if val != None: #Skip this section if val was an identifier

				if going_to_factory: #Are we dealing with an input going _into_ an internal factory?
					#if so then we need to add the input 
					factories, storage = send_const_to_new_factories(val, factories, storage, num_new_factories, new_factory)

				#if not going to an internal factory
				else:
					storage[new_factory['in_id'][-1]] = val #update the latest in_id added, which should correspond to the latest one
					new_factory['num_waiting']-=1
					if new_factory['num_waiting'] <= 0:
						new_factory['status'] = 'ready' 
		else:
			#if r_from is a function string
			r_from = r_from.strip()
			#see if it exists in the current list of factories
			waiting_for = None
			for fact in factories:
				if fact['name'] == r_from:
					waiting_for = fact

			if waiting_for == None:
				#didnt find it
				#see if it exists in the list of defined encapsulated factories
				good = False
				for i_fact in encaped_facts:
					if i_fact['name'] == r_from:
						waiting_for = i_fact
						good = True

				#See if this is recursion? TODO
				pass 

				if not good:
					raise SyntaxError("Cannot wait for input from non-existant factory")

			if sending_to_encap_out:
				in_out_ports['out'] = waiting_for['out_id']
				skip = True
				if DETAILED_DEBUG:
					print("generate_encap_IR(): final out factory is ", waiting_for['name'], " sending to ",waiting_for['out_id'])
			else:	
				if DETAILED_DEBUG:
					print("generate_encap_IR(): changing ",new_factory['name'], " to be waiting for ", waiting_for['name'], " at ",waiting_for['out_id'])

				new_factory['in_id'][-1] = waiting_for['out_id']

					

		#only consider adding the new factory if r_to was not an encapsulated factory
		if not going_to_factory:
			if not exists:
				#Append the new factory if it didnt already exist
				factories.append(new_factory)
			else:
				#otherwise just update it's value
				factories[factory_match_index] = new_factory

	return factories, storage, in_out_ports

#Converts a list of rules to a list of factories and it's associated storage
#Man this really got out of control real fast
def generate_IR(rules,constants, encaped_facts):
	if DETAILED_DEBUG:
		print("GLOBAL RULES: ",rules)
	factories = []
	input_id = 0
	cur_storage_size = 256
	storage = [0]*cur_storage_size #where the inputs are going to be stored, current storage size is 256
	output_id = 50 # this has gotta be big, need a system for dynamically increasing output_id and storage size for when things get big

	for rule in rules:
		if DETAILED_DEBUG:
			print("RULE: ",rule)
		if input_id >= 256 or output_id >=256:
			raise Exception("Not enough storage space, calm down with all those pipes")

		r_from = rule['from']#.strip()
		r_to = rule['to']#.strip()

		#Setup/update the destination factory
		if DETAILED_DEBUG:
			print("generate_IR(): setting up r_to=",r_to,'\n')

		if r_to.find("()") != -1:

			r_to = r_to.strip()

			#check if r_to has [factory_input] syntax
			fixed_fact_str, in_num = check_input_syntax(r_to)

			#check if the factory alredy exists
			exists, new_factory, factory_match_index = search_and_add_id(factories, fixed_fact_str, input_id, in_num)

			#If the factory does not yet exist
			if not exists:
					new_factory, going_to_factory, num_new_factories, factories, storage = make_new_factory(input_id, output_id, fixed_fact_str, factories, storage,in_num)

			input_id+=1 #make sure the id's remain unique
			output_id+=1

		else: #r_to was either an identifier or didn't have ()
			raise SyntaxError("error, cannot pipe into non-function r_to = "+r_to)

		if DETAILED_DEBUG:
			print("generate_IR(): setting up r_from=",r_from)

		#Setup the r_from factory/atom
		if r_from.find("()") == -1:
			#If r_from is a constant or is an identifier
			val = atom(r_from.strip(),constants)

			if going_to_factory: #Are we dealing with an input going _into_ an internal factory?
				#if so then we need to add the input 
				factories, storage = send_const_to_new_factories(val, factories, storage, num_new_factories, new_factory)

			#if not going to an internal factory
			else:
				storage[new_factory['in_id'][-1]] = val #update the latest in_id added, which should correspond to the latest one
				new_factory['num_waiting']-=1
				if new_factory['num_waiting'] <= 0:
					new_factory['status'] = 'ready' 
		else:
			#if r_from is a function
			r_from = r_from.strip()
			#see if it exists in the current list of factories
			waiting_for = None
			for fact in factories:
				if fact['name'] == r_from:
					waiting_for = fact

			if waiting_for == None:
					#didnt find it
					#see if it exists in the list of defined encapsulated factories
					good = False
					for i_fact in encaped_facts:
						if i_fact['name'] == r_from:
							waiting_for = i_fact
							good = True

					#See if this is recursion? TODO
					pass 

					if not good:
						raise SyntaxError("Cannot wait for input from non-existant factory")
			
			new_factory['in_id'][-1] = waiting_for['out_id']
			
		#only consider adding the new factory if r_to was not an encapsulated factory
		if not going_to_factory:
			if not exists:
				#Append the new factory if it didnt already exist
				factories.append(new_factory)
			else:
				#otherwise just update it's value
				factories[factory_match_index] = new_factory

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


					res = factory['fact'](*going_in) #where the magic happens

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

def run_file(f):
	sections,factory_defs = section(f.readlines())

	if DETAILED_DEBUG:
		print("sections=",sections)
		print("factory defs=",factory_defs)

	global_constants = parse_constants(sections[0])
	global_rules = parse_rules(sections[1])

	global env
	env = standard_env()
	env = import_special(env,sections[2])

	internal_facts = []
	if DETAILED_DEBUG:
		print("global rules =",global_rules)
		print("global constants = ",global_constants,'\n')

	for f_name, (f_constants,f_rules,f_imports)in zip(factory_defs.keys(),factory_defs.values()):
		if DETAILED_DEBUG:
			print("-"*10 + "setting up factory f_name=",f_name,"-"*10)
		const = parse_constants(f_constants,True)
		#print(f_constants)
		rules = parse_rules(f_rules,True)
		#env = utils.add_factory(env,f_name)
		if DETAILED_DEBUG:
			print("factory constants",const)
			print("factory rules",rules,'\n')
		#uhh not sure what to do about the env right now...
		#probably just don't allow local only imports?

		#create the portable factory
		facts, storage, in_out_ports = generate_encap_IR(rules,const, internal_facts) #FUCK IT CAN'T RECURSE IF I DO IT LIKE THIS FUCK FUCKFUCKITY FUCK
		#print("list of internal factories",facts)
		if DETAILED_DEBUG:
			utils.pretty_print(facts,storage)
			print("internal factory is waiting for ",in_out_ports['in'])
			print("internal factory is sending to ",in_out_ports['out'],'\n')
			print("-"*40)

		internal_fact = {
			'name':f_name+"()",
			'in_id':in_out_ports['in'],
			'out_id':in_out_ports['out']
		}
		internal_facts.append(internal_fact)

		env[f_name] = (facts,storage,in_out_ports),1,True

	#print("list of internal facts:",internal_facts)

	global_facts,global_storage = generate_IR(global_rules,global_constants, internal_facts)

	print("-"*10+"starting evalutation"+"-"*10)
	eval(global_facts,global_storage)

f = open("test_encap2.fl")
env = None
run_file(f)

f = open("test2.fl")
env = None
run_file(f)