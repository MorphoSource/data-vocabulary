from pathlib import Path
from typing import Optional, List, Tuple, Union, cast

import markdown
from dominate.tags import (
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
    meta,
    p,
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
from pylode.rdf_elements import ONTDOC, OWL_SET_TYPES, RESTRICTION_TYPES
from pylode.utils import generate_fid
from rdflib import BNode, Literal, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, SKOS
from rdflib.paths import ZeroOrMore
from rdflib.term import URIRef

from const import MSDOC, ONT_TYPES

class Page:
    """Creates HTML documentation page for ontology subjects."""

    def __init__(self, ontology_filepath: str, ontology_prefix: str, destination_dir: Path = None):
        self.ontpub = OntPub(ontology_filepath)
        self.ont = self.ontpub.ont
        self.back_onts = self.ontpub.back_onts
        self.fids = self.ontpub.fids
        self.ns = self.ontpub.ns
        self.props_labeled = self.ontpub.props_labeled

        self.ontology_prefix = ontology_prefix

        self.destination_dir = destination_dir
        self.toc = {
            "go_to": [],
            "on_page": []
        }

        # URI refs in page (will hyperlink these using fragments)
        self.page_uris = []

        # Modify some prop labels
        self.props_labeled[RDFS.domain]["title"] = Literal("Property Of")
        self.props_labeled[RDFS.domain]["description"] = Literal("Class or classes that reference this property term as metadata to describe or contextualize a record. Also known as rdfs:domain.")

        self.props_labeled[RDFS.range]["title"] = Literal("Value Restriction")
        self.props_labeled[RDFS.range]["description"] = Literal("Value(s) of the property must conform to this restriction. For Datatype Properties, value must be of the listed data type. For Object Properties, value must be an individual instance of the listed class. Also known as rdfs:range.")

        self.props_labeled[ONTDOC.inDomainOf]["title"] = Literal("Property Terms")
        self.props_labeled[ONTDOC.inDomainOf]["description"] = Literal("Property terms referenced by this class as metadata to describe or contextualize a record. Inverse of rdfs:domain.")

        self.props_labeled[ONTDOC.inRangeOf]["title"] = Literal("Value Of Property Terms")
        self.props_labeled[ONTDOC.inRangeOf]["description"] = Literal("An individual instance of this class can be the value of these property terms. Inverse of rdfs:range.")

        # Add new prop labels
        self.props_labeled[MSDOC.superClassInDomainOf] = {}
        self.props_labeled[MSDOC.superClassInDomainOf]["title"] = Literal("Property Terms Inherited")
        self.props_labeled[MSDOC.superClassInDomainOf]["description"] = Literal("Property terms inherited as Sub Class that are also referenced as metadata to describe or contextualize a record.")
        self.props_labeled[MSDOC.superClassInDomainOf]["ont_title"] = "MS Ontology Documentation Profile."

        self.props_labeled[MSDOC.namedIndividuals] = {}
        self.props_labeled[MSDOC.namedIndividuals]["title"] = Literal("Individual Instances")
        self.props_labeled[MSDOC.namedIndividuals]["description"] = Literal("Individual instance entities that are of this Class type.")
        self.props_labeled[MSDOC.namedIndividuals]["ont_title"] = "MS Ontology Documentation Profile."

    def make_head(self):
        with self.ontpub.doc.head:
            meta(charset="utf-8")
            meta(name="viewport", content="width=device-width, initial-scale=1")
            link(href="msterms.css", rel="stylesheet", type="text/css")
            link(href=f"{self.ontology_prefix}/msterms.css", rel="stylesheet", type="text/css")
            script(
                raw("\n" + self.ontpub._make_schema_org().serialize(format="json-ld") + "\n\t"),
                type="application/ld+json",
                id="schema.org",
            )

    def make_toc(self):
        with self.ontpub.doc:
            self.ontpub.toc = div(id = "toc")
        
        with self.ontpub.toc:
            elems = div(id = "toc-content")
            if len(self.toc["go_to"]):
                elems.appendChild(div("Go to", _class = "toc-title"))
                for item in self.toc["go_to"]:
                    elems.appendChild(div(a(item["title"], href=item["href"]), _class="toc-item"))

            if len(self.toc["on_page"]):
                elems.appendChild(div("On this page", _class = "toc-title"))
                for item in self.toc["on_page"]:
                    elems.appendChild(div(a(item["title"], href=item["href"]), _class="toc-item"))
            
            elems.render()
    
    def _element_html(self, iri: URIRef, fid: str, title_: str, ont_type: URIRef, props_list,
        this_props_):
        if ont_type not in ONT_TYPES:
            ONT_TYPES[ont_type] = ("t", ont_type)

        """Makes all the HTML (div, title & table) for one instance of a
        given RDF class, e.g. owl:Class or owl:ObjectProperty"""
        d = div(
            h3(
                "Term Name {}".format(title_),
                sup(
                    ONT_TYPES[ont_type][0],
                    _class="sup-" + ONT_TYPES[ont_type][0],
                    title=ONT_TYPES[ont_type][1],
                ),
            ),
            id=fid,
            _class="property entity",
        )

        # Special fields before
        t = table(tr(td("Term IRI"), td(a(str(iri), href=self.href_url(iri, allow_frag = False)))))
        if DCTERMS.title in this_props_:
            t.appendChild(tr(td("Label"), td(this_props_[DCTERMS.title])))

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

        # Special fields after
        if "http" in ONT_TYPES[ont_type][1]:
            t.appendChild(
                tr(
                    td("Type"), 
                    td(a(str(ONT_TYPES[ont_type][1]), href=self.href_url(ONT_TYPES[ont_type][1], allow_frag = False)))
                )
            )
        else:
            t.appendChild(tr(td("Type"), td(ONT_TYPES[ont_type][1])))

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
            t = tr(td(prop), td(o))
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
            if prop != DCTERMS.description:
                d = div()
                items = [self._rdf_obj_single_html(x, rdf_type_=rdf_type, prop=prop) for x in obj]
                for idx, anchor in enumerate(items):
                    if idx != 0: d.appendChild(span(" | "))
                    d.appendChild(anchor)
                return d
            else: 
                d = div()
                for x in obj:
                    d.appendChild(div(self._rdf_obj_single_html(x, rdf_type_=rdf_type, prop=prop)))
                return d
    
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

            # old defunct behavior, uses fragment is iri namespace is from this ontology
            # if self.ns is not None and str(iri__).startswith(self.ns):
            #     fid = generate_fid(None, iri__, self.fids)
            #     if fid is not None:
            #         frag_iri = "#" + fid

            # use the objet's label for hyperlink text, if it has one
            # if not, try and use a prefixed hyperlink
            # if not, just the iri
            # v = self.back_onts.value(
            #     subject=iri__, predicate=DCTERMS.title
            # )  # no need to check other labels: inference
            # if v is None:
            #     v = self.ont.value(subject=iri__, predicate=DCTERMS.title)

            # the above has been commented out in favor of just using the prefixed short term for all
            v = None

            if v is not None:
                anchor = a(f"{v}", href=self.href_url(iri__))
            else:
                try:
                    qname = self.ont.compute_qname(iri__, False)
                    if "ASGS" in qname[2]:
                        print(qname)
                except Exception:
                    qname = iri__
                prefix = "" if qname[0] == "" else f"{qname[0]}:"

                if isinstance(qname, tuple) and qname[2]:
                    anchor = a(
                        f"{prefix}{qname[2]}",
                        href=self.href_url(iri__),
                    )
                else:
                    anchor = a(
                        f"{iri__}", href=self.href_url(iri__)
                    )

            # this appends sup-case context codes (c, dp, op)
            # removing this for now
            # if rdf_type__ is not None:
            #     ret = span()
            #     ret.appendChild(anchor)
            #     ret.appendChild(
            #         sup(
            #             ONT_TYPES[rdf_type__][0],
            #             _class="sup-" + ONT_TYPES[rdf_type__][0],
            #             title=ONT_TYPES[rdf_type__][1],
            #         )
            #     )
            #     return ret
            # else:
            #     return anchor
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
    
    def href_url(self, iri, allow_frag = True):
        """ Returns fragment ID or term URL for link HREF based on conditions"""
        
        # if iri is on current page, use a fragment link
        frag_iri = None
        if iri in self.page_uris and allow_frag:
            fid = generate_fid(None, iri, self.fids)
            if fid is not None:
                frag_iri = "#" + fid

        if frag_iri is not None:
            return frag_iri
        else:
            # will return iri, but will make relative if iri root is www.morphosource.org
            if "http://www.morphosource.org" in iri:
                return iri.replace("http://www.morphosource.org", "")
            else:
                return iri