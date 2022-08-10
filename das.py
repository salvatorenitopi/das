#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import hashlib
import pathlib


CHECK_FILE_SIZE = False
CHECK_MODIFIED_TIME = False

DRY_RUN = False
REMOVE_ACTION = False

PARANOID_MODE = False
DIFF_MODE = False

VERBOSE_OUTPUT = 0
NO_COLORS = False


################################################################################################
import argparse


parser = argparse.ArgumentParser()


parser.add_argument('-s', '--file-size', dest="file_size", action="store_true", default=False, help="Check file size when comparing files")
parser.add_argument('-m', '--modified', dest="modified_time", action="store_true", default=False, help="Check which file has the most recent modified time")

parser.add_argument('-n', '--dry-run', dest="dry_run", action="store_true", default=False, help="Simulate command execution, print output")
parser.add_argument('-d', '--delete', dest="remove_action", action="store_true", default=False, help="Removes elements in destination that do not exist in source")

parser.add_argument('-p', '--paranoid', dest="paranoid_mode", action="store_true", default=False, help="Calculate and check md5 hash of source and destination")
parser.add_argument('-x', '--diff', dest="diff_mode", action="store_true", default=False, help="Show different files between source and destination")

parser.add_argument('-c', '--no-colors', dest="no_colors", action="store_true", default=False, help="Verbose output")

# parser.add_argument('-v', '--verbose', dest="verbose_output", action="store_true", default=False, help="Verbose output")
parser.add_argument('-v', '--verbose', dest="verbose_output", action="count", default=0, help="Verbose output (-v: all except skip | -vv: all | -vvv: all+stats)")

parser.add_argument('source', nargs='?', default=None)			# Positional argument
parser.add_argument('destination', nargs='?', default=None)		# Positional argument

args = parser.parse_args()


if (args.file_size == True):
	CHECK_FILE_SIZE = True

if (args.modified_time == True):
	CHECK_MODIFIED_TIME = True

if (args.dry_run == True):
	DRY_RUN = True

if (args.remove_action == True):
	REMOVE_ACTION = True

if (args.paranoid_mode == True):
	PARANOID_MODE = True

if (args.diff_mode == True):
	DIFF_MODE = True

if (args.no_colors == True):
	NO_COLORS = True

VERBOSE_OUTPUT = args.verbose_output


if ((CHECK_FILE_SIZE == True) and (CHECK_MODIFIED_TIME == True)):
	print ("[!] Can not check both file-size and modified time, retry removing either --file-size or --modified")
	exit(-1)


raw_source = args.source
raw_destination = args.destination

if (type(raw_source) != str):
	print ("[!] Invalid or missing 'source' positional argument")
	exit(-1)

if (type(raw_destination) != str):
	print ("[!] Invalid or missing 'destination' positional argument")
	exit(-1)
################################################################################################



class Diff_and_sync:

	def __init__(self, source, destination, verbose_output, no_colors, check_modified_time, check_file_size, dry_run, remove_action, paranoid_mode):
		self.source = source
		self.destination = destination
		self.verbose_output = verbose_output
		self.no_colors = no_colors
		self.check_modified_time = check_modified_time
		self.check_file_size = check_file_size
		self.dry_run = dry_run
		self.remove_action = remove_action
		self.paranoid_mode = paranoid_mode

		self.red = '\033[0;31m'
		self.light_red = '\033[1;31m'
		self.green = '\033[0;32m'
		self.light_green = '\033[1;32m'
		self.orange = '\033[0;33m'
		self.yellow = '\033[1;33m'
		self.blue = '\033[0;34m'
		self.light_blue = '\033[1;34m'
		self.purple = '\033[0;35m'
		self.light_purple = '\033[1;35m'
		self.cyan = '\033[0;36m'
		self.light_cyan = '\033[1;36m'
		self.light_gray = '\033[0;37m'
		self.dark_gray = '\033[1;30m'
		self.white = '\033[1;37m'
		self.nc = '\033[0m'


		self.skipped_files = 0
		self.successful_copies = 0
		self.successful_delete = 0
		self.failed_copies = 0
		self.failed_delete = 0




	def cprint (self, color, text):
		if (self.no_colors == False):			print (color + str(text) + self.nc)
		else:									print (text)



	def md5sum (self, file_name):
		hash_md5 = hashlib.md5()
		with open(file_name, "rb") as f:
			for chunk in iter(lambda: f.read(4096), b""):
				hash_md5.update(chunk)
		return hash_md5.hexdigest()



	def copy (self, source, destination, md5sum=False):
		try:
			if (os.path.islink(source) == True):
				shutil.copy2(source, destination, follow_symlinks=False)

			elif (os.path.isdir(source) == True):
				# shutil.copytree(source, destination, symlinks=True)
				os.mkdir(destination)
				shutil.copystat(source, destination)

			else:
				shutil.copy2(source, destination, follow_symlinks=False)


			if ((md5sum == True)  and (os.path.isdir(source) == False) and (os.path.islink(source) == False)):
				md5_source = self.md5sum(source)
				md5_destination = self.md5sum(destination)

				if (md5_source == md5_destination):
					self.successful_copies += 1
					return { "status": 1, "md5_source": md5_source, "md5_destination": md5_destination }
				else:
					self.failed_copies += 1
					return { "status": -1, "md5_source": md5_source, "md5_destination": md5_destination }

			else:
				self.successful_copies += 1
				return { "status": 0 }


		except Exception as e:
			self.failed_copies += 1
			return { "status": -33, "error": str(e) }





	def remove (self, destination):
		try:
			if (os.path.isdir(destination) == True):
				os.rmdir(destination)
			else:
				os.remove(destination)
			
			self.successful_delete += 1
			return { "status": 0 }

		except Exception as e:
			self.failed_delete += 1
			return { "status": -33, "error": str(e) }




	def sync (self):

		# Copy
		for root, folders, files in os.walk(self.source):
			for filename in folders + files:

				joined = os.path.join(root, filename)
				relative_path = joined[len(self.source):]

				full_source = self.source + relative_path
				full_destination = self.destination + relative_path

				# if ((os.path.exists(full_destination) == True) or (os.path.islink(full_destination) == True)):
				if (os.path.lexists(full_destination) == True):

					

					if ((self.check_modified_time == True) and (os.path.isdir(full_source) == False) and (os.path.isdir(full_destination) == False) and (os.path.islink(full_source) == False) and (os.path.islink(full_destination) == False)):
						src_file_modified_time = pathlib.Path(full_source).stat().st_mtime
						dst_file_modified_time = pathlib.Path(full_destination).stat().st_mtime

						if (src_file_modified_time > dst_file_modified_time):

							if (self.dry_run == True):
								self.cprint (self.green, "[*] (dr) Updated " + full_source + " -> " + full_destination)

							else:
								status = self.copy(full_source, full_destination, self.paranoid_mode)
								if ((status.get('status') >= 0) and (self.verbose_output > 0)):
									if (status.get('status') == 0):			self.cprint (self.green, "[*] Updated " + full_source + " -> " + full_destination)
									elif (status.get('status') == 1):		self.cprint (self.green, "[*] Updated " + full_source + "(" + str(status.get('md5_source')) + ") -> " + full_destination + "(" + str(status.get('md5_destination')) + ")")

								else:
									if (status.get('status') == -1):		self.cprint (self.red, "[!] Different md5: " + full_source + " (" + str(status.get('md5_source')) + ") -> " + full_destination + " (" + str(status.get('md5_destination')) + ")" )
									else:									self.cprint (self.red, "[!] Failed update: " + full_source + " -> " + full_destination + "(" + str(status.get('error')) + ")")
	
						else:
							if ((self.verbose_output > 1) and (self.dry_run == True)):		
								if ((src_file_modified_time == dst_file_modified_time)):		self.cprint (self.light_gray, "[i] (dr) Skipped (same modified time) " + full_source); self.skipped_files += 1
								else:														self.cprint (self.light_gray, "[i] (dr) Skipped (dst modified time more recent) " + full_source); self.skipped_files += 1
							
							elif (self.verbose_output > 1):									
								if ((src_file_modified_time == dst_file_modified_time)):		self.cprint (self.light_gray, "[i] Skipped (same modified time) " + full_source); self.skipped_files += 1
								else:														self.cprint (self.light_gray, "[i] Skipped (dst modified time more recent) " + full_source); self.skipped_files += 1



					
					elif ((self.check_file_size == True) and (os.path.islink(full_source) == False) and (os.path.islink(full_destination) == False)):
						src_file_size = os.path.getsize(full_source)
						dst_file_size = os.path.getsize(full_destination)

						if ((src_file_size != dst_file_size) and (os.path.isdir(full_source) == False)):

							if (self.dry_run == True):
								self.cprint (self.green, "[*] (dr) Updated " + full_source + " -> " + full_destination)

							else:
								status = self.copy(full_source, full_destination, self.paranoid_mode)
								if ((status.get('status') >= 0) and (self.verbose_output > 0)):
									if (status.get('status') == 0):			self.cprint (self.green, "[*] Updated " + full_source + " -> " + full_destination)
									elif (status.get('status') == 1):		self.cprint (self.green, "[*] Updated " + full_source + "(" + str(status.get('md5_source')) + ") -> " + full_destination + "(" + str(status.get('md5_destination')) + ")")

								else:
									if (status.get('status') == -1):		self.cprint (self.red, "[!] Different md5: " + full_source + " (" + str(status.get('md5_source')) + ") -> " + full_destination + " (" + str(status.get('md5_destination')) + ")" )
									else:									self.cprint (self.red, "[!] Failed update: " + full_source + " -> " + full_destination + "(" + str(status.get('error')) + ")")
	
						else:
							if ((self.verbose_output > 1) and (self.dry_run == True)):		self.cprint (self.light_gray, "[i] (dr) Skipped (same size) " + full_source); self.skipped_files += 1
							elif (self.verbose_output > 1):									self.cprint (self.light_gray, "[i] Skipped (same size) " + full_source); self.skipped_files += 1




					else:
						if ((self.verbose_output > 1) and (self.dry_run == True)):			self.cprint (self.light_gray, "[i] (dr) Skipped (already exists) " + full_source); self.skipped_files += 1
						elif (self.verbose_output > 1):										self.cprint (self.light_gray, "[i] Skipped (already exists) " + full_source); self.skipped_files += 1





				else:
					if (self.dry_run == True):					
						self.cprint (self.green, "[*] (dr) Copied " + full_source + " -> " + full_destination)
					
					else:
						status = self.copy(full_source, full_destination, self.paranoid_mode)
						if ((status.get('status') >= 0) and (self.verbose_output > 0)):
							if (status.get('status') == 0):			self.cprint (self.green, "[*] Copied " + full_source + " -> " + full_destination)
							elif (status.get('status') == 1):		self.cprint (self.green, "[*] Copied " + full_source + "(" + str(status.get('md5_source')) + ") -> " + full_destination + "(" + str(status.get('md5_destination')) + ")")

						else:
							if (status.get('status') == -1):		self.cprint (self.red, "[!] Different md5: " + full_source + " (" + str(status.get('md5_source')) + ") -> " + full_destination + " (" + str(status.get('md5_destination')) + ")" )
							else:									self.cprint (self.red, "[!] Failed copy: " + full_source + " -> " + full_destination + "(" + str(status.get('error')) + ")")
	


		# Remove
		if (self.remove_action == True):
			for root, folders, files in os.walk(self.destination):
				for filename in folders + files:

					joined = os.path.join(root, filename)
					relative_path = joined[len(self.destination):]

					full_source = self.source + relative_path
					full_destination = self.destination + relative_path

					
					if (os.path.lexists(full_source) == False):
						if (self.dry_run == True):
							self.cprint (self.orange, "[i] (dr) Removed " + full_destination)

						else:
							status = self.remove (full_destination)
							if ((self.verbose_output > 0) and (status.get('status') == 0)):		self.cprint (self.orange, "[i] Removed " + full_destination)
							else:																self.cprint (self.red, "[!] Failed remove: " + full_destination + "(" + str(status.get('error')) + ")")




	def stats (self):
		if ((self.verbose_output) > 2 and (self.no_colors == False)):
			print ("\n#################################\n# Stats\n#################################")
			print ("Skipped files:     " + self.light_gray + str(self.skipped_files) + self.nc)
			print ("Successful copies: " + self.green + str(self.successful_copies) + self.nc)
			print ("Successful delete: " + self.green + str(self.successful_delete) + self.nc)
			print ("Failed copies:     " + self.red + str(self.failed_copies) + self.nc)
			print ("Failed delete:     " + self.red + str(self.failed_delete) + self.nc)
			print ("\n")

		elif ((self.verbose_output) > 2 and (self.no_colors == True)):
			print ("\n#################################\n# Stats\n#################################")
			print ("Skipped files:     " + str(self.skipped_files))
			print ("Successful copies: " + str(self.successful_copies))
			print ("Successful delete: " + str(self.successful_delete))
			print ("Failed copies:     " + str(self.failed_copies))
			print ("Failed delete:     " + str(self.failed_delete))
			print ("\n")






	def diff_helper (self, source, destination, text_prepend=""):
		for root, folders, files in os.walk(source):
			for filename in folders + files:

				joined = os.path.join(root, filename)
				relative_path = joined[len(source):]

				# if ((os.path.exists(destination + relative_path) == True) or (os.path.islink(destination + relative_path) == True)):
				if (os.path.lexists(destination + relative_path) == True):
					
					if (self.check_file_size == True):
						src_file_size = os.path.getsize(source + relative_path)
						dst_file_size = os.path.getsize(destination + relative_path)

						if ((src_file_size != dst_file_size) and (os.path.isdir(source + relative_path) == False)):
							self.cprint ("", "[i] Different size " + source + relative_path)

						else:
							if (self.verbose_output > 0):	self.cprint (self.light_gray, "[i] Exists (same size) " + source + relative_path)

					else:
						if (self.verbose_output > 0):		self.cprint (self.light_gray, "[i] Exists " + source + relative_path)

				else:
					self.cprint ("", text_prepend + source + relative_path)

	


	def diff (self, forward=True):
		if (forward == True):
			self.diff_helper (self.source, self.destination, "[i] Only in SOURCE\t")
		else:
			self.diff_helper (self.destination, self.source, "[i] Only in DESTINATION\t")





if __name__ == "__main__":
	source = raw_source if (raw_source.endswith("/")) else raw_source + "/"
	destination = raw_destination if (raw_destination.endswith("/")) else raw_destination + "/"


	if (os.path.isdir(source) == False):
		print ("[!] Invalid source: " + str(source) + " (not a folder)")
		exit(-1)

	if (os.path.isdir(destination) == False):
		print ("[!] Invalid destination: " + str(destination) + " (not a folder)")
		exit(-1)


	try:
		das = Diff_and_sync(source, destination, VERBOSE_OUTPUT, NO_COLORS, CHECK_MODIFIED_TIME, CHECK_FILE_SIZE, DRY_RUN, REMOVE_ACTION, PARANOID_MODE)

		if (DIFF_MODE == False):
			das.sync ()
			das.stats ()
		
		else:
			das.diff (True)
			das.diff (False)

	except KeyboardInterrupt:
		print ("[i] Aborted by the user")
		exit(-2)


