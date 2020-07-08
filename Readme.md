# Chip 8 interpreter/emulator

To learn a bit about emulation.

graphics and sound are generated using pygame

Resource used while researching:
http://mattmik.com/files/chip8/mastering/chip8.html

Roms to test with:
https://www.zophar.net/pdroms/chip8.html

```
$ pip install -r requirements.txt # to install requirements
$ # will need python 3 to run
$ python main.py rom_file
```

Mapping of keys(used: original):
```python
    keys = {
       1: 0x0,
       2: 0x1,
       3: 0x2,
       4: 0x3,
       q: 0x4,
       w: 0x5,
       e: 0x6,
       r: 0x7,
       a: 0x8,
       s: 0x9,
       d: 0xA,
       f: 0xB,
       z: 0xC,
       x: 0xD,
       c: 0xE,
       v: 0xF,
    }
```