def min(in_list):
	return sorted(in_list)[0]

def sort(in_list):
	return sorted(in_list)

def concat(in_list,elt):
	return [elt] + in_list

def append(in_list,elt):
	return in_list.append(elt)

def extract(in_list,elt):
	out = []
	for item in in_list:
		if elt != item:
			out.append(item)
	return out
