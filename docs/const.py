from pylode.rdf_elements import CLASS_PROPS, ONTDOC
from rdflib import Namespace
from rdflib.term import URIRef

MSDOC = Namespace("http://www.morphosource.org/profile/msdoc/")

ONT_TYPES = {
    URIRef('http://www.w3.org/2002/07/owl#Class'): ('c', 'Class'), 
    URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#Property'): ('p', 'Property'), 
    URIRef('http://www.w3.org/2002/07/owl#ObjectProperty'): ('op', 'Object Property'), 
    URIRef('http://www.w3.org/2002/07/owl#DatatypeProperty'): ('dp', 'Datatype Property'), 
    URIRef('http://www.w3.org/2002/07/owl#AnnotationProperty'): ('ap', 'Annotation Property'), 
    URIRef('http://www.w3.org/2002/07/owl#FunctionalProperty'): ('fp', 'Functional Property'), 
    URIRef('http://www.w3.org/2002/07/owl#InverseFunctionalProperty'): ('ifp', 'Inverse Functional Property'), 
    URIRef('http://www.w3.org/2002/07/owl#NamedIndividual'): ('ni', 'Individual Instance')
}

CLASS_PROPS.insert(CLASS_PROPS.index(ONTDOC.inDomainOf), MSDOC.superClassInDomainOf)

SERIALIZE_EXCLUDED_PROPS = [
    ONTDOC.restriction,
    ONTDOC.inDomainOf,
    ONTDOC.inDomainIncludesOf,
    ONTDOC.inRangeOf,
    ONTDOC.inRangeIncludesOf,
    ONTDOC.restriction,
    ONTDOC.hasInstance,
    ONTDOC.superClassOf,
    ONTDOC.superPropertyOf,
]
