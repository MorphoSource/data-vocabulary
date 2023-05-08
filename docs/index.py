from os.path import join
from pathlib import Path

from dominate.tags import (
    a,
    div,
    dd,
    dl,
    dt,
    h2,
    link,
    script
)
from dominate.util import raw
from pylode import OntPub
from pylode.rdf_elements import CLASS_PROPS
from pylode.utils import generate_fid
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS

class Index:
    """Creates HTML documentation page for ontology index root."""

    def __init__(self, ontology_filepath: str, destination_dir: Path = None):
        self.ontpub = OntPub(ontology_filepath)
        self.ont = self.ontpub.ont
        self.back_onts = self.ontpub.back_onts
        self.fids = self.ontpub.fids
        self.ns = self.ontpub.ns
        self.destination_dir = destination_dir

    def make_html(self):
        self.make_head()
        self.make_body()

        html_path = join(self.destination_dir, "index.html")
        open(html_path, "w").write(self.ontpub.doc.render())

    def make_head(self):
        with self.ontpub.doc.head:
            link(href="msterms.css", rel="stylesheet", type="text/css")
            script(
                raw("\n" + self.ontpub._make_schema_org().serialize(format="json-ld") + "\n\t"),
                type="application/ld+json",
                id="schema.org",
            )
    
    def make_body(self):
        self.ontpub._make_metadata()
        self.make_class_section()
        self.ontpub._make_namespaces()

    def make_class_section(self):
        with self.ontpub.content:
            elems = div(id="classes", _class="section")
            elems.appendChild(h2("Classes"))

            elem_dl = elems.appendChild(dl())
            for subject_uri in self.ontpub.ont.subjects(predicate=RDF.type, object=OWL.Class):
                if self.ns[1] in subject_uri:
                    label = self.ont.value(subject_uri, RDFS.label)
                    fid = generate_fid(label, subject_uri, self.fids)
                    comment = self.ont.value(subject_uri, RDFS.comment)
                    elem_dl.appendChild(div(dt(a(label, href="{}.html".format(fid))), dd(comment)))

            elems.render()
