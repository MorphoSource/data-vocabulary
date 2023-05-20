import argparse
from glob import glob
from os import makedirs, remove
from os.path import exists, isfile, join
from shutil import copy

from docs import Docs

ONTOLOGIES = [
    {
        "prefix": "ms",
        "file": "../morphosource_terms.rdf"
    },
    {
        "prefix": "mscv",
        "file": "../morphosource_controlled_vocabularies.rdf"
    }
]

parser = argparse.ArgumentParser()

parser.add_argument(
    "-o",
    "--outputdir",
    help="Location directory to write output files",
    default=None,
    required=True
)

def main():
    args = args = parser.parse_args()

    # delete previous files in output dir root
    files = glob(join(args.outputdir, "*"))
    for f in files:
        if isfile(f): remove(f)
    
    for ontology in ONTOLOGIES:
        prefix = ontology["prefix"]
        file = ontology["file"]

        namespace_dir = join(args.outputdir, prefix)
        if not exists(namespace_dir): makedirs(namespace_dir)

        # delete namespace files in output dir
        namespace_dir_files = glob(join(namespace_dir, "*"))
        for f in namespace_dir_files:
            if isfile(f): remove(f)

        copy("static/msterms.css", namespace_dir)

        if exists(join("./static", prefix, "diagram.png")):
            copy(join("./static", prefix, "diagram.png"), namespace_dir)

        copy(file, join(args.outputdir, f"{prefix}.rdf"))

        Docs(file, prefix).make_html_pages(namespace_dir)

if __name__ == "__main__":
    main()