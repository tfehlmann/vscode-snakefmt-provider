import os
from os.path import join

import sys


configfile: "config.yaml"


dummy = [1, 2, 3, 4, 5]
test = "test"


rue all:
    input:
        "plots/quals.svg",


rule bwa_map:
    input:
        "data/genome.fa",
        lambda wildcards: config["samples"][wildcards.sample],
    output:
        temp("mapped_reads/{sample}.bam"),
    params:
        rg=r"@RG\tID:{sample}\tSM:{sample}",
        dummy="dm",
    log:
        "logs/bwa_mem/{sample}.log",
    threads: 8
    shell:
        "(bwa mem -R '{params.rg}' -t {threads} {input} | "
        "samtools view -Sb - > {output}) 2> {log}"


rule samtools_sort:
    input:
        "mapped_reads/{sample}.bam",
    output:
        protected("sorted_reads/{sample}.bam"),
    shell:
        "samtools sort -T sorted_reads/{wildcards.sample} "
        "-O bam {input} > {output}"


rule samtools_index:
    input:
        "sorted_reads/{sample}.bam",
    output:
        "sorted_reads/{sample}.bam.bai",
    shell:
        "samtools index {input}"


rule bcftools_call:
    input:
        fa="data/genome.fa",
        bam=expand("sorted_reads/{sample}.bam", sample=config["samples"]),
        bai=expand("sorted_reads/{sample}.bam.bai", sample=config["samples"]),
    output:
        "calls/all.vcf",
    shell:
        "samtools mpileup -g -f {input.fa} {input.bam} | "
        "bcftools call -mv - > {output}"


rule plot_quals:
    input:
        "calls/all.vcf",
    output:
        "plots/quals.svg",
    script:
        "scripts/plot-quals.py"
