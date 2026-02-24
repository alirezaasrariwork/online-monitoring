# Full backup of everything (all organizations & buckets)
influx backup /path/to/backup-directory

# Backup only specific organization
influx backup \
  --org YourOrgName \
  /path/to/backup-dir

# Backup only one bucket (most common real-world use-case)
influx backup \
  --bucket your-bucket-name \
  --org YourOrgName \
  ./backups/$(date +%Y%m%d_%H%M%S)



  # Restore everything into a fresh / empty InfluxDB 2.x instance
influx restore /path/to/backup-directory

# Restore only one bucket (very useful for migrations or recovery of single dataset)
influx restore \
  --bucket your-bucket-name \
  --org YourOrgName \
  /path/to/backup-dir