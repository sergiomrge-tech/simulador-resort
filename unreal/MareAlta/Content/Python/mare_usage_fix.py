"""Nanite/ISM usage flags for every opaque material under the given folders (comma separated), saved. Without them
the cooked game draws the default material (08/11: the summit trail's Trail_Earth/Trail_Log after its mesh turned
Nanite). PIE stopped."""
import json


def run(arg='/Game/Summit,/Game/World/Island'):
    import mare_boat_tour
    return json.dumps({f: mare_boat_tour.fix_usage(f) for f in arg.split(',') if f})
