"""Copy the pre-built poster image to the output directory.

The poster (entry.png) is built ahead of time and checked into this
repository. This program does no rendering at all: it only validates
the bundled image and byte-copies it to the output directory, so it
runs anywhere with a stock Python 3 interpreter.
"""

import os
import shutil
import struct
import sys

SOURCE_NAME = "entry.png"
EXPECTED_WIDTH = 1024
EXPECTED_HEIGHT = 1024
MAX_SIZE_BYTES = 1024 * 1024
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def fail(message):
    print("error: %s" % message, file=sys.stderr)
    return 1


def validate_png(path):
    """Check that path is a 1024x1024 PNG no larger than 1 MiB."""
    try:
        size = os.path.getsize(path)
    except OSError as exc:
        return "cannot stat %s: %s" % (path, exc)
    if size > MAX_SIZE_BYTES:
        return "%s is %d bytes, over the 1 MiB limit" % (path, size)
    if size < 33:
        return "%s is only %d bytes, too small to be a PNG" % (path, size)
    try:
        with open(path, "rb") as handle:
            header = handle.read(33)
    except OSError as exc:
        return "cannot read %s: %s" % (path, exc)
    if header[:8] != PNG_SIGNATURE:
        return "%s does not start with the PNG signature" % path
    # IHDR chunk: length (4 bytes) + type "IHDR" (4 bytes) + data.
    # Width and height are the first 8 bytes of the IHDR data.
    ihdr_length = struct.unpack(">I", header[8:12])[0]
    ihdr_type = header[12:16]
    if ihdr_type != b"IHDR" or ihdr_length != 13:
        return "%s has no valid IHDR chunk" % path
    width, height = struct.unpack(">II", header[16:24])
    if width != EXPECTED_WIDTH or height != EXPECTED_HEIGHT:
        return "%s is %dx%d, expected %dx%d" % (
            path,
            width,
            height,
            EXPECTED_WIDTH,
            EXPECTED_HEIGHT,
        )
    return None


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(script_dir, SOURCE_NAME)
    output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    destination = os.path.join(output_dir, SOURCE_NAME)

    problem = validate_png(source)
    if problem is not None:
        return fail(problem)

    try:
        os.makedirs(output_dir, exist_ok=True)
        shutil.copyfile(source, destination)
        # Guard against a truncated copy: the output must be byte-identical
        # in size to the validated source.
        if os.path.getsize(destination) != os.path.getsize(source):
            return fail("copied file size mismatch for %s" % destination)
    except OSError as exc:
        return fail("cannot copy %s to %s: %s" % (source, destination, exc))

    print("copied %s to %s" % (source, destination))
    return 0


if __name__ == "__main__":
    sys.exit(main())
