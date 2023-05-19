from glob import glob
from os import remove
from os.path import isfile, join
from pathlib import Path
from shutil import copy

from pylode import OntPub
from rdflib.namespace import OWL, RDF

from all_classes_page    import AllClassesPage
from all_page            import AllPage
from all_properties_page import AllPropertiesPage
from class_page          import ClassPage
from index               import Index
from property_page       import PropertyPage

class Docs:
    """Wraps Ontology Document class to create multiple HTML documentation pages."""

    def __init__(self, ontology_filepath: str):
        self.ontology_filepath = ontology_filepath
        self.ontpub = OntPub(ontology_filepath)
        self.namespace_uri = self.ontpub.ns[1]

    def make_html_pages(self, destination_dir: Path = None):
        """Makes and writes multiple HTML documentation pages."""

        # Write index
        Index(self.ontology_filepath, destination_dir).make_html()

        # Write all page
        AllPage(self.ontology_filepath, destination_dir).make_html()

        # Write all classes page
        AllClassesPage(self.ontology_filepath, destination_dir).make_html()

        # Write all properties page
        AllPropertiesPage(self.ontology_filepath, destination_dir).make_html()

        # Write class pages
        for subject_uri in self.ontpub.ont.subjects(predicate=RDF.type, object=OWL.Class):
            if self.namespace_uri in subject_uri:
                ClassPage(self.ontology_filepath, subject_uri, destination_dir).make_html()

        # Write object property pages
        for subject_uri in self.ontpub.ont.subjects(predicate=RDF.type, object=OWL.ObjectProperty):
            if self.namespace_uri in subject_uri:
                PropertyPage(self.ontology_filepath, subject_uri, destination_dir).make_html()

        # Write data property pages
        for subject_uri in self.ontpub.ont.subjects(predicate=RDF.type, object=OWL.DatatypeProperty):
            if self.namespace_uri in subject_uri:
                PropertyPage(self.ontology_filepath, subject_uri, destination_dir).make_html()

ontology_filepath = "/Users/jmw110/code/data-vocabulary/morphosource_terms.rdf"
output_dir = "/Users/jmw110/code/MorphoSource/public/terms/"
namespace_root = "ms"
namespace_dir = join(output_dir, namespace_root)
print(namespace_dir)
delete_previous_files = True

if delete_previous_files:
    files = glob(join(output_dir, "*"))
    for f in files:
        if isfile(f): remove(f)
    namespace_dir_files = glob(join(namespace_dir, "*"))
    for f in namespace_dir_files:
        if isfile(f): remove(f)

copy("static/msterms.css", namespace_dir)
copy("static/diagram.png", namespace_dir)
copy(ontology_filepath, join(output_dir, f"{namespace_root}.rdf"))

Docs(ontology_filepath).make_html_pages(namespace_dir)
