# Pre-packaged Tests

These basic system tests allow you to play with the basic features of Pavilion with little effort.
They assume a Linux/Slurm/OpenMPI cluster, but are easily modified to handle other systems if needed.

## Activation
The `activate.sh` script will set this directory as Pavilion's config directory, and add Pavilion to
your path.


## Hosts

The hosts/directory contains an example `<hostname>.yaml` file. Pavilion uses 'host' files as the
basis for all test configurations. Several of the tests in this directory expect certain hostwide
configuration, so you'll need to create a host file for the system you intend to run on. By default, 
Pavilion uses the short hostname of the system (basically, the output of `hostname -s`). 

Copy the example file so that it's named for your host, and modify it as needed.


## Test source files

All the tests included here either have no source to compile, have the source already included, or
are configured to download the source from the internet. If you can't download the source directly
on your system, simply download it manually (using the link in given in the `build.source_url`
config item) and put it in the `test_src` directory under the filename given in the test's 
`build.source_path` configuration item.
