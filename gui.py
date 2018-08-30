import pyforms
from pyforms.controls import ControlFile, ControlButton
from csv2owl import csv2owl

class Csv2OwlWidget(pyforms.BaseWidget):
    def __init__(self):
        super(Csv2OwlWidget, self).__init__('csv2owl')

        self._prefix = ControlFile('Prefixes')
        self._classes = ControlFile('Classes')
        self._properties = ControlFile('Properties')

        self._generate = ControlButton('Generate')
        self._generate.value = self.__generateAction

    def __generateAction(self):
        classes = open(self._classes.value, 'r')
        properties = open(self._properties.value, 'r')
        prefix = open(self._prefix.value, 'r')
        graph = csv2owl(classes, properties, prefix)
        print(graph.serialize(format='pretty-xml', index=4).decode('utf8'))





if __name__ == "__main__":
    pyforms.start_app(Csv2OwlWidget)
