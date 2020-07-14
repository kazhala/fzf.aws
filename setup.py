import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="fzfaws",
    version="0.0.1",
    author="Kevin Zhuang",
    author_email="kevin7441@gmail.com",
    description="An interactive aws cli experience with the help of fzf.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kazhala/fzf.aws",
    keywords="aws, fzf, cli, boto3",
    packages=setuptools.find_packages(exclude=["tests*"]),
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Unix",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    install_requires=["boto3>=1.14.20", "PyYAML>=5.3.1"],
    package_data={
        "fzfaws": [
            "libs/fzf-0.21.1-darwin_386",
            "libs/fzf-0.21.1-darwin_amd64",
            "libs/fzf-0.21.1-linux_386",
            "libs/fzf-0.21.1-linux_amd64",
            "fzfaws.yml",
        ],
    },
    entry_points={"console_scripts": ["fzfaws=fzfaws.cli:main"]},
)
