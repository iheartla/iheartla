# H❤️rtDown gallery programs

The I❤️LA code of the papers in the H❤️rtDown editor's Demos menu
(`docs/examples/demos.json` in <https://github.com/iheartla/heartdown>): the
basic example (`starter/`) and the 14 case studies of the
[gallery](https://iheartla.github.io/heartdown/CaseStudies/gallery/index.html),
fetched on 2026-11-02 from
`https://iheartla.github.io/heartdown/CaseStudies/static/gallery_res/<paper>`.

Each `<context>.ihla` is one compile, as H❤️rtDown does it: a paper's inline
`❤ … ❤` code and then its fenced `iheartla` blocks, grouped by context
(`❤: name`) and joined with newlines. H❤️rtDown writes the same files next to
a paper, and contexts import each other from them (`E_q from connection(…)`
in `Elastic/`), so each program is compiled in its own directory.
`index.json` lists each paper's contexts.

To refresh them (the extraction reimplements H❤️rtDown's grouping; it doesn't
run H❤️rtDown), download the papers into `<dir>/<paper>/` and run

    python rust/tools/extract_heartdown.py <dir> rust/corpus/heartdown
