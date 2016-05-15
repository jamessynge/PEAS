#!/usr/bin/env python3

import pymongo
import warnings
import shutil

from datetime import date, timedelta, datetime

from panoptes.utils.database import PanMongo


def main(start_date=None, end_date=None, database=None, collections=list(), yesterday=False, verbose=False):
    me_cmd = shutil.which('mongoexport')
    assert me_cmd, warnings.warn("No mongoexport command found!")

    db = PanMongo()

    if yesterday:
        start_dt = date.today() - timedelta(1)
        start = datetime(start_dt.year, start_dt.month, start_dt.day, 0, 0, 0, 0)
        end = datetime(start_dt.year, start_dt.month, start_dt.day, 23, 59, 59, 0)
    else:
        assert start_date, warnings.warn("start-date required if not using yesterday")

        y, m, d = [int(x) for x in start_date.split('-')]
        start_dt = date(y, m, d)

        if end_date is None:
            end_dt = start_dt
        else:
            y, m, d = [int(x) for x in end_date.split('-')]
            end_dt = date(y, m, d)

        start = datetime.fromordinal(start_dt.toordinal())
        end = datetime(end_dt.year, end_dt.month, end_dt.day, 23, 59, 59, 0)

    date_query = '{"date": {"$gte": "ISODate(' + start.isoformat() + ')", "$lte": "ISODate' + end.isoformat() + ')"}})'

    for collection in collections:
        start_str = start.strftime('%Y-%m-%d')
        end_str = end.strftime('%Y-%m-%d')
        if end_str != start_str:
            out_file = '/var/panoptes/backups/{}_{}-to-{}.json'.format(collection, start_str, end_str)
        else:
            out_file = '/var/panoptes/backups/{}_{}.json'.format(collection, start_str)

        db_col = getattr(db, collection)
        entries = [x for x in db_col.find({'date': {'$gt': start, '$lt': end}}).sort([('date', pymongo.ASCENDING)])]

        print(entries)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Make a plot of the weather for a give date.")

    parser.add_argument('-y', '--yesterday', action="store_true", dest='yesterday', default=True,
                        help="Yeserday\'s data, defaults to True if start-date is not provided, False otherwise.")
    parser.add_argument("-s", "--start-date", type=str, dest="start_date", default=None,
                        help="[yyyy-mm-dd] Start date, defaults to None; if provided, yesterday is ignored.")
    parser.add_argument("-e", "--end-date", type=str, dest="end_date", default=None,
                        help="[yyyy-mm-dd] End date, defaults to None, causing start-date to exports full day.")
    parser.add_argument('-d', '--database', type=str, dest='database',
                        default='panoptes', help="Mongo db to use for export, defaults to 'panoptes'")
    parser.add_argument('-c', '--collections', type=str, nargs='+',
                        dest='collections', help="Collections to export. One file per collection will be generated.")
    parser.add_argument("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Be verbose.")

    args = parser.parse_args()

    if args.end_date is not None:
        assert args.start_date is not None, warnings.warn("Can't use an end date without a start date")

    if args.start_date is not None:
        args.yesterday = False

    main(**vars(args))