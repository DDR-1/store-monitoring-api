# Restaurant Monitoring System

The Restaurant Monitoring System is a backend API that helps track and generate reports for how active a store is for a given period of time. The system contains the business hours for each store in local time and a mapping for which timezone each store is in. There is also a system that polls if the store is active or not roughly every one hour.

## Data Sources

There are 3 sources of data

1. Store Status
   1. This data source contains 3 columns (`store_id, timestamp_utc, status`) where store_id is the identifier for the store, timestamp_utc is the timestamp when the status was recorded for the store and status for whether the store was active or inactive
   2. All timestamps are in **UTC**
2. Menu Hours
   1. The second data source contains the business hours of all the stores - schema of this data is `store_id, dayOfWeek(0=Monday, 6=Sunday), start_time_local, end_time_local`
   2. The store_id is the store identifier, the day of the week is the day for the hours, the start_time_local and end_time_local is the start and end time for the store during that day of the week
   3. These times are in the **local time zone**
   4. If data is missing for a store then it is open 24\*7
3. Timezone
   1. The third data source is the Timezone for the stores - schema is `store_id, timezone_str`
   2. The store_id is the identifer for the store and the timezone_str is the timezone for the store
   3. If data is missing for a store then it is America/Chicago

## Frameworks

The apis were built using flask and the database is a postgres database

## Installation

To install the required packages, run the following command in the project directory:

```
    pip install -r requirements.txt
```

Change the connection string to your postgres server in config.py

## Usage

To start the server, run the following command in the project directory:

```
    python app/app.py

```

The server will start running on http://127.0.0.1:5000

## API Documentation

The system provides two APIs:

- ### /trigger_report

  ```
  curl --location 'http://127.0.0.1:5000/trigger_report'
  ```

  This endpoint triggers the generation of a report from the data provided (stored in the database).

  - Response

  ```
  {
      "report_id": "random_string"
  }

  ```

- ### /get_report

  This endpoint returns the status of the report or the CSV.

  ```
  curl --location 'http://127.0.0.1:5000/get_report?report_id=<report-id>'
  ```

  - Response

  ```
      store_id,uptime_last_hour,downtime_last_hour,uptime_last_day,downtime_last_day,uptime_last_week,downtime_last_week
  8290301463563317096,60.0,0.0,5.0,5.0,27.5,40.0

  ```

## Logic

1. The flask app is initialized once app.py is run. First the app checks if the data sources have been loaded and loads the csv files if no data exists.

2. When the user hits the /trigger_report endpoint it takes the current time (currently set to maximum time stamp in Store Status) and passes it to the generate_report function. The generate report function generates a new id for the report and records it in the database with the path to where the file is stored and status as 'running' when the function is called.

3. The function then iterates through all the unique store ids in the Menu Hours data source to get all the store ids. It then identifies the uptime and downtime for the last 1 hour, last 1 day and last 1 week and writes them to the csv file. Once the data is writen to the the file the status is updated to 'completed'.

4. The uptime and downtime is calculated in the get_uptime_downtime function. This function accepts the current_time from the generate_report function and the duration for whether we want to find the last 1 hour, 1 day or 1 week. Using the current_time and duration, the overlapping business hours is calculated from the Menu Hours.

5. First the start time and end time is calculated for the function assuming the current_time passed is in UTC. The referential Timezone data is used to find the timezone or he store.

6. For each day in the duration, the days on which the duration falls is calculated. For each day on which the duration overlaps, the business hours for the store is queried using store_id. If no business hours are present then the store is assumed to be open 24/7.

7. For each timing that the store is open for that day, the start_time_local and end_time_local is retrieved. This time is converted to UTC based on the timzone of the store that was retrieved.

8. If the start time is greater than the end time after converting to UTC then the end time is for the next day and 1 day is added to the end time. The final start time and end time for that day is calculated by finding the maximium of the time to be checked or the store opening timings for the start time, and the minimum for the time to be checked or the store closing timings for the end time.

9. Using these timings the business hours that overlap with the duration to be checked is calculated. These timings are then passed to calculate uptime function to get uptime. This uptime is subtracted from the total business hours to find the downtime.

10. The calculate_uptime function calculates the uptime for the given time interval. First all the timestamp records of the store status is retrieved. Then it calculates the uptime based on the start that is less, the middle complete hours and the end that is extra

    1. For the partial start, the function checks if there exists a timestamp during that hour. if the store is active then the current time to the nearest hour is considered active for the store. For example if the start range is at 13:17 the 43 minutes is added to the uptime.
    2. For the middle hours 60 minutes is added as each complete hour is in the duration.
    3. For the partial end, the function calculates the nearest previous hour to the end time to check if the store is active or not during that time. For example if the end time is 15:35 and there is a status record between 15:00 and 15:35 then 35 minutes is added to the uptime.

11. Once the uptime, downtime is calculated for the 3 time intervals, it is written into a csv file and the status is marked as complete.

12. The /get_report endpoint accepts the report id as a parameter. If the report id is present in the request parameter and in the data base, it checks if the report is in running status or in completed. If it is in running status - it returns a response that it is in running status and if it is completed then it returns a csv file with the report as an attachment
