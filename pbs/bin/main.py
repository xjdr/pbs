#!/usr/bin/env python

import os
import sys
import yaml
import requests

from IPython import embed
from progressbar import *

def parse_config(path):
  if os.path.exists(path):
    with open(path, "r") as f:
      return yaml.load(f)
  else:
    print "could not load lib file at %s" % path
    sys.exit(1)

def build_uri(dep):
  base_uri = 'http://ftp.us.debian.org/debian/pool/main/'
  complete_uri = base_uri + dep['name'][0] + '/' + dep['name']
  
  return complete_uri

def download_package(name, url):
  widgets = [FormatLabel('Downloading ' + name + ': '), Percentage(), Bar()]

  deb = requests.get(url, stream=True)
  if not deb.status_code == requests.codes.ok:
    print 'Download deb Failed'
    print deb.status_code
    print deb.text
    sys.exit(1)

  # pbar = ProgressBar(maxval=int(deb.headers['Content-Length']), widgets=widgets).start()
  pbar = ProgressBar(maxval=10000, widgets=widgets).start()

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
  manifest = parse_config("manifest.yml")

  for dep in manifest:
    group = dep['dep']['group']
    artifact = dep['dep']['artifact']
    version = dep['dep']['version']
    group_manifest = parse_config(group + '/' + artifact + '.yml')

    if group_manifest == None:
      print "THERE IS NOTHING HERE, YO"
    else:
      for deb in group_manifest:
	# print deb['dep']
	download_package(deb['dep']['name'].split('/')[1], build_uri(deb['dep']))
      # name = lib['dep']['artifact'] + '-' + lib['dep']['version']
    # download_file(build_uri(group, artifact, version), name)
  sys.exit(0)

if __name__ == "__main__":
  main()
