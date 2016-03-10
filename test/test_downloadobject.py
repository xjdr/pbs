import unittest

from ignormaus.downloadobject import DownloadObject

class TestDownloadObject(unittest.TestCase):

  def test_build_uri(self):
    do = DownloadObject('mvn_object')
    result = do.build_uri('group.name', 'artifact', 'version')
    sample_uri = 'http://central.maven.org/maven2/group/name/artifact/version/artifact-version'
    self.assertEqual(result,sample_uri)

