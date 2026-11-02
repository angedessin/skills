---
type: regex
target: trace
pattern: '^(?:(?!"name":"(?:Edit|Write)","input":\{(?:"replace_all":(?:true|false),)?"file_path":"[^"]*\.test\.tsx?")[\s\S])*?"name":"(?:Edit|Write)","input":\{(?:"replace_all":(?:true|false),)?"file_path":"[^"]*/src/(?![^"]*\.test\.)[^"]*"'
match: not_contains
---
