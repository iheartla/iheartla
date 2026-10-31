# Vendor the page's third-party web libraries into docs/vendor/ so the page
# doesn't load anything from a CDN. (Pyodide: see update_pyodide.sh. Ace,
# AngularJS, and jQuery were already in docs/js/.)
# Usage: sh docs/update_vendor.sh
set -e
BOOTSTRAP=5.0.0-beta2
FONTAWESOME=4.7.0
MATHJAX=3.2.2
cd "$(dirname "$0")"
rm -rf vendor && mkdir vendor
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
fetch() {  # npm package name, version -> $tmp/<name>/package
    mkdir -p "$tmp/$1"
    curl -fsSL "https://registry.npmjs.org/$1/-/$1-$2.tgz" | tar -xz -C "$tmp/$1"
}

# Bootstrap: only the CSS is used
fetch bootstrap $BOOTSTRAP
mkdir -p vendor/bootstrap/css
cp "$tmp/bootstrap/package/dist/css/bootstrap.min.css" vendor/bootstrap/css/
cp "$tmp/bootstrap/package/LICENSE" vendor/bootstrap/

# Font Awesome: CSS plus the web fonts it references (../fonts/)
fetch font-awesome $FONTAWESOME
mkdir -p vendor/font-awesome/css vendor/font-awesome/fonts
cp "$tmp/font-awesome/package/css/font-awesome.min.css" vendor/font-awesome/css/
cp "$tmp/font-awesome/package/fonts/fontawesome-webfont."* vendor/font-awesome/fonts/
cp "$tmp/font-awesome/package/README.md" vendor/font-awesome/   # license terms (OFL fonts, MIT CSS)

# MathJax: the combined component plus everything it loads at runtime, including
# what its right-click menu can load (SVG renderer, accessibility, speech).
# The other combined components (~15 MB) are left out.
fetch mathjax $MATHJAX
m="$tmp/mathjax/package/es5"
mkdir -p vendor/mathjax/input/tex
cp "$m/tex-mml-chtml.js" vendor/mathjax/
cp -R "$m/output" "$m/ui" "$m/a11y" "$m/sre" vendor/mathjax/
cp -R "$m/input/tex/extensions" vendor/mathjax/input/tex/
cp "$tmp/mathjax/package/LICENSE" vendor/mathjax/

du -sh vendor/*
