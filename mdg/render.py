#!/usr/bin/python
import json
import os
from typing import Dict, Optional, List, Any

from jinja2 import Environment, FileSystemLoader, Template


from .config import settings
from .util import camelcase, snakecase, titlecase, sentencecase

from .uml import UMLPackage, UMLInstance


def output_level_copy(source_filename: str, dest_file_template: Template, package: UMLPackage) -> None:
    """ Render a jinja template as pass a UML package as data
    """

    # Render template for UML Package
    dest_filename: str = os.path.abspath(dest_file_template.render(package=package))
    dirname: str = os.path.dirname(dest_filename)

    # make sure computed distination path exists
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    print( source_filename )
    print( dest_filename )

    with open(source_filename) as source_fh:
        with open(dest_filename, 'w') as dest_fh:
            dest_fh.write(source_fh.read())


def output_level_package(source_template: Template, dest_file_template: Template, package: UMLPackage) -> None:
    """ Render a jinja template as pass a UML package as data
    """

    # Render template for UML Package
    dest_filename: str = os.path.abspath(dest_file_template.render(package=package))
    dirname: str = os.path.dirname(dest_filename)

    # make sure computed distination path exists
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    with open(dest_filename, 'w') as fh:
        fh.write(source_template.render(package=package))


def output_level_enum(source_template: Template, dest_file_template: Template, filter_template: Optional[Template], package: UMLPackage) -> None:
    """ Render a jinja template for each enumeration in the supplied package
    """

    # Loop through all enumerations in the UML Package, cheeck the filter result and output if True
    for enum in package.enumerations:
        if filter_template is None or filter_template.render(enum=enum) == "True":
            filename = os.path.abspath(dest_file_template.render(enum=enum))
            dirname = os.path.dirname(filename)

            # make sure computed distination path exists
            if not os.path.exists(dirname):
                os.makedirs(dirname)

            with open(filename, 'w') as fh:
                fh.write(source_template.render(enum=enum))


def output_level_class(source_template: Template, dest_file_template: Template, filter_template: Optional[Template], package: UMLPackage) -> None:
    """ Render a jinja template for each class in the supplied package
    """

    # Loop through all classes in the UML Package, cheeck the filter result and output if True
    for cls in package.classes:
        if filter_template is None or filter_template.render(cls=cls) == "True":
            filename = os.path.abspath(dest_file_template.render(cls=cls))
            dirname = os.path.dirname(filename)

            # make sure computed distination path exists
            if not os.path.exists(dirname):
                os.makedirs(dirname)

            with open(filename, 'w') as fh:
                fh.write(source_template.render(cls=cls))


def output_level_assoc(source_template: Template, dest_file_template: Template, filter_template: Optional[Template], package: UMLPackage):
    """ Render a jinja template for each association in the supplied package
    """

    # Loop through all associations in the UML Package, cheeck the filter result and output if True
    for assoc in package.associations:
        if filter_template is None or filter_template.render(association=assoc) == "True":
            filename = os.path.abspath(dest_file_template.render(association=assoc))
            dirname = os.path.dirname(filename)

            # make sure computed distination path exists
            if not os.path.exists(dirname):
                os.makedirs(dirname)

            with open(filename, 'w') as fh:
                fh.write(source_template.render(association=assoc))


def output_model(package: UMLPackage) -> None:
    """ Loops through model templates in the settings and calls render functions

        Each template consists of:
            dest: The filename of the output
            level: Do we generate a file for each package/class/enumeration/association or root
            source: Path to the jinja2 template
            filter: If supplied, If supplied The template must output "True" for a file to be generated
                E.g.: "{% if package.classes %}True{% else %}False{% endif %}"
    """
    print("Generating model output for package {}".format(package.path))

    # Create jinja2 filter dict to pass into templates
    filters = {
        'camelcase': camelcase,
        'snakecase': snakecase,
        'titlecase': titlecase,
        'sentencecase': sentencecase,
    }

    # Create jinja2 environmeent with filters
    source_env = Environment(loader=FileSystemLoader(settings['templates_folder']))
    source_env.filters = {**source_env.filters, **filters}

    # Loop through all template definitions in the config file
    template_definition: Dict
    for template_definition in settings['model_templates']:
        dest_file_template: Template = Template(os.path.join(settings['dest_root'], template_definition['dest']))
        dest_file_template.environment.filters = {**dest_file_template.environment.filters, **filters}

        if template_definition['level'] == 'copy':
            if package.parent is None:
                output_level_copy(os.path.join(settings['templates_folder'], template_definition['source']), dest_file_template, package)
        else:
            # Create jinja2 teemplates for the source file and dest file name
            source_template: Template = source_env.get_template(template_definition['source'])

            # Filter template is optional and used to skip a file generation.
            filter_template: Optional[Template] = None
            if 'filter' in template_definition.keys():
                filter_template = Template(template_definition['filter'])

            # Select the output renderer based on the level requested
            if template_definition['level'] == 'package':
                if filter_template is None or filter_template.render(package=package) == "True":
                    output_level_package(source_template, dest_file_template, package)
            elif template_definition['level'] == 'class':
                output_level_class(source_template, dest_file_template, filter_template, package)
            elif template_definition['level'] == 'enumeration':
                output_level_enum(source_template, dest_file_template, filter_template, package)
            elif template_definition['level'] == 'assocication':
                output_level_assoc(source_template, dest_file_template, filter_template, package)
            elif template_definition['level'] == 'root' and package.parent is None:
                output_level_package(source_template, dest_file_template, package)

    # Walk through the package hierarchy and recurse output
    child: UMLPackage
    for child in package.children:
        output_model(child)


def output_test_cases(test_cases: List[UMLInstance]) -> None:
    """ Test cases are parse into a list of UML instances. Loop through list and serialise
    """
    if settings['test_templates'] is None:
        print("No test templates")
        return

    print("Generating test case output")

    for case in test_cases:
        serialised = json.dumps(serialize_instance(case), indent=2)

        template_definition: Dict
        for template_definition in settings['test_templates']:
            filename_template: Template = Template(template_definition['dest'])
            filename: str = os.path.abspath(filename_template.render(ins=case))
            dirname: str = os.path.dirname(filename)

            # make sure computed distination path exists
            if not os.path.exists(dirname):
                os.makedirs(dirname)

            with open(filename, 'w') as fh:
                fh.write(serialised)


def serialize_instance(instance: UMLInstance):
    """ Generates a dictionary of attributes, values, dicts and lists from UML instance
        Recurses through associations originaing from supplied instance to serialise sub-objects
    """
    ret: Dict = {}

    # Extract attributes and their values
    for attr in instance.attributes:
        ret[attr.name] = attr.value

    # Loop through associations originating from this instance
    for assoc in instance.associations_from:
        dest: Any = assoc.destination
        # If the multiplicity is multiple then generate list
        if assoc.destination_multiplicity[1] == '*':
            if assoc.destination.name not in ret.keys():
                ret[assoc.destination.name] = [serialize_instance(dest), ]
            else:
                ret[assoc.destination.name].append(serialize_instance(dest))
        # If multiplicity is singular then generate dict
        else:
            ret[assoc.destination.name] = serialize_instance(dest)

    return ret
