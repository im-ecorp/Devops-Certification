import subprocess, unittest
from pathlib import Path
class EntrypointTests(unittest.TestCase):
    def test_default_and_override(self):
        script = Path(__file__).with_name("greet.sh")
        self.assertTrue(script.is_file(), "greet.sh must exist")
        for args, expected in (([], "Docker learner"), (["Hossein"], "Hossein")):
            output = subprocess.check_output(["sh", str(script), *args], text=True)
            self.assertEqual(output, f"Hello, {expected}!\n")
if __name__ == "__main__": unittest.main()
