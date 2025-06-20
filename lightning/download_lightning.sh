#!/usr/bin/sh

OUTDIR='/mnt/scratch/stewells/MTG_LI0691'
collection='EO:EUM:DAT:0691'
/home/stewells/AfricaNowcasting/eumdac/eumdac download -c $collection -s `date -u -d "-1hour" "+%Y-%m-%dT%H:%M"` -y -o $OUTDIR

zfiles=`ls $OUTDIR/*.zip`

for zfile in $zfiles
do
  unzip -n $zfile -d $OUTDIR 
  rm $zfile 
  rm $OUTDIR/*TRAIL*.nc
  rm $OUTDIR/*.jpg
done

find $OUTDIR -type f -mmin -2 -exec chmod a+r {} +