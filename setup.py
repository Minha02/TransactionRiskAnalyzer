from setuptools import setup, find_packages

setup(
    name="transaction_risk_analyzer",
    version="0.1",
    packages=find_packages(),
    package_data={
        "main": ["transaction_risk_analysis_prompt.txt"],
    },
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