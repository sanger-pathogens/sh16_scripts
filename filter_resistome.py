#!/usr/bin/env python

##################
# Import modules #
##################

import os, sys
from optparse import OptionParser
import pysam

##############################
# Get command line arguments #
##############################

def get_user_options():
	usage = "usage: %prog [options]"
	version="%prog 1.0. Written by Simon Harris, Wellcome Trust Sanger Institute, 2012"
	parser = OptionParser(usage=usage, version=version)
	
	#do not allow arguments to be interspersed. e.g. -a -b arg1 agr2. MUST be -a arg1 -b arg2.
	parser.disable_interspersed_args()
	

	parser.add_option("-c", "--contigs", action="store", dest="contigs", help="multifasta containing contigs to search in", default="", metavar="FILE")
	parser.add_option("-g", "--genes", action="store", dest="genes", help="multifasta containing genes to search for", default="", metavar="FILE")
	parser.add_option("-b", "--bamfile", action="store", dest="bamfile", help="bamfile of mapped genes", default="", metavar="FILE")
	parser.add_option("-o", "--output", action="store", dest="output", help="prefix for output files", default="", metavar="FILE")
	parser.add_option("-i", "--id", action="store", dest="id", help="minimum id to report match (excluding clipping due to contig breaks) [default = %default]", default=0.9, type="float", metavar="float")
	

	return parser.parse_args()

(options, args)=get_user_options()

if not os.path.isfile(options.contigs):
	print "Could not find contigs file"
	sys.exit()	
if not os.path.isfile(options.bamfile):
	print "Could not find bam file"
	sys.exit()	
if not os.path.isfile(options.genes):
	print "Could not find genes file"
	sys.exit()
try:
	contigsfile=open(options.contigs, "rU").read()
except StandardError:
	print "Could not open contigs file"
	sys.exit()

if options.id<0 or options.id>1:
	print "percent id (-i) must be between 0 and 1"
	sys.exit()

contigs={}
genes_present=[]
for line in contigsfile.split(">")[1:]:
	bits=line.split("\n")
	contigs[bits[0].split()[0]]=''.join(bits[1:])

filename=options.bamfile


try:
	genesfile=open(options.genes, "rU").read()
except StandardError:
	print "Could not open contigs file"
	sys.exit()
	
genes={}
geneorder=[]
for line in genesfile.split(">")[1:]:
	bits=line.split("\n")
	geneorder.append(bits[0].split()[0])
	genes[bits[0].split()[0]]=''.join(bits[1:])
refstarts={}
refends={}
count=0
for x, ref in enumerate(geneorder):
	refstarts[ref]=count
	count+=len(genes[ref])
	refends[ref]=count


if filename.split(".")[-1]=="bam":
	samfile = pysam.Samfile( filename, "rb" )
elif filename.split(".")[-1]=="sam":
        samfile = pysam.Samfile( filename, "r" )
else:
	print filename+" not a bam file"
        sys.exit() 

refs=samfile.references
lengths=samfile.lengths

for read in samfile:
	if read.is_unmapped:
            continue
        if read.is_reverse:
        	strand="-"
        else:
        	strand="+"
        start=read.pos
        readpos=0
        refpos=start
        insertions=0
        inslength=0
        deletions=0
        dellength=0
        SNPs=0
        clipped=0
        cliplength=0
        lcliplen=0
        rcliplen=0
        for cignum, cig in enumerate(read.cigar):
            
            if cig[0]==0:
                for x in range(0,cig[1]):
                    if read.seq[readpos].upper()!=contigs[refs[read.tid]][refpos].upper():
                        SNPs+=1
                    readpos+=1
                    refpos+=1
            elif cig[0]==1:
                insertions+=1
                inslength+=cig[1]
                readpos+=cig[1]
            elif cig[0]==2:
                deletions+=1
                dellength+=cig[1]
                refpos+=cig[1]
            elif cig[0]==4:
                clipped+=1
                cliplength+=cig[1]
                if cignum==0:
                	lcliplen+=cig[1]
                elif cignum==(len(read.cigar)-1):
                	rcliplen+=cig[1]
                else:
                	print "Internal clipping?!"
                	print read.cigar
                readpos+=cig[1]
            else:
                print cig
        end=refpos
        
        
        adjustedcliplen=cliplength
        at_contig_break=0
        
        if lcliplen>start:
        	adjustedcliplen=adjustedcliplen-(lcliplen-start)
        	at_contig_break+=1
        elif (rcliplen+end)>lengths[read.tid]:
        	adjustedcliplen=adjustedcliplen-((rcliplen+end)-lengths[read.tid])
        	at_contig_break+=1
        
        matchlength=len(read.seq)-(cliplength-adjustedcliplen)
        matchpercent=(float(matchlength)/len(read.seq))*100
        
        percentid=((float(len(read.seq))-(SNPs+adjustedcliplen))/len(read.seq))
        if percentid>=options.id:
	        genes_present.append([read.qname, refs[read.tid], start, end, strand, len(read.seq), SNPs, insertions, deletions, clipped, inslength, dellength, cliplength, at_contig_break, 100*percentid, matchlength, matchpercent])
        
        #print filename, read.qname, len(read.seq), SNPs, insertions, deletions, clipped, inslength, dellength, cliplength



bestgene=genes_present[0]
secondary_genes=[]
outputlines=[]
for gene in genes_present[1:]:
    
    #print gene

    if gene[1]==bestgene[1]:
        if gene[2]<bestgene[3]:
            #print "overlap"
            if float(gene[6]+gene[7]+gene[8])/gene[5] < float(bestgene[6]+bestgene[7]+bestgene[8])/bestgene[5]:
                secondary_genes.append(bestgene[0])
                bestgene=gene
            else:
                secondary_genes.append(gene[0])
        else:
            outputlines.append(bestgene+[', '.join(secondary_genes)])
	    #print outputlines
            bestgene=gene
            secondary_genes=[]
    else:
        outputlines.append(bestgene+[', '.join(secondary_genes)])
        bestgene=gene
        secondary_genes=[]

outputlines.append(bestgene+[', '.join(secondary_genes)])


if options.output!="":
	output=open(options.output+"_hits.txt","w")
	plotlines=[]
	print >> output, "\t".join(["gene", "contig", "start", "end", "strand", "length", "SNPs", "No. insertions", "No. deletions", "No. clipped regions", "total insertion length", "total deletion length", "clipped length", "No. contig breaks", "Percent id", "Match length", "Match length percent", "Overlapping secondary gene hits"])
	for line in outputlines:
		print >> output, '\t'.join(map(str,line))

		plotlines.append([refstarts[line[0]],refends[line[0]],((float(line[5])-float(line[6]+line[7]+line[8]))/line[5])*100])

	output.close()
	
	plotout=open(options.output+"_hits.plot","w")
	print >> plotout, "#BASE MATCH"
	plotlines.sort()
	for line in plotlines:
		for x in xrange(line[0],line[1]):
			print >> plotout, x, line[2]
	plotout.close()
    
else:
	print "\t".join(["gene", "contig", "start", "end", "strand", "length", "SNPs", "No. insertions", "No. deletions", "No. clipped regions", "total insertion length", "total deletion length", "clipped length", "No. contig breaks", "Percent id", "Match length", "Match length percent", "Overlapping secondary gene hits"])
	for line in outputlines:
		print '\t'.join(map(str,line))
