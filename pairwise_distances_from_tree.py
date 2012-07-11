#!/usr/bin/env python
import string, re, copy
import os, sys
from Bio import SeqIO
from Bio import AlignIO
from Bio.Nexus import Trees, Nodes
from optparse import OptionParser

sys.path.extend(map(os.path.abspath, ['/nfs/users/nfs_s/sh16/scripts/modules/']))
from Si_nexus import *
from Si_general import *
from Si_SeqIO import *


##########################################
# Function to Get command line arguments #
##########################################


def main():

	usage = "usage: %prog [options]"
	parser = OptionParser(usage=usage)

	parser.add_option("-t", "--tree", action="store", dest="tree", help="tree file", default="", metavar="FILE")
	
	return parser.parse_args()


################################
# Check command line arguments #
################################

def check_input_validity(options, args):

	if options.tree=="":
		DoError("No tree provided")
	elif not os.path.isfile(options.tree):
		DoError("Tree file does not exist")
		
	return




################
# Main program #
################		

if __name__ == "__main__":


	#Get command line arguments

	(options, args) = main()

	#Do some checking of the input files
	
	check_input_validity(options, args)


	
	try:
		tree_string = open(options.tree).read()
	except IOError:
		DoError("Cannot open tree file "+options.tree)
	tree = Trees.Tree(tree_string, rooted=True)
	
	terminals=tree.get_terminals()
	
	for x in xrange(0, len(terminals)):
		for y in xrange(x+1, len(terminals)):
			print tree.node(terminals[x]).data.taxon, tree.node(terminals[y]).data.taxon, tree.distance(terminals[x],terminals[y])
			sys.stdout.flush()
			