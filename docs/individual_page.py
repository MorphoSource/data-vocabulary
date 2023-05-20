from collections import defaultdict
from os.path import join
from pathlib import Path

from dominate.tags import (
    div
)
from pylode.rdf_elements import ONTDOC
from pylode.utils import generate_fid, make_title_from_iri
from rdflib import URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS
from rdflib.term import URIRef

from const import INDIVIDUAL_PROPS
from page import Page

class IndividualPage(Page):
    """Creates HTML documentation page for ontology Individual."""

    def __init__(self, ontology_filepath: str, ontology_prefix: str, individual_uri: str, destination_dir: Path = None):
        super().__init__(ontology_filepath, ontology_prefix, destination_dir)
        
        self.individual_uri = individual_uri
        self.individual_props = defaultdict(list)
        self.individual_fid = ""

        # URI refs in page (will hyperlink these using fragments)
        self.page_uris.append(URIRef(individual_uri))

        self.toc["go_to"].append({ "title": "Terms Index", "href": self.href_url(self.ns[1]) })

    def make_html(self):
        # get all properties of individual
        for p_, o in self.ont.predicate_objects(subject=self.individual_uri):
            # ... in the individual list for this individual
            if p_ in INDIVIDUAL_PROPS:
                if p_ == RDFS.subClassOf and (o, RDF.type, OWL.Restriction) in self.ont:
                    self.individual_props[ONTDOC.restriction].append(o)
                else:
                    self.individual_props[p_].append(o)

        # Find individual RDF.type class URI
        self.class_uri = list(self.ont.objects(self.individual_uri, RDF.type))[1]
        self.toc["go_to"].append({ "title": f"{self.ont.value(self.class_uri, DCTERMS.title)} Class", "href": self.href_url(self.class_uri) })

        # get fragment id and title for individual
        if len(self.individual_props[DCTERMS.title]) == 0:
            self.individual_fid = generate_fid(None, self.individual_uri, self.fids)
        else:
            self.individual_fid = generate_fid(self.individual_props[DCTERMS.title][0], self.individual_uri, self.fids)

        self.make_head()
        self.make_individual_element()
        self.make_toc()

        html_path = join(self.destination_dir, "{}.html".format(generate_fid(None, self.individual_uri, {})))
        open(html_path, "w").write(self.ontpub.doc.render())
    
    def make_individual_element(self):
        """ write html for class table to page_ontpub.doc """
        with self.ontpub.content:
            elems = div(id=self.individual_fid, _class="section")
            elems.appendChild(
                self._element_html(
                    self.individual_uri,
                    self.individual_fid,
                    self.ont.qname(self.individual_uri),
                    self.class_uri,
                    INDIVIDUAL_PROPS,
                    self.individual_props,
                )
            )
            elems.render()

    