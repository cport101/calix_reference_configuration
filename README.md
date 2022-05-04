# calix_reference_configuration
A python/jinja2/yaml script to generate the Calix AXOS E9 reference configuration

Basically, a file that can be "deconstructed/dissasembled" to allow ASCII focused DevOp players to see how I used jinja2/yaml to auto generate 
AXOS configuration stanzas. Follows our publicly published AXOS v21.x "reference configuration."  Still a work in in progress -- some sections 
remain to complete, and I think it might be interesting to create a menu to print and write out the yaml/jinja2 files to allow you to edit your
own. UNIX focused - 
[I use Ubuntu and FreeBSD in my work environment], and currently, option 29 will write all the yaml and jinja2 snipets to a set /tmp/ files, and 
then gen, print and write the full reference configuration. I will get around to making a setup.py to help with the Libs used. 
