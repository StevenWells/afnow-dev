#!/bin/bash
date
source /etc/profile.d/conda.sh
conda activate py37



# Define the start and end dates
start_date="2020-12-01 00:45:00"
end_date="2020-12-31 23:45:00"

# Convert start and end dates to seconds since epoch
start_epoch=$(date -d "$start_date" +%s)
end_epoch=$(date -d "$end_date" +%s)


# Loop over dates at 15-minute intervals
current_epoch=$start_epoch
while [ $current_epoch -le $end_epoch ]; do
    # Format the current date as YYYYMMDDhhmm
    formatted_date=$(date -d "@$current_epoch" +%Y%m%d%H%M)

    echo $formatted_date
    python /home/stewells/AfricaNowcasting/rt_code/sat_transfer.py historical --startDate "$formatted_date" --endDate "$formatted_date" --fStruct YM --feed africa_cloud

    # Increment the current date by 15 minutes (900 seconds)
    current_epoch=$((current_epoch + 900))
done

#