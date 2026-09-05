#!/usr/bin/env python3

import argparse
from pathlib import Path

MARKER = ".mirrors-index-example"
FILES = {
    "alpine/latest-stable/releases/x86_64/README.txt": "Example Alpine release\n",
    "archlinux/core/os/x86_64/core.db": "Example Arch Linux database\n",
    "archlinux/extra/os/x86_64/extra.db": "Example Arch Linux database\n",
    "archlinux/iso/latest/archlinux-2026.09.01-x86_64.iso": "Example Arch Linux ISO\n",
    "debian/dists/stable/Release": "Origin: Debian\nSuite: stable\n",
    "debian/pool/main/h/hello/hello_1.0_amd64.deb": "Example Debian package\n",
    "node/latest-v22.x/node-v22.18.0-x64.msi": "Example Node.js installer\n",
    "ubuntu/dists/noble/Release": "Origin: Ubuntu\nSuite: noble\n",
    "ubuntu/pool/main/h/hello/hello_1.0_amd64.deb": "Example Ubuntu package\n",
    "rust-static/dist/channel-rust-stable.toml": "# Example Rust channel\n",
}


def create_example_tree(root: Path) -> int:
    root = root.expanduser().resolve()
    marker = root / MARKER

    if root.exists() and any(root.iterdir()) and not marker.is_file():
        raise RuntimeError(
            f'refusing to modify non-empty directory without {MARKER}: "{root}"'
        )

    root.mkdir(parents=True, exist_ok=True)
    marker.write_text("Created by tools/create_example_tree.py\n")
    for relative_path, content in FILES.items():
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    return len(FILES)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a small mirror repository tree for local development."
    )
    parser.add_argument(
        "output",
        nargs="?",
        type=Path,
        default=Path("/srv/repo"),
        help="destination directory (default: /srv/repo)",
    )
    args = parser.parse_args()

    try:
        count = create_example_tree(args.output)
    except RuntimeError as error:
        parser.error(str(error))
    print(f'Created {count} example files under "{args.output.resolve()}"')


if __name__ == "__main__":
    main()
