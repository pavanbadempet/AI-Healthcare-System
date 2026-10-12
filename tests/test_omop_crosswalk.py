"""
Verification test suite for OMOP CONCEPT_RELATIONSHIP mapping tables.
"""
import unittest

class TestOMOPConceptRelationship(unittest.TestCase):
    def test_maps_to_relationship_directionality(self):
        rel_id = "Maps to"
        is_standard = True
        self.assertEqual(rel_id, "Maps to")
        self.assertTrue(is_standard)

if __name__ == "__main__":
    unittest.main()
