from collections import defaultdict
from copy import deepcopy
from os.path import join
from pathlib import Path

from dominate.tags import (
    h2,
    div,

)
from pylode.rdf_elements import ONTDOC, PROP_PROPS
from pylode.utils import generate_fid, make_title_from_iri
from rdflib import Graph
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS
from rdflib.term import URIRef

from const import CLASS_PROPS, INDIVIDUAL_PROPS, MSDOC, SERIALIZE_EXCLUDED_PROPS
from page import Page

class ClassPage(Page):
    """ Creates HTML documentation page for ontology Class and associated Properties. """

    def __init__(self, ontology_filepath: str, ontology_prefix: str, class_uri: str, destination_dir: Path = None):
        super().__init__(ontology_filepath, ontology_prefix, destination_dir)

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
        if self.class_props[ONTDOC.inDomainOf]:
            self.class_props[ONTDOC.inDomainOf].sort()
            self.class_prop_properties = self.get_property_properties(self.class_props[ONTDOC.inDomainOf])
            self.page_uris.extend(self.class_props[ONTDOC.inDomainOf])
        else:
            self.class_props.pop(ONTDOC.inDomainOf)
            self.class_prop_properties = {}

        # is class a subclass of a MS class? if so, get superclass props
        if RDFS.subClassOf in self.class_props and self.ns[1] in self.class_props[RDFS.subClassOf][0]:
            self.superclass_uri = self.class_props[RDFS.subClassOf][0]
            self.superclass_props = self.get_class_properties(self.superclass_uri)
            self.superclass_prop_properties = self.get_property_properties(self.superclass_props[ONTDOC.inDomainOf])

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
            self.superclass_prop_properties = {}

        # get and prepare class individuals, if any exist
        self.class_individuals = self.get_class_individuals(self.class_uri)
        if self.class_individuals:
            self.class_props[MSDOC.namedIndividuals] = list(self.class_individuals.keys())
            self.class_props[MSDOC.namedIndividuals].sort()
            self.page_uris.extend(self.class_props[MSDOC.namedIndividuals])

        # get fragment id and title for class
        if len(self.class_props[DCTERMS.title]) == 0:
            self.class_fid = generate_fid(None, self.class_uri, self.fids)
            self.class_title = make_title_from_iri(self.class_uri)
        else:
            self.class_fid = generate_fid(self.class_props[DCTERMS.title][0], self.class_uri, self.fids)
            self.class_title = self.class_props[DCTERMS.title]

        self.make_head()
        self.make_class_element()

        if self.superclass_uri and self.superclass_prop_properties:
            self.make_property_elements(
                self.superclass_props[DCTERMS.title][0], 
                "superclassProperties",
                self.superclass_prop_properties
            )
        if self.class_prop_properties:
            self.make_property_elements(
                self.class_title[0], 
                "properties",
                self.class_prop_properties
            )

        if self.class_individuals:
            self.make_individual_elements(
                self.class_title[0], 
                "individuals",
                self.class_individuals
            )

        self.make_toc()

        html_path = join(self.destination_dir, "{}.html".format(self.class_fid))
        open(html_path, "w").write(self.ontpub.doc.render())

        self.create_rdf_file()

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
            
            for property_uri, property_props in properties.items():
                coperty_props = deepcopy(property_props)                
                if RDFS.domain in coperty_props: coperty_props.pop(RDFS.domain)

                # get fragment id and title for property
                if len(coperty_props[DCTERMS.title]) == 0:
                    this_fid = generate_fid(None, property_uri, self.fids)
                else:
                    this_fid = generate_fid(coperty_props[DCTERMS.title][0], property_uri, self.fids)
                
                elems.appendChild(
                    self._element_html(
                        property_uri,
                        this_fid,
                        self.ont.qname(property_uri),
                        self.ont.value(property_uri, RDF.type),
                        PROP_PROPS,
                        coperty_props
                    )
                )
            elems.render()

    def make_individual_elements(self, section_title, section_fid, individuals):
        elem_title = "{} Individual Instances".format(section_title)
        self.toc["on_page"].append({ "title": elem_title, "href": f"#{section_fid}" })

        with self.ontpub.content:
            elems = div(id=section_fid, _class="section")
            elems.appendChild(h2(elem_title)) # todo add class name back in?
            
            for individual_uri, individual_props in individuals.items():
                coperty_props = deepcopy(individual_props)                
                if RDFS.domain in coperty_props: coperty_props.pop(RDFS.domain)

                # get fragment id and title for property
                if len(coperty_props[DCTERMS.title]) == 0:
                    this_fid = generate_fid(None, individual_uri, self.fids)
                else:
                    this_fid = generate_fid(coperty_props[DCTERMS.title][0], individual_uri, self.fids)
                
                elems.appendChild(
                    self._element_html(
                        individual_uri,
                        this_fid,
                        self.ont.qname(individual_uri),
                        self.class_uri,
                        INDIVIDUAL_PROPS,
                        coperty_props
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
    
    def get_class_individuals(self, class_uri: str):
        """ get all individual URIs of class and properties for each individual """
        class_individuals = {}

        for subject_uri in self.ont.subjects(predicate=RDF.type, object=class_uri):
            individual_props = defaultdict(list)
            
            # get all properties of this subject (excluding some)
            for p_, o in self.ont.predicate_objects(subject=subject_uri):
                # ... in the property list for this class
                if p_ in INDIVIDUAL_PROPS:
                    if p_ == RDFS.subClassOf and (o, RDF.type, OWL.Restriction) in self.ont:
                        individual_props[ONTDOC.restriction].append(o)
                    else:
                        individual_props[p_].append(o)
            
            class_individuals[subject_uri] = individual_props

        return class_individuals
    
    
    def get_property_properties(self, property_uris):
        """ get all properties of object and datatype properties associated with class """
        property_properties = {}

        for property_uri in property_uris:
            this_props = defaultdict(list)
                
            # get all properties of this object (excluding some)
            for p_, o in self.ont.predicate_objects(subject=property_uri):
                # ... in the property list for this class
                if p_ in PROP_PROPS:
                    if p_ == RDFS.subClassOf and (o, RDF.type, OWL.Restriction) in self.ont:
                        this_props[ONTDOC.restriction].append(o)
                    else:
                        this_props[p_].append(o)

            property_properties[property_uri] = this_props
        
        return property_properties

    def create_rdf_file(self):
        sub_graph = Graph()

        for ns_prefix, namespace in self.ont.namespaces():
            sub_graph.bind(ns_prefix, namespace)

        for p, o in self.ont.predicate_objects(subject = self.class_uri):
            if p not in SERIALIZE_EXCLUDED_PROPS:
                sub_graph.add((self.class_uri, p, o))

        for property_uri, property_props in self.class_prop_properties.items():
            for p, o in property_props.items():
                if p not in SERIALIZE_EXCLUDED_PROPS:
                    sub_graph.add((property_uri, p, o[0]))

        for property_uri, property_props in self.superclass_prop_properties.items():
            for p, o in property_props.items():
                if p not in SERIALIZE_EXCLUDED_PROPS:
                    sub_graph.add((property_uri, p, o[0]))

        sub_graph.serialize(
            destination=join(self.destination_dir, "{}.rdf".format(self.class_fid)),
            format="pretty-xml",
            base="http://www.morphosource.org/terms/ms"
        )