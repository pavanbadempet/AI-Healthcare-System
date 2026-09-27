# OMOP CDM Condition Era Logic

## Algorithm
Condition eras collapse discrete condition occurrence records into continuous episodes of illness.

- **Persistence Window**: Standard 30-day window between subsequent diagnostic events.
- **Start Date**: Earliest condition_start_date across overlapping occurrences.
- **End Date**: Latest condition_end_date or start_date + 30 days.
