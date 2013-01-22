# -*- coding: utf-8 -*-

# Copyright (C) 2013 Avencall
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

class HTMLVisualizer(object):
    def __init__(self, output_filename):
        self._output_filename = output_filename

    _HEADER = """\
<html>
<head>
<title>visualplan</title>
<style type="text/css">
table td {
    border-collapse: collapse;
    border-color: #BBBBBB;
    border-spacing: 0;
    border-style: solid;
    border-width: 0;
    font-family: courier,monospace;
    font-size: 11px;
    padding-left: 0.2em;
    padding-right: 0.2em;
}
tr.noCover {
    background-color: #FFFFFF;
}
tr.coverFull {
    background-color: #DDFFDD;
}
tr.coverNone {
    background-color: #FFDDDD;
}
</style>
</head>
<body>
"""

    _FOOTER = """\
</body>
</html>
"""

    def write(self, analyses):
        with open(self._output_filename, 'w') as fobj:
            fobj.write(self._HEADER)
            for analysis in analyses:
                fobj.write('<p>{}</p>'.format(analysis.filename))
                fobj.write('<table>')
                for no_line, line_analysis in enumerate(analysis.line_analyses, 1):
                    if line_analysis.is_executable:
                        if line_analysis.is_executed:
                            fobj.write('<tr class="coverFull">')
                        else:
                            fobj.write('<tr class="coverNone">')
                    else:
                        fobj.write('<tr class="noCover">')
                    fobj.write('<td>{}</td><td>'.format(no_line))
                    fobj.write(line_analysis.content)
                    fobj.write('</td>')
                    fobj.write('</tr>\n')
                fobj.write('</table>')
            fobj.write(self._FOOTER)
        print('Wrote HTML output in {}'.format(self._output_filename))
