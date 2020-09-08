import treelib
from treelib import Node, Tree

def create_mali_tree():
    '''
    Returns an example matching tree of locations in Mali.
    '''
    mali = Tree()
    mali.create_node('Mali', 'Mali')
    mali.create_node('the north', 'the north', parent='Mali')
    mali.create_node('north-east', 'north-east', parent='the north')
    mali.create_node('Algeria', 'Algeria', parent='the north')
    mali.create_node('Kidal', 'Kidal', parent='north-east')
    mali.create_node('Adrar des Iforas', 'Adrar des Iforas', parent='Kidal')
    mali.create_node('Tessalit', 'Tessalit', parent='Adrar des Iforas')
    mali.create_node('W. Inabsar', 'W. Inabsar', parent='Tessalit')
    mali.create_node('W. Takorkat', 'W. Takorkat', parent='Tessalit')
    mali.create_node('Wadi Tinkar', 'Wadi Tinkar', parent='Tessalit')
    mali.create_node('Amachach', 'Amachach', parent='Tessalit')
    mali.create_node('Bolrech', 'Bolrech', parent='Tessalit')
    mali.create_node('Terchichout', 'Terchichout', parent='Tessalit')
    mali.create_node('Timetrine', 'Timetrine', parent='Tessalit')
    mali.create_node('Tombouctou', 'Tombouctou',parent='the north')
    mali.create_node('Gourma', 'Gourma', parent='Tombouctou')
    mali.create_node('Goundam', 'Goundam', parent='Tombouctou')
    mali.create_node('south-east', 'south-east', parent='Mali')
    mali.create_node('Gao', 'Gao', parent='south-east')
    mali.create_node('Tahaka', 'Tahaka', parent='Gao')
    mali.create_node('Menaka', 'Menaka', parent='Gao')
    mali.create_node('Telli', 'Telli', parent='Menaka')
    mali.create_node('Tilemsi Valley', 'Tilemsi Valley', parent='Gao')
    mali.create_node('Lac Fate', 'Lac Fate', parent='Menaka')
    mali.create_node('Tidjalaline', 'Tidjalaline', parent='Menaka')
    mali.create_node('Aguelhoc', 'Aguelhoc', parent='Adrar des Iforas')

    return mali