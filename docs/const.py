from rdflib.term import URIRef

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