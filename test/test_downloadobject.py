import unittest

from pbs.bin.main import download_package,build_uri

class TestDownloadObject(unittest.TestCase):

  def test_build_uri(self):
    name = "multiarch-support_2.19-18+deb8u3_amd64.deb"
    pkg_path = "packages"
    repoyml = "prodng/repo.yml"
    url = "http://security.debian.org/debian-security/pool/updates/main/g/glibc/multiarch-support_2.19-18+deb8u3_amd64.deb"
    dep = {"name":"glibc/multiarch-support_2.19-18+deb8u3_amd64.deb","repo":"security"}
    do = build_uri(dep,repoyml)
    self.assertEqual(do,url)

if __name__ == '__main__':
    unittest.main()
