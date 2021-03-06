import unittest

from mdg.uml import UMLClass, UMLPackage, UMLAssociation


class TestUMLModel(unittest.TestCase):
    def setUp(self):
        self.root_package = UMLPackage("1", "root")
        child = UMLPackage("2", "child1", self.root_package)
        self.root_package.children.append(child)
        cls = UMLClass(child, "class1", "3")
        child.classes.append(cls)

    def test_find_package(self):
        res = self.root_package.find_by_id("2")
        self.assertEqual(UMLPackage, type(res))
        self.assertEqual("child1", res.name)

    def test_find_class(self):
        res = self.root_package.find_by_id("3")
        self.assertEqual(UMLClass, type(res))
        self.assertEqual("class1", res.name)

    def test_string_to_multiplicity(self):
        assoc = UMLAssociation(self.root_package, self.root_package.children[0].classes[0], self.root_package.children[0].classes[0], 1)
        self.assertEqual(assoc.string_to_multiplicity("0..1"), ("0", "1"))
        self.assertEqual(assoc.string_to_multiplicity("0..*"), ("0", "*"))
        self.assertEqual(assoc.string_to_multiplicity("*..1"), ("*", "1"))

    def test_association_type(self):
        assoc = UMLAssociation(self.root_package, self.root_package.children[0].classes[0], self.root_package.children[0].classes[0], 1)

        assoc.source_multiplicity = ("0", "1")
        assoc.destination_multiplicity = ("0", "*")
        self.assertEqual(assoc.association_type, "OneToMany")

        assoc.source_multiplicity = ("0", "1")
        assoc.destination_multiplicity = ("0", "1")
        self.assertEqual(assoc.association_type, "OneToOne")

        assoc.source_multiplicity = ("0", "*")
        assoc.destination_multiplicity = ("0", "1")
        self.assertEqual(assoc.association_type, "ManyToOne")
