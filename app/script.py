from os import environ
from json import dumps, loads
from typing import cast, Any
from datetime import date, timedelta

from ics import Event, Calendar
from tmdb import TMDB
from boto3 import client
from dateutil import parser


BUCKET_NAME = environ['BUCKET_NAME']
CALENDARS_BUCKET_NAME = environ['CALENDARS_BUCKET_NAME']
ACCESS_TOKEN_PARAMETER_NAME = environ['ACCESS_TOKEN_PARAMETER_NAME']

s3 = client('s3')
ssm = client('ssm')
access_token = ssm.get_parameter(Name=ACCESS_TOKEN_PARAMETER_NAME, WithDecryption=True)['Parameter']['Value']
tmdb = TMDB(access_token)


def update_serie(serie_id: int, /) -> None:
    videos = tmdb.series.get_videos(serie_id)
    details = tmdb.series.get_details(serie_id)
    alternative_titles = tmdb.series.get_alternative_titles(serie_id)

    # avoid storing series with the word `sex`
    if 'sex' in [word.strip().lower() for word in details['name'].split()]:
        print(f'serie with id `{serie_id}` and name `{details["name"]}` contains the word `sex`, skipping')
        return

    serie = {
        'id': int(serie_id),
        'images': {
            'poster': '',
            'backdrop': '',
        },
        'videos': videos,
        'details': details,
        'alternative_titles': alternative_titles,
    }

    prefix = 'series/images'
    poster = details['poster_path']
    backdrop = details['backdrop_path']
    if poster:
        ext, data = tmdb.utils.images.get_image(poster)
        key = f'{prefix}/{serie_id}-poster.{ext}'
        s3.put_object(
            Key=key, 
            Body=data, 
            Bucket=BUCKET_NAME,
            ContentType=f'image/{ext}',
        )
        serie['images']['poster'] = f'./images/{serie_id}-poster.{ext}'

    if backdrop:
        ext, data = tmdb.utils.images.get_image(backdrop)
        key = f'{prefix}/{serie_id}-backdrop.{ext}'
        s3.put_object(
            Key=key, 
            Body=data, 
            Bucket=BUCKET_NAME,
            ContentType=f'image/{ext}',
        )
        serie['images']['backdrop'] = f'./images/{serie_id}-backdrop.{ext}'

    s3.put_object(
        Key=f'series/{serie_id}.json', 
        Body=dumps(serie).encode(),
        Bucket=BUCKET_NAME,
        ContentType='application/json',
    )


def update_movie(movie_id: int, /) -> None:
    videos = tmdb.movies.get_videos(movie_id)
    details = tmdb.movies.get_details(movie_id)
    release_dates = tmdb.movies.get_release_dates(movie_id)
    alternative_titles = tmdb.movies.get_alternative_titles(movie_id)

    # this is the event's title
    original_title = details['original_title']
    regional_title = [entry['title'] for entry in alternative_titles if entry['iso_3166_1'] == 'MX']
    title = regional_title[0] if regional_title else original_title

    # avoid storing movies with the word $3x
    if 'sex' in [word.strip().lower() for word in title.split()]:
        print(f'movie with id `{movie_id}` and name `{title}` contains the word `sex`, skipping')
        return

    # do not store movies without release dates
    if not release_dates:
        print(f'movie with id `{movie_id}` and name `{title}` has not release dates, skipping')
        return

    movie = {
        'id': int(movie_id),
        'images': {
            'poster': '',
            'backdrop': '',
        },
        'videos': videos,
        'details': details,
        'release_dates': release_dates,
        'alternative_titles': alternative_titles,
    }

    prefix = 'movies/images'
    poster = details['poster_path']
    backdrop = details['backdrop_path']
    if poster:
        ext, data = tmdb.utils.images.get_image(poster)
        key = f'{prefix}/{movie_id}-poster.{ext}'
        s3.put_object(
            Key=key, 
            Body=data, 
            Bucket=BUCKET_NAME,
            ContentType=f'image/{ext}',
        )
        movie['images']['poster'] = f'./images/{movie_id}-poster.{ext}'

    if backdrop:
        ext, data = tmdb.utils.images.get_image(backdrop)
        key = f'{prefix}/{movie_id}-backdrop.{ext}'
        s3.put_object(
            Key=key, 
            Body=data, 
            Bucket=BUCKET_NAME, 
            ContentType=f'image/{ext}',
        )
        movie['images']['backdrop'] = f'./images/{movie_id}-backdrop.{ext}'

    s3.put_object(
        Key=f'movies/{movie_id}.json', 
        Body=dumps(movie).encode(),
        Bucket=BUCKET_NAME,
        ContentType='application/json',
    )


def write_calendar(*, key: str, calendar: Calendar) -> None:
    s3.put_object(
        Key=key,
        Body=calendar.serialize().encode(),
        Bucket=CALENDARS_BUCKET_NAME,
        ContentType='text/calendar; charset=utf-8',
        ContentDisposition='inline; filename="calendario.ics"',
    )


def get_objects(prefix: str, continuation_token: str | None = None, /) -> list[dict[str, Any]]:
    kwargs: dict[str, Any] = {}
    
    if continuation_token:
        kwargs = {
            'ContinuationToken': continuation_token,
        }
    
    response = s3.list_objects_v2(
        Bucket=BUCKET_NAME,
        Prefix=prefix,
        MaxKeys=1000,
        **kwargs,
    )

    objects = response.get('Contents', [])
    next_continuation_token = response.get('NextContinuationToken')
    if next_continuation_token:
        objects += get_objects(next_continuation_token)
    
    return cast(list[dict[str, Any]], objects)


def create_movies_calendar():
    movies = []
    
    objects = get_objects('movies/')
    for obj in objects:
        key = obj['Key']
        if not key.endswith('.json'):
            continue
        response = s3.get_object(
            Key=key,
            Bucket=BUCKET_NAME,
        )
        
        movie = loads(response['Body'].read().decode())
        mx_release_dates = [rd for rd in movie['release_dates'] if rd['iso_3166_1'] == 'MX']
        mx_release_dates = mx_release_dates[0]['release_dates']

        original_title = movie['details']['original_title']
        regional_title = [entry['title'] for entry in movie['alternative_titles'] if entry['iso_3166_1'] == 'MX']
        
        title = regional_title[0] if regional_title else original_title

        for release_date in mx_release_dates:
            url = f'https://themoviedb.org/movie/{movie["id"]}?language=es'
            description = movie['details']['overview']
            if description:
                description += '\n\n' + url
            else:
                description = url
            event = {
                'name': f'🍿 {title}',
                'begin': release_date['release_date'],
                'description': description,
            }
            event = Event(**event)
            event.make_all_day()

            if release_date['type'] == 3:  # theatrical release
                movies.append(event)

        if movies:
            write_calendar(
                key='ics/peliculas/calendario.ics',
                calendar=Calendar(events=movies),
            )


def create_series_calendar():
    today = date.today()
    series = []
    
    objects = get_objects('series/')
    for obj in objects:
        key = obj['Key']
        if not key.endswith('.json'):
            continue
        response = s3.get_object(
            Key=key,
            Bucket=BUCKET_NAME,
        )
        
        serie = loads(response['Body'].read().decode())

        for season in serie['details']['seasons']:
            air_date = season['air_date']
            season_number = season['season_number']

            if not air_date:
                continue
            air_date = parser.parse(air_date)

            # avoid seasons > 2 years old
            if air_date.year < today.year - 1:
                continue
            
            url = f'https://themoviedb.org/tv/{serie["id"]}?language=es'
            description = season['overview'] if season['overview'] else serie['details']['overview']
            if description:
                description += '\n\n' + url
            else:
                description = url
            
            event = {
                'name': f'📺 T{season_number} {serie["details"]["name"]}',
                'begin': air_date,
                'description': description,
            }

            event = Event(**event)
            event.make_all_day()

            series.append(event)

        if series:
            write_calendar(
                key='ics/series/calendario.ics',
                calendar=Calendar(events=series),
            )


if __name__ == '__main__':
    since = date.today()
    until = since + timedelta(weeks=4 * 6)
    upcoming_movies = tmdb.movies.get_upcoming_movies(since, until)

    # update upcoming movies
    movie_ids = [m['id'] for m in upcoming_movies]
    for movie_id in movie_ids:
        update_movie(movie_id)
    
    # update upcoming series
    upcoming_series = tmdb.series.get_upcoming_series(since, until)
    serie_ids = [m['id'] for m in upcoming_series]b
    for serie_id in serie_ids:
        update_serie(serie_id)

    # create calendars
    create_movies_calendar()
    create_series_calendar()
