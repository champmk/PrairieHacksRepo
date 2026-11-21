"""
ELLUCIAN SELF-SERVICE API
MASTER DEVELOPER REFERENCE

PURPOSE
This file is a comprehensive handoff artifact documenting the reverse-engineered
catalog APIs, observed schemas, collection workflows, normalization strategy,
schedule generation concepts, and implementation recommendations.

=====================================================================
SECTION 1 - DISCOVERED ENDPOINTS
=====================================================================

1. POST /Student/Courses/PostSearchCriteria
2. POST /Student/Courses/Sections
3. POST /Student/Courses/SectionDetails

=====================================================================
SECTION 2 - SEARCH ENDPOINT
=====================================================================

Observed request:
{
  "keyword": "CSC-151",
  "terms": ["2027/SP"],
  "subjects": ["CSC"],
  "faculty": [],
  "days": [],
  "locations": [],
  "academicLevels": [],
  "courseLevels": [],
  "courseTypes": [],
  "topicCodes": [],
  "pageNumber": 1,
  "quantityPerPage": 30
}

Observed null search:
keyword=None returns a catalog page.
Pagination uses pageNumber and quantityPerPage.

Known filters:
subjects
terms
faculty
days
locations
academicLevels
courseLevels
courseTypes
topicCodes
onlineCategories
openSections
openAndWaitlistedSections

Observed response fields:
Courses
CourseFullModels
ActivePlanTerms
Faculty
Subjects
Locations
DaysOfWeek
TermFilters
TotalItems
TotalPages

Critical fields:
CourseFullModels[].Id
CourseFullModels[].MatchingSectionIds
CourseFullModels[].HasSections

=====================================================================
SECTION 3 - SECTION ENDPOINT
=====================================================================

Request:
{
  "courseId":"5044",
  "sectionIds":["99067","99068"]
}

Response root:
SectionsRetrieved.TermsAndSections

Observed fields:
Section.Id
Section.CourseName
Section.Number
Section.TermId
Section.Title
Section.Available
Section.Enrolled
Section.Capacity
Section.Waitlisted
FacultyDisplay
InstructorDetails
FormattedMeetingTimes
Meetings

=====================================================================
SECTION 4 - SECTION DETAILS
=====================================================================

Request:
{
  "sectionId":"99067",
  "studentId":null
}

Returns:
InstructorItems
TimeLocationItems
Comments
AttendanceTrackingType
SectionCourseTypes
AvailabilityDisplay
CourseName
Capacity
Available
Waitlisted

=====================================================================
SECTION 5 - OBSERVED EXAMPLES
=====================================================================

Course:
CSC-151
CourseId=5044
MatchingSectionIds=[99067,99068]

Section 99067:
Instructor=Samuel Rebelsky
Term=2027/SP
Available=10
Capacity=24
Schedule=MWF 8:00-9:20
Building=Noyce Science Ctr
Room=3813

Section 99068:
Instructor=Shawn Ong
Schedule=MWF 1:10-2:30

=====================================================================
SECTION 6 - NORMALIZED DATA MODEL
=====================================================================

Course
Section
Meeting
Instructor
Term

Suggested section schema:
{
 section_id,
 course_id,
 course_code,
 title,
 instructor,
 available,
 enrolled,
 capacity,
 waitlisted,
 meetings[]
}

=====================================================================
SECTION 7 - DATABASE DESIGN
=====================================================================

CREATE TABLE courses(...)
CREATE TABLE sections(...)
CREATE TABLE meetings(...)
CREATE TABLE instructors(...)
CREATE TABLE section_instructors(...)

=====================================================================
SECTION 8 - CONFLICT DETECTION
=====================================================================

Conflict:
shared day and overlapping times.

=====================================================================
SECTION 9 - COLLECTION WORKFLOW
=====================================================================

Search catalog
 -> CourseFullModels
 -> MatchingSectionIds
 -> Sections
 -> Normalize
 -> Persist
 -> Optional SectionDetails enrichment

=====================================================================
SECTION 10 - PRODUCTION NOTES
=====================================================================

Use requests.Session.
Persist authenticated cookies.
Cache responses.
Respect pagination.
Store raw JSON snapshots for debugging.

"""

from dataclasses import dataclass, field
from typing import List
import requests

@dataclass
class Meeting:
    days: List[int]
    start_time: str
    end_time: str
    building: str = ''
    room: str = ''

@dataclass
class Section:
    section_id: str
    course_id: str
    instructor: str
    available: int
    enrolled: int
    capacity: int
    meetings: List[Meeting] = field(default_factory=list)

class EllucianClient:
    def __init__(self, base_url:str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

    def search_courses(self,payload):
        return self.session.post(
            f'{self.base_url}/Student/Courses/PostSearchCriteria',
            json=payload
        ).json()

    def get_sections(self,course_id,section_ids):
        return self.session.post(
            f'{self.base_url}/Student/Courses/Sections',
            json={'courseId':course_id,'sectionIds':section_ids}
        ).json()

    def get_section_details(self,section_id):
        return self.session.post(
            f'{self.base_url}/Student/Courses/SectionDetails',
            json={'sectionId':section_id,'studentId':None}
        ).json()

EXAMPLE_SEARCH={
 'keyword':'CSC-151',
 'terms':['2027/SP'],
 'subjects':['CSC'],
 'pageNumber':1,
 'quantityPerPage':30
}

if __name__=='__main__':
    print('Developer reference loaded')
    print(EXAMPLE_SEARCH)
