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
      if 'fd' not in file:
        file['fd'] = open(file)
  def preflight(self):
    '''Sanity checks prior to looking for orphaned configuration'''
    # check that all files have templates which exist in the configuration
    templates_used_by_files = set([file['template'] for file in self.files])
    templates_in_configuration = set(self.config.get_templates().keys())
    if not templates_used_by_files < templates_in_configuration:
      self.logger.error("The following templates referenced for input files are not present in the configuration: %s", templates_in_configuration-templates_used_by_files)
      return False

    # check that all
  def find_orphans(self):
    for file in self.files:
      # get the template
      orphans = self.templates.execute(file['template'])
      if orphans is None:
        self.logger.error("File %s references template %s which is not loaded.  Aborting search for orphans.", file['filename'], file['template'])
        return None
      # execute the template to parse this configuration

      # find configuration elements with no references and return them
    pass
  def reap_orphans(self):
    pass
