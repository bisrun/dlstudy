import pandas as pd
import geojson
from shapely.geometry import Point, LineString, Polygon
import sqlite3
import os
import common

db_path  = "/project/callbary/stat_log/ctc_stat.db"
log_file_pattern = '/project/callbary/stat_log/**/*.csv'

def run():
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
        filelist = common.getFileList(log_file_pattern)
        conn = sqlite3.connect(db_path)
        # cursor object

        with conn:
            conn.enable_load_extension(True)
            conn.load_extension("mod_spatialite.so")

            for i, filepath in enumerate(filelist):
                line = "{}\t{}\n".format(i, filepath)
                #conn.execute("SELECT InitSpatialMetaData(1);")

                #
                #statlog_wf = open(statlog_filepath, mode='wt', encoding='utf-8')
                df = pd.read_csv(filepath, encoding='utf-8')
                print("len", len(df))
                df.to_sql("ctc_stat", conn, if_exists='append', index=False)

            ## field expand
            conn.execute("ALTER TABLE ctc_stat ADD COLUMN task_name TEXT")
            conn.execute("ALTER TABLE ctc_stat ADD COLUMN _day INT")
            conn.execute("ALTER TABLE ctc_stat ADD COLUMN _hour INT")
            conn.execute("ALTER TABLE ctc_stat ADD COLUMN _min INT")

            conn.execute("update ctc_stat set  _day=substr(timstamp, 9,2), _hour=substr(timstamp, 12,2), "
                         "_min=substr(timstamp, 15,2), task_name=substr(CURRENTTASK, 4,15)")
            conn.execute("update ctc_stat set VALID=0 where  task_name in ('20211118-151813','20211118-152740','20211118-152933')")
            conn.execute("create table ctc_stat2  as select * from ctc_stat where VALID=1 ")

            conn.commit()
            # Close the connection
            #conn.close()

    except KeyboardInterrupt:
        print('\n\rquit')

if __name__ == '__main__':
    run()
    print("finish")

