from time import sleep
import gspread
from loguru import logger


class GoogleSheets:

    def __init__(self, key):
        try:
            gc = gspread.service_account(filename='service.json')  # Google sheets
            sh = gc.open_by_key(key)
            self.sheets = [sh.get_worksheet(0), sh.get_worksheet(1)]
        except:
            logger.error('Not connected to google')

    def get_data(self):
        for i in range(5):
            try:
                data = []
                for sheet in self.sheets:
                    data.append(sheet.get_all_records())

                for i_sh in range(len(data)):
                    link_key = list(data[i_sh][0].keys())[-1]
                    for i in range(len(data[i_sh])):
                        data[i_sh][i]['link'] = data[i_sh][i][link_key]
                        del data[i_sh][i][link_key]

                return data
            except:
                logger.error(f'Not connected to google')
                sleep(5)

    @staticmethod
    def select_data(data):
        res = []
        for sheet in data:
            sheet_new = []
            for s in sheet:
                if all(x != '' for x in [s['match_id'], s['team_1'], s['team_2'], s['link']]):
                    sheet_new.append(s)
            res.append(sheet_new)
        return res

    def get_select_data(self):
        data = self.get_data()
        return self.select_data(data)



