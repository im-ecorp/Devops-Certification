import os, subprocess, tempfile, unittest
from pathlib import Path
class MultiStageTests(unittest.TestCase):
    def test_compiled_greeting(self):
        source = Path(__file__).with_name("hello.c")
        self.assertTrue(source.is_file(), "hello.c must exist")
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as temp:
            binary = Path(temp) / "hello"
            subprocess.run(["gcc", "-Wall", "-Wextra", "-Werror", str(source), "-o", str(binary)], check=True)
            self.assertEqual(subprocess.check_output([str(binary)], text=True), "Hello from a multi-stage build!\n")
if __name__ == "__main__": unittest.main()
