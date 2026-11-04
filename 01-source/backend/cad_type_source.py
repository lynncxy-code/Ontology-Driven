"""Read type identities without expanding geometry in large ASCII drawings."""
from contextlib import contextmanager
import os

import ezdxf
from ezdxf.addons.iterdxf import IterDXF
from ezdxf.lldxf.tagger import ascii_tags_loader


LARGE_DRAWING_BYTES = 32 * 1024 * 1024


@contextmanager
def type_scan_source(path):
    with open(path, 'rb') as stream:
        binary = stream.read(22).startswith(b'AutoCAD Binary DXF')
    if not binary and os.path.getsize(path) >= LARGE_DRAWING_BYTES:
        # Index/stream ENTITIES only: no BLOCKS geometry tree or bbox expansion.
        source = IterDXF(path)
        try:
            unit_code = 0
            with open(path, encoding=source.encoding, errors='surrogateescape') as stream:
                tags = iter(ascii_tags_loader(stream))
                for tag in tags:
                    if tag.code == 0 and tag.value == 'ENDSEC':
                        break
                    if tag.code == 9 and tag.value == '$INSUNITS':
                        unit_code = int(next(tags).value or 0)
                        break
            yield source.modelspace(types=['INSERT']), unit_code, source.encoding, 'identity_only'
        finally:
            source.close()
    else:
        doc = ezdxf.readfile(path)
        yield doc.modelspace().query('INSERT'), int(doc.header.get('$INSUNITS', 0) or 0), doc.encoding, 'full'
