from pathlib import Path
import io
import subprocess


def getParent():
    return Path(".").absolute().parents[0]


def gitPull():
    parent = getParent()
    for dir in parent.iterdir():
        if dir.is_dir():
            subprocess.run(["git", "pull"], cwd=dir)


def pipInstall():
    parent = getParent()
    for dir in parent.iterdir():
        if dir.is_dir():
            subprocess.run(
                ["python", "-m", "pip", "install", "-r", "requirements.txt"], cwd=dir
            )


if __name__ == "__main__":
    main()
