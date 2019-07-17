#!/usr/bin/env python3

from aws_cdk import core

from kalama.kalama_stack import KalamaStack


app = core.App()
KalamaStack(app, "kalama")

app.synth()
