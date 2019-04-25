import os


def expand_path(input_path):
	"""
	This function attempts to coerce input paths in any relative format
	into an absolute path. "~" should be expanded to the user's full
	home directory. "./" or "../" notation needs to be expanded.
	Directories should end in "/"
	:param input_path: the path to be expanded
	:return expanded_path: the expanded path to the file/dir indicated
	"""
	home_dir = os.path.expanduser("~")

	if input_path[0] == "~":
		expanded_path = home_dir + input_path[1:]
	else:
		expanded_path = input_path
	expanded_path = os.path.abspath(expanded_path)
	return expanded_path


def verify_path(expanded_path, kind=None):
	if kind == "file":
		if os.path.isfile(expanded_path) is True:
			return True
		else:
			return False
	elif kind == "dir":
		if os.path.isdir(expanded_path) is True:
			return True
		else:
			return False
	elif kind is None:
		if os.path.exists(expanded_path) is True:
			return True
		else:
			return False
	else:
		print("{} is not a valid kind for this function. Please try again "
			  "using one of (None, dir, file).")


def ask_yes_no(prompt):
	response = False
	response_valid = False
	while response_valid is False:
		response = input(prompt)
		if response.lower() in ["yes", "y", "t", "true"]:
			response = True
			response_valid = True
		elif response.lower() in ["no", "n", "f", "false"]:
			response = False
			response_valid = True
		else:
			print("Invalid response.")
	return response


def close_files(list_of_filehandles):
	for handle in list_of_filehandles:
		handle.close()
	return
