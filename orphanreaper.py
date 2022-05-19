#! /usr/bin/env python3
'''orphanreaper - locate orphaned configuration elements in text-based network device configurations, generate configlets for removal'''
import argparse
import glob
import logging
import os
import sys
from orphanreaper import reaper



class OrphanReaper():
  def __init__(self, logger=None):
    # always cd to the path of orpanreaper when this class is invoked, as numerous configurations, templates, etc use this location
    # for relative paths
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    self.logger = logger if logger else logging.getLogger()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(funcName)s: %(message)s')
    # this will be populated as a dictionary of sets of input filenames
    self.filenames = {}
    # this will be populated as a list of input files (described by dictionaries), after the filenames are sanitized and opened with file descriptors
    self.files = []
    # default to None.  If stdin is to be read, this will be updated with the name of the template
    # that should be used to evaluate stdin
    self.read_stdin = None
    # will be created after args are parsed and init() is called
    self.reaper = None
  def validate_and_open_files(self):
    '''Convert directories to lists of files, sanity-check files for existence, length, etc.  Operates on self.filenames, and populates self.files'''

    # first loop through looking for any templates that are expected to read content from stdin "-"
    # This must be done first to avoid treating "-" as an invalid filename in later tests
    # contains name of the first template to open stdin
    stdin_used = None
    for template_name, filenames in self.filenames.items():
      for filename in filenames:
        if filename == '-' and stdin_used:
          self.logger.error('Exiting -- stdin "-" can only be specified for one template; already used by template %s', stdin_used)
          sys.exit()
        elif filename == '-':
          self.files.append({'filename':'-', 'fd':sys.stdin, 'template':template_name})
          stdin_used = template_name
      if stdin_used:
        self.filenames[stdin_used].difference_update('-')
    # loop through again looking for any dictionaries and expanding those into the list of files contained therein.
    # this results in those files being validated in the next loop.
    for template_name, filenames in self.filenames.items():
      # set sizes cannot change during iteration, so keep a temporary list of files to add after iterating the list of input filenames
      add_files_to_template = set()
      remove_files_from_template = set()
      for filename in filenames:
        if os.path.isdir(filename):
          self.logger.debug("Found directory %s", filename)
          files_in_dir = glob.glob(filename + os.sep + '*')
          self.logger.info("Adding %s files from directory %s to list for template %s", len(files_in_dir), filename, template_name)
          self.logger.debug("Will be adding new files: %s", files_in_dir)
          add_files_to_template.update(set(files_in_dir))
          # this is a directory that should be popped off the list later
          remove_files_from_template.add(filename)
      self.logger.debug("Iteration of files for template %s complete, now removing %s entries that were converted to directories", template_name, len(remove_files_from_template))
      filenames.difference_update(remove_files_from_template)
      filenames.update(add_files_to_template)
      self.logger.debug("File list for template %s now contains: %s", template_name, self.filenames[template_name])          
    for template_name, filenames in self.filenames.items():
      remove_files_from_template = set()
      for filename in filenames:
        if os.path.isfile(filename):
          # this is a file.  Test that it is not empty
          if not os.path.getsize(filename):
            self.logger.debug("Detected empty file: %s ", filename)
            if self.args.skip_empty:
              self.logger.debug("skip_empty was specified, removing %s from files list and continuing with a warning", filename)
              self.logger.warning("Skipping empty file %s", filename)
              # remove the empty file from the list
              remove_files_from_template.add(filename)
              continue # do not open the file
            else:
              self.logger.error("Exiting due to empty file found during validation of input: %s", filename)
              sys.exit()
        else: # error
          if self.args.skip_missing:
            self.logger.debug("skip_missing was specified, removing %s from files list and continuing with a warning", filename)
            # remove the missing file from the list
            self.logger.warning("Skipping missing file %s", filename)
            remove_files_from_template.add(filename)
            continue # do not open the file
          else:
            self.logger.error("Exiting due to missing or invalid file found during validation of input: %s", filename)
            sys.exit()
        self.files.append({'filename':filename, 'fd':open(filename), 'template':template_name})
      self.logger.debug("Iteration of files for template %s complete, now removing %s entries that were found to be empty or missing", template_name, len(remove_files_from_template))
      self.filenames[template_name].difference_update(remove_files_from_template)
      self.logger.debug("File list for template %s now contains: %s", template_name, self.filenames[template_name])
      return len(self.files)
  def run(self):
    '''Run the CLI behavior'''

    # define parse command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-q','--quiet', action="store_true", help="Suppress informational output.  Errors and warnings will still be printed to stderr")
    parser.add_argument('-d','--debug', action="store_true", help="Debug output.  Overrides -q if both are specified")
    parser.add_argument('--config', default=os.path.dirname(os.path.realpath(__file__)) + os.sep + "conf" + os.sep + "reaper.cfg.yaml",help="Configuration file location.  Default: reaper.cfg.yaml")
    parser.add_argument('--defaultconfig', default=os.path.dirname(os.path.realpath(__file__)) + os.sep + "conf" + os.sep + "reaper.cfg.defaults.yaml",help="Configuration defaults file location.  Default: reaper.cfg.defaults.yaml.  Normal users should never change this.")
    parser.add_argument('--skip-missing', action="store_true", help="Treat missing and other bad files as warnings instead of errors")
    parser.add_argument('--skip-empty', action="store_true", help="Treat empty files as warnings instead of errors")
    parser.add_argument('deviceconfigs', nargs='+', help="Device config filename and the template to use for parsing.  Specify directory names instead of file names, for all files in that directory to be included with the specified template.")
    self.args = parser.parse_args()
    # set verbosity in logger
    if self.args.quiet:
      self.logger.setLevel(logging.WARN)
      self.logger.debug("args.quiet specified  - setting log level to logging.WARN")
    if self.args.debug:
      self.logger.setLevel(logging.DEBUG)
      self.logger.debug("args.debug specified  - setting log level to logging.DEBUG")
    # load device configs with specified syntax
    # dictionary of template name to set of files
    # intentionally using a set to dedupe
    self.filenames = {}
    for entry in self.args.deviceconfigs:
      template_name, filename = entry.split(':', 2)
      if template_name not in self.filenames:
        self.filenames[template_name] = set()
      self.filenames[template_name].add(filename)

    # validate that files exist, have at least 2 lines, etc
    files_opened = self.validate_and_open_files()
    self.logger.info("Successfully opened %s files", files_opened)
    # create reaper object, etc
    self.init()
    # identify orphans
    orphans = self.reaper.find_orphans()
    if orphans is None:
      self.logger.error("Application run aborted due to prior errors, see above.")
      sys.exit()
    # print the orphans, if requested and in the style specified

    # print the remediation script, if requested and in the style specified
    reaped = self.reaper.reap_orphans(orphans)
  def init(self):
      self.reaper = reaper.Reaper(ucf=self.args.config, dcf=self.args.defaultconfig, files=self.files, logger=self.logger)

if __name__ == '__main__':
  oreaper = OrphanReaper()
  oreaper.run()