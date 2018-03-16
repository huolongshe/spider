
'''
This is a way to save the startup time when running img2py on lots of
files...
'''

import sys
from wx.tools import img2py


command_lines = [
    '-a -F -n zhangjiashan zhangjiashan.png images.py',
    '-a -F -n edit_enter edit_enter.png images.py',
    '-a -F -n edit_quit edit_quit.png images.py',
    '-a -F -n start start.png images.py',
    '-a -F -n end end.png images.py',
    '-a -F -n del_pt del_pt.png images.py',
    '-a -F -n del_seg del_seg.png images.py',
    '-a -F -n merge merge.png images.py',
    '-a -F -n split split.png images.py',
    '-a -F -n map_dlg map_dlg.png images.py',
    '-a -F -n tile_transparent tile_transparent.png images.py',
    '-a -F -n transparent16 transparent16.png images.py',
    '-a -F -n tile_blank tile_blank.png images.py',
    '-a -F -n lighting96 lighting96.png images.py',
    ]

if __name__ == '__main__':
    for line in command_lines:
        args = line.split()
        img2py.main(args)

