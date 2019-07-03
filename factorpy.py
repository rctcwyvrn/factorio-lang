import operator as op
import math, re,time

#Big todo's

#Make labels for when the same factory is called twice but under different circumstances
	#Make it assume that if a single input factory is called twice that it should be given a seperate label

#Make the system for defining factories
#Comment the code properly, since the first pass was super quick and jank, especially setup_for_eval


#Small Todo's
#make 1-> special()[0] ->print() possible??
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

def standard_env():
	env = {}
	env.update(vars(math)) # sin, cos, sqrt, pi, ...
	env.update({
	    'print()':(print,1),
	    'plus()':(op.add,2),
	    'special()':(special,2)
	})
	return env

def generate_factory(fact_str):
	fact_str = fact_str.strip()
	try:
		fn, number_of_inputs = env[fact_str]
		return fn, number_of_inputs
	except KeyError:
		raise SyntaxError("No function in current env called:"+fact_str)

def setup_for_eval(rules):
	factories = []
	input_id = 0
	storage = [0]*256 #where the inputs are going to be stored, current storage size is 256
	output_id = 0
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
				print("weirdo, fixed=",fixed_fact_str,"in_num=",in_num)

			#check if the factory alredy exists
			l = [x if x['name'] == fixed_fact_str else None  for x in factories]
			i=0
			exists = False
			for x in l:
				if x != None:
					#Match, append on the input_id
					x['in_id'].append(input_id)
					x['id_to_in_num'].append(in_num)
					factories[i] = x
					exists = True
					break
				i+=1

			if not exists:
				factory, input_num = generate_factory(fixed_fact_str)
				input_list = [input_id]
				data = {
					'name':fixed_fact_str,
					'fact': factory,
					'in_id': input_list, #the port it is waiting on 
					'out_id':output_id, #the port it outputs on
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
			storage[data['in_id'][-1]] = int(r_from) #THIS IS JANK AND TEMPORARY
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
	return factories, storage

#TODO: make this multithreaded!! that is the main point of the language after all
def eval(facts,storage):
	new_outputs = []
	loops = 0
	while loops < 10:
		#print(facts)
		for factory in facts:
			if factory['status'] == 'ready':
				going_in = [storage[i] for i in factory['in_id']]
				if len(going_in) != factory['in_num']:
					raise SyntaxError("Number of inputs does not match number of inputs required by factory")
				if factory['id_to_in_num'][0] != None:
					print("reordering going_in")
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
rules = parse_rules(f.readlines())
env = standard_env()
#print(env["print()"][0]("holy shit that works"))
print("rules =",rules)
facts,storage = setup_for_eval(rules)

print("-"*10+"starting evalutation"+"-"*10)
eval(facts,storage)

