# das
Diff And Sync: a (very) simplified version of rsync


## Install
```bash
chmod +x setup.sh
./setup.sh
```


## Uninstall
```bash
chmod +x uninstall.sh
./uninstall.sh
```

## Usage
```text
usage: das [-h] [-s] [-m] [-n] [-d] [-p] [-x] [-c] [-v] [source] [destination]

positional arguments:
  source
  destination

optional arguments:
  -h, --help       show this help message and exit
  -s, --file-size  Check file size when comparing files
  -m, --modified   Check which file has the most recent modified time
  -n, --dry-run    Simulate command execution, print output
  -d, --delete     Removes elements in destination that do not exist in source
  -p, --paranoid   Calculate and check md5 hash of source and destination
  -x, --diff       Show different files between source and destination
  -c, --no-colors  Verbose output
  -v, --verbose    Verbose output (-v: all except skip | -vv: all | -vvv: all+stats)
```

## Examples
Copy files from source (path_a) to destination (path_b) that do not exist in destination, print relevant actions.
```text
das ~/path_a ~/path_b -v
```

Simulate copy files from source (path_a) to destination (path_b) that do not exist in destination, print relevant actions.
```text
das ~/path_a ~/path_b -vn
```

Copy files from source (path_a) to destination (path_b) that do not exist in destination, delete from destination files that do not exist in source, print relevant actions.
```text
das ~/path_a ~/path_b -vd
```
