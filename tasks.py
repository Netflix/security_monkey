import invoke
import requests

@invoke.task
def release(version):
    """
    ``version`` should be a string like '0.4' or '1.0'.
    """
    invoke.run("git tag -s {0} -m '{0} release'".format(version))
    invoke.run("git push --tags")

    invoke.run("python setup.py sdist")

    invoke.run(
        "twine upload -s dist/security_monkey-{0}* ".format(version)
    )

    session = requests.Session()

    response = session.request(
        "PURGE", "https://pypi.python.org/simple/security_monkey/"
    )
    response.raise_for_status()

    invoke.run("twine upload dist/security_monkey-{0}".format(version))
