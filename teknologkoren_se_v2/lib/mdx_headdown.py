"""
Downgrade headings.

Supports a single optional argument, `offset`, which sets the number of
heading levels to offset by. This will automatically be absolutised and
integerised.

(c) 2018, Sascha Cowley under the MIT Licence.

-----

Copyright 2018, Sascha Cowley.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to
deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
"""

# Import relevant modules.
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor
import re

name = "mdx_headdown"


class DowngradeHeadingsTreeprocessor(Treeprocessor):
    """ Downgrade headings via the Treeprocessor interface. """
    def run(self, root):
        # Ensure the offset value is a positive (or zero) integer.
        offset = abs(int(self.config['offset']))

        # Match headings 1-6 case insensitively if they're the entirety of the
        # string, and capture the heading number.
        heading_pattern = re.compile('^h([1-6])$', re.I)

        for element in root:
            # Attempt matching each tag against the heading pattern.
            match = heading_pattern.match(element.tag)
            if match:
                # For all headings, increase their heading number by `offset`.
                # If the new heading number is > 6, use 6 instead.
                element.tag = 'h%d' % min(6, int(match.group(1))+offset)


class DowngradeHeadingsExtension(Extension):
    """ Setup the extension for usage. """
    def __init__(self, **kwargs):
        # Default configuration.
        self.config = {
            'offset': [1, 'Number of heading levels to offset by.'],
        }
        # Initialise superclass, allowing configuration to be overridden.
        super(DowngradeHeadingsExtension, self).__init__(**kwargs)

    def extendMarkdown(self, md):
        # Register the plugin as a Treeprocessor. """
        md.treeprocessors.register(
            DowngradeHeadingsTreeprocessor(md),
            'downgradeheadings', 200
        )
        # And give the actual processor access to the configuration.
        DowngradeHeadingsTreeprocessor.config = self.getConfigs()


def makeExtension(*args, **kwargs):
    # Tell Markdown to make this an extension.
    return DowngradeHeadingsExtension(*args, **kwargs)
