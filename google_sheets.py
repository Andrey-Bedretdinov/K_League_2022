import traceback
from time import sleep
import gspread
from loguru import logger


class GoogleSheets:

    def __init__(self, key):
        try:
            gc = gspread.service_account(filename='service.json')  # Google sheets
            sh = gc.open_by_key(key)
            self.sheet = sh.get_worksheet(1)
        except:
            logger.error(f'Not connected to google\n{traceback.format_exc()}')

    def find_modified_rows(self, search_value, columns):
        modified_rows = set()
        for column in columns:
            cells = self.sheet.findall(search_value, in_column=column)
            for cell in cells:
                modified_rows.add(cell.row)
        return list(modified_rows)

    def get_row_data(self, row_number):
        return self.sheet.get(f"A{row_number}:{self.sheet.get_highest_column_letter()}{row_number}")[0]
