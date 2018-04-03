import datetime

entries = [
  {
    'emplid': 'fake322',
    'empl_rcdno': '0',
    'jobcode': '9742R6',
    'jobcode_descr': 'Researcher 6',
    'deptid': '11030',
    'position_nbr': '256802',
    'effdt': datetime.datetime(2017,8,31,0,0),
    'effseq': '0',
    'job_entry_dt': datetime.datetime(2017,8,31,0,0),
    'position_entry_dt': datetime.datetime(2017,8,31,0,0),
    'last_date_worked': None,
    'empl_status': 'A',
    'job_terminated': 'N',
    'status_flg': 'H',
  },
  {
    'emplid': 'fake322',
    'empl_rcdno': '0',
    'jobcode': '9403R',
    'jobcode_descr': 'Research Assistant Professor',
    'deptid': '11030',
    'position_nbr': '256802',
    'effdt': datetime.datetime(2018,3,12,0,0),
    'effseq': '0',
    'job_entry_dt': datetime.datetime(2018,3,12,0,0),
    'position_entry_dt': datetime.datetime(2017,8,31,0,0),
    'last_date_worked': None,
    'empl_status': 'A',
    'job_terminated': 'N',
    'status_flg': 'H',
  },
  {
    'emplid': 'fake322',
    'empl_rcdno': '0',
    'jobcode': '9403R',
    'jobcode_descr': 'Research Assistant Professor',
    'deptid': '11030',
    'position_nbr': '256802',
    'effdt': datetime.datetime(2018,3,13,0,0),
    'effseq': '0',
    'job_entry_dt': datetime.datetime(2018,3,12,0,0),
    'position_entry_dt': datetime.datetime(2017,8,31,0,0),
    'last_date_worked': None,
    'empl_status': 'A',
    'job_terminated': 'N',
    'status_flg': 'C',
  },
]

stints = [entries[0:1], entries[1:],]

entry_groups = [
  {
    'position_nbr': '256802',
    'job_entry_dt': datetime.datetime(2017,8,31,0,0),
    'jobcode': '9742R6',
    'deptid': '11030',
    'entries': entries[0:1],
  },
  {
    'position_nbr': '256802',
    'jobcode': '9403R',
    'deptid': '11030',
    'job_entry_dt': datetime.datetime(2018,3,12,0,0),
    'entries': entries[1:],
  },
]

jobs = [
  {
   'deptid': '11030',
   'org_id': 'AJPAUKII',
   'empl_rcdno': '0',
   'job_title': 'Researcher 6',
   'employment_type': 'researcher',
   'staff_type': 'academic',
   'start_date': datetime.datetime(2017,8,31,0,0),
   'end_date': datetime.datetime(2018,3,12,0,0),
   'visibility': 'Public',
   'profiled': True,
  },
  {
   'deptid': '11030',
   'org_id': 'AJPAUKII',
   'empl_rcdno': '0',
   'job_title': 'Research Assistant Professor',
   'employment_type': 'research_faculty',
   'staff_type': 'academic',
   'start_date': datetime.datetime(2018,3,12,0,0),
   'end_date': None,
   'visibility': 'Public',
   'profiled': True,
  },
]
