from collections import defaultdict
from os.path import join
from pathlib import Path

from dominate.tags import (
    h2,
    div,

)
from pylode.rdf_elements import CLASS_PROPS, ONTDOC, PROP_PROPS
from pylode.utils import generate_fid, make_title_from_iri
from rdflib import URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS
from rdflib.term import URIRef

from page import Page

class ClassPage(Page):
    """Creates HTML documentation page for ontology Class and associated Properties."""

    def __init__(self, ontology_filepath: str, class_uri: str, destination_dir: Path = None):
        super().__init__(ontology_filepath, destination_dir)

        self.class_uri = class_uri
        self.class_props = defaultdict(list)
        self.class_fid = ""
        self.class_title = ""

        # URI refs in page (will hyperlink these using fragments)
        self.page_uris.append(URIRef(class_uri))

    def make_html(self):
        # get all properties of class
        for p_, o in self.ont.predicate_objects(subject=self.class_uri):
            # ... in the property list for this class
            if p_ in CLASS_PROPS:
                if p_ == RDFS.subClassOf and (o, RDF.type, OWL.Restriction) in self.ont:
                    self.class_props[ONTDOC.restriction].append(o)
                else:
                    self.class_props[p_].append(o)

        # prepare for listing class inDomainOf properties
        self.class_props[ONTDOC.inDomainOf].sort()
        self.page_uris.extend(self.class_props[ONTDOC.inDomainOf])

        # get fragment id and title for class
        if len(self.class_props[DCTERMS.title]) == 0:
            self.class_fid = generate_fid(None, self.class_uri, self.fids)
            self.class_title = make_title_from_iri(self.class_uri)
        else:
            self.class_fid = generate_fid(self.class_props[DCTERMS.title][0], self.class_uri, self.fids)
            self.class_title = self.class_props[DCTERMS.title]

        self.make_head()
        self.make_class_element()
        self.make_property_elements()

        html_path = join(self.destination_dir, "{}.html".format(self.class_fid))
        open(html_path, "w").write(self.ontpub.doc.render())

    def make_class_element(self):
        """ write html for class table to page_ontpub.doc """
        with self.ontpub.content:
            elems = div(id=self.class_fid, _class="section")
            elems.appendChild(h2("{} Class".format(self.class_title[0])))
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

    def make_property_elements(self):
        with self.ontpub.content:
            elems = div(id="properties", _class="section")
            elems.appendChild(h2("{} Properties".format(self.class_title[0]))) # todo add class name back in?
            
            for s_ in self.class_props[ONTDOC.inDomainOf]:
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
