#!/usr/bin/env python3
import re

import click
import csv

import rdflib
from rdflib.namespace import RDF, RDFS, OWL, SKOS

DEFAULT_NAMESPACE = SKOS


class NotMatchingNamespaceValue(Exception):
    pass


def split_namespace_value(string):
    pattern = re.compile(r'(?P<namespace>[^:]+):(?P<value>\w+)')
    matches = pattern.search(string)
    if not matches:
        raise NotMatchingNamespaceValue(f'{string} does not match namespace:value')

    namespace, value = matches.group('namespace'), matches.group('value')

    if not hasattr(rdflib.namespace, namespace.upper()):
        raise Exception(f'Unknown namespace: {namespace}')

    return getattr(rdflib.namespace, namespace.upper()), value


def get_uri(string):
    try:
        namespace, value = split_namespace_value(string)
    except NotMatchingNamespaceValue:
        return DEFAULT_NAMESPACE[string]
    return namespace[value]


def setup_graph(graph, config):
    graph.bind("owl", OWL)
    graph.bind("skos", SKOS)


def handle_classes(graph, classes_file, delimiter=','):
    class_reader = csv.reader(classes_file, delimiter=delimiter)
    field_names = next(class_reader)
    class_rows = list(class_reader)

    existing_classes = {}
    # Create all the classes
    for class_row in class_rows:
        class_uri = get_uri(class_row[0])

        existing_classes[class_row[0]] = class_uri
        graph.add((class_uri, RDF.type, OWL.Class))

    for class_row in class_rows:
        for index, field_value in enumerate(class_row):
            if index == 0 or not field_value:
                continue
            class_uri = existing_classes[class_row[0]]
            print(index, field_names[index])
            if field_names[index] == 'superClass':
                graph.add((class_uri, RDFS.subClassOf, get_uri(field_value)))
            else:
                graph.add((class_uri, get_uri(field_names[index]), rdflib.Literal(field_value)))

def handle_properties(graph, properties_file, delimiter=','):
    properties_reader = csv.reader(properties_file, delimiter=delimiter)
    field_names = next(properties_reader)
    property_rows = list(properties_reader)

    current_property = None
    for property_row in property_rows:
        for index, field_value, in enumerate(property_row):
            if index == 0:
                current_property = get_uri(field_value)
                graph.add((current_property, RDF.type, OWL.ObjectProperty))
                continue
            if not field_value:
                continue
            if field_names[index] == 'superProperties':
                graph.add((current_property, RDFS.subPropertyOf, get_uri(field_value)))
            else:
                graph.add((current_property, get_uri(field_names[index]), rdflib.Literal(field_value)))



@click.command()
@click.argument('classes', type=click.File('r'))
@click.argument('properties', type=click.File('r'))
@click.option('--delimiter', default=',', help='CSV delimiter character')
@click.option('--config', default=None, help='Config file path')
def csv2owl(classes, properties, delimiter, config):
    graph = rdflib.Graph()
    setup_graph(graph, config)
    handle_classes(graph, classes, delimiter)
    handle_properties(graph, properties, delimiter)
    print(graph.serialize(format='json-ld', indent=4).decode('utf8'))
    pass


if __name__ == '__main__':
    csv2owl()
