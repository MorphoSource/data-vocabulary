from collections import defaultdict
from os.path import join
from pathlib import Path

from dominate.tags import (
    h2,
    div,
)
from pylode.rdf_elements import ONTDOC
from pylode.utils import generate_fid, make_title_from_iri
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS

from const import CLASS_PROPS, MSDOC
from page import Page

class AllClassesPage(Page):
    """ Creates HTML documentation page for all ontology Classes. """

    def __init__(self, ontology_filepath: str, destination_dir: Path = None):
        super().__init__(ontology_filepath, destination_dir)

        self.toc["go_to"].append({ "title": "Terms Index", "href": self.href_url(self.ns[1]) })

    def make_html(self):
        """ Generate and write HTML elements for ontology all Classes page """

        self.make_head()

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

                self.make_class_element(class_uri, class_title, class_fid, class_props)
        
        self.make_toc()

        html_path = join(self.destination_dir, "classes.html")
        open(html_path, "w").write(self.ontpub.doc.render())

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