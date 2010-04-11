#! /usr/bin/env python
import re
import sys
import socket
import time

from urllib2 import urlopen, URLError
from urllib import urlencode
from urlparse import urlparse, urljoin
from os.path import basename
from optparse import OptionParser
from xml.dom import minidom

from astrometry.util.starutil_numpy import *
from astrometry.util.file import *
from astrometry.util.run_command import run_command

# args: radius in deg
# returns list of local filenames to which images were written
def get_2mass_images(ra, dec, radius=1, basefn=None):

	formvals = {
		'type': 'at', # Atlas images (not quicklook)
		'INTERSECT': 'OVERLAPS', # Images overlapping region
		'asky': 'asky', # All-sky release
		'POS': '%g %g' % (ra,dec), # RA,Dec position
		'SIZE': '%g' % (radius), # Search radius (deg)
		# scan, coadd, hem, date
		'band': 'A', # All bands (J,H,K_s)
		}

	if basefn is None:
		#basefn = '2mass-%g-%g-' % (ra,dec)
		basefn = '2mass-'

	queryurl = 'http://irsa.ipac.caltech.edu/cgi-bin/2MASS/IM/nph-im_inv'
	print 'submitting form values:'
	for k,v in formvals.items():
		print '  ',k,'=',v
	print 'encoded as:'
	print '  ' + urlencode(formvals)
	print
	print 'waiting for results...'
	socket.setdefaulttimeout(300)
	f = urlopen(queryurl, urlencode(formvals))
	doc = f.read()
	write_file(doc, 'res.html')

	m = re.search(r'<base href="(.*)" />', doc)
	if not m:
		raise 'no results page: server output written to file'
	resurl = m.group(1)
	print 'result base url', resurl

	resurl += 'found.xml'

	print 'requesting result url', resurl
	res = urlopen(resurl)
	print
	doc = res.read()
	write_file(doc, 'res2.xml')

	xmldoc = minidom.parseString(doc)

	imgs = xmldoc.getElementsByTagName('TR')
	if len(imgs) == 0:
		print 'no <TR> tags found'
		return None
	fns = []
	for imgtag in imgs:
		print
		if not imgtag.hasChildNodes():
			print '<TR> tag has no child node:', imgtag
			return None
		#print 'Image:', imgtag
		tds = imgtag.getElementsByTagName('TD')
		if not len(tds):
			print '<TR> tag has no <TD> child nodes:', imgtag
			return None

		print 'Image:',  tds[0].firstChild.data
		print '  URL:',  tds[1].firstChild.data
		print '  Band:', tds[11].firstChild.data
		print '  dataset (asky):', tds[18].firstChild.data
		print '  date (yymmdd):', tds[22].firstChild.data
		print '  hem (n/s):', tds[23].firstChild.data
		print '  scan:', tds[24].firstChild.data
		print '  image num:', tds[25].firstChild.data

		url = tds[1].firstChild.data
		band = tds[11].firstChild.data
		dataset = tds[18].firstChild.data
		date = tds[22].firstChild.data
		hem = tds[23].firstChild.data
		scan = int(tds[24].firstChild.data)
		imgnum = int(tds[25].firstChild.data)

		fn = basefn + '%s_%s_%s%s%03i%04i.fits' % (band, dataset, date, hem, scan, imgnum)

		cmd = 'wget -c %s -O %s' % (url, fn)
		print 'Running command:', cmd

		#(rtn, out, err) = run_command(cmd)
		#if rtn:
		#	print 'wget failed: return val', rtn
		#	print 'Out:

		os.system(cmd)
		fns.append(fn)
	return fns


if __name__ == '__main__':
	parser = OptionParser(usage='%prog [options] <ra> <dec>')

	parser.add_option('-r', dest='radius', help='Search radius, in deg (default 1 deg)')
	parser.add_option('-b', dest='basefn', help='Base filename (default: 2mass-)')
	parser.set_defaults(radius=1.0)

	(opt, args) = parser.parse_args()
	if len(args) != 2:
		parser.print_help()
		print
		print 'Got extra arguments:', args
		sys.exit(-1)

	# parse RA,Dec.
	ra = float(args[0])
	dec = float(args[1])

	args = {}
	get_2mass_images(ra, dec, **args)