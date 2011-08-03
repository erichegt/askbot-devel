"""script for digesting profiling output
to profile functions, wrap them into decorator @profile('file_name.prof')

source: http://code.djangoproject.com/wiki/ProfilingDjango
"""

import hotshot.stats
import sys

stats = hotshot.stats.load(sys.argv[1])
#stats.strip_dirs()
stats.sort_stats('time', 'calls')
stats.print_stats(20)
