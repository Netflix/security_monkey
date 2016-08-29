// Note: This does not handle dates using hourly offset like '2012-02-27T14+00:00'
// Assume dates from API are ZULU.  Append 'z' if needed.
DateTime localDateFromAPIDate(String apiDate) {
  if (apiDate.endsWith('z')||apiDate.endsWith('Z')) {
    return DateTime.parse(apiDate).toLocal();
  }
  return DateTime.parse(apiDate+"z").toLocal();
}