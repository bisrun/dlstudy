import pandas as pd
import geojson
from shapely.geometry import Point, LineString, Polygon
import sqlite3
import os
import common
import pandas.io.sql as sql
import csv

db_path  = "/project/callbary/output/ctc_stat.db"
log_file_pattern = '/project/callbary/output/**/ctc_info_proc_route03.txt'
output_text_file_path = "/project/callbary/output/ctc_stat.txt"

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
                df = pd.read_csv(filepath,  sep='|', encoding='utf-8')
                print("len", len(df))
                df.to_sql("ctc_stat", conn, if_exists='append', index=False)

            ## field expand
            conn.execute("ALTER TABLE ctc_stat ADD COLUMN task_set TEXT")
            conn.execute("ALTER TABLE ctc_stat ADD COLUMN _date INT")
            conn.execute("ALTER TABLE ctc_stat ADD COLUMN _hour INT")
            conn.execute("ALTER TABLE ctc_stat ADD COLUMN _min INT")
            conn.execute("ALTER TABLE ctc_stat ADD COLUMN VALID INT default 1")
            conn.execute("update ctc_stat set distance =1 , eta=1 WHERE pos_from_x=pos_to_x and pos_from_y = pos_to_y and pos_from_x not null and pos_to_x not null")
            conn.execute("update ctc_stat set task_set=substr(task_name, 1,15), _date=substr(task_name, 1,8), _hour=substr(task_name, 10,2), "
                         "_min=substr(task_name, 12,2)")
            conn.execute("update ctc_stat set VALID=0 where  task_set in ('20211118-151813','20211118-152740','20211118-152933')")
            conn.execute("create table ctc_stat2  as select * from ctc_stat where VALID=1 ")

            ###
            cur = conn.cursor()
            cur.execute("SELECT * FROM ctc_stat")
            rows = cur.fetchall()
            with open(output_text_file_path, "w", newline="") as csv_file:
                csv_writer = csv.writer(csv_file, delimiter="\t")
                # Write headers.
                csv_writer.writerow([i[0] for i in cur.description])
                # Write data.
                csv_writer.writerows(rows)


            conn.commit()
            # Close the connection
            #conn.close()

    except KeyboardInterrupt:
        print('\n\rquit')

if __name__ == '__main__':
    run()
    print("finish")

