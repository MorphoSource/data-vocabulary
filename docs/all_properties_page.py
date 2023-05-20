from collections import defaultdict
from os.path import join
from pathlib import Path

from dominate.tags import (
    div,
    h2
)
from pylode.rdf_elements import ONTDOC, PROP_PROPS
from pylode.utils import generate_fid
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS

from page import Page

class AllPropertiesPage(Page):
    """Creates HTML documentation page for all ontology Properties."""

    def __init__(self, ontology_filepath: str, ontology_prefix: str, destination_dir: Path = None):
        super().__init__(ontology_filepath, ontology_prefix, destination_dir)
        
        self.toc["go_to"].append({ "title": "Terms Index", "href": self.href_url(self.ns[1]) })

    def make_html(self):
        """ Generate and write HTML elements for ontology all Properties page """

        self.make_head()

        props = []

        # Get object properties
        for property_uri in self.ontpub.ont.subjects(predicate=RDF.type, object=OWL.ObjectProperty):
            props.append(self.get_property_attributes(property_uri))
               

        # Get data properties
        for property_uri in self.ontpub.ont.subjects(predicate=RDF.type, object=OWL.DatatypeProperty):
            props.append(self.get_property_attributes(property_uri))
        
        props_sorted = sorted(props, key=lambda d: d["property_uri"])

        with self.ontpub.content:
            h2("Properties")

        for prop in props_sorted:
            self.make_property_element(prop["property_uri"], prop["property_props"], prop["property_fid"])

        self.make_toc()

        html_path = join(self.destination_dir, "properties.html")
        open(html_path, "w").write(self.ontpub.doc.render())

    def get_property_attributes(self, property_uri):
        # get all properties of property
        property_props = defaultdict(list)
        for p_, o in self.ont.predicate_objects(subject=property_uri):
            # ... in the property list for this property
            if p_ in PROP_PROPS:
                if p_ == RDFS.subClassOf and (o, RDF.type, OWL.Restriction) in self.ont:
                    property_props[ONTDOC.restriction].append(o)
                else:
                    property_props[p_].append(o)

        # get fragment id and title for property
        if len(property_props[DCTERMS.title]) == 0:
            property_fid = generate_fid(None, property_uri, self.fids)
        else:
            property_fid = generate_fid(property_props[DCTERMS.title][0], property_uri, self.fids)

        return { 
            "property_uri": property_uri,
            "property_props": property_props,
            "property_fid": property_fid
        }
    
    def make_property_element(self, property_uri, property_props, property_fid):
        """ write html for class table to page_ontpub.doc """
        with self.ontpub.content:
            elems = div(id=property_fid, _class="section")
            elems.appendChild(
                self._element_html(
                    property_uri,
                    property_fid,
                    self.ont.qname(property_uri),
                    self.ont.value(property_uri, RDF.type),
                    PROP_PROPS,
                    property_props,
                )
            )
            elems.render()
