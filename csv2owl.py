#!/usr/bin/env python3
import re

import click
import csv

import rdflib
import sys
from rdflib.namespace import RDF, RDFS, OWL, SKOS

DEFAULT_NAMESPACE = RDFS
NAMESPACES = {}


class NotMatchingNamespaceValue(RuntimeError):
    pass


class UnknownNamespace(RuntimeError):
    pass


class InvalidURI(RuntimeError):
    pass

def csv_auto_reader(f, delimiter=None):
    if delimiter:
        return csv.reader(f, delimiter=delimiter)
    dialect = csv.Sniffer().sniff(f.readline())
    f.seek(0)
    return csv.reader(f, dialect)


def split_namespace_value(string):
    pattern = re.compile(r'\s*(?P<namespace>[^:]+):(?P<value>\w+)\s*')
    matches = pattern.search(string)
    if not matches:
        raise NotMatchingNamespaceValue(f'{string} does not match namespace:value')

    namespace, value = matches.group('namespace'), matches.group('value')
    namespace = namespace.upper()

    if namespace in NAMESPACES.keys():
        return NAMESPACES[namespace], value
    elif hasattr(rdflib.namespace, namespace.upper()):
        return getattr(rdflib.namespace, namespace.upper()), value
    else:
        raise UnknownNamespace(f'\'{namespace}\'')


def get_uri(string, force=True):
    string = string.strip()
    if ' ' in string:
        return None
    try:
        namespace, value = split_namespace_value(string)
    except NotMatchingNamespaceValue:
        if force:
            return DEFAULT_NAMESPACE[string]
        return None
    except UnknownNamespace as e:
        if not force:
            return None
        raise e

    return namespace[value]


def setup_graph(graph):
    for namespace, uri in NAMESPACES.items():
        graph.bind(namespace.lower(), uri)


def handle_prefix(prefix_file, delimiter=None):
    global DEFAULT_NAMESPACE
    prefix_reader = csv_auto_reader(prefix_file, delimiter=delimiter)

    for row in prefix_reader:
        row = [field.strip() for field in row]
        namespace = rdflib.Namespace(row[2])
        NAMESPACES[row[1].upper()] = namespace
        if 'default' in row[0]:
            DEFAULT_NAMESPACE = namespace


def handle_file(graph, f, file_type, delimiter=None):
    file_reader = csv_auto_reader(f, delimiter=delimiter)
    field_names = next(file_reader)
    type_rows = list(file_reader)

    current_value = None
    for row in type_rows:
        if not row[0]:
            continue
        current = get_uri(row[0])
        if not current:
            raise InvalidURI(f'\'{row[0]}\'')

        if file_type == 'classes':
            graph.add((current, RDF.type, OWL.Class))
        for index, field_value, in enumerate(row[1:], 1):
            field_value = field_value.strip()
            if not field_value:
                continue

            _, field_type = split_namespace_value(field_names[index]) or (None, None)
            force_uri = field_type not in ['label', 'comment']

            lang = None
            if field_names[index][-3] == '@':
                lang = field_names[index][-2:]

            value = get_uri(field_value, force=force_uri) or rdflib.Literal(field_value, lang=lang)
            graph.add((current, get_uri(field_names[index]), value))


def csv2owl(classes, properties, prefix, delimiter=None):
    graph = rdflib.Graph()

    if prefix:
        handle_prefix(prefix, delimiter)
    setup_graph(graph)
    handle_file(graph, classes, 'classes', delimiter)
    handle_file(graph, properties, 'properties', delimiter)

    return graph


@click.command()
@click.argument('classes', type=click.File('r'))
@click.argument('properties', type=click.File('r'))
@click.option('--prefix', '-p', default=None, help='Prefix CSV File', type=click.File('r'))
@click.option('--delimiter', '-d', default=',', help='CSV delimiter character')
@click.option('--output', '-o', default=sys.stdout, help='Output file', type=click.File('w'))
@click.option('--format', '-f', default='json-ld', help='Output format')
def command(classes, properties, prefix, delimiter, output, format):
    graph = csv2owl(classes, properties, prefix, delimiter)
    print(graph.serialize(format=format, indent=4).decode('utf8'), file=output)


if __name__ == '__main__':
    command()
