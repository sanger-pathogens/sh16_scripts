#!/bin/tcsh
# by zn1@sanger.ac.uk
# 11/07/2008
#

set prog=/nfs/pathogen/sh16_scripts/ # set fuzzyProgramPath

set kmer=19
set depth=1500
set length=3000
set insert=0
set cover=2.5
set reads=0
set fuzzy=0

if($#argv < 2) then
	echo "Usage:    $0 [options] reads.fastq genome_assembly"
	echo "		options:"
	echo "			-kmer <kmer size> defult: 19"
	echo "			-depth <maximum kmer depth> defult: 1500"
	echo "			-length <length of extended reads> default: 3000"
	echo "			-insert < mean insert size> default: 0"
	echo "			-cover < mean read coverage to use read pair > default: 2.5"
	echo "			-reads <number of extended reads> default: 15000 - depending on the genome size:"
	echo "			Genome size: 2Mb - 15000:"
	echo "			Genome size: 5Mb - 40000:"
        exit
endif

@ n = 1
while ( $n <= $#argv - 3 ) 
	switch ($argv[$n])
            case -kmer:
		@ n = $n + 1
                set kmer=$argv[$n]
		@ n = $n + 1
                continue
            case -depth:
		@ n = $n + 1
		set depth=$argv[$n]
		@ n = $n + 1
                continue
            case -length:
		@ n = $n + 1
		set length=$argv[$n]
		@ n = $n + 1
                continue
	    case -insert:
		@ n = $n + 1
		set insert=$argv[$n]
		@ n = $n + 1
		continue
	    case -reads:
		@ n = $n + 1
		set reads=$argv[$n]
		@ n = $n + 1
		continue
	    case -cover:
		@ n = $n + 1
		set cover=$argv[$n]
		@ n = $n + 1
		continue
	    case -fuzzy:
		@ n = $n + 1
		set fuzzy=$argv[$n]
		@ n = $n + 1
		continue
	    default:
		echo unknown $argv[$n]
		exit
      endsw
end

set readsfile=$argv[$n]
@ n = $n + 1
set genome=$argv[$n]

echo "--------------------------------------------"
echo "settings to run the pipeline:"
echo "--------------------------------------------"
echo "\t" "readFile: $readsfile" 
echo "\t" "genomeFile: $genome.contigs.fa"
echo "\t" kmer: $kmer
echo "\t" depth: $depth
echo "\t" length: $length
echo "\t" insert: $insert
echo "\t" cover: $cover
echo "\t" reads: $reads
echo "\t" fuzzy: $fuzzy
echo "\t" genome: $genome
echo "the pipeline is running ..."
echo 

if($reads > 0) then

$prog/fuzzy/fuzzypath -kmer $kmer -depth $depth -cover $cover -length $length -reads $reads -insert $insert mates $readsfile $genome.ext.fastq > tmp.fuzzyout.$$

endif

echo "setting read number by the code\t"
if($reads == 0) then
$prog/fuzzy/fuzzypath -kmer $kmer -depth $depth -cover $cover -length $length -insert $insert mates $readsfile $genome.ext.fastq > tmp.fuzzyout.$$

endif


$prog/fastq2fasta/fastq2fasta $genome.ext.fastq $genome.ext.fasta > tmp.phrap.out.$$ 


set arch=`uname -m`
if(! -f $prog/phrap/phrap_$arch/phrap.manylong) then
	echo "Error: can not find phrap program for $arch"
	exit
endif

$prog/phrap/phrap_$arch/phrap.manylong $genome.ext.fasta > tmp.phrap.out.$$

\mv $genome.ext.fasta.contigs $genome.contigs.fa
\rm -f $genome.ext.fasta.*
\rm -f tmp.*.$$

