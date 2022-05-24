'''Main business logic module for identifying orphans and proposing configuration changes'''
import logging
from . import config
from . import templates
class Reaper():
  '''Main logic class for Orphan Reaper: load configurations, parse objects, identify references, generate cleanup configuration scripts'''
  def __init__(self, ucf, dcf, files=None,logger=None):
    self.logger = logger if logger else logging.getLogger()
    self.config = config.Config(ucf, dcf)
    self.config.load()
    self.templates = templates.Templates(self.config)
    self.templates.load()
    self.files = files # list of dicts describing files

  def open_files(self):
    '''Loop through self.files and open each file that is not yet opened'''
    for file in self.files:
      if 'contents' not in file:
        with open(file) as f:
          file['contents'] = f.read()
  def preflight(self):
    '''Sanity checks prior to looking for orphaned configuration'''
    # check that all files have templates which exist in the configuration
    templates_used_by_files = set([file['template'] for file in self.files])
    self.logger.debug("Templates referenced by user input: %s", templates_used_by_files)
    templates_in_configuration = set(self.templates.index.keys())
    self.logger.debug("Templates loaded from configuration: %s", templates_in_configuration)
    if not templates_used_by_files <= templates_in_configuration:
      self.logger.error("The following templates referenced for input files are not present in the configuration: %s", templates_used_by_files-templates_in_configuration)
      return False

    return True
  def find_orphans(self):
    if not self.preflight():
      return None
    orphan_count = 0
    for file in self.files:
      
      file['orphans'] = self.templates.get_orphans(file)
      orphan_count += len(file['orphans'])
    return orphan_count
  def reap_orphans(self,orphans):
    pass
