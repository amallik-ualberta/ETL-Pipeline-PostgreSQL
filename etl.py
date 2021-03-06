import os
import glob
import psycopg2
import pandas as pd
from sql_queries import *


def process_song_file(cur, filepath):
    
    """
        processes 1 song file and extracts necessary information to load the songs and aritsts table
        Parameters : curson, filepath.
        Retruns : None.
    """
    
    # open song file
    df = pd.read_json(filepath, lines = True)

    # insert song record
    
    song_id = list(df["song_id"].values)[0]
    title = list(df["title"].values)[0]
    artist_id = list(df["artist_id"].values)[0]
    year = int(list(df["year"].values)[0])
    duration = float(list(df["duration"].values)[0])
    
    if (song_id is not None and artist_id is not None):
        song_data = (song_id, title, artist_id, year, duration)
        cur.execute(song_table_insert, song_data)
        
    
    # insert artist record
    
    artist_name = list(df["artist_name"].values)[0]
    location = list(df["artist_location"].values)[0]
    latitude = float(df["artist_latitude"].values[0])
    longitude = float(df["artist_longitude"].values[0])
    
    if (artist_id is not None):
        artist_data = (artist_id, artist_name, location, latitude, longitude)
        cur.execute(artist_table_insert, artist_data)
    
    


def process_log_file(cur, filepath):
    
    """
        processes 1 log file and extracts necessary information to load time, users and songplays table.
        Parameters : curson, filepath.
        Retruns : None.
    """
    
    # open log file
    df = pd.read_json(filepath, lines=True)

    # filter by NextSong action
    df = df[df["page"] == "NextSong"]

    # convert timestamp column to datetime
    t = pd.to_datetime(df["ts"], unit='ms')
    
    hour = t.map(lambda datetime : datetime.hour)
    day = t.map(lambda datetime : datetime.day)
    weekofyear = t.map(lambda datetime : datetime.weekofyear)
    month = t.map(lambda datetime : datetime.month)
    year = t.map(lambda datetime : datetime.year)
    dayofweek = t.map(lambda datetime : datetime.dayofweek)
    
    # insert time data records
    time_data = (df["ts"], hour, day, weekofyear, month, year, dayofweek)
    column_labels = ("timestamp", "hour", "day", "week of year", "month", "year", "weekday")
    dictionary = dict(zip(column_labels, time_data)) 
    time_df = pd.DataFrame(dictionary)

    for i, row in time_df.iterrows():
        cur.execute(time_table_insert, list(row))

    # load user table
    user_df = pd.DataFrame([df["userId"], df["firstName"], df["lastName"], df["gender"], df["level"]]).T

    # insert user records
    for i, row in user_df.iterrows():
        cur.execute(user_table_insert, row)

    # insert songplay records
    for index, row in df.iterrows():
        
        # get songid and artistid from song and artist tables
        cur.execute(song_select, (row.song, row.artist, row.length))
        results = cur.fetchone()
        
        if results:
            songid, artistid = results
        else:
            songid, artistid = None, None

        # insert songplay record
        if (row.userId is not None and songid is not None and artistid is not None):
            songplay_data = (row.ts, row.userId, row.level, songid, artistid, row.sessionId, row.location, row.userAgent)
            cur.execute(songplay_table_insert, songplay_data)


def process_data(cur, conn, filepath, func):
    
    """
        Gets all the data files by traversing through all the subdirectories of a directory.
        Iterates over the files and calls the appropriate processing function for each of the files.
        
        Parameters : cursor, connection, filepath, function
    """
    # get all files matching extension from directory
    all_files = []
    for root, dirs, files in os.walk(filepath):
        files = glob.glob(os.path.join(root,'*.json'))
        for f in files :
            all_files.append(os.path.abspath(f))

    # get total number of files found
    num_files = len(all_files)
    print('{} files found in {}'.format(num_files, filepath))

    # iterate over files and process
    for i, datafile in enumerate(all_files, 1):
        func(cur, datafile)
        conn.commit()
        print('{}/{} files processed.'.format(i, num_files))


def main():
    conn = psycopg2.connect("host=127.0.0.1 dbname=sparkifydb user=student password=student")
    cur = conn.cursor()

    process_data(cur, conn, filepath='data/song_data', func=process_song_file)
    process_data(cur, conn, filepath='data/log_data', func=process_log_file)

    conn.close()


if __name__ == "__main__":
    main()