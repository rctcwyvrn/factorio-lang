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

DEBUG = False

def section(lines):
	cons_section = []
	rule_section = []
	imports = []
	for line in lines:
		if line[:3] == "let":
			cons_section.append(line)
		elif line[:6] == "import":
			imports.append(line)
		else:
			rule_section.append(line)
	return cons_section,rule_section,imports

def parse_constants(c_lines):
	cons_dict = {}
	#print(v_lines)
	for line in c_lines:
		line = line[3:]
		name, value = line.split("=")
		value = atom(value,cons_dict)
		cons_dict[name.strip()] = value
	#print(var_dict)
	return cons_dict

def parse_rules(lines):
	rules = []
	for line in lines:
		parts  = line.split("->")
		for i in range(len(parts)-1):
			rule = {
				'from':parts[i],
				'to':parts[i+1]
			}
			rules.append(rule)
	return rules

def special(a,b):
	return a+3*b

def all_waiting(facts):
	res = True
	for fact in facts:
		res = res and fact['status'] == "waiting"
	return res
def standard_env():
	env = {}
	env.update(vars(math)) # sin, cos, sqrt, pi, ...
	env.update({
	    'print':(print,1),
	    'plus':(op.add,2),
	    'special':(special,2)
	})
	#env.update(standard_lib.env_data)
	return env

def import_special(env,i_lines):
	for line in i_lines:
		filename = line.replace("import","").replace(".py","").strip()
		if DEBUG:
			print("importing:",filename)
		f = importlib.import_module(filename)
		env = utils.update_env(env,f)
	utils.update_env(env, importlib.import_module("standard_lib"))
	return env

def generate_factory(fact_str):
	fact_str = fact_str.strip()
	fact_str,label = fact_str.split("()")
	#fact_str+="()" #maybe, not sure
	try:
		fn, number_of_inputs = env[fact_str]
		return fn, number_of_inputs,label
	except KeyError:
		raise SyntaxError("No function in current env called:"+fact_str)
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
						val = x.replace("\"","")
	return val

#Converts a list of rules to a list of factories and it's associated storage
def setup_for_eval(rules,constants):
	factories = []
	input_id = 0
	storage = [0]*256 #where the inputs are going to be stored, current storage size is 256
	output_id = 50 # this has gotta be big, need a system for dynamically increasing output_id and storage size for when things get big
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
				if DEBUG:
					print("weirdo, fixed=",fixed_fact_str,"in_num=",in_num)

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
					if DEBUG:
						print("adding input to factory "+x['name']+ " new in_id = ",input_id)
					break
				i+=1

			if not exists:
				factory, input_num, label = generate_factory(fixed_fact_str)
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
			raise SyntaxError("error, cannot pipe into non-function")

		#Setup the from_factory
		if r_from.find("()") == -1:
			#storage[data['in_id'][-1]] = int(r_from)
			#storage[data['in_id'][-1]] = utils.parse_list(r_from)#THIS IS JANK AND TEMPORARY :: the int part, the other part is pretty smart
			val = atom(r_from,constants)
			storage[data['in_id'][-1]] = val
			data['num_waiting']-=1
			if data['num_waiting'] == 0:
				data['status'] = 'ready' 
		else:
			try:
				waiting_for = None
				for fact in factories:
					if fact['name'] == r_from:
						waiting_for = fact
				data['in_id'][-1] = waiting_for['out_id']
			except TypeError:
				raise SyntaxError("Cannot wait for input from non-existant factory")

		if not exists:
			factories.append(data)
		else:
			factories[i] = data
	return factories, storage

#TODO: make this multithreaded!! that is the main point of the language after all
def eval(facts,storage):
	new_outputs = []
	loops = 0
	while loops < 10:
		#print(facts)
		#print(storage)
		if DEBUG:
			utils.pretty_print(facts,storage)
		if all_waiting(facts):
			print("All factories have stopped, halting evaluation")
			loops = 99
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
			loops+=1
			new_outputs = []
			#time.sleep(10)

f = open("test.fl")
sections = section(f.readlines())

constants = parse_constants(sections[0])
rules = parse_rules(sections[1])
env = standard_env()
env = import_special(env,sections[2])

if DEBUG:
	print("rules =",rules)
facts,storage = setup_for_eval(rules,constants)

print("-"*10+"starting evalutation"+"-"*10)
eval(facts,storage)

