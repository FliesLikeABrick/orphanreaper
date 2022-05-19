import glob
import logging
import yaml


'''The below class is not in use, but may be developed further if the Templates class 
becomes too cluttered with helpers for the actual template-specific logic'''
class Template():
  '''Helper class for handling file content with a specific template's behavior'''
  def __init__(self, config_contents, logger=None):
    self.logger = logger if logger else logging.getLogger()
    self.config_contents = config_contents
    self.section = None

    self.load()
  def load(self):
    '''Load attributes/behavior from the configuration provided to __init__'''

class Templates():
  '''Class to load the vendor/OS-specific template yaml which defines the objects that the tool should inspect and clean up'''
  def __init__(self, config, logger=None):
    self.logger = logger if logger else logging.getLogger()
    self.config = config
    self.index = None
  def load(self):
    '''Public method for triggering load of template files, and secondary actions such as building the index of templates based on name'''
    return self._load() and self._build_template_index()
  def _load(self):
    '''Load all templates from globs listed in the configuration file'''
    number_of_loaded_templates = 0
    if not self.config.has_section('templates'):
      self.logger.error("No templates are referenced in configuration from %s and %s", self.ucf, self.dcf)
      return None
    for template_config_row in self.config.get_section('templates'):
      number_of_loaded_templates_from_this_row = 0
      # each entry in this list is a row with a glob that matches one or more template files to load
      if 'path_glob' not in template_config_row:
        self.logger.warning("Skipping a row of configuration which does not contain any templates path_glob definition.  The content of this row is: %s", template_config_row)
        continue
      template_files = glob.glob(template_config_row['path_glob'])
      # dict of file path to contents
      template_config_row['file_contents'] = {}
      for template_file in template_files:
        try:
          with open(template_file) as f:
            template_file_data = f.read()
        except Exception as exc:
          self.logger.error("Failed to open template file %s, check file existence, permissions, etc.  Exception raised: %s", template_file, exc)
          return None
        try:
          template_file_yaml = yaml.safe_load(template_file_data)
        except Exception as exc:
          self.logger.error("Failed to load YAML from template file %s, check file contents.  Exception raised: %s", template_file, exc)
          return None
        if template_file in template_config_row['file_contents']:
          # this should not be able to happen, it would require two files of the same name in the same glob from the config
          self.logger.error("Template file %s appears to already be loaded, but the glob %s may be matching it or one of the same name again, please check configuration and template files for sanity.", template_file, template_config_row['path_glob'])
          return None
        template_config_row['file_contents'][template_file] = template_file_yaml
        number_of_loaded_templates_from_this_row += 1
        number_of_loaded_templates += number_of_loaded_templates_from_this_row
      self.logger.info("Loaded %s templates from path_glob %s", number_of_loaded_templates, template_config_row['path_glob'])
    return number_of_loaded_templates
  def _build_template_index(self):
    '''To be used only after load() is called - build a dictionary based index of names to templates within the configuration. 
    Log an error and return False when duplicate template names are encountered within one directory or if other undefined conditions are encountered'''
    self.index = {}
    for template_config_row in self.config.get_section('templates'):
      template_names_in_this_path = {}
      for template_file, file_contents in template_config_row['file_contents'].items():
        template_name = file_contents['meta']['name']
        if template_name in template_names_in_this_path:
          self.logger.error("Template file %s is attempting to use the name %s which is already in use from template file %s", template_file, template_names_in_this_path[template_name])
          return False
        # this will overwrite entries in the order they appear in the configuration, if the check above passed
        self.index[template_name] = template_config_row 
        # update the cache of template names used in this path/glob of files
        template_names_in_this_path[template_name] = template_file
    return True
  def get(self, template_name):
    '''Return a template when referenced by name'''
    if self.index is None:
      self.logger.error("Template index has been accessed before it was built.  Application behavior may continue with incomplete results.")
      return None
    if template_name in self.index:
      return index[template_name]
    else:
      return None
 

  def parse(self, file, template_name):
    '''Parse configuration and return elements'''
    # call helper method to get configuration sections depending on block style
    
    # keys used in each row: type, name, contents


    return elements
