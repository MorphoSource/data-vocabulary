from os.path import join
from pathlib import Path

from ontology_class_page import OntologyClassPage
from pylode import OntPub
from rdflib.namespace import OWL, RDF

class OntologyDocs:
    """Wraps Ontology Document class to create multiple HTML documentation pages."""

    def __init__(self, ontology_filepath: str):
        self.ontology_filepath = ontology_filepath
        self.ontpub = OntPub(ontology_filepath)

    def make_html_pages(self, destination_dir: Path = None):
        """Makes and writes multiple HTML documentation pages."""
        for subject_uri in self.ontpub.ont.subjects(predicate=RDF.type, object=OWL.Class):
            OntologyClassPage(self.ontology_filepath, subject_uri, join(destination_dir, "sections/")).make_html()

ontology_filepath = "/Users/jmw110/code/data-vocabulary/morphosource_terms.rdf"
output_dir = "output/"
OntologyDocs(ontology_filepath).make_html_pages(output_dir)
