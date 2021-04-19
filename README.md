## pcurate

Pcurate is a command line utility with the purpose of 'curating' or carefully arranging lists of explicitly installed Arch Linux software packages.

I created this because I was often updating text files with lists of installed software and notes concerning many packages.  It became a chore to manage that information for a number of uniquely configured hosts, and keep everything in sync with changes being made.

This utility provides a convenient way to organize software stacks into package lists which can either be fed back to the package manager for automatic installation, or simply used for reference and planning for configuration management.

### Features include
 
 - Tagging/categorization of curated packages, for easier filtering and sorting
 - Alternate package descriptions can be set, such as the reason for installation
 - Data is exportable to a simple package list or comma delimited (csv) format
 - Optional filter.txt file for specifying packages or package groups to be excluded

Note:  Package version information is untracked because Arch Linux is a rolling release distribution, and this utility is not meant to aid in maintaining partial upgrades.  If needed, notes on versioning can be stored in a package tag or description attribute.

###  Installation

This is an early beta, and I have not yet created an AUR package.   

Install with pip

	$ python -m pip install pcurate

### Usage

	$ pcurate -h
	pcurate

	Usage:
	  pcurate PACKAGE_NAME [-u | -s [-t TAG] [-d DESCRIPTION]]
	  pcurate ( -c | -n | -m ) [-v]
	  pcurate ( -h | --help | --version)

	Options:
	  -u --unset              Unset package curated status
	  -s --set                Set package curated status
	  -t tag --tag tag        Set package tag
	  -d desc --desc desc     Set package description
	  -c --curated            Display all curated packages
	  -n --normal             Display packages not curated
	  -m --missing            Display missing curated packages
	  -v --verbose            Display additional info (csv)
	  -h --help               Display help
	  --version               Display pcurate version


### Examples

Display information for a package

	$ pcurate firefox

Set a package as curated status (a keeper)
	
	$ pcurate -s neovim

Unset a package to revoke its curated status (and remove any tag or custom description)

	$ pcurate -u emacs

Set a package with an optional tag and custom description

	$ pcurate -s mousepad -t editors -d "my cat installed this"


The following is a command I use to interactively mark multiple packages as curated.  **Tab** or **Shift**+**Tab** to mark or unmark, commit with **Enter** or cancel with **Esc**.  This requires [fzf](https://archlinux.org/packages/community/x86_64/fzf/) to be installed.

	$ pcurate -n | fzf -m | xargs -I % pcurate -s %

#### Package Lists

Display a list of normal packages (those which are installed but not yet curated)
	
	$ pcurate -n
	
Display a list of curated packages that are missing (either no longer installed or their install reason has been changed to dependency).

	$ pcurate -m

Set curated status for all packages listed in an existing pkglist.txt file (a simple text file containing a newline separated list of package names)

	$ cat pkglist.txt | xargs -I % pcurate -s %

Export a new pkglist.txt file
	
	$ pcurate -c > pkglist.txt
	
Send a pkglist.txt to package manager for automatic installation
	
	$ pacman -S --needed - < pkglist.txt
	
Write a detailed list of curated packages to csv format so you can view it as a spreadsheet, etc.
	
	$ pcurate -c -v > pkglist.csv
	
#### Configuration

**$XDG_CONFIG_HOME/pcurate** or **~/.config/pcurate** is the default location for the package database and filter.txt file.  The optional filter.txt file is a simple newline separated list of packages or package groups.  Single line comments can also be added.

Any packages or members of package groups listed in the filter.txt will be purged from the pcurate database and excluded from command output.  Filter rules are only applied against normal packages, and curated packages are ignored.
	
### License
The MIT License (MIT)

Copyright © 2021 Scott Reed
	
	

	
	

