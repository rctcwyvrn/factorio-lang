import inspect

def in_identifier():
	print("you arent supposed to be here")
def out_identifier():
	print("you arent supposed to be here")

def parse_list(list_str):
	out = []
	building = ""
	for char in list_str:
		if char != "["  and char != "]":
			if char != ",":
				building+=char
			else:
				t = int(building)
				out.append(t)
				building = ""
	out.append(int(building))
	return out

def pretty_print(facts,storage):
	print("-"*10 + "factories" + "-"*30)
	for factory in facts:
		status_line = ""
		status_line += factory['name'] +" "*(32-len(factory['name']+factory['status'])) + factory['status']
		if factory['status'] == "waiting":
			status_line += "\t\t"+"listening to ports " + str(factory['in_id'])
		else:
			status_line += "\t\t"+"sending to " + str(factory['out_id']) + ", consuming storage indexes= " + str(factory['in_id'])
		print(status_line)
	#print("-"*20)
	print("-"*10 + "storage" + "-"*10)
	print("index in storage, value")
	index = 0
	to_print = []
	for val in storage:
		if val != 0:
			to_print.append((index,val))
		index+=1
	for line in to_print:
		print(line)
	print("-"*40)

def update_env(env,module):
	mems = inspect.getmembers(module)
	for mem in mems:
		if mem[0][:2] != "__":
			y = inspect.getmembers(mem[1])
			#print(y[4][1])
			z = inspect.getmembers(y[4][1])
			#print(z[23])
			arg_num = z[23][1]
			env[mem[0]] = (mem[1],arg_num,False)
			#print("adding fn=",mem[0])
	return env


def all_waiting(facts):
	res = True
	for fact in facts:
		res = res and fact['status'] == "waiting"
	return res