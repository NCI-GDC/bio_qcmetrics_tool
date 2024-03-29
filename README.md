# bio_qcmetrics_tool

[![Docker Repository on Quay](https://quay.io/repository/ncigdc/bio-qcmetrics-tool/status?token=6f93e569-076e-45cc-b52f-ac0aba79b5c5 "Docker Repository on Quay")](https://quay.io/repository/ncigdc/bio-qcmetrics-tool)

[![Build Status](https://travis-ci.com/NCI-GDC/bio_qcmetrics_tool.svg?token=p66Cyx1mwd8vvwEuBvRM&branch=master)](https://travis-ci.com/NCI-GDC/bio_qcmetrics_tool)

Framework for serializing QC metrics into different formats for bioinformatics workflows. Currently,
only the ability to take the metrics files and convert to sqlite is supported. The ability to add new
modules is simple, by just inheriting the `ExportQcModule` class and the tool is automatically
added to the CLI.

Some of the log/metrics file parsing logic was adapted from:

```
    MultiQC: Summarize analysis results for multiple tools and samples in a single report
    Philip Ewels, Mans Magnusson, Sverker Lundin and Max Kaller
    Bioinformatics (2016)
    doi: 10.1093/bioinformatics/btw354
    PMID: 27312411 
    https://github.com/ewels/MultiQC
```

## Install

In a python3.5 virtual environment, run `make init`.

This will install `pre-commit` and `pip install` the dependencies in the `requirements.txt` file.

## Export

Extract raw metrics files into a sqlite db.

* Fastqc
```
usage: bio-qcmetrics-tool export fastqc [-h] -i INPUTS -j JOB_UUID
                                        --export_format {sqlite} -o OUTPUT

Extract FastQC report from zip archive(s).

optional arguments:
  -h, --help            show this help message and exit
  -i INPUTS, --inputs INPUTS
                        Input fastqc zip file. May be used one or more times
  -j JOB_UUID, --job_uuid JOB_UUID
                        The job uuid associated with the inputs.
  --export_format {sqlite}
                        The available formats to export
  -o OUTPUT, --output OUTPUT
                        The path to the output file
```

* Picard
```
usage: bio-qcmetrics-tool export picardmetrics [-h] -i INPUTS -j JOB_UUID
                                               [--derived_from_file DERIVED_FROM_FILE]
                                               --export_format {sqlite} -o
                                               OUTPUT

Extract Picard metrics.

optional arguments:
  -h, --help            show this help message and exit
  -i INPUTS, --inputs INPUTS
                        Input picard metrics file. May be used one or more
                        times
  -j JOB_UUID, --job_uuid JOB_UUID
                        The job uuid associated with the inputs.
  --derived_from_file DERIVED_FROM_FILE
                        The file that the metrics were drived from (e.g., bam
                        file).
  --export_format {sqlite}
                        The available formats to export
  -o OUTPUT, --output OUTPUT
                        The path to the output file
                        
 ```
 
 * Readgroup metadata
 ```
 usage: bio-qcmetrics-tool export readgroup [-h] -i INPUTS -j JOB_UUID -b BAM
                                           --export_format {sqlite} -o OUTPUT

Extract readgroup metadata

optional arguments:
  -h, --help            show this help message and exit
  -i INPUTS, --inputs INPUTS
                        Input readgroup JSON files
  -j JOB_UUID, --job_uuid JOB_UUID
                        The job uuid associated with the inputs.
  -b BAM, --bam BAM     The bam associated with the inputs.
  --export_format {sqlite}
                        The available formats to export
  -o OUTPUT, --output OUTPUT
                        The path to the output file
 ```
 
 * samtools
 
 **flagstats**
 
 ```
 usage: bio-qcmetrics-tool export samtoolsflagstats [-h] -i INPUTS -j JOB_UUID
                                                   -b BAM --export_format
                                                   {sqlite} -o OUTPUT

Extract samtools flagstats metrics.

optional arguments:
  -h, --help            show this help message and exit
  -i INPUTS, --inputs INPUTS
                        Input flagstats file. May be used one or more times
  -j JOB_UUID, --job_uuid JOB_UUID
                        The job uuid associated with the inputs.
  -b BAM, --bam BAM     The bam that the metrics were derived from.
  --export_format {sqlite}
                        The available formats to export
  -o OUTPUT, --output OUTPUT
                        The path to the output file

 ```
 
 **idxstats**
 
 ```
 usage: bio-qcmetrics-tool export samtoolsidxstats [-h] -i INPUTS -j JOB_UUID
                                                  -b BAM --export_format
                                                  {sqlite} -o OUTPUT

Extract samtools idxstats metrics.

optional arguments:
  -h, --help            show this help message and exit
  -i INPUTS, --inputs INPUTS
                        Input idxstats file. May be used one or more times
  -j JOB_UUID, --job_uuid JOB_UUID
                        The job uuid associated with the inputs.
  -b BAM, --bam BAM     The bam that the metrics were derived from.
  --export_format {sqlite}
                        The available formats to export
  -o OUTPUT, --output OUTPUT
                        The path to the output file
 ```
 
 **stats**
 
 ```
 usage: bio-qcmetrics-tool export samtoolsstats [-h] -i INPUT -j JOB_UUID -b
                                               BAM --export_format {sqlite} -o
                                               OUTPUT

Extract samtools stats metrics.

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Input stats file
  -j JOB_UUID, --job_uuid JOB_UUID
                        The job uuid associated with the inputs.
  -b BAM, --bam BAM     The bam that the metrics were derived from.
  --export_format {sqlite}
                        The available formats to export
  -o OUTPUT, --output OUTPUT
                        The path to the output file
 ```
 
 * STAR
 ```
 usage: bio-qcmetrics-tool export starstats [-h]
                                           [--final_log_inputs FINAL_LOG_INPUTS]
                                           [--gene_counts_inputs GENE_COUNTS_INPUTS]
                                           -j JOB_UUID [--bam BAM]
                                           --export_format {sqlite} -o OUTPUT

Extract STAR logs/gene counts metrics.

optional arguments:
  -h, --help            show this help message and exit
  --final_log_inputs FINAL_LOG_INPUTS
                        Input star log file.
  --gene_counts_inputs GENE_COUNTS_INPUTS
                        Input star gene counts file.
  -j JOB_UUID, --job_uuid JOB_UUID
                        The job uuid associated with the inputs.
  --bam BAM             The bam file associated with the inputs in the same
                        order.
  --export_format {sqlite}
                        The available formats to export
  -o OUTPUT, --output OUTPUT
                        The path to the output file
 ```

## Adding new exporters

All new exporter tools should inherit from `bio_qcmetrics_tool.modules.base.ExportQcModule`. All exporters will
automatically have `--export_format` and `--output` command-line parameters added.
