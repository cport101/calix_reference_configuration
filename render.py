#!/usr/bin/env python3 
# Render
import sys
import yaml
from jinja2 import Environment, FileSystemLoader

# Initialize the Jinja2 environment to load templates
# from the current directory
env = Environment(loader=FileSystemLoader('.'))
template = env.get_template(sys.argv[1])

# Load the inflow YAML file into a Python dictionary
with open(sys.argv[2], 'r') as datafile:
    inflow = yaml.load(datafile, yaml.FullLoader)

# Render the template and print the resulting document
rendered_template = template.render(**inflow)
print(rendered_template)
