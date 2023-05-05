from collections import defaultdict
from os.path import join
from pathlib import Path
from typing import Optional, List, Tuple, Union, cast

import markdown
from dominate.tags import (
    h2,
    br,
    th,
    pre,
    a,
    span,
    sup,
    tr,
    td,
    ul,
    li,
    code,
    table,
    h3,
    div,
    dt,
    dd,
    script,
    link
)
from dominate.util import raw
from pylode import OntPub
from pylode.rdf_elements import CLASS_PROPS, ONTDOC, ONT_TYPES, OWL_SET_TYPES, PROP_PROPS, RESTRICTION_TYPES
from pylode.utils import generate_fid, make_title_from_iri
from rdflib import BNode, Literal, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, SKOS
from rdflib.paths import ZeroOrMore
from rdflib.term import URIRef

class OntologyClassPage:
    """Creates HTML documentation page for ontology Class and associated Properties."""

    def __init__(self, ontology_filepath: str, class_uri: str, destination_dir: Path = None):
        self.ontpub = OntPub(ontology_filepath)
        self.ont = self.ontpub.ont
        self.back_onts = self.ontpub.back_onts
        self.fids = self.ontpub.fids
        self.ns = self.ontpub.ns
        self.class_uri = class_uri
        self.destination_dir = destination_dir

        # class attributes
        self.class_props = defaultdict(list)
        self.class_fid = ""
        self.class_title = ""

        # URI refs in page (will hyperlink these using fragments)
        self.page_uris = [URIRef(class_uri)]

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
    
    def make_head(self):
        with self.ontpub.doc.head:
            link(href="test.css", rel="stylesheet", type="text/css")
            script(
                raw("\n" + self.ontpub._make_schema_org().serialize(format="json-ld") + "\n\t"),
                type="application/ld+json",
                id="schema.org",
            )

    def make_class_element(self):
        """ write html for class table to page_ontpub.doc """
        with self.ontpub.content:
            elems = div(id=self.class_fid, _class="section")
            elems.appendChild(h2("{} Class".format(self.class_title[0])))
            elems.appendChild(
                self._element_html(
                    self.class_uri,
                    self.class_fid,
                    self.class_title,
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
                    this_title = make_title_from_iri(s_)
                else:
                    this_fid = generate_fid(this_props[DCTERMS.title][0], s_, self.fids)
                    this_title = this_props[DCTERMS.title]
                
                elems.appendChild(
                    self._element_html(
                        s_,
                        this_fid,
                        this_title,
                        self.ont.value(s_, RDF.type),
                        PROP_PROPS,
                        this_props
                    )
                )
            elems.render()
    
    def _element_html(self, iri: URIRef, fid: str, title_: str, ont_type: URIRef, props_list,
        this_props_):
        """Makes all the HTML (div, title & table) for one instance of a
        given RDF class, e.g. owl:Class or owl:ObjectProperty"""
        d = div(
            h3(
                title_,
                sup(
                    ONT_TYPES[ont_type][0],
                    _class="sup-" + ONT_TYPES[ont_type][0],
                    title=ONT_TYPES[ont_type][1],
                ),
            ),
            id=fid,
            _class="property entity",
        )
        t = table(tr(th("IRI"), td(code(str(iri)))))
        # order the properties as per PROP_PROPS list order
        for prop in props_list:
            if prop != DCTERMS.title:
                if prop in this_props_.keys():
                    t.appendChild(
                        self._prop_obj_pair_html(
                            "table",
                            prop,
                            self.ontpub.props_labeled.get(prop).get("title")
                            if self.ontpub.props_labeled.get(prop) is not None
                            else None,
                            self.ontpub.props_labeled.get(prop).get("description")
                            if self.ontpub.props_labeled.get(prop) is not None
                            else None,
                            self.ontpub.props_labeled.get(prop).get("ont_title")
                            if self.ontpub.props_labeled.get(prop) is not None
                            else None,
                            this_props_[prop],
                        )
                    )
        d.appendChild(t)
        return d
    
    def _prop_obj_pair_html(self, 
        table_or_dl: str,
        prop_iri: URIRef,
        property_title: Literal,
        property_description: Literal,
        ont_title: Literal,
        obj: List[Union[URIRef, BNode, Literal, Tuple[Union[URIRef, BNode], str]]],
        obj_type: Optional[str] = None,
    ):
        """Makes an HTML Definition list dt & dd pair or a Table tr, th & td set,
        for a given RDF property & resource pair"""
        prop = a(
            str(property_title).title(),
            title=str(property_description).rstrip(".") + ". Defined in " + str(ont_title),
            _class="hover_property",
            href=str(prop_iri),
        )
        o = self._rdf_obj_html(obj, rdf_type=obj_type, prop=prop_iri)

        if table_or_dl == "table":
            t = tr(th(prop), td(o))
        else:  # dl
            t = div(dt(prop), dd(o))

        return t
    
    def _rdf_obj_html(self,
        obj: List[Union[URIRef, BNode, Literal, Tuple[Union[URIRef, BNode], str]]],
        rdf_type=None,
        prop=None,
    ):
        """Makes a sensible HTML rendering of an RDF resource.

        Can handle IRIs, Blank Nodes of Agents [removed] or OWL Restrictions or Literals"""
        if len(obj) == 1:
            return self._rdf_obj_single_html(
                obj[0], rdf_type_=rdf_type, prop=prop
            )
        else:
            u_ = ul()
            for x in obj:
                u_.appendChild(
                    li(
                        self._rdf_obj_single_html(
                            x, rdf_type_=rdf_type, prop=prop
                        )
                    )
                )
            return u_
    
    def _rdf_obj_single_html(self,
        obj_: Union[URIRef, BNode, Literal, Tuple[Union[URIRef, BNode], str]],
        rdf_type_=None,
        prop=None,
    ):
        def _hyperlink_html(
            iri__: URIRef,
            rdf_type__: Optional[URIRef] = None,
        ):
            def _get_ont_type(iri___):
                types_we_know = [
                    OWL.Class,
                    OWL.ObjectProperty,
                    OWL.DatatypeProperty,
                    OWL.AnnotationProperty,
                    OWL.FunctionalProperty,
                    RDF.Property,
                ]

                this_objects_types = []
                for o in self.ont.objects(iri___, RDF.type):
                    if o in ONT_TYPES.keys():
                        this_objects_types.append(o)

                for x_ in types_we_know:
                    if x_ in this_objects_types:
                        return x_

                for o in self.back_onts.objects(iri___, RDF.type):
                    if o in ONT_TYPES.keys():
                        this_objects_types.append(o)

                for x_ in types_we_know:
                    if x_ in this_objects_types:
                        return x_

            # find type
            if rdf_type__ is None:
                rdf_type__ = _get_ont_type(iri__)

            # if iri is on current page, use a fragment link
            frag_iri = None
            if iri__ in self.page_uris:
                fid = generate_fid(None, iri__, self.fids)
                if fid is not None:
                    frag_iri = "#" + fid

            # old defunct behavior, uses fragment is iri namespace is from this ontology
            # if self.ns is not None and str(iri__).startswith(self.ns):
            #     fid = generate_fid(None, iri__, self.fids)
            #     if fid is not None:
            #         frag_iri = "#" + fid

            # use the objet's label for hyperlink text, if it has one
            # if not, try and use a prefixed hyperlink
            # if not, just the iri
            v = self.back_onts.value(
                subject=iri__, predicate=DCTERMS.title
            )  # no need to check other labels: inference
            if v is None:
                v = self.ont.value(subject=iri__, predicate=DCTERMS.title)
            if v is not None:
                anchor = a(f"{v}", href=frag_iri if frag_iri is not None else iri__)
            else:
                try:
                    qname = self.ont.compute_qname(iri__, False)
                    if "ASGS" in qname[2]:
                        print(qname)
                except Exception:
                    qname = iri__
                prefix = "" if qname[0] == "" else f"{qname[0]}:"

                if isinstance(qname, tuple):
                    anchor = a(
                        f"{prefix}{qname[2]}",
                        href=frag_iri if frag_iri is not None else iri__,
                    )
                else:
                    anchor = a(
                        f"{qname}", href=frag_iri if frag_iri is not None else iri__
                    )

            if rdf_type__ is not None:
                ret = span()
                ret.appendChild(anchor)
                ret.appendChild(
                    sup(
                        ONT_TYPES[rdf_type__][0],
                        _class="sup-" + ONT_TYPES[rdf_type__][0],
                        title=ONT_TYPES[rdf_type__][1],
                    )
                )
                return ret
            else:
                return anchor

        def _literal_html(obj__):
            if str(obj__).startswith("http"):
                return _hyperlink_html(cast(URIRef, obj__))
            else:
                if prop == SKOS.example:
                    return pre(str(obj__))
                else:
                    return raw(markdown.markdown(str(obj__)))

        def _restriction_html(obj__):
            prop = None
            card = None
            cls = None

            for px, o in self.ont.predicate_objects(obj__):
                if px != RDF.type:
                    if px == OWL.onProperty:
                        prop = _hyperlink_html(o)
                    elif px in RESTRICTION_TYPES + OWL_SET_TYPES:
                        if px in [
                            OWL.minCardinality,
                            OWL.minQualifiedCardinality,
                            OWL.maxCardinality,
                            OWL.maxQualifiedCardinality,
                            OWL.cardinality,
                            OWL.qualifiedCardinality,
                        ]:
                            if px in [OWL.minCardinality, OWL.minQualifiedCardinality]:
                                card = "min"
                            elif px in [
                                OWL.maxCardinality,
                                OWL.maxQualifiedCardinality,
                            ]:
                                card = "max"
                            elif px in [OWL.cardinality, OWL.qualifiedCardinality]:
                                card = "exactly"

                            card = span(span(card, _class="cardinality"), span(str(o)))
                        else:
                            if px == OWL.allValuesFrom:
                                card = "only"
                            elif px == OWL.someValuesFrom:
                                card = "some"
                            elif px == OWL.hasValue:
                                card = "value"
                            elif px == OWL.unionOf:
                                card = "union"
                            elif px == OWL.intersectionOf:
                                card = "intersection"

                                card = span(
                                    span(card, _class="cardinality"),
                                    raw(self._rdf_obj_single_html),
                                )
                            else:
                                card = span(
                                    span(card, _class="cardinality"),
                                    span(
                                        _hyperlink_html(
                                            o, OWL.Class
                                        )
                                    ),
                                )

            restriction = span(prop, card, br()) if card is not None else prop
            restriction = (
                span(restriction, cls, br()) if cls is not None else restriction
            )

            return span(restriction) if restriction is not None else "None"

        def _setclass_html(obj__):
            """Makes lists of (union) 'ClassX or Class Y or ClassZ' or
            (intersection) 'ClassX and Class Y and ClassZ'"""
            if (obj__, OWL.unionOf, None) in self.ont:
                joining_word = ' <span class="cardinality">or</span> '
            elif (obj__, OWL.intersectionOf, None) in self.ont:
                joining_word = ' <span class="cardinality">and</span> '
            else:
                joining_word = ' <span class="cardinality">,</span> '

            class_set = set()
            for o in self.ont.objects(obj__, OWL.unionOf | OWL.intersectionOf):
                for o2 in self.ont.objects(o, RDF.rest * ZeroOrMore / RDF.first):
                    class_set.add(
                        self._rdf_obj_single_html(
                            o2, OWL.Class
                        )
                    )

            return raw(joining_word.join([mem.render() for mem in class_set]))

        def _bn_html(obj__: BNode):
            # TODO: remove back_onts and fids if not needed by subfunctions
            # What kind of BN is it?
            # An Agent [removed], a Restriction or a Set Class (union/intersection)
            # handled all typing added in OntDoc inferencing
            if (obj__, RDF.type, OWL.Restriction) in self.ont:
                return _restriction_html(obj__)
            else:  # (obj, RDF.type, OWL.Class) in ont:  # Set Class
                return _setclass_html(obj__)

        if isinstance(obj_, Tuple) or isinstance(obj_, URIRef):
            ret = _hyperlink_html(
                obj_, rdf_type__=rdf_type_
            )
        elif isinstance(obj_, BNode):
            ret = _bn_html(obj_)
        else:  # isinstance(obj, Literal):
            ret = _literal_html(obj_)

        return ret if ret is not None else span()