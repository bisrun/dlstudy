import json
import requests

def parse_data(data_json):
    tmp_data_json = json.loads(data_json)

    poi_str = ''
    lcode_nm = ''
    epoi_x = ''
    epoi_y = ''
    poi_x = ''
    poi_y = ''

    if tmp_data_json['ItemCnt'] == '1':
        item = tmp_data_json['Item'][0]
        poi_str = item['PoiStr']
        lcode_nm = item['LCodeNm']
        epoi_x = item['EPoiX']
        epoi_y = item['EPoiY']
        poi_x = item['PoiX']
        poi_y = item['PoiY']

    return poi_str, lcode_nm, epoi_x, epoi_y, poi_x, poi_y
def get_coordinate(loc):
    url = 'http://searchtest.atlan.co.kr/geocode.jsp'
    params = {'SchString': loc, 'SchType' : 20, 'ResPerPage': 1, 'IsTest': '1'}
    res = requests.get(url, params=params, timeout=10, headers={'Connection':'close'})
    if res.status_code == 200:
        return res.text
    else:
        return None

start_location = '서울시 송파구 송파동'
result_start_loc_json = get_coordinate(start_location)

if result_start_loc_json is not None:
    poi_str_start, lcode_nm_start, epoi_x_start, epoi_y_start, poi_x_start, poi_y_start = parse_data(result_start_loc_json)
    print('poi_str_start : ', poi_str_start, 'lcode_nm_start : ', lcode_nm_start, 'epoi_x_start : ', epoi_x_start, 'epoi_y_start : '
          , 'poi_x_start : ', poi_x_start, 'poi_y_start : ', poi_y_start)