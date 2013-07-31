import logging
import math

from mako import exceptions
from mako.template import Template

# I would love templates to be in a data file.  PR encouraged!

html_template = """<!DOCTYPE html><%! import isodate %>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>
Bisection results for ${", ".join([x.name.title() for x in projects])}
</title>
<script type="text/javascript">

function setup_page() {
  var checkboxes = document.querySelectorAll('input[type="checkbox"].filter');
    for (var i = 0; i < checkboxes.length; i++) {
      show_hide_row(checkboxes[i].getAttribute('value'),
                    checkboxes[i].checked);
    }
    var tags_chk = document.querySelector("input#tags");
    show_tags(tags_chk.checked);

}

function show_hide_row(clsname, show) {
  var rows = document.querySelectorAll("tr." + clsname)
  if (show) {
    display = ''
  } else {
    display = 'none'
  }
  for (var i = 0; i < rows.length; i++) {
    rows[i].style.display = display;
  }
}

function show_tags(chkbox) {
  var cells = document.querySelectorAll("td.commitish");
  attr_to_set = chkbox.checked ? 'tag' : 'hash';
  for (var i = 0; i < cells.length; i++) {
    cells[i].innerHTML = cells[i].getAttribute(attr_to_set)
  }
}

</script>
<style>
  table {
    border-collapse: collapse ;
    border: solid 1px black ;
  }
  thead {
    border-bottom: solid 3px red ;
  }
  tfoot {
    border-top: solid 3px red ;
    font-weight: bold ;
  }
  th,td {
    border: solid 1px black ;
  }
  tr.pass {
    background: #90EE90 ;
  }
  tr.fail {
    background: #FA8072 ;
  }
  tr.found {
    background: #89CFF0 ;
  }
  tr.untested.even {
    background: #999 ;
    color: #666 ;
  }
  tr.untested.odd {
    background: #666 ;
    color: #999 ;
  }
</style>
</head>
<body onload="setup_page()">
<h1>Bisection results for ${", ".join([x.name.title() for x in projects])}</h1>
% for cls in ('found', 'pass', 'fail', 'untested'):
<% checked = 'checked="checked"' if cls != 'untested' else '' %>
<input value="${cls}" type="checkbox" ${checked}
    onclick="show_hide_row(this.value, this.checked)"
    class="filter">${cls.title()}</input>
% endfor
<input value="tags" type="checkbox" onclick="show_tags(this)"
    id="tags" class="option">Show Tags</input>
<table>
  <thead>
  <tr>
    <th>Count</th>
    % for project in sorted(projects, key=lambda x: x.name):
    % for info in ('Hash', 'Date'):
    <th>${project.name.title()} ${info}</th>
    % endfor
    % endfor
  </tr>
  </thead>
  <tfoot>
  <tr>
    <td>${len(history)}</td>
    % for project in sorted(projects, key=lambda x: x.name):
      <%
        commits = []
        oldest = None
        newest = None
        for line in history:
          for rev in line:
            if rev.prj == project:
              if project and not rev.hash in commits:
                commits.append(rev.hash)
              if newest is None or rev.date > newest:
                newest = rev.date
              if oldest is None or rev.date < oldest:
                oldest = rev.date

        time_delta = newest - oldest
      %>
    <td>${len(commits)} ${project.name.title()} commits</td>
    <td>${time_delta}</td>
    % endfor
  </tr>
  </tfoot>
  <tbody>
  % for line in history:
  <%
    classes = []
    if loop.index == found_i:
      classes.append('found')
    if loop.index in pass_i:
      classes.append('pass')
    elif loop.index in fail_i:
      classes.append('fail')
    else:
      classes.append('untested')
    classes = " ".join(classes)

    if loop.index in order:
      line_num = "%d (%d)" % (loop.index+1, order.index(loop.index)+1)
    else:
      line_num = str(loop.index + 1)

  %>
  <tr class="${classes} ${"even" if loop.even else "odd"}">
    <td>${line_num}</td>
    % for rev in sorted(line, key=lambda x: x.prj.name):
    <td class="commitish" hash="${rev.hash}"
      tag="${rev.tag()}">${rev.hash}</td>
    <td>${rev.date.isoformat()}</td>
    % endfor
  </tr>
  % endfor
  </tbody>
</table>
</body>
</html>
"""

log = logging.getLogger(__name__)


class Bisection(object):

    def __init__(self, projects, history, evaluator):
        object.__init__(self)
        self.projects = projects
        self.history = history
        self.evaluator = evaluator
        self.max_recursions = \
            round(math.log(len(history), 2))
        self.pass_i = []
        self.fail_i = []
        self.order = []
        self.found = self._bisect(self.history, 0, 0)

    def _bisect(self, history, num, offset_b):
        middle = len(history) / 2
        overall_index = middle + offset_b
        self.order.append(overall_index)
        if len(history) == 1:
            self.pass_i.append(overall_index)
            self.found_i = overall_index
            if num == self.max_recursions - 1:
                # Sometimes, we do log2(N), others log2(N)-1
                log.info("Psych!")
                log.debug("We don't need to do the last recursion")
            return history[0]
        else:
            cur = history[middle]
            log.info("Running test %d of %d", num + 1,
                     self.max_recursions)

            map(log.info, cur)

            for rev in cur:
                log.debug("Setting revision for %s" % rev)
                rev.prj.set_rev(rev.hash)

            outcome = self.evaluator.eval(cur)

            log.info("Test %s", "passed" if outcome else "failed")

            if outcome:
                self.pass_i.append(overall_index)
                return self._bisect(history[middle:], num+1, offset_b + middle)
            else:
                self.fail_i.append(overall_index)
                return self._bisect(history[:middle], num+1, offset_b)

    def write(self, filename, fmt='html'):
        if fmt == 'html':
            return self.write_html(filename)
        else:
            raise Exception("Format '%s' is not implemented" % fmt)

    def write_html(self, filename):
        try:
            template = Template(html_template)
            with open(filename, "w+b") as f:
                f.write(template.render(
                    history=self.history,
                    projects=self.projects,
                    pass_i=self.pass_i,
                    fail_i=self.fail_i,
                    found_i=self.found_i,
                    order=self.order
                ))
        except:
            with open("error.html", "w+b") as f:
                f.write(exceptions.html_error_template().render())
