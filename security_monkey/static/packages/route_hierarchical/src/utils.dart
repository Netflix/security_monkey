library route.utils;

bool mapsShallowEqual(Map a, Map b) => a.length == b.length &&
    a.keys.every((k) => b.containsKey(k) && a[k] == b[k]);
