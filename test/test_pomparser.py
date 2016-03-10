import unittest

from ignormaus.pomparser import PomParser

class TestPomParser(unittest.TestCase):

  def test_pom_parser_init(self):
    pp = PomParser()
    self.assertEqual(pp.ok, 'OK')

  def test_pom_parser_simple_parse(self):
    pp = PomParser()
    uris = pp.parse_pom('test/simple.xml')
    res = uris[0]
    self.assertEqual(res['group'], 'org.hamcrest')
    self.assertEqual(res['artifact'], 'hamcrest-core')
    self.assertEqual(res['version'], '1.3')

  def test_pom_parser_parent_parse(self):
    pp = PomParser()
    uris = pp.parse_pom('test/parent.xml')
    res = uris[0]
    self.assertEqual(res['group'], 'io.netty')
    self.assertEqual(res['artifact'], 'netty-buffer')
    self.assertEqual(res['version'], '4.0.26.Final')
    self.assertEqual(len(uris), 11)


