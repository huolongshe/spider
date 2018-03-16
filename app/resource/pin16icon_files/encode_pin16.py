
"""
This is a way to save the startup time when running img2py on lots of
files...
"""

import sys
from wx.tools import img2py


if __name__ == '__main__':
    for i in range(100):
        args = ['-a', '-F', '-n', 'pin%02d' % i, 'pin%02d.png' % i, 'pin16_icons.py']
        img2py.main(args)

