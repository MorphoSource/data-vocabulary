from collections import defaultdict
from os.path import join
from pathlib import Path

from dominate.tags import (
    div
)
from pylode.rdf_elements import ONTDOC, PROP_PROPS
from pylode.utils import generate_fid, make_title_from_iri
from rdflib import URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS
from rdflib.term import URIRef

from page import Page

class PropertyPage(Page):
    """Creates HTML documentation page for ontology Property."""

    def __init__(self, ontology_filepath: str, property_uri: str, destination_dir: Path = None):
        super().__init__(ontology_filepath, destination_dir)
        
        self.property_uri = property_uri
        self.property_props = defaultdict(list)
        self.property_fid = ""

        # URI refs in page (will hyperlink these using fragments)
        self.page_uris.append(URIRef(property_uri))

    def make_html(self):
        # get all properties of property
        for p_, o in self.ont.predicate_objects(subject=self.property_uri):
            # ... in the property list for this property
            if p_ in PROP_PROPS:
                if p_ == RDFS.subClassOf and (o, RDF.type, OWL.Restriction) in self.ont:
                    self.property_props[ONTDOC.restriction].append(o)
                else:
                    self.property_props[p_].append(o)

        # get fragment id and title for property
        if len(self.property_props[DCTERMS.title]) == 0:
            self.property_fid = generate_fid(None, self.property_uri, self.fids)
        else:
            self.property_fid = generate_fid(self.property_props[DCTERMS.title][0], self.property_uri, self.fids)

        self.make_head()
        self.make_property_element()

        html_path = join(self.destination_dir, "{}.html".format(generate_fid(None, self.property_uri, {})))
        open(html_path, "w").write(self.ontpub.doc.render())
    
    def make_property_element(self):
        """ write html for class table to page_ontpub.doc """
        with self.ontpub.content:
            elems = div(id=self.property_fid, _class="section")
            elems.appendChild(
                self._element_html(
                    self.property_uri,
                    self.property_fid,
                    self.ont.qname(self.property_uri),
                    self.ont.value(self.property_uri, RDF.type),
                    PROP_PROPS,
                    self.property_props,
                )
            )
            elems.render()

    