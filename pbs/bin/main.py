#!/usr/bin/env python

import commands
import os
import sys
import yaml
import requests
import urllib2

#from IPython import embed
#from progressbar import *
from tqdm import tqdm

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
  #widgets = [FormatLabel('Downloading ' + name + ': '), Percentage(), Bar()]
  
  deb = requests.get(url, stream=True)
  if not deb.status_code == requests.codes.ok:
    print 'Download deb Failed'
    print deb.status_code
    print deb.text
    sys.exit(1)

 # pbar = ProgressBar(maxval=10000, widgets=widgets).start() # TODO(JR): Fix the PB max value

  pbar = tqdm(total=4096)
  pbar.set_description("Downloading " + name + ":")
  try:
    if not os.path.exists(pkg_path):
      os.makedirs(pkg_path)

    with open(pkg_path+"/"+ name, 'wb') as f:
      for chunk in deb.iter_content(chunk_size=1024):
        pbar.update(12)
        if chunk: # filter out keep-alive new chunks
          f.write(chunk)
          f.flush()

    pbar.close()

  except Exception as e:
    print 'Download ' + name + ' Failed'
    print e

def setup_env(env):
  chroot_path=os.path.join(env['target'])
  #Create a base folder for building the image
  create_folder(chroot_path)
  return chroot_path

def unpack_pkg(pkgname,gz,chroot_path):
  if(gz):
    unpackstr = "cd %s; ar p %s data.tar.gz | tar xz "%(chroot_path, pkgname);
  else:
    unpackstr = "cd %s; ar p %s data.tar.xz | tar xJ "%(chroot_path, pkgname);
  os.system(unpackstr);

def create_folder(path):
  if not os.path.exists(path):
    os.mkdir(path,0755);
  return path

def download_unpack(chroot_path,repoyml,group_manifest):
  for deb in group_manifest:
      # Download the package 
      download_package(deb['dep']['name'].split('/')[-1], chroot_path ,build_uri(deb['dep'],repoyml))
      # Unpack the package 
      unpack_pkg(deb['dep']['name'].split('/')[-1],deb['dep']['format']=='gz', chroot_path)

def download_packages(chroot_path,repoyml,group_manifest):
    for deb in group_manifest:
      download_package(deb['dep']['name'].split('/')[-1], chroot_path ,build_uri(deb['dep'],repoyml))


def install(group_manifest, chroot_path, pkg_path, force_install):
  if force_install:
    force_str="--force-depends"
  else:
    force_str=""

  for deb in group_manifest:
    force_install_str="LANG=C chroot %s /bin/bash -c \"dpkg %s --install %s/%s\""%(chroot_path,force_str,pkg_path,deb['dep']['name'].split('/')[-1])
    print force_install_str
    run_status=commands.getoutput(force_install_str)
    print run_status

def main():
  # print path
  manifest = parse_config(path)
  chroot_path=setup_env(manifest['env'])
  for dep in manifest['stages']:
    group = dep['dep']['group']
    artifact = dep['dep']['artifact']
    version = dep['dep']['version']
    group_manifest = parse_config(cwd+"/"+group + '/' + artifact + '.yml')
    pkg_path = "packages"
    pkg_path_abs = os.path.join(chroot_path,pkg_path)
    create_folder(pkg_path_abs)
    repoyml = cwd+"/"+group+"/repo.yml"
    if group_manifest == None:
      print "THERE IS NOTHING HERE, YO"
    else:
      if "defaults" in artifact:
        download_unpack(chroot_path,repoyml,group_manifest)
        #Move the packages to folder
        os.system("mv %s/*.deb %s"%(chroot_path,pkg_path_abs))
        os.system("cd %s; touch var/lib/dpkg/status"%(chroot_path))
      #Install all the packages with force-depends
      elif "stage1" in artifact:
        #Force install stage1 packages
        install(group_manifest, chroot_path, pkg_path, True)
      elif "stage2" in artifact:
        # Install stage2 packages normally
        install(group_manifest, chroot_path, pkg_path, False)
        run_status=commands.getoutput("LANG=C chroot %s /bin/bash -c \"dpkg --configure -a\""%(chroot_path))
        print run_status
      elif "system" in artifact:
        # Install system packages normally
        download_packages(chroot_path,repoyml,group_manifest)
        os.system("mv %s/*.deb %s"%(chroot_path,pkg_path_abs))
        install(group_manifest, chroot_path, pkg_path, False)
        run_status=commands.getoutput("LANG=C chroot %s /bin/bash -c \"dpkg --configure -a\""%(chroot_path))
        print run_status
  #   elif "networking" in artifact:
  #      download_packages(chroot_path,repoyml,group_manifest)
  #      install(group_manifest, chroot_path, pkg_path, False)
  #      os.system("mv %s/*.deb %s"%(chroot_path,pkg_path_abs))
  #      run_status=commands.getoutput("LANG=C chroot %s /bin/bash -c \"dpkg --configure -a\""%(chroot_path))
  #      print run_status

if __name__ == "__main__":
  main()
