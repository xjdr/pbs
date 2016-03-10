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

def build_uri(dep,repoyml):
  repos = parse_config(repoyml);
  try:
    base_uri = repos[dep['repo']]['url']
  except:
      print "URL not found in the yml for repo: "+dep['repo']
      sys.exit(1)
  complete_uri = base_uri + dep['name'][0] + '/' + dep['name']
  uri_true=validate_uri(complete_uri)
  if uri_true == 0:
      print " Download URI : " , complete_uri
      return complete_uri
  else:
      complete_uri = base_uri + '/' + dep['name']
      uri_true=validate_uri(complete_uri)
      if uri_true == 0:
          print " Download URI : " , complete_uri
          return complete_uri
      else:
         print " Not a valid Download link :"+ complete_uri
	 sys.exit(1)


def download_package(name, pkg_path ,url):
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
    if not os.path.exists(pkg_path):
      os.makedirs(pkg_path)

    with open(pkg_path+"/"+ name, 'wb') as f:
      for chunk in deb.iter_content(chunk_size=1024):
	pbar.update(12)
	if chunk: # filter out keep-alive new chunks
	  f.write(chunk)
	  f.flush()

    pbar.finish()

  except Exception as e:
    print 'Download ' + name + ' Failed'
    print e

def setup_env(env):
  chroot_path=os.path.join(env['target'])
  pkg_path = os.path.join(chroot_path,'packages')
  #Create a base folder for building the image
  if not os.path.exists(chroot_path):
    os.mkdir(chroot_path,0755);
  if not os.path.exists(pkg_path):
    os.mkdir(pkg_path,0755);
  return chroot_path

def unpack_pkg(pkgname,gz,chroot_path):
    if(gz):
        unpackstr = "cd %s; ar p %s data.tar.gz | tar xz "%(chroot_path, pkgname);
    else:
        unpackstr = "cd %s; ar p %s data.tar.xz | tar xJ "%(chroot_path, pkgname);
    os.system(unpackstr);

def main():
  print path
  manifest = parse_config(path)
  chroot_path=setup_env(manifest['env'])
  pkg_path = os.path.join(chroot_path,'packages')
  for dep in manifest['stages']:
    group = dep['dep']['group']
    artifact = dep['dep']['artifact']
    version = dep['dep']['version']
    group_manifest = parse_config(cwd+"/"+group + '/' + artifact + '.yml')
    repoyml = cwd+"/"+group+"/repo.yml"

    if group_manifest == None:
      print "THERE IS NOTHING HERE, YO"
    else:
      for deb in group_manifest:
        download_package(deb['dep']['name'].split('/')[-1], chroot_path ,build_uri(deb['dep'],repoyml))
        unpack_pkg(deb['dep']['name'].split('/')[-1],deb['dep']['format']=='gz', chroot_path)
      #Move the packages to folder
      os.system("mv %s/*.deb %s"%(chroot_path,pkg_path))
      os.system("cd %s; touch var/lib/dpkg/status"%(chroot_path))
      #Install all the packages with force-depends
      force_install_str="LANG=C chroot %s /bin/bash -c \"dpkg --force-depends --install %s/*.deb\""%(chroot_path,"packages")
      for i in range(0,3):
        os.system(force_install_str);
  sys.exit(0)

if __name__ == "__main__":
  main()
