from sqlalchemy import func
from models import db, MenuHours, StoreStatus, Timezone
import pandas as pd

def load_data_from_csv():
    if MenuHours.query.first() or StoreStatus.query.first() or Timezone.query.first():
        print("Skipping CSV load")
        return
    
    menu_hours_df = pd.read_csv('data/MenuHours.csv')
    print("Loading hours for each store...")
    for _, row in menu_hours_df.iterrows():
        menu_hour = MenuHours(
            store_id=row['store_id'],
            dayOfWeek=row['day'],
            start_time_local=pd.to_datetime(row['start_time_local']).time(),
            end_time_local=pd.to_datetime(row['end_time_local']).time()
        )
        db.session.add(menu_hour)
    
    i = 0
    store_status_df = pd.read_csv('data/StoreStatus.csv')
    print("Loading store status...")
    for _, row in store_status_df.iterrows():
        print(i)
        i+= 1
        store_status = StoreStatus(
            store_id=row['store_id'],
            timestamp_utc=pd.to_datetime(row['timestamp_utc']),
            status=row['status']
        )
        db.session.add(store_status)
    
    timezone_df = pd.read_csv('data/Timezone.csv')
    print("loading timezone for each store...")
    for _, row in timezone_df.iterrows():
        timezone = Timezone(
            store_id=row['store_id'],
            timezone_str=row['timezone_str']
        )
        db.session.add(timezone)
    
    db.session.commit()