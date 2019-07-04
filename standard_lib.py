def min(in_list):
	smallest = in_list[0]
	for i in in_list:
		if i<smallest:
			smallest = i
	return smallest

def sort(in_list):
	return sorted(in_list)

def append_front(in_list,elt):
	return [elt] + in_list

def append(in_list,elt):
	return in_list.append(elt)

def concat(l,n):
	return l + n

def extract(in_list,elt):
	out = []
	for item in in_list:
		if elt != item:
			out.append(item)
	return out
