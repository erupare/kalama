import setuptools


with open("README.md") as fp:
    long_description = fp.read()


setuptools.setup(
    name="kalama",
    version="0.0.1",

    description="(re) Build awsgeek.com",
    long_description=long_description,
    long_description_content_type="text/markdown",

    author="author",

    package_dir={"": "kalama"},
    packages=setuptools.find_packages(where="kalama"),

    install_requires=[
        "aws-cdk.core",
        "aws-cdk.aws_s3",
        "aws-cdk.aws_lambda",
        "aws-cdk.aws_events",
        "aws-cdk.aws_cloudtrail",
        "aws-cdk.aws_stepfunctions",
        "aws-cdk.aws_events_targets",
        "aws-cdk.aws_stepfunctions_tasks",
    ],

    python_requires=">=3.6",

    classifiers=[
        "Development Status :: 4 - Beta",

        "Intended Audience :: Developers",

        "License :: OSI Approved :: Apache Software License",

        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",

        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",

        "Typing :: Typed",
    ],
)
