#!/usr/bin/python
"""Raise the stage-0 Sisu indexer's class-file ceiling to the running JDK.

javapackages-bootstrap shades ASM inside org.eclipse.sisu.inject. That copy
rejects class files newer than Java 25 (major 69). The indexer only parses
class structure, and this JDK's classes parse once the ceiling is the
running major version. The check is a bipush, so the major must fit in a
signed byte.
"""

import os
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ENTRY = "org/eclipse/sisu/space/asm/ClassReader.class"
# The constructor does readShort(); bipush 69; if_icmple. 69 is Java 25.
OLD_MAJOR = 69


def java_home() -> Path:
    env = os.environ.get("JAVA_HOME")
    if env:
        return Path(env)
    java = shutil.which("java")
    if not java:
        raise SystemExit("JAVA_HOME is unset and java is not on PATH")
    return Path(java).resolve().parent.parent


def runtime_major(home: Path) -> int:
    jimage = home / "bin" / "jimage"
    modules = home / "lib" / "modules"
    if not jimage.is_file() or not modules.is_file():
        raise SystemExit(f"not a JDK: {home}")
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.check_call(
            [
                str(jimage), "extract",
                "--dir", tmp,
                "--include", "regex:.*/java/lang/Object.class",
                str(modules),
            ],
            stdout=subprocess.DEVNULL,
        )
        found = [path for path in Path(tmp).rglob("Object.class") if path.as_posix().endswith("java/lang/Object.class")]
        if len(found) != 1:
            raise SystemExit(f"expected java/lang/Object.class from {modules}, found {found}")
        data = found[0].read_bytes()
    if data[:4] != b"\xca\xfe\xba\xbe":
        raise SystemExit("Object.class is not a class file")
    return struct.unpack(">H", data[6:8])[0]


def patch(data: bytes, major: int) -> bytes:
    if major > 127:
        raise SystemExit(f"class major {major} does not fit in the ASM bipush check")
    ceiling = max(OLD_MAJOR, major)
    found = []
    start = 0
    tail = bytes((0x10, OLD_MAJOR, 0xA4))
    while True:
        index = data.find(tail, start)
        if index < 0:
            break
        if index >= 3 and data[index - 3] == 0xB6:
            found.append(index)
        start = index + 1
    if len(found) != 1:
        raise SystemExit(f"expected one ASM version check, found {len(found)}")
    out = bytearray(data)
    out[found[0] + 1] = ceiling
    return bytes(out)


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(f"usage: {sys.argv[0]} SOURCE.jar DEST.jar")
    source = Path(sys.argv[1])
    dest = Path(sys.argv[2])
    major = runtime_major(java_home())
    with zipfile.ZipFile(source) as archive:
        original = archive.read(ENTRY)
        info = archive.getinfo(ENTRY)
        patched = patch(original, major)
        if dest.exists():
            dest.unlink()
        with zipfile.ZipFile(dest, "w") as out:
            for item in archive.infolist():
                blob = patched if item.filename == ENTRY else archive.read(item.filename)
                out.writestr(item if item.filename != ENTRY else info, blob)
    print(f"sisu indexer class-file ceiling {max(OLD_MAJOR, major)} (running JDK major {major})")


if __name__ == "__main__":
    main()
