from setuptools import setup, find_packages

setup(
    name="transaction_risk_analyzer",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'flask',
        'flask-sqlalchemy',
        'python-dotenv',
        'requests',
        'pytest',
        'pytest-mock',
        'sqlalchemy'
    ],
)