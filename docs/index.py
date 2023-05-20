import io
from collections import defaultdict
from itertools import chain
from os.path import join
from pathlib import Path

import markdown
from dominate.tags import (
    a,
    div,
    dd,
    dl,
    dt,
    h1,
    h2,
    link,
    meta,
    script,
    strong,
    table,
    tbody,
    thead,
    th,
    tr,
    th,
    td
)
from dominate.util import raw
from pylode import OntPub
from pylode.rdf_elements import ONT_PROPS
from pylode.utils import generate_fid
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, SKOS, PROF

from page import Page

class Index(Page):
    """Creates HTML documentation page for ontology index root."""

    def __init__(self, ontology_filepath: str, ontology_prefix: str, destination_dir: Path = None):
        super().__init__(ontology_filepath, ontology_prefix, destination_dir)
        self.ontology_prefix = ontology_prefix

    def make_html(self):
        self.make_head()
        self.make_body()

        if self.destination_dir.endswith("/"):
            html_path = f"{self.destination_dir[:-1]}.html"
        else:
            html_path = f"{self.destination_dir}.html"

        open(html_path, "w").write(self.ontpub.doc.render())
    
    def make_body(self):
        self.make_metadata()
        self.make_introduction()
        self.make_class_section()
        self.make_namespaces()
        self.make_acknowledgements()
        self.make_toc()

    def make_metadata(self):
        # get all ONT_PROPS props and their (multiple) values
        this_onts_props = defaultdict(list)
        for s_ in chain(
            self.ont.subjects(predicate=RDF.type, object=OWL.Ontology),
            self.ont.subjects(predicate=RDF.type, object=SKOS.ConceptScheme),
            self.ont.subjects(predicate=RDF.type, object=PROF.Profile),
        ):
            iri = s_
            for p_, o in self.ont.predicate_objects(s_):
                if p_ in ONT_PROPS:
                    this_onts_props[p_].append(o)

        # make HTML for all props in order of ONT_PROPS
        sec = div(h1(this_onts_props[DCTERMS.title]), id="metadata", _class="section")
        d = dl(div(dt(strong("IRI")), dd(str(iri))))
        for prop in ONT_PROPS:
            if prop in this_onts_props.keys():
                d.appendChild(
                    div(
                        dt(strong(self.ontpub.props_labeled[prop]["title"].title())), 
                        dd(this_onts_props[prop])
                    )
                )
        sec.appendChild(d)
        self.ontpub.content.appendChild(sec)
        self.toc["on_page"].append({ "title": "Metadata", "href": "#metadata" })

    def make_introduction(self):
        with self.ontpub.content:
            with div(id="introduction", _class="section"):
                with open(join("markdown", self.ontology_prefix, "introduction.md"), 'r') as f:
                    html = markdown.markdown(f.read())
                    raw(str(html))
        self.toc["on_page"].append({ "title": "Introduction", "href": "#introduction" })

    def make_class_section(self):
        with self.ontpub.content:
            with div(id="classes", _class="section"):
                h2("Classes")
                with table():
                    thead(tr(th("Label"), th("Description")))
                    tb = tbody()
                    for subject_uri in self.ontpub.ont.subjects(predicate=RDF.type, object=OWL.Class):
                        if self.ns[1] in subject_uri:
                            label = self.ont.value(subject_uri, RDFS.label)
                            fid = generate_fid(label, subject_uri, self.fids)
                            comment = self.ont.value(subject_uri, RDFS.comment) or ""
                            tb.appendChild(tr(td(a(label, href="/terms/{}/{}".format(self.ontology_prefix, fid))), td(comment)))
        self.toc["on_page"].append({ "title": "Classes", "href": "#classes" })

    def make_namespaces(self):
        # only get namespaces used in ont
        nses = {}
        for n in chain(self.ont.subjects(), self.ont.predicates(), self.ont.objects()):
            # a list of prefixes we don't like
            excluded_namespaces = ()
            if not str(n).startswith(excluded_namespaces):
                for prefix, ns in self.ont.namespaces():
                    if str(n).startswith(ns):
                        nses[prefix] = ns

        with self.ontpub.content:
            with div(id="namespaces", _class="section"):
                h2("Namespace abbreviations")
                t = table()
                t.appendChild(thead(tr(th("abbreviation"), th("IRI"))))
                tb = t.appendChild(tbody())
                for prefix, ns in sorted(nses.items()):
                    p_ = prefix if prefix != "" else ":"
                    tb.appendChild(tr(td(p_), td(ns)))

        self.toc["on_page"].append({ "title": "Namespaces", "href": "#namespaces" })

    def make_acknowledgements(self):
        with self.ontpub.content:
            with div(id="acknowledgements", _class="section"):
                with open(join("markdown", self.ontology_prefix, "acknowledgements.md"), 'r') as f:
                    html = markdown.markdown(f.read())
                    raw(str(html))
        self.toc["on_page"].append({ "title": "Acknowledgements", "href": "#acknowledgements" })
