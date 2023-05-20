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
from individual_page     import IndividualPage
from property_page       import PropertyPage

class Docs:
    """Wraps Ontology Document class to create multiple HTML documentation pages."""

    def __init__(self, ontology_filepath: str, ontology_prefix: str):
        self.ontology_filepath = ontology_filepath
        self.ontology_prefix = ontology_prefix
        self.ontpub = OntPub(ontology_filepath)
        self.namespace_uri = self.ontpub.ns[1]

    def make_html_pages(self, destination_dir: Path = None):
        """Makes and writes multiple HTML documentation pages."""

        # Write index
        Index(self.ontology_filepath, self.ontology_prefix, destination_dir).make_html()

        # Write all page
        AllPage(self.ontology_filepath, self.ontology_prefix, destination_dir).make_html()

        # Write all classes page
        AllClassesPage(self.ontology_filepath, self.ontology_prefix, destination_dir).make_html()

        # Write all properties page
        AllPropertiesPage(self.ontology_filepath, self.ontology_prefix, destination_dir).make_html()

        # Write class pages
        for subject_uri in self.ontpub.ont.subjects(predicate=RDF.type, object=OWL.Class):
            if self.namespace_uri in subject_uri:
                ClassPage(self.ontology_filepath, self.ontology_prefix, subject_uri, destination_dir).make_html()

        # Write object property pages
        for subject_uri in self.ontpub.ont.subjects(predicate=RDF.type, object=OWL.ObjectProperty):
            if self.namespace_uri in subject_uri:
                PropertyPage(self.ontology_filepath, self.ontology_prefix, subject_uri, destination_dir).make_html()

        # Write data property pages
        for subject_uri in self.ontpub.ont.subjects(predicate=RDF.type, object=OWL.DatatypeProperty):
            if self.namespace_uri in subject_uri:
                PropertyPage(self.ontology_filepath, self.ontology_prefix, subject_uri, destination_dir).make_html()

        # Write individual names
        for subject_uri in self.ontpub.ont.subjects(predicate=RDF.type, object=OWL.NamedIndividual):
            if self.namespace_uri in subject_uri:
                IndividualPage(self.ontology_filepath, self.ontology_prefix, subject_uri, destination_dir).make_html()


