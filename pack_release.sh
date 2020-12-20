#!/bin/bash
# A Simple Shell Script To pack app on Mac, it will create a new tag and the first parameter is the message for the tag.
# usage: In poetry shell, run "sh  pack_release.sh  msg" in the current directory

# update local parsers
# python la_local_parsers.py
# generate zip file
# target='iheartla.app.zip'
# rm -rf ./dist
# rm -rf ./build
# rm "$target"
# pyinstaller iheartla.spec
# cd dist
# zip "$target" iheartla.app/ -r
# mv "$target" ../
# cd ..
# check zip file
# if [[ ! -f "$target" ]]; then
#     echo "$target not exists."
#     exit
# fi
# git tag 
if [ $# -ge 1 ]
then
    msg=$1
else
    msg="New release"
fi
# increase the last number
cur_ver=`git tag | tail -1`
minor=`git tag | grep 'v'| cut -f4 -d '.' | sort -g | tail -1`
# prefix=`echo $cur_ver | cut -f-3 -d '.'`
prefix='v1.0.0'
new_ver="$prefix.$(($minor + 1))"
# create a new tag and push, this will trigger release workflow
git tag -a $new_ver -m "$msg" 
git push origin --tags