Rich XForms Submissions
=======================

A simple ETL _(Extract Transform and Load)_ tool meant to process XForms
submissions including (but not limited to) enriching the submissions by adding
the original question labels to the submissions and serializing the final
result into a suitable format ready for consumption.

This tool exists primary to cater for the differences in implementations of
XForms compliant servers such as ODK Central, KoBoToolbox, etc. when it comes
to exporting/extracting form submissions. The goal of the tool is to provide a
unified interface from which other XForms submissions consuming tools can be
build on top of.


Getting Started
---------------
*__Note:__ Currently the tool can only be run by cloning this repo and running
the app locally. The eventual goal is to package the tool allowing it to be run
as either a cli app or used as a library.*

Before running the tool locally, clone this repo and install the requirements
by running:
```bash
pip install -r requirements.txt
```

You will  then need to define a configuration file. A template for the config
file is provided with the tool, check the `.config.template.yaml` file and edit
it to match your setup/needs.

Once you are done with the config file, you can run the tool as follows:
```bash
python -m app -c /path/to/your/config.yaml
```
Replace `/path/to/your/config.yaml` with the correct path to your config file.

You are now good to go :thumbsup:.

You can additionally provide the `-o /path/to/output_folder` option to specify
a directory to store the programs output. The programs output includes the
retrieved forms and the form submissions. If you don't specify this option, it
defaults to the `out` directory relatively to the working directly of the tool.

License
-------

MIT License

Copyright (c) 2022, Savannah Informatics Global Health Institute