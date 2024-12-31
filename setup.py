from setuptools import setup, find_packages

setup(
    name="webcrawlerapi",
    version="1.0.2",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
    ],
    author="Andrew",
    description="Python SDK for WebCrawler API",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/webcrawlerapi-python",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
) 