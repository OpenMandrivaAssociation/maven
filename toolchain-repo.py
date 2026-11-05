#!/usr/bin/python
"""Point Maven's built-in lifecycle at javapackages-bootstrap plugins.

Maven 3.10 binds the jar lifecycle to plugins whose versions are read
from plugin-versions.properties at startup. Those jars are not system
packages. This writes them, and their compile and runtime dependencies,
as a normal Maven repository under the destination. sysjar links that
tree into the build repository without indexing it, so a project
dependency is still missing when the distribution has not packaged it.

Artifacts exported by maven-core are left out. The running Maven already
puts them on the plugin realm, and a second copy drops the session.
"""

from __future__ import annotations

import hashlib
import sys
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

PROP_NAME = "org/apache/maven/lifecycle/providers/plugin-versions.properties"
POM_NS = "http://maven.apache.org/POM/4.0.0"

# Versions that exist in javapackages-bootstrap. The four jar-lifecycle
# plugins are resolved while building to package, including surefire.
PINNED = {
    "maven-resources-plugin": "3.3.1.MBI",
    "maven-compiler-plugin": "3.12.1.MBI",
    "maven-surefire-plugin": "3.2.2.MBI",
    "maven-jar-plugin": "3.3.0.MBI",
}

# Other bindings only need a version string Maven will accept. package
# does not resolve install or deploy, and the other packagings are not
# what the distribution builds with this Maven yet.
FALLBACK = {
    "maven-clean-plugin": "3.5.0",
    "maven-site-plugin": "3.21.0",
    "maven-install-plugin": "3.1.4",
    "maven-deploy-plugin": "3.1.4",
    "maven-ear-plugin": "3.3.0",
    "maven-ejb-plugin": "3.3.0",
    "maven-plugin-plugin": "3.9.0",
    "maven-rar-plugin": "3.1.0",
    "maven-war-plugin": "3.4.0",
}

SEEDS = (
    ("org.apache.maven.plugins", "maven-resources-plugin", "3.3.1.MBI"),
    ("org.apache.maven.plugins", "maven-compiler-plugin", "3.12.1.MBI"),
    ("org.apache.maven.plugins", "maven-surefire-plugin", "3.2.2.MBI"),
    ("org.apache.maven.plugins", "maven-jar-plugin", "3.3.0.MBI"),
)

SKIP_SCOPES = {"test", "provided", "system", "import"}


class Record:
    def __init__(self, group, artifact, classifier, extension, version, path):
        self.group = group
        self.artifact = artifact
        self.classifier = classifier
        self.extension = extension
        self.version = version
        self.path = path
        self.deps = []

    def ga(self):
        return f"{self.group}:{self.artifact}"


def main(argv):
    if len(argv) != 4:
        raise SystemExit("usage: toolchain-repo.py BOOTSTRAP MAVEN_CORE_JAR DEST")
    bootstrap = Path(argv[1])
    core = Path(argv[2])
    dest = Path(argv[3])
    if not bootstrap.is_dir():
        raise SystemExit(f"no bootstrap tree at {bootstrap}")
    if not core.is_file():
        raise SystemExit(f"no maven-core jar at {core}")
    patch_properties(core)
    records = load_metadata(bootstrap)
    exported = load_exported(core)
    chosen = closure(records, exported, bootstrap)
    write_repo(dest, chosen, records, exported, bootstrap)
    print(f"toolchain: {len(chosen)} artifacts")


def patch_properties(jar_path):
    tmp = jar_path.with_name(jar_path.name + ".toolchain")
    seen = set()
    with zipfile.ZipFile(jar_path) as src, zipfile.ZipFile(tmp, "w") as dst:
        found = False
        for info in src.infolist():
            data = src.read(info.filename)
            if info.filename == PROP_NAME:
                data, seen = rewrite_properties(data)
                found = True
            out = zipfile.ZipInfo(filename=info.filename, date_time=info.date_time)
            out.compress_type = info.compress_type
            out.external_attr = info.external_attr
            out.flag_bits = info.flag_bits
            dst.writestr(out, data)
    if not found:
        tmp.unlink(missing_ok=True)
        raise SystemExit(f"{PROP_NAME} is not in {jar_path}")
    missing = [name for name in PINNED if name not in seen]
    if missing:
        tmp.unlink(missing_ok=True)
        raise SystemExit(f"plugin-versions.properties has no {', '.join(missing)}")
    tmp.replace(jar_path)


def rewrite_properties(data):
    text = data.decode("utf-8")
    newline = "\r\n" if "\r\n" in text else "\n"
    seen = set()
    out = []
    for line in text.splitlines():
        body, sep, comment = line.partition("#")
        if "=" not in body:
            out.append(line)
            continue
        key, value = body.split("=", 1)
        name = key.strip()
        if name in PINNED:
            value = PINNED[name]
            seen.add(name)
        elif "${" in value and name in FALLBACK:
            value = FALLBACK[name]
        rebuilt = f"{key}={value}"
        if sep:
            rebuilt = f"{rebuilt}#{comment}"
        out.append(rebuilt)
    return newline.join(out).encode("utf-8") + (newline.encode("ascii") if text.endswith(("\n", "\r\n")) else b""), seen


def load_exported(jar_path):
    names = set()
    with zipfile.ZipFile(jar_path) as archive:
        try:
            raw = archive.read("META-INF/maven/extension.xml")
        except KeyError:
            raise SystemExit(f"{jar_path} has no META-INF/maven/extension.xml")
    root = ET.fromstring(raw)
    for node in root.iter():
        if node.tag.endswith("exportedArtifact") and node.text and ":" in node.text:
            names.add(node.text.strip())
    if "org.apache.maven:maven-core" not in names:
        raise SystemExit(f"extension.xml in {jar_path} does not export maven-core")
    return names


def load_metadata(bootstrap):
    meta = bootstrap / "maven-metadata"
    if not meta.is_dir():
        raise SystemExit(f"no metadata under {meta}")
    records = {}
    aliases = {}
    for path in sorted(meta.glob("*.xml")):
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            raise SystemExit(f"cannot parse {path}: {exc}")
        parents = {child: parent for parent in root.iter() for child in list(parent)}
        for node in root.iter("artifact"):
            parent = parents.get(node)
            if parent is None or parent.tag != "artifacts":
                continue
            group = text(node, "groupId")
            artifact = text(node, "artifactId")
            version = text(node, "version")
            if not group or not artifact or not version:
                continue
            extension = text(node, "extension") or "jar"
            classifier = text(node, "classifier")
            rec = Record(group, artifact, classifier, extension, version, text(node, "path"))
            rec.deps = dependencies(node)
            records.setdefault((group, artifact, classifier, extension), []).append(rec)
            for alias in aliases_of(node, extension):
                aliases.setdefault(alias, []).append(rec)
    for key, recs in aliases.items():
        records.setdefault(key, []).extend(recs)
    return records


def aliases_of(node, extension):
    found = []
    box = node.find("aliases")
    if box is None:
        return found
    for alias in box.findall("alias"):
        group = text(alias, "groupId")
        artifact = text(alias, "artifactId")
        if group and artifact:
            found.append((
                group,
                artifact,
                text(alias, "classifier"),
                text(alias, "extension") or extension,
            ))
    return found


def dependencies(node):
    box = node.find("dependencies")
    if box is None:
        return []
    found = []
    for dep in box.findall("dependency"):
        group = text(dep, "groupId")
        artifact = text(dep, "artifactId")
        if not group or not artifact:
            continue
        extension = text(dep, "extension") or text(dep, "type") or "jar"
        scope = text(dep, "scope") or "compile"
        optional = text(dep, "optional").lower() == "true"
        version = text(dep, "requestedVersion") or text(dep, "resolvedVersion") or text(dep, "version")
        found.append((group, artifact, text(dep, "classifier"), extension, version, scope, optional))
    return found


def text(node, tag):
    child = node.find(tag)
    if child is None or child.text is None:
        return ""
    return child.text.strip()


def closure(records, exported, bootstrap):
    seeds = {(group, artifact) for group, artifact, _version in SEEDS}
    chosen = []
    seen = set()
    queue = [(group, artifact, "", "jar", version, True) for group, artifact, version in SEEDS]
    while queue:
        group, artifact, classifier, extension, version, required = queue.pop(0)
        rec = pick(records, group, artifact, classifier, extension, version)
        if rec is None:
            message = f"missing {group}:{artifact}:{version or '(any)'}"
            if required:
                raise SystemExit(message)
            print(message, file=sys.stderr)
            continue
        ident = (rec.group, rec.artifact, rec.classifier, rec.extension, rec.version)
        if ident in seen:
            continue
        if rec.ga() in exported and (rec.group, rec.artifact) not in seeds:
            continue
        path = resolve_path(rec.path, bootstrap)
        if path is None:
            message = f"missing file for {rec.ga()} {rec.version}: {rec.path or '(none)'}"
            if required:
                raise SystemExit(message)
            print(message, file=sys.stderr)
            continue
        seen.add(ident)
        rec.path = str(path)
        chosen.append(rec)
        for dep in dep_list(records, rec):
            dep_group, dep_artifact, dep_classifier, dep_extension, dep_version, scope, optional = dep
            if optional or scope in SKIP_SCOPES:
                continue
            if dep_extension == "pom":
                continue
            if f"{dep_group}:{dep_artifact}" in exported:
                continue
            queue.append((dep_group, dep_artifact, dep_classifier, dep_extension or "jar", dep_version, False))
    return chosen


def dep_list(records, rec):
    if rec.deps:
        return rec.deps
    pom = pick(records, rec.group, rec.artifact, "", "pom", rec.version)
    if pom is None:
        return []
    return pom.deps


def pick(records, group, artifact, classifier, extension, version):
    found = records.get((group, artifact, classifier, extension or "jar")) or []
    uniq = []
    seen = set()
    for rec in found:
        ident = (rec.group, rec.artifact, rec.classifier, rec.extension, rec.version, rec.path)
        if ident in seen:
            continue
        seen.add(ident)
        uniq.append(rec)
    found = uniq
    if version:
        exact = [rec for rec in found if versions_match(rec.version, version)]
        if len(exact) == 1:
            return exact[0]
        if len(exact) > 1:
            return plain_filename(exact)
    if len(found) == 1:
        return found[0]
    # A versionless request is what the bootstrap build resolved to the
    # unversioned filename. The other file is there for a request that
    # names its version.
    return plain_filename(found)


def versions_match(have, want):
    if not want:
        return False
    if have == want:
        return True
    return have == f"{want}.MBI" or want == f"{have}.MBI"


def plain_filename(records):
    plain = []
    for rec in records:
        name = Path(rec.path).name
        ext = rec.extension or "jar"
        if name in {f"{rec.artifact}.{ext}", f"{rec.artifact}.jar"}:
            plain.append(rec)
    if len(plain) == 1:
        return plain[0]
    return None


def resolve_path(stored, bootstrap):
    if not stored:
        return None
    direct = Path(stored)
    if direct.is_file():
        return direct
    marker = "javapackages-bootstrap/"
    if marker in stored:
        candidate = bootstrap / stored.split(marker, 1)[1]
        if candidate.is_file():
            return candidate
    return None


def write_repo(dest, chosen, records, exported, bootstrap):
    if dest.exists():
        raise SystemExit(f"{dest} already exists")
    versions = {}
    for rec in chosen:
        directory = version_dir(dest, rec.group, rec.artifact, rec.version)
        directory.mkdir(parents=True, exist_ok=True)
        ext = "jar" if rec.extension in {"", "jar", "maven-plugin"} else rec.extension
        blob = directory / file_name(rec.artifact, rec.version, rec.classifier, ext)
        copy_file(Path(rec.path), blob)
        if not rec.classifier:
            pom = directory / file_name(rec.artifact, rec.version, "", "pom")
            write_pom(pom, rec, records, exported, bootstrap)
            checksums(pom)
        versions.setdefault((rec.group, rec.artifact), set()).add(rec.version)
    for (group, artifact), vers in sorted(versions.items()):
        write_metadata(dest, group, artifact, sorted(vers))


def write_pom(path, rec, records, exported, bootstrap):
    ET.register_namespace("", POM_NS)
    root = ET.Element(f"{{{POM_NS}}}project")
    add(root, "modelVersion", "4.0.0")
    add(root, "groupId", rec.group)
    add(root, "artifactId", rec.artifact)
    add(root, "version", rec.version)
    packaging = "maven-plugin" if is_plugin(Path(rec.path)) else "jar"
    add(root, "packaging", packaging)
    deps = []
    for item in dep_list(records, rec):
        group, artifact, classifier, extension, version, scope, optional = item
        if optional or scope in SKIP_SCOPES or extension == "pom":
            continue
        if f"{group}:{artifact}" in exported:
            continue
        picked = pick(records, group, artifact, classifier, extension or "jar", version)
        if picked is None or resolve_path(picked.path, bootstrap) is None:
            continue
        # Publish the coordinate the file is stored under. An alias such as
        # plexus-build-api0 is a different path from the name the dependency used.
        ext = picked.extension or "jar"
        if ext == "maven-plugin":
            ext = "jar"
        deps.append((picked.group, picked.artifact, picked.classifier, ext, picked.version, scope))
    if deps:
        box = ET.SubElement(root, f"{{{POM_NS}}}dependencies")
        for group, artifact, classifier, extension, version, scope in deps:
            node = ET.SubElement(box, f"{{{POM_NS}}}dependency")
            add(node, "groupId", group)
            add(node, "artifactId", artifact)
            add(node, "version", version)
            if classifier:
                add(node, "classifier", classifier)
            if extension != "jar":
                add(node, "type", extension)
            if scope and scope != "compile":
                add(node, "scope", scope)
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def add(parent, tag, value):
    node = ET.SubElement(parent, f"{{{POM_NS}}}{tag}")
    node.text = value
    return node


def is_plugin(path):
    try:
        with zipfile.ZipFile(path) as archive:
            return "META-INF/maven/plugin.xml" in archive.namelist()
    except (OSError, zipfile.BadZipFile):
        return False


def write_metadata(dest, group, artifact, versions):
    root = ET.Element("metadata")
    add_plain(root, "groupId", group)
    add_plain(root, "artifactId", artifact)
    versioning = ET.SubElement(root, "versioning")
    latest = versions[-1]
    add_plain(versioning, "latest", latest)
    add_plain(versioning, "release", latest)
    box = ET.SubElement(versioning, "versions")
    for version in versions:
        add_plain(box, "version", version)
    path = dest.joinpath(*group.split("."), artifact, "maven-metadata.xml")
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
    checksums(path)


def add_plain(parent, tag, value):
    node = ET.SubElement(parent, tag)
    node.text = value
    return node


def version_dir(dest, group, artifact, version):
    parts = group.split(".")
    if not parts or not artifact or not version:
        raise SystemExit(f"unsafe coordinate {group}:{artifact}:{version}")
    if any(part in {"", ".", ".."} for part in parts + [artifact, version]):
        raise SystemExit(f"unsafe coordinate {group}:{artifact}:{version}")
    return dest.joinpath(*parts, artifact, version)


def file_name(artifact, version, classifier, extension):
    mark = f"-{classifier}" if classifier else ""
    return f"{artifact}-{version}{mark}.{extension}"


def copy_file(src, dest):
    dest.write_bytes(src.read_bytes())
    checksums(dest)


def checksums(path):
    data = path.read_bytes()
    for algo in ("sha1", "md5"):
        digest = hashlib.new(algo, data).hexdigest()
        path.with_name(path.name + "." + algo).write_text(digest + "\n", encoding="ascii")


if __name__ == "__main__":
    main(sys.argv)
