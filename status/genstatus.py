# genstatus.py is a seperate, one-time use script that generates the status HTML pages when template files are updated.

import jinja2

CONFIG = {
    "index.html": {
        "main_page": True,
        "grafana": True,
        "title": "Sync Status",
        "endpoint": "https://admin.mirrors.ustc.edu.cn/api/v1/metas"
    },
    "rsync.html": {
        "main_page": False,
        "grafana": False,
        "title": "Mirrors2 Sync Status",
        "endpoint": "https://admin.mirrors.ustc.edu.cn/rsync"
    },
    "mirrors3.html": {
        "main_page": False,
        "grafana": False,
        "title": "Mirrors3 Sync Status",
        "endpoint": "https://admin.mirrors.ustc.edu.cn/mirrors3"
    }
}

def main():
    with open("template.html", "r") as f:
        template = jinja2.Template(f.read())
    for filename in CONFIG:
        with open(filename, "w") as f:
            f.write(template.render(**CONFIG[filename]))

if __name__ == "__main__":
    main()
