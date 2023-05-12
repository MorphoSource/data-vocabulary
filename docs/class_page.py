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
from rdflib.term import URIRef

from const import CLASS_PROPS, MSDOC
from page import Page

class ClassPage(Page):
    """ Creates HTML documentation page for ontology Class and associated Properties. """

    def __init__(self, ontology_filepath: str, class_uri: str, destination_dir: Path = None):
        super().__init__(ontology_filepath, destination_dir)

        self.class_uri = class_uri
        self.class_fid = ""
        self.class_title = ""

        # URI refs in page (will hyperlink these using fragments)
        self.page_uris.append(URIRef(class_uri))

        self.toc["go_to"].append({ "title": "Terms Index", "href": self.href_url(self.ns[1]) })

    def make_html(self):
        """ Generate and write HTML elements for ontology Class page """
        
        self.class_props = self.get_class_properties(self.class_uri)

        # prepare for listing class inDomainOf properties
        self.class_props[ONTDOC.inDomainOf].sort()
        self.page_uris.extend(self.class_props[ONTDOC.inDomainOf])

        # is class a subclass of a MS class? if so, get superclass props
        if RDFS.subClassOf in self.class_props and self.ns[1] in self.class_props[RDFS.subClassOf][0]:
            self.superclass_uri = self.class_props[RDFS.subClassOf][0]
            self.superclass_props = self.get_class_properties(self.superclass_uri)
            self.class_props[MSDOC.superClassInDomainOf] = self.superclass_props[ONTDOC.inDomainOf]
            self.class_props[MSDOC.superClassInDomainOf].sort()
            self.page_uris.extend(self.class_props[MSDOC.superClassInDomainOf])
            self.toc["go_to"].append({ 
                "title": f"{self.superclass_props[DCTERMS.title][0]} Class", 
                "href": self.href_url(self.superclass_uri) 
            })
        else:
            self.superclass_uri = None
            self.superclass_props = {}

        # get fragment id and title for class
        if len(self.class_props[DCTERMS.title]) == 0:
            self.class_fid = generate_fid(None, self.class_uri, self.fids)
            self.class_title = make_title_from_iri(self.class_uri)
        else:
            self.class_fid = generate_fid(self.class_props[DCTERMS.title][0], self.class_uri, self.fids)
            self.class_title = self.class_props[DCTERMS.title]

        self.make_head()
        self.make_class_element()
        if self.superclass_uri:
            self.make_property_elements(
                self.superclass_props[DCTERMS.title][0], 
                "superclassProperties",
                self.superclass_props[ONTDOC.inDomainOf]
            )
        self.make_property_elements(
            self.class_title[0], 
            "properties",
            self.class_props[ONTDOC.inDomainOf]
        )
        self.make_toc()

        html_path = join(self.destination_dir, "{}.html".format(self.class_fid))
        open(html_path, "w").write(self.ontpub.doc.render())

    def make_class_element(self):
        """ write html for class table to page_ontpub.doc """
        elem_title = "{} Class".format(self.class_title[0])
        self.toc["on_page"].append({ "title": elem_title, "href": f"#{self.class_fid}" })

        with self.ontpub.content:
            elems = div(id=self.class_fid, _class="section")
            elems.appendChild(h2(elem_title))
            elems.appendChild(
                self._element_html(
                    self.class_uri,
                    self.class_fid,
                    self.ont.qname(self.class_uri),
                    OWL.Class,
                    CLASS_PROPS,
                    self.class_props,
                )
            )
            elems.render()

    def make_property_elements(self, section_title, section_fid, properties):
        elem_title = "{} Properties".format(section_title)
        self.toc["on_page"].append({ "title": elem_title, "href": f"#{section_fid}" })

        with self.ontpub.content:
            elems = div(id=section_fid, _class="section")
            elems.appendChild(h2(elem_title)) # todo add class name back in?
            
            for s_ in properties:
                this_props = defaultdict(list)
                
                # get all properties of this object (excluding some)
                for p_, o in self.ont.predicate_objects(subject=s_):
                    # ... in the property list for this class
                    if p_ in PROP_PROPS:
                        if p_ == RDFS.subClassOf and (o, RDF.type, OWL.Restriction) in self.ont:
                            this_props[ONTDOC.restriction].append(o)
                        else:
                            this_props[p_].append(o)
                if RDFS.domain in this_props: this_props.pop(RDFS.domain)

                # get fragment id and title for property
                if len(this_props[DCTERMS.title]) == 0:
                    this_fid = generate_fid(None, s_, self.fids)
                else:
                    this_fid = generate_fid(this_props[DCTERMS.title][0], s_, self.fids)
                
                elems.appendChild(
                    self._element_html(
                        s_,
                        this_fid,
                        self.ont.qname(s_),
                        self.ont.value(s_, RDF.type),
                        PROP_PROPS,
                        this_props
                    )
                )
            elems.render()

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