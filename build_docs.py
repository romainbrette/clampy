import os
import sys
import webbrowser

import sphinx
from pkg_resources import parse_version

if not parse_version(sphinx.__version__) >= parse_version('1.7'):
    raise ImportError('Need Sphinx >= 1.7')

doc_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'docs'))
output_dir = os.path.join(doc_dir, '_build', 'html')

from sphinx.cmd.build import main as sphinx_main
ret_val = sphinx_main(['-q', doc_dir, output_dir])

if ret_val != 0:
    print('Building documentation failed.')
    sys.exit(ret_val)

print('Documentation built successfully')
webbrowser.open('file://{}/index.html'.format(output_dir))
