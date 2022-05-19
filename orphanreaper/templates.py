import ciscoconfparse
import glob
import logging
import re
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
      for template_file_name in template_files:
        try:
          with open(template_file_name) as f:
            template_file_data = f.read()
        except Exception as exc:
          self.logger.error("Failed to open template file %s, check file existence, permissions, etc.  Exception raised: %s", template_file_name, exc)
          return None
        try:
          template_file_yaml = yaml.safe_load(template_file_data)
        except Exception as exc:
          self.logger.error("Failed to load YAML from template file %s, check file contents.  Exception raised: %s", template_file_name, exc)
          return None
        if template_file_name in template_config_row['file_contents']:
          # this should not be able to happen, it would require two files of the same name in the same glob from the config
          self.logger.error("Template file %s appears to already be loaded, but the glob %s may be matching it or one of the same name again, please check configuration and template files for sanity.", template_file, template_config_row['path_glob'])
          return None
        template_config_row['file_contents'][template_file_name] = template_file_yaml
        number_of_loaded_templates_from_this_row += 1
        number_of_loaded_templates += number_of_loaded_templates_from_this_row
      self.logger.info("Loaded %s templates from path_glob %s", number_of_loaded_templates, template_config_row['path_glob'])
    return number_of_loaded_templates
  def _build_template_index(self):
    '''To be used only after load() is called - build a dictionary based index of names to templates within the configuration. 
    Log an error and return False when duplicate template names are encountered within one directory or if other undefined conditions are encountered'''
    self.index = {}
    for template_config_row in self.config.get_section('templates'):
      templates_in_this_path = {}
      for template_file_name, file_contents in template_config_row['file_contents'].items():
        template_slug = file_contents['meta']['slug']
        if template_slug in templates_in_this_path:
          self.logger.error("Template file %s is attempting to use the name %s which is already in use from template file %s", template_file_name, template_names_in_this_path[template_slug])
          return False
        # this will overwrite entries in the order they appear in the configuration, if the check above passed
        self.index[template_slug] = template_config_row 
        # update the cache of template names used in this path/glob of files
        templates_in_this_path[template_slug] = file_contents
    self.logger.debug("Template Index has loaded template slugs: %s", ','.join(self.index.keys()))
    return True
  def get(self, template_slug=None):
    '''Return a template when referenced by name.  Returns all templates when no name is specified'''
    if self.index is None:
      self.logger.error("Template index has been accessed before it was built.  Application behavior may continue with incomplete results.")
      return None
    if template_slug is None:
      return list(self.index.values())
    if template_slug in self.index:
      return self.index[template_slug]
    else:
      return None
 
  def get_objects(self, file):
    '''Returns a list of dicts describing configuration objects present in the given input file'''
    parser = ciscoconfparse.CiscoConfParse(config=file['lines'])
    template = self.get(file['template'])
    return_objects = []
    for obj_def in template['objects']:
      cfg_line_matches = parser.find_lines(obj_def['regex'])
      if cfg_line_matches:
        self.logger.debug("In input file %s, found %s matching lines for template `%s` object definition `%s`", file['filename'], len(matches), template['name'])
        # extract the object name
        # TODO - precompile regexes back when the configs were loaded
        for line in cfg_line_matches:
          new_obj = {}
          name_matches = re.search(obj_def['regex'], line)
          if not name_matches:
            self.logger.warning("In input file %s, the following line matched the initial search but a name could not be extracted.  Check template `%s` regex for object `%s`: %s", file['filename'], template['meta']['name'], obj_def['slug'], line)
            continue
          new_obj['name'] = name_matches.group(name)
          new_obj['type'] = obj_def['name']
          return_objects.append(new_obj)
      return return_objects
  def get_references(self, file):
    '''Returns a dictionary mapping of object-to-list-of-references for each object found in this file'''
    parser = ciscoconfparse.CiscoConfParse(config=file['lines'])
  def get_orphans(self, file):
    '''Returns list of dicts describing configuration objects present in the given input file which have no known configuration references'''
    objects = self.get_objects(file)
    references = self.get_references(file)
    for obj in objects:
      if obj['name'] not in references:
        self.logger.info("Object %s has no references", obj['name'])


