from setuptools import setup, find_packages

setup(
    name="polkadot-community-analyzer",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
        "beautifulsoup4>=4.11.0",
        "pandas>=1.5.0",
        "matplotlib>=3.6.0",
        "seaborn>=0.12.0",
        "numpy>=1.23.0",
        "networkx>=2.8.0",
        "nltk>=3.7.0",
        "wordcloud>=1.8.0",
        "lxml>=4.9.0",
        "python-dateutil>=2.8.0",
        "jinja2>=3.1.0",
        "markdown>=3.4.0",
        "pyyaml>=6.0",
        "tabulate>=0.9.0",
    ],
    author="Polkadot Community",
    author_email="community@polkadot.network",
    description="Tools for analyzing Polkadot forum and on-chain governance",
    keywords="polkadot, analysis, governance, community",
    python_requires=">=3.8",
)