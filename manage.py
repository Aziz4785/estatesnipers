from flask.cli import FlaskGroup
import unittest
import src as src

cli = FlaskGroup(src)

@cli.command("test")
def test():
    """Runs the unit tests without coverage."""
    tests = unittest.TestLoader().discover("tests")
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    if result.wasSuccessful():
        return 0
    else:
        return 1
    
app = src.app #expose the app object

if __name__ == "__main__":
    cli()