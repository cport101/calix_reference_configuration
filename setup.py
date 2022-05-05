import sys
from setuptools import setup

dependencies = [ "Jinja2>=3.0.3", "netmiko>=3.4.0", "PyYAML>=6.0" ]

setup(
    name="calix_reference_config",
    version="0.0.0",
    author="Charles Port",
    author_email="charles.port@calix.com",
    description="A python Jinja2/YAML approach to building an AXOS cfg file",
    license="MIT",
    classifiers=[
        'Programming Language :: Python :: 3',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Topic :: System :: Networking',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Ubuntu 20.04 LTS',
    ],
    install_requires=dependencies,
    python_requires='>=3.6',
)
