# Instance local PostgreSQL

Usage and description of the instance local PostgreSQL database.

## Usages

- Advanced Python Scheduler (APScheduler) job store
- Local instance pipeline store

### APScheduler

The APScheduler is used to schedule pipeline executions on a single MAO instance. This library stores job and scheduling information in the `apscheduler_jobs` table.

### Pipeline Store

The MAO instances uses the table `pipelines` to store all pipelines that registered via the `pipeline/init` API with the instance. The following table structure is used to store these information.

Column name and purpose:
- `name` (varchar): stores the `name` field of the pipeline registration and uniquely identifies a pipeline
- `steps` (jsonb): stores the steps list of the pipeline as JSON
