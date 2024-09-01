from sqlalchemy import func, distinct
from models import db, StoreStatus, MenuHours, Timezone, Report
from datetime import datetime, timedelta, time
import tempfile
import os
import pytz
import csv

def generate_report(app, current_time, report_id):
    with app.app_context():
        try:
            store_ids = db.session.query(distinct(MenuHours.store_id)).all()
            store_ids = [store_id[0] for store_id in store_ids]
            store_ids = store_ids[0:5]
            
            temp_dir = tempfile.gettempdir()
            file_path = os.path.join(temp_dir, f"{report_id}.csv")
            report_record = Report(
                    report_id=report_id,
                    status="running",
                    path=file_path
                )
            db.session.add(report_record)
            db.session.commit()

            with open(file_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                
                writer.writerow([
                    'store_id',
                    'uptime_last_hour', 'downtime_last_hour',
                    'uptime_last_day', 'downtime_last_day',
                    'uptime_last_week', 'downtime_last_week'
                ])

                for store_id in store_ids:
                    uptime_last_hour, downtime_last_hour = get_uptime_downtime(store_id, current_time, 1)
                    uptime_last_day, downtime_last_day = get_uptime_downtime(store_id, current_time, 24)
                    uptime_last_week, downtime_last_week = get_uptime_downtime(store_id, current_time, 168)
                    
                    writer.writerow([
                        store_id,
                        round(uptime_last_hour, 2), round(downtime_last_hour, 2),
                        round(uptime_last_day / 60.0, 2), round(downtime_last_day / 60.0, 2),
                        round(uptime_last_week / 60.0, 2), round(downtime_last_week / 60.0, 2)
                    ])

            db.session.query(Report).filter_by(report_id=report_id).update({
                Report.status: 'completed'
            })
            db.session.commit()

            return file_path
        except Exception as e:
            return str(e)

def get_uptime_downtime(store_id, current_time, duration_hours):
    timezone_record = db.session.query(Timezone).filter_by(store_id=store_id).first()
    if timezone_record is None:
        timezone_str = "America/Chicago"
    else:
        timezone_str = timezone_record.timezone_str
    local_timezone = pytz.timezone(timezone_str)

    now_local = current_time.replace(tzinfo=pytz.utc)
    prev_local = now_local - timedelta(hours=duration_hours)
    total_business_hours = 0.0
    total_uptime = 0
    total_downtime = 0

    for day_offset in range(duration_hours // 24 + 1):
        day_to_check = (prev_local + timedelta(days=day_offset)).date()
        day_of_week = day_to_check.weekday()

        business_hours_for_day = db.session.query(MenuHours).filter(
            MenuHours.store_id == store_id,
            MenuHours.dayOfWeek == day_of_week
        ).all()
        if not business_hours_for_day:
            business_hours_for_day = [MenuHours(store_id=store_id,dayOfWeek=day_of_week,start_time_local=time(0, 0),end_time_local=time(0, 0))]

        for hours in business_hours_for_day:
            start_time_utc = local_timezone.localize(datetime.combine(day_to_check, hours.start_time_local)).astimezone(pytz.utc)
            end_time_utc = local_timezone.localize(datetime.combine(day_to_check, hours.end_time_local)).astimezone(pytz.utc)

            if start_time_utc >= end_time_utc:
                end_time_utc += timedelta(days=1)
            day_start_final = max(prev_local, start_time_utc)
            day_end_final = min(now_local, end_time_utc)
            
            overlap = (day_end_final - day_start_final).total_seconds() / 3600
            overlap = max(overlap, 0)
            
            uptime = calculate_uptime(store_id, day_start_final.replace(tzinfo=None), day_end_final.replace(tzinfo=None))
            
            total_business_hours += overlap
            total_uptime += uptime
            total_downtime += overlap * 60 - uptime

    return total_uptime, total_downtime

def calculate_uptime(store_id, start_time, end_time):
    
    total_uptime = 0

    status_records = db.session.query(StoreStatus).filter(
        StoreStatus.store_id == store_id,
        StoreStatus.timestamp_utc >= start_time,
        StoreStatus.timestamp_utc <= end_time,
        # StoreStatus.status == 'active'
    ).all()

    if not status_records:
        return total_uptime

    current_time = start_time
    while current_time < end_time:
        hour_end_time = current_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        if hour_end_time > end_time:
            hour_end_time = end_time 

        records_in_hour = [
            record for record in status_records 
            if current_time <= record.timestamp_utc < hour_end_time
        ]

        if records_in_hour:
            if current_time == start_time and start_time.minute != 0:
                uptime = (hour_end_time - start_time).total_seconds() / 60 #partial start
            elif hour_end_time == end_time and end_time.minute != 0:
                uptime = (end_time - current_time).total_seconds() / 60 #partial end
            else:
                uptime = (hour_end_time - current_time).total_seconds() / 60 #complete hour

            total_uptime += uptime

        current_time = hour_end_time

    return total_uptime 

