from collections import defaultdict
from os.path import join
from pathlib import Path

from dominate.tags import (
    h2,
    div,
)
from pylode.rdf_elements import ONTDOC, PROP_PROPS
from pylode.utils import generate_fid, make_title_from_iri
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS

from const import CLASS_PROPS, MSDOC
from page import Page

class AllPage(Page):
    """ Creates HTML documentation page for all ontology Classes and Properties. """

    def __init__(self, ontology_filepath: str, ontology_prefix: str, destination_dir: Path = None):
        super().__init__(ontology_filepath, ontology_prefix, destination_dir)

        self.toc["go_to"].append({ "title": "Terms Index", "href": self.href_url(self.ns[1]) })

    def make_html(self):
        """ Generate and write HTML elements for ontology all Classes and Properties page """

        self.make_head()

        # get all properties first to add to page_uri
        self.get_all_properties()
        self.page_uris.extend([p["property_uri"] for p in self.props])

        self.make_all_class_elements()
        self.make_all_property_elements()
        self.make_toc()

        html_path = join(self.destination_dir, "all.html")
        open(html_path, "w").write(self.ontpub.doc.render())

    def make_all_class_elements(self):
        with self.ontpub.content:
            h2("Classes", id="classes")
        self.toc["on_page"].append({ "title": "Classes", "href": "#classes" })
        
        for class_uri in self.ontpub.ont.subjects(predicate=RDF.type, object=OWL.Class):
            if self.ontpub.ns[1] in class_uri:
                class_props = self.get_class_properties(class_uri)

                # is class a subclass of a MS class? if so, get superclass props
                if RDFS.subClassOf in class_props and self.ns[1] in class_props[RDFS.subClassOf][0]:
                    superclass_uri = class_props[RDFS.subClassOf][0]
                    superclass_props = self.get_class_properties(superclass_uri)
                    class_props[MSDOC.superClassInDomainOf] = superclass_props[ONTDOC.inDomainOf]
                    class_props[MSDOC.superClassInDomainOf].sort()
                else:
                    self.superclass_uri = None
                    self.superclass_props = {}

                if len(class_props[DCTERMS.title]) == 0:
                    class_fid = generate_fid(None, class_uri, self.fids)
                    class_title = make_title_from_iri(class_uri)
                else:
                    class_fid = generate_fid(class_props[DCTERMS.title][0], class_uri, self.fids)
                    class_title = class_props[DCTERMS.title]

                self.page_uris.append(class_uri)
                self.make_class_element(class_uri, class_title, class_fid, class_props)

    def get_class_properties(self, class_uri: str):
        """ get all properties of class """
        class_props = defaultdict(list)
        for p_, o in self.ont.predicate_objects(subject=class_uri):
            # ... in the property list for this class
            if p_ in CLASS_PROPS:
                if p_ == RDFS.subClassOf and (o, RDF.type, OWL.Restriction) in self.ont:
                    class_props[ONTDOC.restriction].append(o)
                else:
                    class_props[p_].append(o)
        return class_props
    
    def make_class_element(self, class_uri, class_title, class_fid, class_props):
        """ write html for class table to page_ontpub.doc """
        elem_title = "{} Class".format(class_title[0])
        self.toc["on_page"].append({ "title": elem_title, "href": f"#{class_fid}" })

        with self.ontpub.content:
            elems = div(id=class_fid, _class="section")
            elems.appendChild(h2(elem_title))
            elems.appendChild(
                self._element_html(
                    class_uri,
                    class_fid,
                    self.ont.qname(class_uri),
                    OWL.Class,
                    CLASS_PROPS,
                    class_props,
                )
            )
            elems.render()

    def get_all_properties(self):
        self.props = []

        # Get object properties
        for property_uri in self.ontpub.ont.subjects(predicate=RDF.type, object=OWL.ObjectProperty):
            self.props.append(self.get_property_attributes(property_uri))
               

        # Get data properties
        for property_uri in self.ontpub.ont.subjects(predicate=RDF.type, object=OWL.DatatypeProperty):
            self.props.append(self.get_property_attributes(property_uri))
        
        self.props = sorted(self.props, key=lambda d: d["property_uri"])

    def make_all_property_elements(self):
        with self.ontpub.content:
            h2("Properties", id="properties")
        self.toc["on_page"].append({ "title": "Properties", "href": "#properties" })

        for prop in self.props:
            self.make_property_element(prop["property_uri"], prop["property_props"], prop["property_fid"])

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