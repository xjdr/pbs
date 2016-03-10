#!/usr/bin/env python

import os
import sys
import yaml
import requests
import urllib2

from IPython import embed
from progressbar import *

cwd=os.getcwd()

# rootDir=os.path.dirname(os.path.dirname(cwd))
path=cwd+"/manifest.yml"

def parse_config(path):
  if os.path.exists(path):
    with open(path, "r") as f:
      return yaml.load(f)
  else:
    print "could not load lib file at %s" % path
    sys.exit(1)

def validate_uri(complete_uri):
    try:
	ret = urllib2.urlopen(complete_uri)
	if ret.code == 200:
	  return 0
	else:
	  return 1;
    except:
	return 1

def build_uri(dep):
  base_uri = 'http://ftp.us.debian.org/debian/pool/main/'
  complete_uri = base_uri + dep['name'][0] + '/' + dep['name']
  print " Download URI : " , complete_uri
  uri_true=validate_uri(complete_uri)
  if uri_true == 0:
     return complete_uri
  else:
      complete_uri = base_uri + '/' + dep['name']
      uri_true=validate_uri(complete_uri)
      if uri_true == 0:
	 return complete_uri
      else:
	 print " Not a valid Download link "
	 sys.exit(1)


def download_package(name, url):
  widgets = [FormatLabel('Downloading ' + name + ': '), Percentage(), Bar()]

  deb = requests.get(url, stream=True)
  if not deb.status_code == requests.codes.ok:
    print 'Download deb Failed'
    print deb.status_code
    print deb.text
    sys.exit(1)

  # pbar = ProgressBar(maxval=int(deb.headers['Content-Length']), widgets=widgets).start()
  pbar = ProgressBar(maxval=10000, widgets=widgets).start() # TODO(JR): Fix the PB max value

  try:
    if not os.path.exists('packages'):
      os.makedirs('packages')

    with open('packages/' + name, 'wb') as f:
      for chunk in deb.iter_content(chunk_size=1024):
	pbar.update(12)
	if chunk: # filter out keep-alive new chunks
	  f.write(chunk)
	  f.flush()

    pbar.finish()

  except Exception as e:
    print 'Download ' + name + ' Failed'
    print e

def main():
  print path
  manifest = parse_config(path)

  for dep in manifest:
    group = dep['dep']['group']
    artifact = dep['dep']['artifact']
    version = dep['dep']['version']
    group_manifest = parse_config(cwd+"/"+group + '/' + artifact + '.yml')

    if group_manifest == None:
      print "THERE IS NOTHING HERE, YO"
    else:
      for deb in group_manifest:
	download_package(deb['dep']['name'].split('/')[1], build_uri(deb['dep']))
  sys.exit(0)

if __name__ == "__main__":
  main()
