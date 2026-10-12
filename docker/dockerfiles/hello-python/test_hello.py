import subprocess, sys, unittest
from pathlib import Path
class HelloTests(unittest.TestCase):
    def test_greeting(self):
        script = Path(__file__).with_name("hello.py")
        self.assertTrue(script.is_file(), "hello.py must exist")
        self.assertEqual(subprocess.check_output([sys.executable, str(script)], text=True), "Hello from a Docker container!\n")
if __name__ == "__main__": unittest.main()
