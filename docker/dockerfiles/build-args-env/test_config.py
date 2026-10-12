import os, subprocess, sys, unittest
from pathlib import Path
class ConfigTests(unittest.TestCase):
    def test_runtime_environment(self):
        script = Path(__file__).with_name("app.py")
        self.assertTrue(script.is_file(), "app.py must exist")
        for name in (None, "Hossein"):
            env = os.environ.copy()
            env.pop("APP_NAME", None)
            if name is not None: env["APP_NAME"] = name
            output = subprocess.check_output([sys.executable, str(script)], env=env, text=True)
            self.assertEqual(output, f"Hello, {name or 'Docker learner'}!\n")
if __name__ == "__main__": unittest.main()
