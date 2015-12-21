# Dependencies

* python3
* python3-requests 2.7.0
* python3-jinja2 2.7.3
* incron

# Install

Add a following line to incrontab:

```/srv/www IN_CREATE,IN_DELETE,IN_MOVE /home/mirror/newindex/genindex.py```

## Locales

Install zh_CN locales since the `genisolist.ini` file contains Chinese characters.

# Copyright

    Copyright © 2013-2015 USTC Linux User Group <lug@ustc.edu.cn>
    All rights reserved.

    This file is part of Mirrors-index.

    Mirrors-index is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License version 2 as
    published by the Free Software Foundation.

    Mirrors-index is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Mirrors-index.  If not, see <http://www.gnu.org/licenses/>.

* * *
LUG@USTC
