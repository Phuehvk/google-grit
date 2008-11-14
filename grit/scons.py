#!/usr/bin/python2.4
# Copyright (c) 2006-2008 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

'''SCons integration for GRIT.
'''

# NOTE:  DO NOT IMPORT ANY GRIT STUFF HERE - we import lazily so that grit and
# its dependencies aren't imported until actually needed.

import os
import types

def _IsDebugEnabled():
  return 'GRIT_DEBUG' in os.environ and os.environ['GRIT_DEBUG'] == '1'

def _SourceToFile(source):
  '''Return the path to the source file, given the 'source' argument as provided
  by SCons to the _Builder or _Emitter functions.
  '''
  # Get the filename of the source.  The 'source' parameter can be a string,
  # a "node", or a list of strings or nodes.
  if isinstance(source, types.ListType):
    # TODO(gspencer):  Had to add the .rfile() method to the following
    # line to get this to work with Repository() directories.
    # Get this functionality folded back into the upstream grit tool.
    #source = str(source[0])
    source = str(source[0].rfile())
  else:
    # TODO(gspencer):  Had to add the .rfile() method to the following
    # line to get this to work with Repository() directories.
    # Get this functionality folded back into the upstream grit tool.
    #source = str(source))
    source = str(source.rfile())
  return source


def _Builder(target, source, env):
  from grit import grit_runner
  from grit.tool import build
  options = grit_runner.Options()
  # This sets options to default values  TODO(joi) Remove verbose
  options.ReadOptions(['-v'])
  options.input = _SourceToFile(source)
  
  # TODO(joi) Check if we can get the 'verbose' option from the environment.  
  
  builder = build.RcBuilder()
  
  # Get the CPP defines from the environment.
  for flag in env.get('RCFLAGS', []):
    if flag.startswith('/D'):
      flag = flag[2:]
    name, val = build.ParseDefine(flag)
    # Only apply to first instance of a given define
    if name not in builder.defines:
      builder.defines[name] = val
  
  # To ensure that our output files match what we promised SCons, we
  # use the list of targets provided by SCons and update the file paths in
  # our .grd input file with the targets.
  builder.scons_targets = [str(t) for t in target]
  builder.Run(options, [])
  return None  # success


def _Emitter(target, source, env):
  '''A SCons emitter for .grd files, which modifies the list of targes to
  include all files in the <outputs> section of the .grd file as well as
  any other files output by 'grit build' for the .grd file.
  '''
  from grit import util
  from grit import grd_reader
  
  # TODO(gspencer):  Had to use .abspath, not str(target[0]), to get
  # this to work with Repository() directories.
  # Get this functionality folded back into the upstream grit tool.
  #base_dir = util.dirname(str(target[0]))
  base_dir = util.dirname(target[0].abspath)
  
  grd = grd_reader.Parse(_SourceToFile(source), debug=_IsDebugEnabled())
  
  target = []
  lang_folders = {}
  # Add all explicitly-specified output files
  for output in grd.GetOutputFiles():
    path = os.path.join(base_dir, output.GetFilename())
    target.append(path)
    if _IsDebugEnabled():
      print "GRIT: Added target %s" % path
    if output.attrs['lang'] != '':
      lang_folders[output.attrs['lang']] = os.path.dirname(path)
  
  # Add all generated files, once for each output language.
  for node in grd:
    if node.name == 'structure':
      # TODO(joi) Should remove the "if sconsdep is true" thing as it is a
      # hack - see grit/node/structure.py
      if node.HasFileForLanguage() and node.attrs['sconsdep'] == 'true':
        for lang in lang_folders:
          path = node.FileForLanguage(lang, lang_folders[lang],
                                      create_file=False,
                                      return_if_not_generated=False)
          if path:
            target.append(path)
            if _IsDebugEnabled():
              print "GRIT: Added target %s" % path
  
  # return target and source lists
  return (target, source)


def _Scanner(file_node, env, path):
  '''A SCons scanner function for .grd files, which outputs the list of files
  that changes in could change the output of building the .grd file.
  '''
  from grit import grd_reader
  
  grd = grd_reader.Parse(str(file_node), debug=_IsDebugEnabled())
  files = []
  for node in grd:
    if (node.name == 'structure' or node.name == 'skeleton' or
        (node.name == 'file' and node.parent and
         node.parent.name == 'translations')):
      files.append(os.path.abspath(node.GetFilePath()))
  return files


# Function name is mandated by newer versions of SCons.
def generate(env):
  # Importing this module should be possible whenever this function is invoked
  # since it should only be invoked by SCons.
  import SCons.Builder
  import SCons.Action
  
  # The varlist parameter tells SCons that GRIT needs to be invoked again
  # if RCFLAGS has changed since last compilation.
  action = SCons.Action.FunctionAction(_Builder, varlist=['RCFLAGS'])
  
  builder = SCons.Builder.Builder(action=action,
                              emitter=_Emitter,
                              src_suffix='.grd')
  
  scanner = env.Scanner(function=_Scanner, name='GRIT', skeys=['.grd'])
  
  # add our builder and scanner to the environment
  env.Append(BUILDERS = {'GRIT': builder})
  env.Prepend(SCANNERS = scanner)


# Function name is mandated by newer versions of SCons.
def exists(env):
  return 1

