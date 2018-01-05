from PyOrgMode import PyOrgMode

import datetime
import json
import re
import os 

##
# CREAZIONE
##

def create_todo(path, heading, priority, collaborator, tags, content, deadline): 
	now = datetime.datetime.now()

	base = PyOrgMode.OrgDataStructure()
	base.load_from_file(path)

	tags_dict = tags.split(", ")
	tags_dict.insert(1, collaborator)

	new_node = PyOrgMode.OrgNode.Element()
	new_node.level = 1
	new_node.heading = heading + " "
	new_node.priority = str(priority)
	new_node.tags = tags_dict
	new_node.content = [content + " \n"]
	new_node.todo = "TODO"

	split_dict = deadline.split(" ")

	new_schedule = PyOrgMode.OrgSchedule()
	new_schedule._append(new_node, new_schedule.Element(scheduled="<" + str(now.strftime("%Y-%m-%d")) + ">"))
	new_schedule._append(new_node, new_schedule.Element(deadline="<" + str(split_dict[0]) + ">"))
	# new_schedule._append(new_node, new_schedule.Element(closed="<" + str(now.strftime("%Y-%m-%d %H:%M")) + ">"))

	base.root.append_clean(new_node)
	base.save_to_file(path)

def create_title(path, heading, content):
	base = PyOrgMode.OrgDataStructure()
	base.load_from_file(path)

	new_title = PyOrgMode.OrgNode.Element()
	new_title.level = 1
	new_title.heading = heading
	new_title.content = [ content + " \n" ]

	base.root.append_clean(new_title)
	base.save_to_file(path)

##
# DISPLAY
##

def load_content(node):
	content_json = []

	for cidx, content in enumerate(node.content): 
				
		if isinstance(content, str): 
			content_json.append({
				"enumerate": cidx,
				"content": str(content)
				})

		else:

			if str(content).startswith( '**' ):
				content_json.append({
					"sublevel": str(content)
					})

			elif "SCHEDULED:" in str(content):

				match = re.search(r'\d{4}-\d{2}-\d{2}', str(content))
				date = datetime.datetime.strptime(match.group(), '%Y-%m-%d').date()

				content_json.append({
					"scheduled": date.strftime('%Y-%m-%d')
					})

			elif "DEADLINE:" in str(content):

				match = re.search(r'\d{4}-\d{2}-\d{2}', str(content))
				date = datetime.datetime.strptime(match.group(), '%Y-%m-%d').date()

				content_json.append({
					"deadline": date.strftime('%Y-%m-%d')
					})

			else: 
				print("else: " + str(content))

	return content_json

def display(path):
	orgbase = PyOrgMode.OrgDataStructure()
	orgbase.load_from_file(path)

	node_json = []

	for idx, node in enumerate(orgbase.root.content):

		content_json = []
		content_type = ""
		todo_state = ""

		if isinstance(node, PyOrgMode.OrgNode.Element):

			if "TODO" in str(node): 
				# print("sono un TODO: " + str(node))

				content_type = "todo"
				todo_state = "TODO"
				content_json = load_content(node=node)


			elif "DONE" in str(node): 
				# print("sono un DONE: " + str(node))
				
				content_type = "done"
				todo_state = "DONE"
				content_json = load_content(node=node)

			elif "NEXT" in str(node): 
				# print("sono un NEXT: " + str(node))

				content_type = "next"
				todo_state = "NEXT"
				content_json = load_content(node=node)

			else: 
				# print("sono un ---: " + str(node))

				content_type = "titel"
				content_json = load_content(node=node)


			node_json.append({
				"enumerate": idx,
				"type": content_type,
				"content": content_json,
				"level": str(node.level),
				"heading": str(node.heading),
				"priority": str(node.priority),
				"tags": node.tags,
				"todo_state": todo_state
				})

	return node_json

def set_done(path, index):
	base = PyOrgMode.OrgDataStructure()
	new_base = PyOrgMode.OrgDataStructure()

	base.load_from_file(path)

	for idx, node in enumerate(base.root.content):
		if str(idx) == str(index): 
			node.todo = "DONE"
			new_base.root.append_clean(node)
		else: 
			new_base.root.append_clean(node)

	new_base.save_to_file(path)

def edit_title():
	pass

def edit_todo():
	pass

def remove_title(path, index):
	base = PyOrgMode.OrgDataStructure()
	new_base = PyOrgMode.OrgDataStructure()

	base.load_from_file(path)

	print("index: " + str(index))

	for idx, node in enumerate(base.root.content):

		if str(idx) == str(index): 
			print("ELIMINO " + str(idx) + ": " + str(node))
		else: 
			new_base.root.append_clean(node)

	new_base.save_to_file(path)

def remove_todo(path, index):
	base = PyOrgMode.OrgDataStructure()
	new_base = PyOrgMode.OrgDataStructure()

	base.load_from_file(path)

	print("index: " + str(index))

	for idx, node in enumerate(base.root.content):

		if str(idx) == str(index): 
			print("ELIMINO " + str(idx) + ": " + str(node))
		else: 
			new_base.root.append_clean(node)

	new_base.save_to_file(path)

##
# RETURN REPOSITORY GRAPH
##

##
# count all todos 
# return number of done 
# return number of done pro user 
# count number of day used to complete todo 
##
