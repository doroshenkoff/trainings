import xml.etree.ElementTree as ET
from collections import namedtuple
from datetime import datetime
from functools import total_ordering
import re
import pyproj
from bs4 import BeautifulSoup
from pathlib import Path



@total_ordering
class TimeDelta:
    def __init__(self, seconds):
        self._check_seconds(seconds)
        self._parse_time(seconds)

    def _parse_time(self, seconds):
        self._hours = int(seconds // 3600)
        self._minutes = int(seconds // 60 - self.hours * 60)
        self._seconds = int(seconds - self.hours * 3600 - self.minutes * 60)

    def _check_seconds(self, seconds):
        if isinstance(seconds, int) or isinstance(seconds, float):
            if seconds >= 0:
                self._total_seconds = seconds
        return ValueError('The value must be only positive integer or float')

    @property
    def hours(self):
        return self._hours

    @property
    def minutes(self):
        return self._minutes

    @property
    def seconds(self):
        return self._seconds

    @property
    def total_seconds(self):
        return self._total_seconds

    def __repr__(self):
        return f'TimeDelta({self.hours}:{self.minutes}:{self.seconds})'

    def __str__(self):
        return f'{self.hours}:{self.minutes:02}:{self.seconds:02}'

    def __gt__(self, other):
        if not isinstance(other, self.__class__):
            raise TypeError('The comparable values must be TimeDelta class instances')
        if self.hours == other.hours:
            if self.minutes == other.minutes:
                return self.seconds > other.seconds
            else:
                return self.minutes > other.minutes
        else:
            return self.hours > other.hours

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.hours == other.hours \
               and self.minutes == other.minutes and self.seconds == other.seconds

    def __add__(self, other):
        if isinstance(other, TimeDelta):
            return TimeDelta(self._total_seconds + other._total_seconds)
        return ValueError('You can add only TimeDelta class instances')


class Track:
    def __init__(self, file_source):
        if isinstance(file_source, Path):
            self._file = str(file_source)
        else:
            self._file = file_source
        self._geod = pyproj.Geod(ellps='WGS84')
        self._get_data_from_file(file_source)
        self._distance = 0
        self._best_km = 0
        self._best_3km = 0
        self._best_5km = 0
        self._best_10km = 0


    # #Basic points parser. Uses standart python XML parser
    # def _get_data_from_file(self, file):
    #     Point = namedtuple('Point', 'lat lon date')
    #     tree = ET.parse(file)
    #     root = tree.getroot()
    #     points = root[0][0] or root[0][1]
    #     fmt = "%Y-%m-%dT%H:%M:%SZ"
    #     track = []
    #     for point in points:
    #         lat = float(point.attrib.get('lat'))
    #         lon = float(point.attrib.get('lon'))
    #         date = datetime.strptime(point[0].text, fmt)
    #         track.append(Point(lat, lon, date))
    #     self._beginning_date = track[0].date
    #     self._end_date = track[-1].date
    #     self._track = track


    #Updated points parser. Uses BS4. Grabs information about height if it exists
    def _get_data_from_file(self, file):
        Point = namedtuple('Point', 'lat lon hr date')
        with open(file) as f:
            soup = BeautifulSoup(f, 'xml')
        track_info = soup.findAll(lambda tag: tag.attrs.get('lat') and tag.attrs.get('lon'))
        track = []
        fmt = "%Y-%m-%dT%H:%M:%S"
        for point in track_info:
            lat = float(point.attrs['lat'])
            lon = float(point.attrs['lon'])
            t = point.find('time')
            date = datetime.strptime(t.text[:19], fmt) if t else None
            height = point.find(re.compile('hr|ele'))
            hr = float(height.text) if height is not None else 0 
            track.append(Point(lat, lon, hr, date))
        self._beginning_date = track[0].date
        self._end_date = track[-1].date
        self._track = track    


    def _best_time(self, distance: int):
        if self.distance / 1000 < distance:
            return 0, 0, 0
        f = self.total_time.total_seconds
        i_max = 1
        results = self.track_result
        try:
            for i in range(len(results) - distance + 1):
                s = sum((results[n]['temp'] for n in range(i, i+distance)))
                if s < f:
                    f = s
                    i_max = i + 1
            return i_max, i_max + distance - 1, f
        except:
            return 0

    @property
    def total_time(self):
        return TimeDelta(len(self._track))

    @property
    def avg_speed(self):
        return TimeDelta(len(self._track) * 1000 / self.distance)

    @property
    def track_result(self):
        return self._track_result

    def get_track_result(self):
        self._track_result = []
        km_count = 1
        point_count = 0
        for i in range(len(self._track) - 1):
            p1, p2 = self._track[i:i + 2]
            self._distance += self._geod.inv(p1.lon, p1.lat, p2.lon, p2.lat)[2]
            if self._distance >= km_count * 1000:
                self._track_result.append({
                    'total_time': TimeDelta(i).total_seconds,
                    'temp': TimeDelta(i - point_count).total_seconds,
                    'avg_speed': int(TimeDelta(i / km_count).total_seconds),
                    'point': {
                        'lat': p2.lat,
                        'lon': p2.lon,
                        'hr': p2.hr,
                    }                })
                km_count += 1
                point_count = i
  

    @property
    def distance(self):
        return int(self._distance)

    @property
    def best_km(self):
        if not self._best_km:
            best_km = min(self.track_result, key=lambda item: item['temp'])
            self._best_km = self.track_result.index(best_km) + 1, best_km['temp']
        return self._best_km

    @property
    def best_3km(self):
        if not self._best_3km:
            self._best_3km = self._best_time(3)
        return self._best_3km

    @property
    def best_5km(self):
        if not self._best_5km:
            self._best_5km = self._best_time(5)
        return self._best_5km

    @property
    def best_10km(self):
        if not self._best_10km:
            self._best_10km = self._best_time(10)
        return self._best_10km
    

    @property
    def track_date(self):
        return self._beginning_date

    def serialize(self):
        out = {
            'date': self._beginning_date,
            'distance': self.distance,
            'total_time': self.total_time.total_seconds,
            'average_speed': (round(self.avg_speed.total_seconds, 0)),
            'best_km': {
                'lap': self.best_km[0],
                'speed': self.best_km[1]
            },
            'best_3km': {
                'first_lap': self.best_3km[0],
                'last_lap': self.best_3km[1],
                'speed': self.best_3km[2],
            },
            'best_5km': {
                'first_lap': self.best_5km[0],
                'last_lap': self.best_5km[1],
                'speed': self.best_5km[2],
            },
            'best_10km': {
                'first_lap': self.best_10km[0],
                'last_lap': self.best_10km[1],
                'speed': self.best_10km[2],
            },
            # 'laps': self.track_result,
            'laps': self.track_result
        }
        return out

    def serialize_points(self):
        return [{'lat': p.lat, 'lon': p.lon, 'hr': p.hr} for i, p in enumerate(self._track) if i % 3 == 0]    


if __name__ == '__main__':
    track = Track('C:\data\geo_data\Zepp20220920154200.gpx')
    print(track.serialize_points())







