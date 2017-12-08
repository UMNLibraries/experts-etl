# Experts@Minnesota ETL

Moves data from UMN to Pure (Experts@Minnesota), and vice versa.

## High-level Data Flow

**TODO**: How to handle organisations, like centers and institutes, that have no UMN deptid, and exist only in Pure? Related: how to handle people who have jobs with those organisations, which also exist only in Pure? (Meaning neither of these exist in PS.) Will any of the syncing options for Pure uploads overwrite that data that we created in Pure, if we're not careful? Also, how do we handle cases where a person leaves UMN, but had a job at one of these organisations? Can we automatically alert center/insitute administrators about the situation?

* Create "all jobs new", by subtracting the "all jobs previous" snapshot from "all jobs current".
  * Create "all jobs deferred", by subtracting from "all jobs new" any jobs where "dept id" exists in "pure internal orgs", i.e., the org already exists in Pure. (The org must exist before we can add the job to Pure.)
    * Set "defer" to "Y", and "defer reason" to "Org with $deptid does not yet exist in Pure" in each corresponding "all jobs new" record.
    * Add all emplids to "person changes deferred".
    * Add all deptids to "orgs to be added to Pure".
  * For all other "all jobs new", set "defer" to "N".
* Create "emplids new", by subtracting the distinct emplids in the "all jobs previous" snapshot from the distinct emplids in "all jobs current".
  * For "all jobs new" where emplid is in "emplids new", set "person change description" to "add".
  * For all other "all jobs new", set "person change description" to "update".
* Create "emplids removed", by subtracting the distinct emplids from "all jobs new" from the distinct emplids in the "all jobs previous" snapshot.
  * For "all jobs previous" where emplid is in "emplids removed", add a record to "all jobs new", with a "person change description" of "remove".
  * Not sure "remove" is the best language here, because we should never remove persons from Pure. The most we will do is discontinue refining their profiles.
* Add "all jobs new" to the "all jobs history" table, along with a timestamp.
* Add "all jobs new" emplids to "persons needing new Pure records", _except_ for those emplids in "person changes deferred".
* Add "emplids new" to a list of "all emplids", along with a timestamp.
* Create "demographics new", by subtracting the "demographics previous" snapshot from "demographics current", which queries demographics for "all emplids".
  * For all emplids in "person changes deferred", set "defer" to "Y", and "defer reason" to "Org with $deptid does not yet exist in Pure". For all other "demographics new", set "defer" to "N".
  * For all emplids in the "demographics history" table, set "change description" to "update". For all other emplids, set "change description" to "add".
* Add "demographics new" to the "demographics history" table, along with a timestamp.
* Add "demographics new" emplids to "persons needing new Pure records", if they're not already there, _and_ if they're not in "person changes deferred".
* For all emplids in "persons needing new Pure records", generate new Pure records, using data from "all jobs current" and "demographics current".
