import logging
import math
import xml.etree.ElementTree as ET

import isodate

from bisect_b2g.repository import Project, Rev


log = logging.getLogger(__name__)

class Bisection(object):

    def __init__(self, projects, history, evaluator):
        object.__init__(self)
        self.projects = projects
        self.history = history
        self.evaluator = evaluator
        self.max_recursions = round(math.log(len(history) + len(history) % 2, 2))
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
                log.info("Psych!") # Sometimes, we do log2(N), othertimes log2(N)-1
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

            outcome = self.evaluator(cur)

            log.info("Test %s", "passed" if outcome else "failed")
            
            if outcome:
                self.pass_i.append(overall_index)
                return self._bisect(history[middle:], num + 1, offset_b + middle)
            else:
                self.fail_i.append(overall_index)
                return self._bisect(history[:middle], num + 1, offset_b)
                    
    def write(self, filename, fmt='html'):
        if fmt == 'html':
            return self.write_html(filename)
        elif fmt == 'xml':
            return self.write_xml(filename)
        else:
            raise Exception("Format '%s' is not implemented" % fmt)


    def write_html(self, filename):
        """ Holy shit, why don't I use a templating engine?"""
        style_rules = ['table { border-collapse: collapse }',
                       'td { border: solid 1px black }',
                       'thead { border-bottom: solid 3px red }',
                       'tr.pass-line { background: green }',
                       'tr.fail-line { background: red }',
                       'tr.found-line { background: blue ; color: white }',
                       'tr.untested-line { background: grey ; color: dark-grey }',
                      ]
        tree = ET.ElementTree()
        root = ET.Element('html')
        root.text = '\n'
        root.tail = '\n'
        tree._setroot(root)
        head = ET.SubElement(root, 'head')
        head.text = '\n  '
        head.tail = '\n'
        style = ET.SubElement(head, 'style')
        style.text = "  \n".join(style_rules)
        style.tail = '\n'
        body = ET.SubElement(root, 'body')
        body.text = '\n'
        body.tail = '\n'
        table = ET.SubElement(body, 'table')
        table.text = '\n  '
        table.tail = '\n  '
        th = ET.SubElement(table, 'thead')
        th.text = '\n    '
        th.tail = '\n  '
        th = ET.SubElement(th, 'th')
        th.text = 'Count'
        for prj in sorted(self.projects, key=lambda x: x.name):
            for i in ('Hash', 'Date'):
                th = ET.SubElement(th, 'th')
                th.text = '%s %s' % (prj.name, i)
        th.tail = '\n  '
        for i in range(len(self.history)):
            tr = ET.SubElement(table, 'tr')
            tr.text = '\n    '
            tr.tail = '\n  '
            classes = []
            if i == self.found_i:
                classes.append('found-line')
            if i in self.pass_i:
                classes.append('pass-line')
            elif i in self.fail_i:
                classes.append('fail-line')
            else:
                classes.append('untested-line')
            tr.set('class', ' '.join(classes))
            td = ET.SubElement(tr, 'td')
            if i in self.order:
                td.text = "%d (%d)" % (i + 1, self.order.index(i) + 1)
            else:
                td.text = str(i+1)
            for rev in sorted(self.history[i], key=lambda x: x.prj.name):
                td = ET.SubElement(tr, 'td')
                td.text = rev.hash 
                td = ET.SubElement(tr, 'td')
                td.text = isodate.datetime_isoformat(rev.date)
            td.tail = '\n  '
        
        tree.write(filename, method='html')

    def write_xml(self, filename):
        tree = ET.ElementTree()
        root = ET.Element('history')
        root.text = '\n'
        root.tail = '\n'
        tree._setroot(root)
        for prj in self.projects:
            p = ET.SubElement(root, 'project')
            p.set('name', prj.name)
            p.set('good', prj.good)
            p.set('bad', prj.bad)
            p.tail = '\n'
        for i in range(len(self.history)):
            line = self.history[i]
            l = ET.SubElement(root, 'rev_pair')
            if i == self.found_i:
                outcome = 'found'
            elif i in self.pass_i:
                outcome = 'pass'
            elif i in self.fail_i:
                outcome = 'failed'
            else:
                outcome = 'untested'
            l.set('outcome', outcome)
            l.text = '\n  '
            l.tail = '\n'
            for rev in sorted(line, key=lambda x: x.prj.name):
                r = ET.SubElement(l, rev.prj.name)
                r.set('commit', rev.hash)
                r.set('date', isodate.datetime_isoformat(rev.date))
                r.tail = '\n  '
            r.tail = '\n'
        
        return tree.write(filename)

