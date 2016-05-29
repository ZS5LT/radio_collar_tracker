#!/usr/bin/env python
import argparse
import fileChooser
import os
import read_meta_file
import getRunNum
import shutil
import platform
import getCollars
import get_beat_frequency
import subprocess
import raw_gps_analysis
import display_data
import fileinput

# Constants
config_dir = ""
fft_detect = ""
if platform.system() == "Windows":
	config_dir = os.path.join("C:", os.sep, "Users", "e4e", ".rct", "")
	fft_detect = os.path.join("C:", os.sep, "Users", "e4e", "fft_detect", "fft_detect.exe")
elif platform.system() == "Linux" or platform.system() == 'Darwin':
	config_dir = os.path.join(os.sep, "usr", "local", "etc", "rct", "")
	fft_detect = os.path.join(os.sep, "usr", "local", "bin", "fft_detect")

parser = argparse.ArgumentParser(description='Processes Radio Collar Tracker Data')

parser.add_argument('-s', '--signal-distance', action = 'store_true', default = False, help = 'Enables distance to signal plots', dest = 'signal_dist')
parser.add_argument('-r', '--record', action = 'store_true', default = False, help = 'Records the current run configuration', dest = 'record')
parser.add_argument('-c', '--clear', action = 'store_true', default = False, help = 'Clears the existing run configuration', dest = 'clear_run')
parser.add_argument('-i', '--input', help = 'Input Directory', metavar = 'data_dir', dest = 'data_dir', default = None)

args = parser.parse_args()
signal_dist_output = args.signal_dist
record = args.record
clean_run = args.clear_run
data_dir = ""
if args.data_dir is None:
	data_dir = fileChooser.getFileName()
	if data_dir == "":
		exit
else:
	data_dir = args.data_dir

runFileName = os.path.join(data_dir, 'RUN')
altFileName = os.path.join(data_dir, 'ALT')
colFileName = os.path.join(data_dir, 'COL')
collarDefinitionFilename = os.path.join(".", 'COL"')

# clear run if needed
if clean_run is True:
	try:
		os.remove(runFileName)
	except Exception, e:
		pass
	try:
		os.remove(altFileName)
	except Exception, e:
		pass
	try:
		os.remove(colFileName)
	except Exception, e:
		pass

# Get run number
run = -1
if os.path.isfile(runFileName):
	run = int(read_meta_file.read_meta_file(runFileName, 'run_num'))
else:
	runString = getRunNum.getRunNum()
	if runString is None:
		exit
	else:
		run = int(runString)

# record run
if record:
	runFile = open(runFileName, 'w')
	runFile.write("run: %s", run)
	runFile.close()

# Get Altitude
alt = -1
if os.path.isfile(altFileName):
	alt = int(read_meta_file.read_meta_file(altFileName, 'flt_alt'))
else:
	altString = getFltAlt.getFltAlt()
	if altString is None:
		exit
	else:
		alt = int(altString)

# record altitude
if record:
	altFile = open(altFileName, 'w')
	altFile.write("flt_alt: %s", alt)
	altFile.close()

# Get collar definition
hasCollarDefinitions = os.path.isfile(colFileName)
collars = []
if hasCollarDefinitions:
	shutil.copyfile(colFileName, collarDefinitionFilename)
	for line in fileinput.input(collarDefinitionFilename):
		collars.append(int(line.strip().split(':')[1].strip()))
	fileinput.close()
else:
	collars = getCollars.getCollars()
	if len(collars) == 0:
		exit
	colFile = open(collarDefinitionFilename, 'w')
	for i in xrange(len(collars)):
		colFile.write("%d: %d" % (i + 1, collars[i]))
	colFile.close()

# record collar definitions
if record and not hasCollarDefinitions:
	shutil.copyfile(colFileName, collarDefinitionFilename)

fileList = os.listdir(data_dir)
# Count the number of raw data files
num_raw_files = 0
for file in fileList:
	if "RAW_DATA_" in file:
		num_raw_files += 1
# count the number of collars
numCollars = len(collars)
# Generate collar file prefix
collar_file_prefix = "%s/RUN_%06d_" % (data_dir, run)
# Find meta file and get data
meta_file_name = "%s/META_%06d" % (data_dir, run)
sdr_center_freq = int(read_meta_file.read_meta_file(meta_file_name, "center_freq"))
sdr_ppm = float(read_meta_file.read_meta_file(os.path.join(config_dir, "SDR.cfg"), "sdr_ppm"))

# Generate fixed frequencies
beat_frequencies = [get_beat_frequency.getBeatFreq(sdr_center_freq, freq, sdr_ppm) for freq in collars]

# Generate raw files
args = ""
args += " -i %s " % (data_dir)
args += " -o %s " % (data_dir)
args += " -r %d " % (run)
for freq in beat_frequencies:
	args += " %s " % (freq)
subprocess.call(fft_detect + args, shell=True)

for i in xrange(len(collars)):
	raw_gps_analysis.process(data_dir, data_dir, run, i + 1, alt)
	data_file = '%s/RUN_%06d_COL_%06d.csv' % (data_dir, run, i + 1)
	display_data.generateGraph(run, i + 1, data_file, data_dir, collarDefinitionFilename)

os.remove(collarDefinitionFilename)