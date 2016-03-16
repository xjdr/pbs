#!/usr/bin/env python

import commands
import os
import sys
import yaml
import requests
import urllib2
import shutil
import time

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
      complete_uri = base_uri + dep['name']
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
  create_folder(chroot_path,True)
  make_block_disk(chroot_path)
  return chroot_path

def unpack_pkg(pkgname,gz,chroot_path):
  if(gz):
    unpackstr = "cd %s; ar p %s data.tar.gz | tar xz "%(chroot_path, pkgname);
  else:
    unpackstr = "cd %s; ar p %s data.tar.xz | tar xJ "%(chroot_path, pkgname);
  os.system(unpackstr);

def create_folder(path,remove_if_present=False):

  if (os.path.exists(path) and remove_if_present):
    shutil.rmtree(path)

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
    install_str="LANG=C DEBIAN_FRONTEND=noninteractive DEBCONF_NONINTERACTIVE_SEEN=true chroot %s /bin/bash -c \"dpkg %s --install %s/%s\""%(chroot_path,force_str,pkg_path,deb['dep']['name'].split('/')[-1])
    print install_str
    run_status=commands.getoutput(install_str)
    print run_status

def configure_all(chroot_path):
  run_status=commands.getoutput("LANG=C chroot %s /bin/bash -c \"dpkg --configure -a\""%(chroot_path))
  print run_status

def touch_shadow(chroot_path):
  run_status=commands.getoutput("LANG=C chroot %s /bin/bash -c \"touch /etc/shadow\""%(chroot_path))
  print run_status
  run_status=commands.getoutput("LANG=C chroot %s /bin/bash -c \"touch /etc/gshadow\""%(chroot_path))
  print run_status

def bind_sys(chroot_path):
  run_status=commands.getoutput("mount -o bind /dev %s/dev"%(chroot_path))
  print run_status
  run_status=commands.getoutput("mount -o bind /dev/pts %s/dev/pts"%(chroot_path))
  print run_status
  run_status=commands.getoutput("mount -o bind /proc %s/proc"%(chroot_path))
  print run_status
  run_status=commands.getoutput("mount -o bind /sys %s/sys"%(chroot_path))
  print run_status

def download_install(chroot_path,repoyml,group_manifest,pkg_path,pkg_path_abs):
  download_packages(chroot_path,repoyml,group_manifest)
  os.system("mv %s/*.deb %s"%(chroot_path,pkg_path_abs))
  install(group_manifest, chroot_path, pkg_path, False)
  configure_all(chroot_path)

def make_block_disk(chroot_path):
  raw_file="output.raw"
  commands.getoutput("dd if=/dev/zero of=%s bs=512 count=5242880"%(raw_file))
  time.sleep(5)
  commands.getoutput("losetup -f %s"%(raw_file))
  loop_dev="/dev/loop0"
  commands.getoutput("losetup -a")
  commands.getoutput("mkfs.ext4 -L ProdNG /dev/loop0")
  commands.getoutput("mount /dev/loop0 %s"%(chroot_path))

def extlinux(chroot_path):
  r = commands.getoutput("LANG=C chroot %s /bin/bash -c \"extlinux --install \\boot\""%(chroot_path))
  print r
  boot_path=os.path.join(chroot_path,"boot")
  conf_file=os.path.join(boot_path,"extlinux.conf")
  for file in os.listdir(boot_path):
    if file.startswith("initrd"):
      initrd=os.path.join("/boot",file)
    elif file.startswith("vmlinuz"):
      vmlinuz=os.path.join("/boot",file)
  file = open(conf_file,"w")
  file.write("DEFAULT PRODNG \nPROMPT 1 \nTIMEOUT 60 \n  SAY Now booting the kernel from SYSLINUX...\n")
  file.write("LABEL PRODNG\n")
  file.write("  KERNEL %s\n"%(vmlinuz))
  file.write("  APPEND rw initrd=%s root=LABEL=ProdNG\n"%(initrd))
  file.close()
  
def reconfigure_all(chroot_path):
  pkg_list=commands.getoutput("LANG=C DEBIAN_FRONTEND=noninteractive DEBCONF_NONINTERACTIVE_SEEN=true chroot " + chroot_path + " dpkg -l | egrep 'all|amd' | awk {'print $2'} ").split()
  for pkg in pkg_list:
    print " reconfiguring pkg ",pkg
    reconfig_cmd="LANG=C DEBIAN_FRONTEND=noninteractive DEBCONF_NONINTERACTIVE_SEEN=true chroot " + chroot_path + " dpkg-reconfigure " + pkg
    print reconfig_cmd
    result=commands.getstatusoutput(reconfig_cmd)
    print result
  

def update_initramfs(chroot_path):
  update_status=commands.getstatusoutput("chroot " + chroot_path + " update-initramfs -u")
  print update_status
  

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
      continue

    if "defaults" in artifact:
      print "\n\n####################  Installing the base packages  ############################\n\n"
      download_unpack(chroot_path,repoyml,group_manifest)
      #Move the packages to folder
      os.system("mv %s/*.deb %s"%(chroot_path,pkg_path_abs))
      os.system("cd %s; touch var/lib/dpkg/status"%(chroot_path))
    #Install all the packages with force-depends
    elif "stage1" in artifact:
      #Force install stage1 packages
      install(group_manifest, chroot_path, pkg_path, True)
    elif "stage2" in artifact:
      print "\n\n####################  Installing the stage2 packages  ############################\n\n"
      # Install stage2 packages normally
      install(group_manifest, chroot_path, pkg_path, False)
      configure_all(chroot_path)
    elif "system" in artifact:
      print "\n\n####################  Installing the system packages  ############################\n\n"
      # Install system packages normally
      touch_shadow(chroot_path)
      download_install(chroot_path,repoyml,group_manifest,pkg_path,pkg_path_abs)
    elif "networking" in artifact:
      print "\n\n####################  Installing the netowrking packages  ############################\n\n"
      bind_sys(chroot_path)
      download_install(chroot_path,repoyml,group_manifest,pkg_path,pkg_path_abs)
    elif "development" in artifact:
      print "\n\n####################  Installing the development packages  ############################\n\n"
      download_install(chroot_path,repoyml,group_manifest,pkg_path,pkg_path_abs)
    elif "physical" in artifact:
      print "\n\n####################  Installing the physical packages  ############################\n\n"
      download_install(chroot_path,repoyml,group_manifest,pkg_path,pkg_path_abs)
 
  extlinux(chroot_path)
  reconfigure_all(chroot_path) 
  update_initramfs(chroot_path)

if __name__ == "__main__":
  main()
