#!/usr/bin/python3 -O
# -*- coding: utf-8 -*-

from flask import Flask, render_template
import genindex
import genisolist

app=Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html',
            repolist=genindex.genRepoList(),
            isoinfo=genisolist.getImageList() )

if __name__=='__main__':
    app.run(debug=True)
