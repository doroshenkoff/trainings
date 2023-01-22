import os
from bson import ObjectId
from dotenv import load_dotenv, find_dotenv
from pymongo import MongoClient, DESCENDING
from gpx_parser import Track
from gridfs import Database
from pathlib import Path
from datetime import datetime


load_dotenv(find_dotenv())
password = os.environ.get('MONGODB_PASS')
connection_str = f"mongodb+srv://swamibase:{password}@tutclaster.yiyxzfd.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(connection_str)
records_db = client.records
trainings = records_db.trainings


def insert_record(track: Track):
    if not get_track_numbers_by_params(date=track.track_date):
        track.get_track_result()
        out = track.serialize()
        trainings.insert_one(out)
        add_track_points(track, records_db)
        print('The record is succesfully inserted to the database')
        return True     
    else:
        print('There is already this track record in the database')
        return False


def add_track_points(track: Track, db: Database):
    track_points = db.points
    trainings = db.trainings
    track_date = track.track_date
    mongo_track = trainings.find_one({'date': track_date}, {'_id': 1})
    print(mongo_track)
    if mongo_track:
        if not track_points.count_documents({'track_id': mongo_track['_id']}):
            out = {
            'track_id': mongo_track['_id'],
            'points': track.serialize_points()
             }
            track_points.insert_one(out)
            print('Track point are successfully added to the database')
        else:
            print('points of this track are alredy added to the database')    
    else:
        print('This track is not recorded to the database') 


def _parse_results(results):
    def func(item):
        item['_id'] = str(item['_id'])
        worst_lap = max(item['laps'], key=lambda lap: lap['temp'])
        item['worst'] = worst_lap['temp']
        return item
    return map(func, results.sort('date', DESCENDING))    


def get_trainings_to_request(beg: int=0, limit: int=0, **params):
    count = trainings.count_documents(params)       
    results = trainings.find(params, {'user_id': 0,})
    results = _parse_results(results)
    if beg >= count:
        beg = 0
    if limit:
        if beg + limit >= count:    
            return {'records': list(results)[beg:]}
        return {'records': list(results)[beg: beg + limit]}    
    return {'records': list(results)}        


def get_track_numbers_by_params(**params):
    count = trainings.count_documents(params)
    return count        


def get_points_by_id(id):
    table = records_db.points
    track_id = ObjectId(id)
    result = table.find_one({'track_id': track_id}, {'_id': 0, 'track_id': 0, })
    return result


def add_tracks_from_dir_to_db(dir='C:/data/geo_data/'):
    path = Path(dir)
    files = [f for f in path.iterdir() if f.suffix == '.gpx']
    for file in files:
        track = Track(file)
        insert_record(track, records_db) 


def get_user(**params):
    users = records_db.users
    return users.find_one(params, {'_id': 0})


#returns all the tracks by the cirtain month
def get_tracks(year: int, month: int):
    down_date = datetime(year, month, 1)
    up_date = datetime(year if month < 12 else year+1, 1 if month==12 else month+1, 1)
    results = trainings.find({'$and': 
                            [{'date': {'$gt': down_date}}, {'date': {'$lt': up_date}}]
                            },
                            {'user_id': 0,})
    results = _parse_results(results)
    return {'records': list(results)}         
    


#-----Just for one-time updating--------------
def update_trainings():
    users = records_db.users
    andy = users.find_one({'username': 'andy'})
    try:
        trainings.update_many({}, {'$set': {'user_id': andy['_id']}}) 
        print('Updated')
    except Exception as err:
        print('Not updated')   
        print(err.args)


if __name__ == '__main__':
    print(get_tracks(2023, 1))
#------------------------------------------

  