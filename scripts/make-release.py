#!/usr/bin/env python

"""Make a release by packaging binaries and uploading them to the server.

Usage:
  make-release.py [upload | simulate]
  
When run in "simulate" mode, this script only simulates upload without
actually uploading anything. Instead, the files are placed in the directory
named "temp".
"""

import datetime, os, re, shutil, sys, tempfile, zipfile
from docopt import docopt
from subprocess import call, check_call

server = "pandora.local"
project = "ampl"

summaries = {
  "amplgsl": "AMPL bindings for the GNU Scientific Library",
  "ampltabl": "ODBC table handler",
  "cbc": "COIN-OR Cbc solver",
  "gecode": "Gecode solver",
  "ipopt": "COIN-OR Ipopt solver",
  "jacop": "JaCoP solver"
}

sys2label = {
  "linux32": "OpSys-Linux",
  "linux64": "OpSys-Linux",
  "macosx": "OpSys-OSX",
  "win32": "OpSys-Windows",
  "win64": "OpSys-Windows"
}

def rmtree_if_exists(path):
  "Delete an entire directory tree if it exists."
  if os.path.exists(path):
    shutil.rmtree(path)

def upload(filename, summary, labels, simulate):
  "Upload a file to the server."
  print("Uploading {}".format(filename))
  return
  # TODO: implement
  from netrc import netrc
  authenticators = netrc().authenticators("code.google.com")
  username = authenticators[0]
  password = authenticators[2]
  if simulate:
    return
  status, reason, url = googlecode_upload.upload(
    filename, project, username, password, summary, labels)
  if not url:
    print('Google Code upload error: {} ({})'.format(reason, status))

def archive_and_upload(tempdir, simulate):
  "Create archives and upload them to the server."
  dir = os.path.join(tempdir, 'files')
  gecode_version = None
  for platform in reversed(sorted(sys2label.keys())):
    rmtree_if_exists(dir)
    print("Downloading binaries for {}:".format(platform))
    check_call("scp -r {}:/var/lib/buildbot/upload/{} {}".format(server, platform, dir),
        shell=True)
    # Get versions.
    versions_filename = os.path.join(dir, "versions")
    versions = {}
    if os.path.exists(versions_filename):
      with open(versions_filename) as f:
        for line in f:
          items = line.rstrip().split(' ')
          if len(items) < 2:
            continue
          version = items[1].rstrip(',')
          m = re.match(r'.*(driver|library)\(([0-9]+)\)', line)
          if m:
            version += '-' + m.group(2)
          versions[items[0].lower()] = version
    date = datetime.datetime.today()
    date = "{}{:02}{:02}".format(date.year, date.month, date.day)
    dirlen = len(dir) + 1
    jacop_version = versions['jacop']
    jacop_version = jacop_version[:jacop_version.rfind('-')]
    extra_files = {
      'amplgsl': ['gsl.ampl'],
      'gecode': ['gecode.ampl'],
      'ipopt': ['libipoptfort.dll:win', 'libblas.dll:win', 'libgfortran-3.dll:win',
                'libquadmath-0.dll:win', 'libgcc_s_seh-1.dll:win64', 'libgcc_s_dw2-1.dll:win32'],
      'jacop': ['ampljacop.jar', 'JaCoP-' + jacop_version + '.jar']
    }
    file_package = {'cp.ampl': None, 'cp.dll': None}
    for package, files in extra_files.iteritems():
      for f in files:
        file_package[f.split(':')[0]] = package
    # Upload individual files.
    paths = []
    for base, dirs, files in os.walk(dir):
      for file in files:
        path = os.path.join(base, file)
        name = path[dirlen:]
        if name == "versions" or name in file_package or 'ampl-lic' in name:
          continue
        basename = os.path.splitext(name)[0]
        suffix = versions.get(basename, date)
        archive_name = os.path.join(tempdir, "{}-{}-{}.zip".format(basename, suffix, platform))
        with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zip:
          zip.write(path, name)
          files = extra_files.get(basename)
          if files:
            for f in files:
              items = f.split(':')
              filename = items[0]
              if len(items) > 1 and not platform.startswith(items[1]):
                continue
              extra_path = os.path.join(base, filename)
              zip.write(extra_path, filename)
              paths.append(extra_path)
        upload(archive_name, summaries[basename], [sys2label[platform]], simulate)
        paths.append(path)
    # Upload all in one archive.
    archive_name = os.path.join(tempdir, "ampl-open-{}-{}.zip".format(date, platform))
    with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zip:
      for path in paths:
        zip.write(path, path[dirlen:])
      zip.write("LICENSE", "LICENSE")
    upload(archive_name, "Open-source AMPL solvers and libraries", None, simulate)
  return versions

def update_redir_page(repo_path, name, versions):
  filename = os.path.join(repo_path, name + ".html")
  with open(filename, 'r') as f:
    content = f.read()
  version = re.sub(r".*-()", r"\1", versions.get(name))
  print 'changing version: {}, {}'.format(versions.get(name), version)
  content = re.sub(r"q={}\+(\d+)".format(name), "q={}+{}".format(name, version), content)
  with open(filename, 'w') as f:
    f.write(content)

if __name__ == '__main__':
  args = docopt(__doc__)
  simulate = args['simulate']
  if not args['upload'] and not simulate:
    print(__doc__)
    sys.exit()
  if simulate:
    tempdir = "temp"
    rmtree_if_exists(tempdir)
    os.mkdir(tempdir)
  else:
    tempdir = tempfile.mkdtemp()
  try:
    versions = archive_and_upload(tempdir, simulate)
    # Update the pages that redirect to the downloads for the most recent versions of binaries.
    #check_call(["git", "clone", "https://code.google.com/p/ampl.wiki/"], cwd=tempdir)
    #ampl_wiki_path = os.path.join(tempdir, "ampl.wiki")
    #update_redir_page(ampl_wiki_path, 'ampltabl', versions)
    #update_redir_page(ampl_wiki_path, 'gecode', versions)
    #update_redir_page(ampl_wiki_path, 'jacop', versions)
    #if call(["git", "diff-index", "--quiet", "HEAD"], cwd=ampl_wiki_path):
    #  check_call(["git", "commit", "-a", "-m", "update versions"], cwd=ampl_wiki_path)
    #  if not simulate:
    #    check_call(["git", "push"], cwd=ampl_wiki_path)
  finally:
    if not simulate:
      shutil.rmtree(tempdir)