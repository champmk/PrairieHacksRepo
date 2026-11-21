"""
Ellucian Course Catalog Collection Example
=========================================

PURPOSE
-------
This file documents the reverse-engineered API workflow discovered during
analysis of an Ellucian Self-Service catalog installation.

CORE ENDPOINTS
--------------
1. POST /Student/Courses/PostSearchCriteria
   Performs catalog searches and returns CourseFullModels.

2. POST /Student/Courses/Sections
   Retrieves section offerings for a course using MatchingSectionIds.

3. POST /Student/Courses/SectionDetails
   Retrieves detailed metadata for a specific section.

WORKFLOW
--------
Search
  -> CourseFullModels
      -> MatchingSectionIds
          -> Sections
              -> SectionDetails (optional)

EXAMPLE SEARCH PAYLOAD
----------------------
{
    "keyword": "CSC-151",
    "terms": ["2027/SP"],
    "subjects": ["CSC"],
    "pageNumber": 1,
    "quantityPerPage": 30
}

AUTHENTICATION
--------------
In production, use requests.Session() and authenticate through the
institution's normal login process. Reuse cookies established by the
authenticated browser session.

This demonstration file contains MOCK DATA based on captured responses.
Replace the mocked responses with real requests once authentication is
implemented.
"""

from pprint import pprint


def search_courses():
    return {
        "CourseFullModels": [
            {
                "Id": "5044",
                "SubjectCode": "CSC",
                "Number": "151",
                "Title": "Functional Prob Solving w/lab",
                "MatchingSectionIds": ["99067", "99068"],
                "HasSections": True,
            }
        ]
    }


def get_sections(course_id, section_ids):
    return {
        "SectionsRetrieved": {
            "TermsAndSections": [
                {
                    "Term": {"Code": "2027/SP", "Description": "Spring 2027"},
                    "Sections": [
                        {
                            "Section": {
                                "Id": "99067",
                                "CourseName": "CSC-151",
                                "Number": "01",
                                "Available": 10,
                                "Capacity": 24,
                            },
                            "FacultyDisplay": "Samuel Rebelsky",
                        }
                    ],
                }
            ]
        }
    }


def get_section_details(section_id):
    return {
        "Id": section_id,
        "CourseName": "CSC-151",
        "AvailabilityDisplay": "10 / 14 / 24 / 0",
        "InstructorItems": [{"Name": "Samuel Rebelsky"}],
    }


if __name__ == "__main__":
    print("=== SEARCH RESULTS ===")
    search = search_courses()
    pprint(search)

    course = search["CourseFullModels"][0]

    print("=== SECTION QUERY ===")
    sections = get_sections(course["Id"], course["MatchingSectionIds"])
    pprint(sections)

    first_section = sections["SectionsRetrieved"]["TermsAndSections"][0]["Sections"][0]["Section"]

    print("=== SECTION DETAILS ===")
    details = get_section_details(first_section["Id"])
    pprint(details)

    print("=== PROOF OF DATA ACCESS ===")
    print(f"Course: {course['SubjectCode']}-{course['Number']}")
    print(f"Section ID: {first_section['Id']}")
    print(f"Available Seats: {first_section['Available']}")
    print(f"Instructor: {details['InstructorItems'][0]['Name']}")
