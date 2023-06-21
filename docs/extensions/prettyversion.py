from docutils.statemachine import StringList
from docutils.parsers.rst import Directive
from docutils.parsers.rst import states, directives
from docutils.parsers.rst.roles import set_classes
from docutils import nodes
from sphinx.locale import _


class pretty_version_added(nodes.General, nodes.Element):
    pass


class pretty_version_changed(nodes.General, nodes.Element):
    pass


class pretty_version_removed(nodes.General, nodes.Element):
    pass


def visit_pretty_version_added_node(self, node):
    self.body.append(self.starttag(node, 'div', CLASS='pretty-version pv-added'))
    self.body.append(self.starttag(node, 'i', CLASS='fa-solid fa-circle-plus'))
    self.body.append('</i>')


def visit_pretty_version_changed_node(self, node):
    self.body.append(self.starttag(node, 'div', CLASS='pretty-version pv-changed'))
    self.body.append(self.starttag(node, 'i', CLASS='fa-solid fa-wrench'))
    self.body.append('</i>')


def visit_pretty_version_removed_node(self, node):
    self.body.append(self.starttag(node, 'div', CLASS='pretty-version pv-removed'))
    self.body.append(self.starttag(node, 'i', CLASS='fa-solid fa-trash'))
    self.body.append('</i>')


def depart_pretty_version_node(self, node):
    self.body.append('</div>\n')


class PrettyVersionAddedDirective(Directive):
    has_content = True
    required_arguments = 1

    def run(self):
        version = self.arguments[0]

        joined = '\n'.join(self.content) if self.content else ''
        content = [f'**New in version:**  *{version}*{" - " if joined else ""}', joined]

        node = pretty_version_added('\n'.join(content))
        self.state.nested_parse(StringList(content), self.content_offset, node)

        return [node]


class PrettyVersionChangedDirective(Directive):
    has_content = True
    required_arguments = 1

    def run(self):
        version = self.arguments[0]

        joined = '\n'.join(self.content) if self.content else ''
        content = [f'**Version changed:** *{version}*{" - " if joined else ""}', joined]

        node = pretty_version_changed('\n'.join(content))
        self.state.nested_parse(StringList(content), self.content_offset, node)

        return [node]


class PrettyVersionRemovedDirective(Directive):
    has_content = True
    required_arguments = 1

    def run(self):
        version = self.arguments[0]

        joined = '\n'.join(self.content)
        content = [f'**Removed in version:** *{version}*{" - " if joined else ""}', joined]

        node = pretty_version_removed('\n'.join(content))
        self.state.nested_parse(StringList(content), self.content_offset, node)

        return [node]


def setup(app):
    app.add_node(pretty_version_added, html=(visit_pretty_version_added_node, depart_pretty_version_node))
    app.add_node(pretty_version_changed, html=(visit_pretty_version_changed_node, depart_pretty_version_node))
    app.add_node(pretty_version_removed, html=(visit_pretty_version_removed_node, depart_pretty_version_node))

    app.add_directive('versionadded', PrettyVersionAddedDirective, override=True)
    app.add_directive('versionchanged', PrettyVersionChangedDirective, override=True)
    app.add_directive('versionremoved', PrettyVersionRemovedDirective, override=True)

    return {'parallel_read_safe': True}
