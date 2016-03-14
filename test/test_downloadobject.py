import unittest

from pbs.bin.main import download_package,build_uri

class TestDownloadObject(unittest.TestCase):
  repoyml = "prodng/repo.yml"

  def test_build_uri(self):
    name = "multiarch-support_2.19-18+deb8u3_amd64.deb"
    pkg_path = "packages"
    dep = [{"name":"glibc/multiarch-support_2.19-18+deb8u3_amd64.deb","repo":"security","url":"http://security.debian.org/debian-security/pool/updates/main/g/glibc/multiarch-support_2.19-18+deb8u3_amd64.deb"},
           {"name": "mawk/mawk_1.3.3-17_amd64.deb","repo": "main", "url":"http://ftp.us.debian.org/debian/pool/main/m/mawk/mawk_1.3.3-17_amd64.deb"}]
    for d in dep:
      do = build_uri(d,self.repoyml)
      self.assertEqual(do,d["url"])

if __name__ == '__main__':
    unittest.main()
