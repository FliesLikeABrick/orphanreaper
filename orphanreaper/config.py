import glob
import logging
import sys
import yaml

class Config():
  '''Class for loading Orphan Reaper's own configuration'''
  def __init__(self, ucf, dcf, logger=None):
    self.logger = logger if logger else logging.getLogger()
    self.ucf = ucf
    self.dcf = dcf
  def load(self):
    self._load_config_defaults()
    self._load_config()

  def _load_config_defaults(self):
    '''Load configuration defaults'''
    try:
        with open(self.dcf) as yf:
            self.cfg = yaml.safe_load(yf.read())
    except Exception as e:
        sys.stderr.write("Failed to load configuration defaults from file %s\n%s\n" % (self.dcf,str(e)))
        sys.exit(1)
  def _load_config(self):
    # If no user config file is specified, return the defaults.
    if self.ucf is None:
        self.logger.debug("Skipping load of config because self.ucf is None")
        return
    # open user configuration file
    try:
        with open(self.ucf) as yf:
            userCfg = yaml.safe_load(yf.read())
    except FileNotFoundError as e:
        sys.stderr.write("Failed to open configuration file %s\n%s\n" % (ucf,str(e)))
        sys.stderr.write("Copy reaper.cfg.example.yaml to reaper.cfg.yaml or\n")
        sys.stderr.write("use --defaults to run without a configuration file, which will all default values (not recommended).\n")
        sys.exit(1)
    except Exception as e:
        sys.stderr.write("Failed to load configuration file %s\n%s\n" % (ucf,str(e)))
        sys.exit(1)
    if not userCfg:
      self.logger.warning("User config %s contains no data, only configuration defaults from %s will be used", self.ucf, self.dcf)
      return
    # update the default's config sections
    # Alternatively this could recursively update the dcfg dict with self.cfg
    # in the meantime, however, this requires a line for each section of the config
    # and potentially more depth/care if layers of the config should not be wholesale replaced
    for section in userCfg.keys():
        if section in self.cfg:
            self.cfg[section].update(userCfg[section])
        else:
            self.cfg[section] = userCfg[section]
  def has_section(self, section_name):
    return section_name in self.cfg
  def get_section(self, section_name):
    if section_name in self.cfg:
      return self.cfg[section_name]
    else:
      self.logger.debug("Requested section_name %s which is not found in config", section_name)
      return None
